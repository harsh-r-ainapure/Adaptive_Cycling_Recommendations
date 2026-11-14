import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { gunzip } from "zlib";
import { promisify } from "util";

const gunzipAsync = promisify(gunzip);

function runPython(scriptPath, ...args) {
    return new Promise((resolve, reject) => {
        const pythonCommand = process.platform === "win32" ? "py" : "python3";
        const pythonProcess = spawn(pythonCommand, [scriptPath, ...args]);
        let stderr = "";

        pythonProcess.stdout.on("data", (data) => console.log(data.toString()));
        pythonProcess.stderr.on("data", (data) => {
            stderr += data.toString();
            console.error(data.toString());
        });
        pythonProcess.on("error", reject);
        pythonProcess.on("close", (code) => {
            if (code === 0) resolve();
            else reject(new Error(`${path.basename(scriptPath)} exited with code ${code}\n${stderr}`));
        });
    });
}

function numberOrNull(value) {
    if (value === undefined || value === null || value === "") return null;
    const number = Number(value);
    return Number.isFinite(number) ? number : null;
}

function dateOrNull(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

async function decompressIfGzipped(buffer) {
    const data = Buffer.from(buffer);
    const isGzip = data.length >= 2 && data[0] === 0x1f && data[1] === 0x8b;
    if (!isGzip) return data;
    return await gunzipAsync(data);
}

// Download FIT file from Garmin Activity callback URL
async function downloadGarminFitFile(fileUrl, accessToken, fitPath) {
    const response = await axios.get(fileUrl, {
        headers: {
            Authorization: `Bearer ${accessToken}`
        },
        responseType: "arraybuffer",
        timeout: 60000
    });

    let fitBuffer = Buffer.from(response.data);
    fitBuffer = await decompressIfGzipped(fitBuffer);

    if (fitBuffer.length < 12) {
        throw new Error("Downloaded data is too small to be a FIT file");
    }

    const fitSignature = fitBuffer.subarray(8, 12).toString("ascii");
    if (fitSignature !== ".FIT") {
        console.warn(`File does not contain expected FIT signature: ${fitSignature}`);
    }

    await fs.writeFile(fitPath, fitBuffer);
    return true;
}

async function runMlPipeline(tempFolder, userID) {
    const pythonDir = path.join(process.cwd(), "python");
    console.log("Running preprocess.py...");
    await runPython(path.join(pythonDir, "preprocess.py"), userID);
    console.log("Running features.py...");
    await runPython(path.join(pythonDir, "features.py"), tempFolder, userID);
    console.log("Running fatigue.py...");
    await runPython(path.join(pythonDir, "fatigue.py"), userID);
    console.log("Running capacities.py...");
    await runPython(path.join(pythonDir, "capacities.py"), userID);
    console.log("Running severity.py...");
    await runPython(path.join(pythonDir, "severity.py"), userID);
    console.log("Running recommendation.py...");
    await runPython(path.join(pythonDir, "recommendation.py"), userID);
}

// ============================================================
// 1. GARMIN WEBHOOK VERIFICATION (GET)
// ============================================================
const verifyGarminWebhook = (req, res) => {
    const challenge = req.query.challenge;
    if (challenge) {
        return res.status(200).type("text/plain").send(challenge);
    }
    return res.status(200).json({ message: "Garmin webhook endpoint active." });
};

// ============================================================
// 2. HANDLE INCOMING GARMIN ACTIVITY PUSH (POST)
// ============================================================
const handleGarminWebhook = async (req, res) => {
    let tempFolder = null;

    try {
        const body = req.body;
        console.log("Received Garmin webhook payload:", JSON.stringify(body, null, 2));

        const activities = body?.activities || [];

        if (activities.length === 0) {
            return res.status(200).json({ status: "received", processed: 0 });
        }

        let processedCount = 0;

        for (const activity of activities) {
            const garminId = activity.userId;
            const activityId = activity.activityId || activity.summaryId;

            if (!garminId || !activityId) continue;

            // Find user in database by Garmin ID
            const userResult = await pool.query(
                `SELECT id, access_token FROM users WHERE garmin_id = $1`,
                [garminId]
            );

            if (userResult.rows.length === 0) {
                console.warn(`User with Garmin ID ${garminId} not found in database.`);
                continue;
            }

            const user = userResult.rows[0];
            const userID = user.id;
            const accessToken = user.access_token;

            const activityDate = dateOrNull(
                activity.startTimeInSeconds ? activity.startTimeInSeconds * 1000 : activity.startTimeLocal
            );
            const distance = numberOrNull(activity.distanceInMeters);
            const movingTime = numberOrNull(activity.durationInSeconds);
            const elapsedTime = numberOrNull(activity.elapsedDurationInSeconds);
            const averageSpeed = numberOrNull(activity.averageSpeedInMetersPerSecond);
            const averagePower = numberOrNull(activity.averageWatts);
            const averageHR = numberOrNull(activity.averageHeartRateInBeatsPerMinute);
            const maxHR = numberOrNull(activity.maxHeartRateInBeatsPerMinute);
            const averageCadence = numberOrNull(activity.averageCadenceInRpm);
            const elevationGain = numberOrNull(activity.elevationGainInMeters);
            const elevationLoss = numberOrNull(activity.elevationLossInMeters);

            // Upsert into activities table
            await pool.query(
                `
                INSERT INTO activities
                (
                    user_id,
                    intervals_activity_id,
                    activity_date,
                    distance,
                    moving_time,
                    elapsed_time,
                    average_speed,
                    average_power,
                    average_hr,
                    max_hr,
                    average_cadence,
                    elevation_gain,
                    elevation_loss,
                    fit_available,
                    raw_data
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (user_id, intervals_activity_id)
                DO UPDATE SET
                    activity_date   = EXCLUDED.activity_date,
                    distance        = EXCLUDED.distance,
                    moving_time     = EXCLUDED.moving_time,
                    elapsed_time    = EXCLUDED.elapsed_time,
                    average_speed   = EXCLUDED.average_speed,
                    average_power   = EXCLUDED.power,
                    average_hr      = EXCLUDED.average_hr,
                    max_hr          = EXCLUDED.max_hr,
                    average_cadence = EXCLUDED.average_cadence,
                    elevation_gain  = EXCLUDED.elevation_gain,
                    elevation_loss  = EXCLUDED.elevation_loss,
                    fit_available   = EXCLUDED.fit_available,
                    raw_data        = EXCLUDED.raw_data
                `,
                [
                    userID,
                    String(activityId),
                    activityDate,
                    distance,
                    movingTime,
                    elapsedTime,
                    averageSpeed,
                    averagePower,
                    averageHR,
                    maxHR,
                    averageCadence,
                    elevationGain,
                    elevationLoss,
                    !!activity.callbackURL,
                    JSON.stringify(activity)
                ]
            );

            processedCount++;

            // Download FIT file if callback URL is provided
            if (activity.callbackURL) {
                tempFolder = path.join(process.cwd(), "temp", String(userID));
                await fs.mkdir(tempFolder, { recursive: true });
                const fitPath = path.join(tempFolder, `${activityId}.fit`);

                try {
                    await downloadGarminFitFile(activity.callbackURL, accessToken, fitPath);
                    // Run ML pipeline for this user
                    await runMlPipeline(tempFolder, userID);
                } catch (err) {
                    console.error(`Failed to download FIT or run ML pipeline for activity ${activityId}:`, err.message);
                }
            }
        }

        // Always return 200 immediately so Garmin doesn't retry webhook delivery
        return res.status(200).json({ status: "success", processed: processedCount });

    } catch (err) {
        console.error("Garmin webhook processing failed:", err);
        return res.status(200).json({ status: "error", message: err.message });
    } finally {
        if (tempFolder) {
            try {
                await fs.rm(tempFolder, { recursive: true, force: true });
            } catch (cleanupErr) {
                console.error("Cleanup error:", cleanupErr.message);
            }
        }
    }
};

// ============================================================
// 3. MANUAL RECENT RIDES FETCH (POST /api/sync/recent)
// ============================================================
const syncRecentRides = async (req, res) => {
    const userId = req.user.id; // From authenticate middleware

    try {
        // Fetch user's Garmin refresh token from database
        const userQuery = await pool.query(
            "SELECT refresh_token FROM users WHERE id = $1", 
            [userId]
        );
        
        if (userQuery.rows.length === 0 || !userQuery.rows[0].refresh_token) {
            return res.status(400).json({ error: "Garmin account not linked or refresh token missing." });
        }

        const refreshToken = userQuery.rows[0].refresh_token;

        // Exchange refresh token for a fresh access token from Garmin
        const tokenResponse = await axios.post("https://connect.garmin.com/oauth-reference/oauth/token", null, {
            params: {
                grant_type: "refresh_token",
                refresh_token: refreshToken,
                client_id: process.env.GARMIN_CLIENT_ID,
                client_secret: process.env.GARMIN_CLIENT_SECRET
            }
        });

        const accessToken = tokenResponse.data.access_token;

        // Fetch recent activities from Garmin API
        const activitiesResponse = await axios.get("https://apis.garmin.com/wellness-api/rest/activities", {
            headers: { Authorization: `Bearer ${accessToken}` },
            params: {
                uploadStartTime: Math.floor((Date.now() - 30 * 24 * 60 * 60 * 1000) / 1000)
            }
        });

        const recentActivities = activitiesResponse.data || [];
        let insertedCount = 0;

        for (const act of recentActivities) {
            const activityType = String(act.activityType || "").toLowerCase();
            if (!["cycling", "ride", "biking", "virtual_ride"].some(t => activityType.includes(t))) {
                continue;
            }

            const activityId = String(act.activityId);
            const activityDate = dateOrNull(
                act.startTimeInSeconds ? act.startTimeInSeconds * 1000 : act.startTimeLocal
            );

            // Insert into activities table (avoiding duplicates)
            const result = await pool.query(
                `
                INSERT INTO activities
                (
                    user_id, intervals_activity_id, activity_date, distance,
                    moving_time, elapsed_time, average_speed, average_power,
                    average_hr, max_hr, average_cadence, elevation_gain, elevation_loss
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (user_id, intervals_activity_id) DO NOTHING
                `,
                [
                    userId,
                    activityId,
                    activityDate,
                    numberOrNull(act.distanceInMeters),
                    numberOrNull(act.durationInSeconds),
                    numberOrNull(act.elapsedDurationInSeconds),
                    numberOrNull(act.averageSpeedInMetersPerSecond),
                    numberOrNull(act.averageWatts),
                    numberOrNull(act.averageHeartRateInBeatsPerMinute),
                    numberOrNull(act.maxHeartRateInBeatsPerMinute),
                    numberOrNull(act.averageCadenceInRpm),
                    numberOrNull(act.elevationGainInMeters),
                    numberOrNull(act.elevationLossInMeters)
                ]
            );

            if (result.rowCount > 0) {
                insertedCount++;
            }
        }

        return res.status(200).json({
            success: true,
            message: `Successfully synced recent rides. Added ${insertedCount} new activities.`
        });

    } catch (error) {
        console.error("Error syncing recent Garmin rides:", error.response?.data || error.message);
        return res.status(500).json({ error: "Failed to fetch recent rides from Garmin." });
    }
};

export {
    verifyGarminWebhook,
    handleGarminWebhook,
    syncRecentRides
};