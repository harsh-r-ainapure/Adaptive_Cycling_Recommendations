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
// SYNC ACTIVITIES
// ============================================================

const syncActivities = async (req, res) => {

    let tempFolder = null;

    try {

        // ====================================================
        // 1. GET LOGGED-IN USER
        // ====================================================

        const userID = req.user.id;

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

                // Go back one day so we don't miss
                // activities around the boundary.
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

            const summaryResponse = await axios.get(
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

            console.log("Intervals API status:", summaryResponse.status);

console.log(
    "Intervals raw activity count:",
    Array.isArray(summaryResponse.data)
        ? summaryResponse.data.length
        : "NOT AN ARRAY"
);

console.log(
    "Intervals activity types:",
    Array.isArray(summaryResponse.data)
        ? summaryResponse.data.map(a => ({
            id: a.id,
            type: a.type,
            name: a.name,
            start_date: a.start_date
        }))
        : summaryResponse.data
);

        } catch (error) {

            console.error(
                "Intervals API request failed:"
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
                message: "Failed to fetch activities from Intervals.icu."
            });

        }


        const allActivities =
            Array.isArray(summaryResponse.data)
                ? summaryResponse.data
                : [];


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


        // ====================================================
        // 5. KEEP ONLY CYCLING ACTIVITIES
        // ====================================================

        // const activities = allActivities.filter(
        //     (activity) =>
        //         activity.type === "Ride" ||
        //         activity.type === "VirtualRide"
        // );

        const activities = allActivities;


        console.log(
            `Intervals returned ${allActivities.length} total activities`
        );

        console.log(
    "RAW ACTIVITIES:",
    allActivities.length
);

console.log(
    "ACTIVITIES WE WILL PROCESS:",
    activities.length
);


        // ====================================================
        // 6. NOTHING TO SYNC
        // ====================================================

        if (activities.length === 0) {

            return res.status(200).json({
                message:
                    "No cycling activities found for the requested date range.",
                fetched: 0,
                inserted: 0
            });

        }


        // ====================================================
        // 7. INSERT / UPDATE ACTIVITIES
        // ====================================================

        let insertedCount = 0;


        for (const activity of activities) {

            if (!activity.id) {

                console.warn(
                    "Skipping activity without an ID."
                );

                continue;

            }


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

                    activity.id,

                    activity.start_date || null,

                    activity.distance || null,

                    activity.moving_time || null,

                    activity.elapsed_time || null,

                    activity.average_speed || null,

                    activity.icu_average_watts || null,

                    activity.average_heartrate || null,

                    activity.max_heartrate || null,

                    activity.average_cadence || null,

                    activity.total_elevation_gain || null,

                    activity.total_elevation_loss || null,

                    JSON.stringify(activity)
                ]
            );


            insertedCount++;

        }


        console.log(
            `Inserted/updated ${insertedCount} activities`
        );


        // ====================================================
        // 8. CREATE TEMP DIRECTORY FOR FIT FILES
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
        // 9. DOWNLOAD FIT FILES
        // ====================================================

        let fitCount = 0;


        for (const activity of activities) {

            if (!activity.id) {
                continue;
            }


            try {

                const fitResponse = await axios.get(
                    `https://intervals.icu/api/v1/activity/${activity.id}/file`,
                    {
                        headers: {
                            Authorization: `Bearer ${accessToken}`
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
        // 10. RUN FEATURE PREPROCESSING
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
        // 11. EXTRACT FEATURES FROM FIT FILES
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
        // 12. RUN FATIGUE MODEL
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
        // 13. RUN CAPACITY MODEL
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
        // 14. RUN SEVERITY MODEL
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
        // 15. RUN RECOMMENDATION MODEL
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
        // 16. SUCCESS
        // ====================================================

        console.log(
            "Activity sync and ML pipeline completed successfully."
        );


        return res.status(200).json({

            message:
                "Sync and analysis completed successfully.",

            fetched: activities.length,

            activities_processed: insertedCount,

            fit_files_downloaded: fitCount

        });


    } catch (err) {

        console.error(
            "Sync failed:"
        );

        console.error(err);


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