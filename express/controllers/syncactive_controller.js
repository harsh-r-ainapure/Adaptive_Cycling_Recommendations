import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { gunzip } from "zlib";
import { promisify } from "util";

const gunzipAsync = promisify(gunzip);

const GARMIN_TOKEN_URL = "https://connectapi.garmin.com/di-oauth2-service/oauth/token";

// ------------------------------------------------------------
// helpers
// ------------------------------------------------------------
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

const first = (...values) => values.find((v) => v !== undefined && v !== null);

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

// Exact cycling values from Garmin Activity API 2.1, Appendix A. (A substring match on "BIK" would wrongly accept
// BIKE_TO_RUN_TRANSITION etc.)
const CYCLING_TYPES = new Set([
    "CYCLING", "BMX", "CYCLOCROSS", "DOWNHILL_BIKING", "E_BIKE_FITNESS", "E_BIKE_MOUNTAIN",
    "E_ENDURO_MTB", "ENDURO_MTB", "GRAVEL_CYCLING", "INDOOR_CYCLING", "MOUNTAIN_BIKING",
    "RECUMBENT_CYCLING", "ROAD_BIKING", "TRACK_CYCLING", "VIRTUAL_RIDE", "HANDCYCLING", "INDOOR_HANDCYCLING"
]);
function isCycling(activityType) {
    return CYCLING_TYPES.has(String(activityType || "").toUpperCase());
}

async function decompressIfGzipped(buffer) {
    const data = Buffer.from(buffer);
    const isGzip = data.length >= 2 && data[0] === 0x1f && data[1] === 0x8b;
    if (!isGzip) return data;
    return await gunzipAsync(data);
}

// One job at a time: keeps Render memory/CPU sane and avoids two pipelines touching the same user at once.
let jobQueue = Promise.resolve();
function enqueue(job) {
    jobQueue = jobQueue.then(job).catch((err) => console.error("[Garmin] Job failed:", err.message));
    return jobQueue;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ------------------------------------------------------------
// OAuth 2.0: access tokens last ~24h, refresh tokens ~90 days
// ------------------------------------------------------------
async function refreshAccessToken(user) {
    if (!user.refresh_token || !process.env.GARMIN_CLIENT_ID || !process.env.GARMIN_CLIENT_SECRET) {
        throw new Error(
            "Garmin rejected the access token (401) and it can't be refreshed: need users.refresh_token plus " +
            "GARMIN_CLIENT_ID / GARMIN_CLIENT_SECRET env vars."
        );
    }

    const body = new URLSearchParams({
        grant_type: "refresh_token",
        client_id: process.env.GARMIN_CLIENT_ID,
        client_secret: process.env.GARMIN_CLIENT_SECRET,
        refresh_token: user.refresh_token
    });

    const { data } = await axios.post(GARMIN_TOKEN_URL, body.toString(), {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        timeout: 30000
    });

    // Garmin returns a NEW refresh token every time; the old one must be replaced.
    const newRefresh = data.refresh_token || user.refresh_token;
    await pool.query(
        `UPDATE users SET access_token = $1, refresh_token = $2 WHERE id = $3`,
        [data.access_token, newRefresh, user.id]
    );
    user.access_token = data.access_token;
    user.refresh_token = newRefresh;
    console.log(`[Garmin] Refreshed access token for user ${user.id}`);
    return data.access_token;
}

// ------------------------------------------------------------
// FIT download (callbackURL comes from an "activityFiles" push item)
// ------------------------------------------------------------
async function downloadGarminFitFile(fileUrl, user, fitPath) {
    const get = (token) =>
        axios.get(fileUrl, {
            headers: { Authorization: `Bearer ${token}` },
            responseType: "arraybuffer",
            timeout: 60000
        });

    let response;
    try {
        response = await get(user.access_token);
    } catch (err) {
        if (err.response?.status !== 401) throw err;
        response = await get(await refreshAccessToken(user));
    }

    let fitBuffer = await decompressIfGzipped(Buffer.from(response.data));

    if (fitBuffer.length < 12) {
        throw new Error("Downloaded data is too small to be a FIT file");
    }
    const fitSignature = fitBuffer.subarray(8, 12).toString("ascii");
    if (fitSignature !== ".FIT") {
        throw new Error(`Not a FIT file (signature: ${fitSignature})`);
    }

    await fs.writeFile(fitPath, fitBuffer);
}

async function runMlPipeline(tempFolder, userID) {
    const pythonDir = path.join(process.cwd(), "python");
    // NOTE: preprocess.py is NOT run here. It expects (folder, user_id) and reads summarizedActivities.json from a
    // Garmin export; in the webhook flow the activities row is already written by upsertActivity().
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

// ------------------------------------------------------------
// DB
// ------------------------------------------------------------
async function findUser(garminUserId) {
    // payload.userId is the Garmin API user id (GET /wellness-api/rest/user/id), NOT the Garmin Connect profile id.
    const result = await pool.query(`SELECT * FROM users WHERE garmin_id = $1`, [String(garminUserId)]);
    if (result.rows.length === 0) {
        console.warn(`[Garmin] No user with garmin_id=${garminUserId}. Is users.garmin_id the Garmin API userId?`);
        return null;
    }
    return result.rows[0];
}

async function upsertActivity(user, activity, activityId) {
    // Field names are the exact ones in Garmin Activity API 2.1, section 6.1 (Activity Summaries).
    // The summary has NO power field and no separate moving/elapsed time: average_power stays null here
    // (power only exists in the FIT file / Activity Details samples as powerInWatts).
    const activityDate = dateOrNull(
        activity.startTimeInSeconds ? activity.startTimeInSeconds * 1000 : null
    );
    const values = [
        user.id,
        String(activityId),
        activityDate,
        numberOrNull(activity.distanceInMeters),
        numberOrNull(activity.durationInSeconds),   // moving_time (no moving-time field in the summary)
        numberOrNull(activity.durationInSeconds),   // elapsed_time
        numberOrNull(activity.averageSpeedInMetersPerSecond),
        null,                                       // average_power: not in the summary
        numberOrNull(activity.averageHeartRateInBeatsPerMinute),
        numberOrNull(activity.maxHeartRateInBeatsPerMinute),
        numberOrNull(activity.averageBikeCadenceInRoundsPerMinute),
        numberOrNull(activity.totalElevationGainInMeters),
        numberOrNull(activity.totalElevationLossInMeters),
        JSON.stringify(activity)
    ];

    // Requires a UNIQUE index on (user_id, intervals_activity_id), see the SQL in the chat reply.
    await pool.query(
        `
        INSERT INTO activities
        (
            id, user_id, intervals_activity_id, activity_date, distance, moving_time, elapsed_time,
            average_speed, average_power, average_hr, max_hr, average_cadence,
            elevation_gain, elevation_loss, raw_data
        )
        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (user_id, intervals_activity_id)
        DO UPDATE SET
            activity_date   = EXCLUDED.activity_date,
            distance        = EXCLUDED.distance,
            moving_time     = EXCLUDED.moving_time,
            elapsed_time    = EXCLUDED.elapsed_time,
            average_speed   = EXCLUDED.average_speed,
            average_power   = EXCLUDED.average_power,
            average_hr      = EXCLUDED.average_hr,
            max_hr          = EXCLUDED.max_hr,
            average_cadence = EXCLUDED.average_cadence,
            elevation_gain  = EXCLUDED.elevation_gain,
            elevation_loss  = EXCLUDED.elevation_loss,
            raw_data        = EXCLUDED.raw_data
        `,
        values
    );
}

// The FIT push and the summary push can arrive in either order, so wait briefly for the summary row.
async function waitForActivityRow(userID, activityId, attempts = 6, delayMs = 10000) {
    for (let i = 0; i < attempts; i++) {
        const r = await pool.query(
            `SELECT id FROM activities WHERE user_id = $1 AND intervals_activity_id = $2`,
            [userID, String(activityId)]
        );
        if (r.rows.length > 0) return r.rows[0];
        if (i < attempts - 1) await sleep(delayMs);
    }
    return null;
}

// ------------------------------------------------------------
// payload handling (runs AFTER we've already answered Garmin)
// ------------------------------------------------------------
async function processSummary(activity) {
    const activityId = first(activity.activityId, activity.summaryId);
    if (!activity.userId || activityId === undefined) {
        console.warn("[Garmin] activities item without userId/activityId, skipped.");
        return;
    }
    if (!isCycling(activity.activityType)) {
        console.log(`[Garmin] Skipping ${activity.activityType} activity ${activityId} (not cycling).`);
        return;
    }
    const user = await findUser(activity.userId);
    if (!user) return;

    await upsertActivity(user, activity, activityId);
    console.log(`[Garmin] Saved cycling activity ${activityId} for user ${user.id}`);
}

async function processFile(file) {
    const activityId = first(file.activityId, file.summaryId);
    if (!file.userId || activityId === undefined || !file.callbackURL) {
        console.warn("[Garmin] activityFiles item missing userId/activityId/callbackURL, skipped.", Object.keys(file));
        return;
    }
    if (file.fileType && String(file.fileType).toUpperCase() !== "FIT") return;
    // activityFiles items carry activityType, so non-cycling files are dropped without touching the download quota.
    if (!isCycling(file.activityType)) {
        console.log(`[Garmin] Skipping ${file.activityType} file for activity ${activityId} (not cycling).`);
        return;
    }

    const user = await findUser(file.userId);
    if (!user) return;

    // Only rides that were saved as cycling by processSummary() get a FIT run: this is also our cycling filter.
    const row = await waitForActivityRow(user.id, activityId);
    if (!row) {
        console.warn(`[Garmin] FIT for ${activityId} arrived but no activities row exists (not cycling, or IDs differ). Skipped.`);
        return;
    }

    const tempFolder = path.join(process.cwd(), "temp", String(user.id), String(activityId));
    try {
        await fs.mkdir(tempFolder, { recursive: true });
        await downloadGarminFitFile(file.callbackURL, user, path.join(tempFolder, `${activityId}.fit`));
        await pool.query(
            `UPDATE activities SET fit_available = true WHERE user_id = $1 AND intervals_activity_id = $2`,
            [user.id, String(activityId)]
        );
        await runMlPipeline(tempFolder, user.id);
        console.log(`[Garmin] Pipeline finished for activity ${activityId}`);
    } catch (err) {
        // Garmin: callbackURL is valid for 24h and can be downloaded ONCE; a repeat download returns HTTP 410.
        if (err.response?.status === 410) {
            console.warn(`[Garmin] FIT for activity ${activityId} was already downloaded (410). Skipped.`);
            return;
        }
        throw err;
    } finally {
        await fs.rm(tempFolder, { recursive: true, force: true }).catch((e) =>
            console.error("Cleanup error:", e.message)
        );
    }
}

async function processPayload(body) {
    for (const activity of body.activities || []) {
        try { await processSummary(activity); }
        catch (err) { console.error("[Garmin] Summary failed:", err.message); }
    }
    for (const file of body.activityFiles || []) {
        try { await processFile(file); }
        catch (err) { console.error("[Garmin] FIT processing failed:", err.message); }
    }
}

// ============================================================
// 1. GARMIN WEBHOOK VERIFICATION (GET), harmless, kept for manual checks
// ============================================================
const verifyGarminWebhook = (req, res) => {
    const challenge = req.query.challenge;
    if (challenge) {
        return res.status(200).type("text/plain").send(challenge);
    }
    return res.status(200).json({ message: "Garmin webhook endpoint active." });
};

// ============================================================
// 2. INCOMING GARMIN PUSH (POST): ANSWER 200 FIRST, WORK AFTER
// ============================================================
const handleGarminWebhook = (req, res) => {
    const body = req.body || {};
    const raw = JSON.stringify(body);
    console.log(`[Garmin] Webhook received. keys=${Object.keys(body).join(",")} bytes=${raw.length}`);
    console.log(raw.slice(0, 4000));

    // Garmin retries / disables endpoints that don't answer 200 quickly. Never do the heavy work before this line.
    res.status(200).json({ status: "received" });

    enqueue(() => processPayload(body));
};

export {
    verifyGarminWebhook,
    handleGarminWebhook
};