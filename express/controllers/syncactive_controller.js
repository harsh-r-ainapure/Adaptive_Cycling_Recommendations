import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";
import { gunzip } from "zlib";
import { promisify } from "util";


// ============================================================
// GZIP HELPER
// ============================================================

const gunzipAsync = promisify(gunzip);


// ============================================================
// RUN PYTHON SCRIPT
// ============================================================

function runPython(scriptPath, ...args) {

    return new Promise((resolve, reject) => {

        const pythonCommand =
            process.platform === "win32"
                ? "py"
                : "python3";

        const pythonProcess = spawn(
            pythonCommand,
            [scriptPath, ...args]
        );

        let stderr = "";

        pythonProcess.stdout.on("data", (data) => {
            console.log(data.toString());
        });

        pythonProcess.stderr.on("data", (data) => {
            const message = data.toString();
            stderr += message;
            console.error(message);
        });

        pythonProcess.on("error", (error) => {
            reject(error);
        });

        pythonProcess.on("close", (code) => {

            if (code === 0) {
                resolve();
            } else {
                reject(
                    new Error(
                        `${path.basename(scriptPath)} exited with code ${code}\n${stderr}`
                    )
                );
            }

        });

    });

}


// ============================================================
// SAFE NUMBER
// ============================================================

function numberOrNull(value) {

    if (value === undefined || value === null || value === "") {
        return null;
    }

    const number = Number(value);

    return Number.isFinite(number) ? number : null;

}


// ============================================================
// SAFE DATE
// ============================================================

function dateOrNull(value) {

    if (!value) {
        return null;
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return null;
    }

    return date.toISOString();

}


// ============================================================
// DECOMPRESS FIT DATA
// ============================================================
//
// Intervals.icu returns downloaded FIT files gzip-compressed.
// We check the gzip magic bytes instead of blindly trying to
// decompress everything.
//
// gzip magic bytes: 0x1F 0x8B
//
// ============================================================

async function decompressIfGzipped(buffer) {

    const data = Buffer.from(buffer);

    const isGzip =
        data.length >= 2 &&
        data[0] === 0x1f &&
        data[1] === 0x8b;

    if (!isGzip) {
        return data;
    }

    return await gunzipAsync(data);

}


// ============================================================
// DOWNLOAD FIT FILE
// ============================================================
//
// Strategy:
//
// 1. Try original activity file:
//      /activity/{id}/file
//
// 2. If unavailable (422, 404, etc.):
//      /activity/{id}/fit-file
//
// The second endpoint generates a FIT file from Intervals.icu.
//
// Some activities (e.g. synced in via Strava, or manually
// entered) will NEVER have a FIT file available on either
// endpoint. Callers should check `fit_available` on the
// activity row before calling this, and record the outcome
// afterward via markFitAvailability() so we stop retrying
// permanently-unavailable activities on every sync.
//
// ============================================================

async function downloadFitFile(activityId, accessToken, fitPath) {

    let fitBuffer = null;

    // ATTEMPT 1: ORIGINAL ACTIVITY FILE

    try {

        const response = await axios.get(

            `https://intervals.icu/api/v1/activity/${activityId}/file`,

            {
                headers: {
                    Authorization: `Bearer ${accessToken}`
                },
                responseType: "arraybuffer",
                timeout: 60000,
                validateStatus: () => true
            }

        );

        if (response.status >= 200 && response.status < 300) {
            fitBuffer = Buffer.from(response.data);
        }

    } catch (error) {

        console.warn(
            `Original file request failed for ${activityId}: ${error.message}`
        );

    }

    // ATTEMPT 2: GENERATED FIT FILE

    if (!fitBuffer) {

        try {

            const response = await axios.get(

                `https://intervals.icu/api/v1/activity/${activityId}/fit-file`,

                {
                    headers: {
                        Authorization: `Bearer ${accessToken}`
                    },
                    responseType: "arraybuffer",
                    timeout: 60000,
                    validateStatus: () => true
                }

            );

            if (response.status >= 200 && response.status < 300) {
                fitBuffer = Buffer.from(response.data);
            }

        } catch (error) {

            console.warn(
                `Generated FIT request failed for ${activityId}: ${error.message}`
            );

        }

    }

    // NOTHING DOWNLOADED

    if (!fitBuffer) {
        throw new Error(
            `Could not obtain FIT file for activity ${activityId}`
        );
    }

    // DECOMPRESS IF NECESSARY

    fitBuffer = await decompressIfGzipped(fitBuffer);

    // BASIC FIT VALIDATION
    //
    // FIT files normally contain ".FIT" at byte 8.
    // This prevents us from accidentally saving an HTML/JSON
    // error response as a .fit file.

    if (fitBuffer.length < 12) {
        throw new Error(
            `Downloaded data for activity ${activityId} is too small to be a FIT file`
        );
    }

    const fitSignature =
        fitBuffer.subarray(8, 12).toString("ascii");

    if (fitSignature !== ".FIT") {

        console.warn(
            `Activity ${activityId} does not contain the expected FIT signature (bytes 8-12: ${fitSignature})`
        );

    }

    // WRITE TEMP FIT FILE

    await fs.writeFile(fitPath, fitBuffer);

    return true;

}


// ============================================================
// MARK FIT AVAILABILITY
// ============================================================
//
// Records whether a FIT file could be obtained for an activity,
// so future syncs skip permanently-unavailable activities
// instead of re-attempting a doomed download every time.
//
// available:
//   true  - FIT file downloaded successfully
//   false - both download attempts failed, do not retry
//
// ============================================================

async function markFitAvailability(userID, intervalsActivityId, available) {

    await pool.query(

        `
        UPDATE activities
        SET fit_available = $3
        WHERE user_id = $1
          AND intervals_activity_id = $2
        `,

        [userID, intervalsActivityId, available]

    );

}


// ============================================================
// RUN THE ML PIPELINE FOR A USER
// ============================================================
//
// Shared by both syncActivities (fresh downloads) and
// backfillMissingFeatures (catching up on activities that
// exist in the DB but never made it through the pipeline).
//
// ============================================================

async function runMlPipeline(tempFolder, userID) {

    const pythonDir =
        path.join(process.cwd(), "python");

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
// GET USER + ACCESS TOKEN
// ============================================================

async function getUserAndToken(userID) {

    const userResult = await pool.query(

        `
        SELECT
            intervals_id,
            access_token,
            has_power_meter,
            power_meter_month,
            power_meter_year

        FROM users

        WHERE id = $1
        `,

        [userID]

    );

    if (userResult.rows.length === 0) {
        return { error: { status: 404, message: "User not found." } };
    }

    const user = userResult.rows[0];

    if (!user.intervals_id) {
        return { error: { status: 400, message: "Intervals.icu account is not connected." } };
    }

    if (!user.access_token) {
        return { error: { status: 400, message: "Intervals.icu access token is missing." } };
    }

    return { user };

}


// ============================================================
// SYNC ACTIVITIES
// ============================================================

const syncActivities = async (req, res) => {

    let tempFolder = null;

    try {

        // 1. GET LOGGED-IN USER

        const userID = req.user?.id;

        if (!userID) {
            return res.status(401).json({ message: "User is not authenticated." });
        }

        console.log(`Starting activity sync for user: ${userID}`);

        // 2. GET USER + TOKEN

        const { user, error } = await getUserAndToken(userID);

        if (error) {
            return res.status(error.status).json({ message: error.message });
        }

        const accessToken = user.access_token;

        // 3. DETERMINE DATE RANGE

        const today =
            new Date().toISOString().split("T")[0];

        const activityCountResult = await pool.query(
            `SELECT COUNT(*) AS count FROM activities WHERE user_id = $1`,
            [userID]
        );

        const activityCount =
            Number(activityCountResult.rows[0].count);

        let oldest;

        if (activityCount === 0) {

            // FIRST SYNC

            if (
                user.has_power_meter &&
                user.power_meter_month != null &&
                user.power_meter_year != null
            ) {

                oldest =
                    `${user.power_meter_year}-` +
                    `${String(user.power_meter_month).padStart(2, "0")}-01`;

            } else {

                oldest = "2020-11-19";

            }

        } else {

            // INCREMENTAL SYNC

            const latestResult = await pool.query(
                `SELECT MAX(activity_date) AS latest FROM activities WHERE user_id = $1`,
                [userID]
            );

            const latest = latestResult.rows[0].latest;

            if (latest) {

                const latestDate = new Date(latest);
                latestDate.setDate(latestDate.getDate() - 1);
                oldest = latestDate.toISOString().split("T")[0];

            } else {

                oldest = "2020-11-19";

            }

        }

        console.log(`Fetching activities from ${oldest} to ${today}`);

        // 4. FETCH ACTIVITIES

        let summaryResponse;

        try {

            summaryResponse = await axios.get(

                `https://intervals.icu/api/v1/athlete/0/activities`,

                {
                    headers: {
                        Authorization: `Bearer ${accessToken}`
                    },
                    params: {
                        oldest,
                        newest: today
                    },
                    timeout: 60000
                }

            );

        } catch (error) {

            console.error(
                "Intervals API request failed:",
                error.response?.status,
                error.response?.data || error.message
            );

            return res.status(502).json({
                message: "Failed to fetch activities from Intervals.icu."
            });

        }

        // 5. READ ACTIVITIES

        const activities =
            Array.isArray(summaryResponse?.data)
                ? summaryResponse.data
                : [];

        console.log(`Intervals returned ${activities.length} activities`);

        // 6. NOTHING TO SYNC

        if (activities.length === 0) {

            return res.status(200).json({
                message: "No activities found for the requested date range.",
                fetched: 0,
                inserted: 0,
                fit_files_downloaded: 0
            });

        }

        // 7. INSERT / UPDATE ACTIVITIES

        let insertedCount = 0;

        for (const activity of activities) {

            if (!activity?.id) {
                continue;
            }

            const activityDate =
                activity.start_date_local ??
                activity.start_date ??
                activity.startDate ??
                null;

            const distance =
                activity.distance ??
                activity.distance_km ??
                null;

            const movingTime =
                activity.moving_time ??
                activity.movingTime ??
                null;

            const elapsedTime =
                activity.elapsed_time ??
                activity.elapsedTime ??
                null;

            const averageSpeed =
                activity.average_speed ??
                activity.averageSpeed ??
                null;

            const averagePower =
                activity.icu_average_watts ??
                activity.average_watts ??
                activity.average_power ??
                activity.averagePower ??
                null;

            const averageHR =
                activity.average_heartrate ??
                activity.average_hr ??
                activity.averageHeartRate ??
                null;

            const maxHR =
                activity.max_heartrate ??
                activity.max_hr ??
                activity.maxHeartRate ??
                null;

            const averageCadence =
                activity.average_cadence ??
                activity.averageCadence ??
                null;

            const elevationGain =
                activity.total_elevation_gain ??
                activity.elevation_gain ??
                activity.elevationGain ??
                null;

            const elevationLoss =
                activity.total_elevation_loss ??
                activity.elevation_loss ??
                activity.elevationLoss ??
                null;

            // ------------------------------------------------
            // FIT AVAILABILITY
            // ------------------------------------------------
            // Intervals cannot provide a FIT file for activities
            // synced in via Strava, or for manually-entered
            // activities - it only has summary metadata for
            // those, never the underlying file. We mark those
            // as false up front so we never attempt (or
            // re-attempt) a download for them.
            //
            // Anything else is left null ("unknown, try it")
            // until the download loop below confirms one way
            // or the other.
            // ------------------------------------------------

            const knownUnavailable =
                activity.source === "STRAVA";

            const fitAvailable =
                knownUnavailable ? false : null;

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

                VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)

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
                    -- Never downgrade a confirmed true/false back to unknown,
                    -- and never overwrite a confirmed false with unknown.
                    fit_available   = COALESCE(activities.fit_available, EXCLUDED.fit_available),
                    raw_data        = EXCLUDED.raw_data
                `,

                [
                    userID,
                    String(activity.id),
                    dateOrNull(activityDate),
                    numberOrNull(distance),
                    numberOrNull(movingTime),
                    numberOrNull(elapsedTime),
                    numberOrNull(averageSpeed),
                    numberOrNull(averagePower),
                    numberOrNull(averageHR),
                    numberOrNull(maxHR),
                    numberOrNull(averageCadence),
                    numberOrNull(elevationGain),
                    numberOrNull(elevationLoss),
                    fitAvailable,
                    JSON.stringify(activity)
                ]

            );

            insertedCount++;

        }

        console.log(`Inserted/updated ${insertedCount} activities`);

        // 8. CREATE TEMP FOLDER

        tempFolder = path.join(process.cwd(), "temp", userID);

        await fs.mkdir(tempFolder, { recursive: true });

        // 9. DOWNLOAD FIT FILES

        let fitCount = 0;

        for (const activity of activities) {

            if (!activity?.id) {
                continue;
            }

            const activityId = String(activity.id);

            // Skip activities we already know (from this batch,
            // via source) or have previously confirmed have no
            // FIT file available - no point burning two failed
            // API calls on something that will never succeed.

            if (activity.source === "STRAVA") {
                console.log(`Skipping ${activityId}: no FIT available (Strava-sourced).`);
                continue;
            }

            const fitPath =
                path.join(tempFolder, `${activityId}.fit`);

            try {

                await downloadFitFile(activityId, accessToken, fitPath);

                await markFitAvailability(userID, activityId, true);

                fitCount++;

            } catch (error) {

                console.error(`Could not obtain FIT for activity ${activityId}: ${error.message}`);

                await markFitAvailability(userID, activityId, false);

            }

        }

        console.log(`Downloaded ${fitCount} FIT files`);

        // 10. NO FIT FILES

        if (fitCount === 0) {

            console.warn("No FIT files were downloaded. Skipping Python ML pipeline.");

            return res.status(200).json({
                message: "Activities synced, but no FIT files were available for processing.",
                fetched: activities.length,
                activities_processed: insertedCount,
                fit_files_downloaded: 0
            });

        }

        // 11. RUN ML PIPELINE

        await runMlPipeline(tempFolder, userID);

        console.log("Activity sync and ML pipeline completed successfully.");

        return res.status(200).json({
            message: "Sync and analysis completed successfully.",
            fetched: activities.length,
            activities_processed: insertedCount,
            fit_files_downloaded: fitCount
        });

    } catch (err) {

        console.error("SYNC FAILED:", err);

        return res.status(500).json({
            message: "Sync failed.",
            error: process.env.NODE_ENV === "production" ? undefined : err.message
        });

    } finally {

        if (tempFolder) {

            try {
                await fs.rm(tempFolder, { recursive: true, force: true });
            } catch (cleanupError) {
                console.error("Failed to clean temporary FIT files:", cleanupError.message);
            }

        }

    }

};


// ============================================================
// BACKFILL MISSING FEATURES
// ============================================================
//
// Catches up on activities that already exist in the DB but
// never made it through the ML pipeline - either because their
// FIT download failed in a past run, or because the run they
// were synced in had fitCount === 0 and skipped the pipeline
// entirely.
//
// Only attempts activities where fit_available is NULL (unknown)
// or true (previously confirmed available) - never retries ones
// already confirmed to have no FIT file.
//
// ============================================================

const backfillMissingFeatures = async (req, res) => {

    let tempFolder = null;

    try {

        const userID = req.user?.id;

        if (!userID) {
            return res.status(401).json({ message: "User is not authenticated." });
        }

        console.log(`Starting backfill for user: ${userID}`);

        const { user, error } = await getUserAndToken(userID);

        if (error) {
            return res.status(error.status).json({ message: error.message });
        }

        const accessToken = user.access_token;

        // FIND ACTIVITIES MISSING DOWNSTREAM DATA

        const missingResult = await pool.query(

            `
            SELECT a.id, a.intervals_activity_id
            FROM activities a
            LEFT JOIN activity_features af ON af.activity_id = a.id
            WHERE af.id IS NULL
              AND a.user_id = $1
              AND (a.fit_available IS NULL OR a.fit_available = true)
            `,

            [userID]

        );

        const missingActivities = missingResult.rows;

        console.log(`Found ${missingActivities.length} activities missing features`);

        if (missingActivities.length === 0) {

            return res.status(200).json({
                message: "No activities need backfilling.",
                fit_files_downloaded: 0
            });

        }

        // CREATE TEMP FOLDER

        tempFolder = path.join(process.cwd(), "temp", `${userID}-backfill`);

        await fs.mkdir(tempFolder, { recursive: true });

        // DOWNLOAD FIT FILES

        let fitCount = 0;

        for (const row of missingActivities) {

            const activityId = row.intervals_activity_id;

            const fitPath =
                path.join(tempFolder, `${activityId}.fit`);

            try {

                await downloadFitFile(activityId, accessToken, fitPath);

                await markFitAvailability(userID, activityId, true);

                fitCount++;

            } catch (error) {

                console.error(`Could not obtain FIT for activity ${activityId}: ${error.message}`);

                await markFitAvailability(userID, activityId, false);

            }

        }

        console.log(`Downloaded ${fitCount} FIT files for backfill`);

        if (fitCount === 0) {

            return res.status(200).json({
                message: "Backfill found candidates, but no FIT files were available for processing.",
                fit_files_downloaded: 0
            });

        }

        // RUN ML PIPELINE

        await runMlPipeline(tempFolder, userID);

        console.log("Backfill completed successfully.");

        return res.status(200).json({
            message: "Backfill completed successfully.",
            candidates: missingActivities.length,
            fit_files_downloaded: fitCount
        });

    } catch (err) {

        console.error("BACKFILL FAILED:", err);

        return res.status(500).json({
            message: "Backfill failed.",
            error: process.env.NODE_ENV === "production" ? undefined : err.message
        });

    } finally {

        if (tempFolder) {

            try {
                await fs.rm(tempFolder, { recursive: true, force: true });
            } catch (cleanupError) {
                console.error("Failed to clean temporary FIT files:", cleanupError.message);
            }

        }

    }

};


// ============================================================
// EXPORT
// ============================================================

export {
    syncActivities,
    backfillMissingFeatures
};