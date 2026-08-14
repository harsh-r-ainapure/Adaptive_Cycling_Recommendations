import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";


// ============================================================
// RUN PYTHON SCRIPT
// ============================================================

function runPython(scriptPath, ...args) {
    return new Promise((resolve, reject) => {

        const pythonCommand =
            process.platform === "win32" ? "py" : "python3";

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
// SAFE NUMBER HELPER
// ============================================================

function numberOrNull(value) {

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {
        return null;
    }

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : null;
}


// ============================================================
// SAFE DATE HELPER
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
// SYNC ACTIVITIES
// ============================================================

const syncActivities = async (req, res) => {

    let tempFolder = null;

    try {

        // ====================================================
        // 1. GET LOGGED-IN USER
        // ====================================================

        const userID = req.user?.id;

        if (!userID) {

            return res.status(401).json({
                message: "User is not authenticated."
            });

        }

        console.log(
            `Starting activity sync for user: ${userID}`
        );


        // ====================================================
        // 2. GET USER'S INTERVALS ACCOUNT DETAILS
        // ====================================================

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

            return res.status(404).json({
                message: "User not found."
            });

        }


        const user = userResult.rows[0];

        const intervalsId = user.intervals_id;
        const accessToken = user.access_token;


        if (!intervalsId) {

            return res.status(400).json({
                message: "Intervals.icu account is not connected."
            });

        }


        if (!accessToken) {

            return res.status(400).json({
                message: "Intervals.icu access token is missing."
            });

        }


        console.log(
            `Intervals athlete ID: ${intervalsId}`
        );


        // ====================================================
        // 3. DETERMINE DATE RANGE
        // ====================================================

        const today = new Date()
            .toISOString()
            .split("T")[0];


        const activityCountResult = await pool.query(
            `
            SELECT COUNT(*) AS count
            FROM activities
            WHERE user_id = $1
            `,
            [userID]
        );


        const activityCount =
            Number(activityCountResult.rows[0].count);


        let oldest;


        // ----------------------------------------------------
        // FIRST SYNC
        // ----------------------------------------------------

        if (activityCount === 0) {

            if (
                user.has_power_meter &&
                user.power_meter_month != null &&
                user.power_meter_year != null
            ) {

                oldest =
                    `${user.power_meter_year}-` +
                    `${String(user.power_meter_month).padStart(2, "0")}-01`;

            } else {

                // Historical fallback
                oldest = "2020-11-19";

            }

        }


        // ----------------------------------------------------
        // INCREMENTAL SYNC
        // ----------------------------------------------------

        else {

            const latestResult = await pool.query(
                `
                SELECT MAX(activity_date) AS latest
                FROM activities
                WHERE user_id = $1
                `,
                [userID]
            );


            const latest =
                latestResult.rows[0].latest;


            if (latest) {

                const latestDate = new Date(latest);

                latestDate.setDate(
                    latestDate.getDate() - 1
                );

                oldest = latestDate
                    .toISOString()
                    .split("T")[0];

            } else {

                oldest = "2020-11-19";

            }

        }


        console.log(
            `Fetching activities from ${oldest} to ${today}`
        );


        // ====================================================
        // 4. FETCH ACTIVITIES FROM INTERVALS
        // ====================================================

        let summaryResponse;


        try {

            // IMPORTANT:
            // DO NOT PUT "const" HERE.
            //
            // We declared summaryResponse above so that
            // it remains available after this try block.

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


            console.log(
                "Intervals API status:",
                summaryResponse.status
            );


        } catch (error) {

            console.error(
                "Intervals API request failed."
            );


            if (error.response) {

                console.error(
                    "Status:",
                    error.response.status
                );

                console.error(
                    "Response:",
                    error.response.data
                );

            } else {

                console.error(
                    error.message
                );

            }


            return res.status(502).json({
                message:
                    "Failed to fetch activities from Intervals.icu."
            });

        }


        // ====================================================
        // 5. SAFELY READ API RESPONSE
        // ====================================================

        const allActivities =
            Array.isArray(summaryResponse?.data)
                ? summaryResponse.data
                : [];


        console.log(
            "Intervals raw activity count:",
            allActivities.length
        );


        // ====================================================
        // DEBUG FIRST RAW ACTIVITY
        // ====================================================

        if (allActivities.length > 0) {

            console.log(
                "========== FIRST RAW ACTIVITY =========="
            );

            console.log(
                JSON.stringify(
                    allActivities[0],
                    null,
                    2
                )
            );

            console.log(
                "========================================"
            );

        }


        // ====================================================
        // DEBUG ACTIVITY IDs
        // ====================================================

        console.log(
            "Intervals activity IDs:"
        );

        console.log(
            allActivities.map(
                activity => activity?.id
            )
        );


        // ====================================================
        // 6. KEEP ACTIVITIES
        // ====================================================
        //
        // We are intentionally NOT filtering by type yet.
        //
        // Your previous logs showed:
        //
        // type: undefined
        //
        // So filtering by activity.type right now could
        // incorrectly remove every activity.
        //
        // Once we inspect the real raw object, we can add
        // an exact cycling filter if necessary.

        const activities = allActivities;


        console.log(
            `Intervals returned ${allActivities.length} total activities`
        );

        console.log(
            `ACTIVITIES WE WILL PROCESS: ${activities.length}`
        );


        // ====================================================
        // 7. NOTHING TO SYNC
        // ====================================================

        if (activities.length === 0) {

            return res.status(200).json({
                message:
                    "No activities found for the requested date range.",

                fetched: 0,

                inserted: 0,

                fit_files_downloaded: 0
            });

        }


        // ====================================================
        // 8. INSERT / UPDATE ACTIVITIES
        // ====================================================

        let insertedCount = 0;


        for (const activity of activities) {

            if (!activity?.id) {

                console.warn(
                    "Skipping activity without an ID."
                );

                continue;

            }


            // ------------------------------------------------
            // INTERVALS FIELD MAPPING
            // ------------------------------------------------
            //
            // Keep multiple fallbacks because the exact
            // activity payload can vary depending on source.
            //
            // raw_data always stores the complete API object.

            const activityDate =
                activity.start_date_local ||
                activity.start_date ||
                activity.startDate ||
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


            console.log(
                `Processing activity ${activity.id}`
            );


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
                    raw_data
                )

                VALUES
                (
                    $1,
                    $2,
                    $3,
                    $4,
                    $5,
                    $6,
                    $7,
                    $8,
                    $9,
                    $10,
                    $11,
                    $12,
                    $13,
                    $14
                )

                ON CONFLICT
                (
                    user_id,
                    intervals_activity_id
                )

                DO UPDATE SET

                    activity_date =
                        EXCLUDED.activity_date,

                    distance =
                        EXCLUDED.distance,

                    moving_time =
                        EXCLUDED.moving_time,

                    elapsed_time =
                        EXCLUDED.elapsed_time,

                    average_speed =
                        EXCLUDED.average_speed,

                    average_power =
                        EXCLUDED.average_power,

                    average_hr =
                        EXCLUDED.average_hr,

                    max_hr =
                        EXCLUDED.max_hr,

                    average_cadence =
                        EXCLUDED.average_cadence,

                    elevation_gain =
                        EXCLUDED.elevation_gain,

                    elevation_loss =
                        EXCLUDED.elevation_loss,

                    raw_data =
                        EXCLUDED.raw_data
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

                    JSON.stringify(activity)
                ]
            );


            insertedCount++;

        }


        console.log(
            `Inserted/updated ${insertedCount} activities`
        );


        // ====================================================
        // 9. CREATE TEMP DIRECTORY FOR FIT FILES
        // ====================================================

        tempFolder = path.join(
            process.cwd(),
            "temp",
            userID
        );


        await fs.mkdir(
            tempFolder,
            {
                recursive: true
            }
        );


        console.log(
            `FIT temporary folder: ${tempFolder}`
        );


        // ====================================================
        // 10. DOWNLOAD FIT FILES
        // ====================================================

        let fitCount = 0;


        for (const activity of activities) {

            if (!activity?.id) {
                continue;
            }


            try {

                console.log(
                    `Downloading FIT for activity ${activity.id}...`
                );


                const fitResponse = await axios.get(
                    `https://intervals.icu/api/v1/activity/${activity.id}/file`,
                    {
                        headers: {
                            Authorization:
                                `Bearer ${accessToken}`
                        },

                        responseType: "arraybuffer",

                        timeout: 60000
                    }
                );


                const fitPath = path.join(
                    tempFolder,
                    `${activity.id}.fit`
                );


                await fs.writeFile(
                    fitPath,
                    fitResponse.data
                );


                fitCount++;


                console.log(
                    `Saved FIT: ${activity.id}.fit`
                );


            } catch (error) {

                console.error(
                    `Failed to download FIT for activity ${activity.id}:`,
                    error.response?.status ||
                    error.message
                );

            }

        }


        console.log(
            `Downloaded ${fitCount} FIT files`
        );


        // ====================================================
        // 11. IF NO FIT FILES WERE AVAILABLE
        // ====================================================

        if (fitCount === 0) {

            console.warn(
                "No FIT files were downloaded. Skipping Python ML pipeline."
            );


            return res.status(200).json({

                message:
                    "Activities synced, but no FIT files were available for processing.",

                fetched:
                    activities.length,

                activities_processed:
                    insertedCount,

                fit_files_downloaded:
                    0

            });

        }


        // ====================================================
        // 12. RUN PREPROCESSING
        // ====================================================

        const preprocessPath = path.join(
            process.cwd(),
            "python",
            "preprocess.py"
        );


        console.log(
            "Running preprocess.py..."
        );


        await runPython(
            preprocessPath,
            userID
        );


        // ====================================================
        // 13. EXTRACT FEATURES
        // ====================================================

        const featuresPath = path.join(
            process.cwd(),
            "python",
            "features.py"
        );


        console.log(
            "Running features.py..."
        );


        await runPython(
            featuresPath,
            tempFolder,
            userID
        );


        // ====================================================
        // 14. RUN FATIGUE MODEL
        // ====================================================

        const fatiguePath = path.join(
            process.cwd(),
            "python",
            "fatigue.py"
        );


        console.log(
            "Running fatigue.py..."
        );


        await runPython(
            fatiguePath,
            userID
        );


        // ====================================================
        // 15. RUN CAPACITY MODEL
        // ====================================================

        const capacityPath = path.join(
            process.cwd(),
            "python",
            "capacities.py"
        );


        console.log(
            "Running capacities.py..."
        );


        await runPython(
            capacityPath,
            userID
        );


        // ====================================================
        // 16. RUN SEVERITY MODEL
        // ====================================================

        const severityPath = path.join(
            process.cwd(),
            "python",
            "severity.py"
        );


        console.log(
            "Running severity.py..."
        );


        await runPython(
            severityPath,
            userID
        );


        // ====================================================
        // 17. RUN RECOMMENDATION MODEL
        // ====================================================

        const recommendationPath = path.join(
            process.cwd(),
            "python",
            "recommendation.py"
        );


        console.log(
            "Running recommendation.py..."
        );


        await runPython(
            recommendationPath,
            userID
        );


        // ====================================================
        // 18. SUCCESS
        // ====================================================

        console.log(
            "Activity sync and ML pipeline completed successfully."
        );


        return res.status(200).json({

            message:
                "Sync and analysis completed successfully.",

            fetched:
                activities.length,

            activities_processed:
                insertedCount,

            fit_files_downloaded:
                fitCount

        });


    } catch (err) {

        console.error(
            "========================================"
        );

        console.error(
            "SYNC FAILED"
        );

        console.error(err);

        console.error(
            "========================================"
        );


        return res.status(500).json({

            message:
                "Sync failed.",

            error:
                process.env.NODE_ENV === "production"
                    ? undefined
                    : err.message

        });


    } finally {

        // ====================================================
        // ALWAYS DELETE TEMP FIT FILES
        // ====================================================

        if (tempFolder) {

            try {

                await fs.rm(
                    tempFolder,
                    {
                        recursive: true,
                        force: true
                    }
                );


                console.log(
                    "Temporary FIT files deleted."
                );


            } catch (cleanupError) {

                console.error(
                    "Failed to clean temporary FIT files:",
                    cleanupError.message
                );

            }

        }

    }

};


export {
    syncActivities
};