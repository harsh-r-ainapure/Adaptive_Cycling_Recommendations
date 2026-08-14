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

            console.log(
                data.toString()
            );

        });


        pythonProcess.stderr.on("data", (data) => {

            const message =
                data.toString();

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

    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        return null;

    }


    const number =
        Number(value);


    return Number.isFinite(number)
        ? number
        : null;

}


// ============================================================
// SAFE DATE
// ============================================================

function dateOrNull(value) {

    if (!value) {

        return null;

    }


    const date =
        new Date(value);


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

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
// gzip magic bytes:
// 0x1F 0x8B
//
// ============================================================

async function decompressIfGzipped(buffer) {

    const data =
        Buffer.from(buffer);


    const isGzip =
        data.length >= 2 &&
        data[0] === 0x1f &&
        data[1] === 0x8b;


    if (!isGzip) {

        return data;

    }


    console.log(
        "FIT response is gzip compressed. Decompressing..."
    );


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
// ============================================================

async function downloadFitFile(
    activityId,
    accessToken,
    fitPath
) {

    let fitBuffer = null;


    // ========================================================
    // ATTEMPT 1
    // ORIGINAL ACTIVITY FILE
    // ========================================================

    try {

        console.log(
            `Downloading original FIT/file for activity ${activityId}...`
        );


        const response =
            await axios.get(

                `https://intervals.icu/api/v1/activity/${activityId}/file`,

                {
                    headers: {
                        Authorization:
                            `Bearer ${accessToken}`
                    },

                    responseType:
                        "arraybuffer",

                    timeout:
                        60000,

                    validateStatus:
                        () => true
                }

            );


        console.log(
            `Original file response for ${activityId}: ${response.status}`
        );


        if (
            response.status >= 200 &&
            response.status < 300
        ) {

            fitBuffer =
                Buffer.from(
                    response.data
                );


            console.log(
                `Original activity file downloaded for ${activityId}`
            );

        } else {

            console.warn(
                `Original file unavailable for ${activityId}: HTTP ${response.status}`
            );

        }


    } catch (error) {

        console.warn(
            `Original file request failed for ${activityId}:`,
            error.message
        );

    }


    // ========================================================
    // ATTEMPT 2
    // GENERATED FIT FILE
    // ========================================================

    if (!fitBuffer) {

        try {

            console.log(
                `Trying generated FIT for activity ${activityId}...`
            );


            const response =
                await axios.get(

                    `https://intervals.icu/api/v1/activity/${activityId}/fit-file`,

                    {
                        headers: {
                            Authorization:
                                `Bearer ${accessToken}`
                        },

                        responseType:
                            "arraybuffer",

                        timeout:
                            60000,

                        validateStatus:
                            () => true
                    }

                );


            console.log(
                `Generated FIT response for ${activityId}: ${response.status}`
            );


            if (
                response.status >= 200 &&
                response.status < 300
            ) {

                fitBuffer =
                    Buffer.from(
                        response.data
                    );


                console.log(
                    `Generated FIT downloaded for ${activityId}`
                );

            } else {

                console.error(
                    `Generated FIT unavailable for ${activityId}: HTTP ${response.status}`
                );

            }


        } catch (error) {

            console.error(
                `Generated FIT request failed for ${activityId}:`,
                error.message
            );

        }

    }


    // ========================================================
    // NOTHING DOWNLOADED
    // ========================================================

    if (!fitBuffer) {

        throw new Error(
            `Could not obtain FIT file for activity ${activityId}`
        );

    }


    // ========================================================
    // DECOMPRESS IF NECESSARY
    // ========================================================

    fitBuffer =
        await decompressIfGzipped(
            fitBuffer
        );


    // ========================================================
    // BASIC FIT VALIDATION
    // ========================================================
    //
    // FIT files normally contain ".FIT" at byte 8.
    //
    // This prevents us from accidentally saving an HTML/JSON
    // error response as a .fit file.
    //
    // ========================================================

    if (
        fitBuffer.length < 12
    ) {

        throw new Error(
            `Downloaded data for activity ${activityId} is too small to be a FIT file`
        );

    }


    const fitSignature =
        fitBuffer
            .subarray(8, 12)
            .toString("ascii");


    if (
        fitSignature !== ".FIT"
    ) {

        console.warn(
            `Warning: activity ${activityId} does not contain the expected FIT signature.`
        );

        console.warn(
            `Bytes 8-12: ${fitSignature}`
        );

    }


    // ========================================================
    // WRITE TEMP FIT FILE
    // ========================================================

    await fs.writeFile(
        fitPath,
        fitBuffer
    );


    console.log(
        `Saved temporary FIT: ${fitPath}`
    );


    return true;

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

        const userID =
            req.user?.id;


        if (!userID) {

            return res.status(401).json({
                message:
                    "User is not authenticated."
            });

        }


        console.log(
            "========================================"
        );

        console.log(
            `Starting activity sync for user: ${userID}`
        );

        console.log(
            "========================================"
        );


        // ====================================================
        // 2. GET USER
        // ====================================================

        const userResult =
            await pool.query(

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


        if (
            userResult.rows.length === 0
        ) {

            return res.status(404).json({

                message:
                    "User not found."

            });

        }


        const user =
            userResult.rows[0];


        const intervalsId =
            user.intervals_id;


        const accessToken =
            user.access_token;


        if (!intervalsId) {

            return res.status(400).json({

                message:
                    "Intervals.icu account is not connected."

            });

        }


        if (!accessToken) {

            return res.status(400).json({

                message:
                    "Intervals.icu access token is missing."

            });

        }


        console.log(
            `Intervals athlete ID: ${intervalsId}`
        );


        // ====================================================
        // 3. DETERMINE DATE RANGE
        // ====================================================

        const today =
            new Date()
                .toISOString()
                .split("T")[0];


        const activityCountResult =
            await pool.query(

                `
                SELECT COUNT(*) AS count

                FROM activities

                WHERE user_id = $1
                `,

                [userID]

            );


        const activityCount =
            Number(
                activityCountResult.rows[0].count
            );


        let oldest;


        // ====================================================
        // FIRST SYNC
        // ====================================================

        if (
            activityCount === 0
        ) {

            if (
                user.has_power_meter &&
                user.power_meter_month != null &&
                user.power_meter_year != null
            ) {

                oldest =
                    `${user.power_meter_year}-` +
                    `${String(
                        user.power_meter_month
                    ).padStart(2, "0")}-01`;

            } else {

                oldest =
                    "2020-11-19";

            }

        }


        // ====================================================
        // INCREMENTAL SYNC
        // ====================================================

        else {

            const latestResult =
                await pool.query(

                    `
                    SELECT
                        MAX(activity_date) AS latest

                    FROM activities

                    WHERE user_id = $1
                    `,

                    [userID]

                );


            const latest =
                latestResult.rows[0].latest;


            if (latest) {

                const latestDate =
                    new Date(latest);


                latestDate.setDate(
                    latestDate.getDate() - 1
                );


                oldest =
                    latestDate
                        .toISOString()
                        .split("T")[0];

            } else {

                oldest =
                    "2020-11-19";

            }

        }


        console.log(
            `Fetching activities from ${oldest} to ${today}`
        );


        // ====================================================
        // 4. FETCH ACTIVITIES
        // ====================================================

        let summaryResponse;


        try {

            // IMPORTANT:
            //
            // No "const" here.
            //
            // We need the outer summaryResponse variable.

            summaryResponse =
                await axios.get(

                    `https://intervals.icu/api/v1/athlete/0/activities`,

                    {
                        headers: {

                            Authorization:
                                `Bearer ${accessToken}`

                        },

                        params: {

                            oldest,
                            newest: today

                        },

                        timeout:
                            60000

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


            if (
                error.response
            ) {

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
        // 5. READ ACTIVITIES
        // ====================================================

        const allActivities =
            Array.isArray(
                summaryResponse?.data
            )
                ? summaryResponse.data
                : [];


        console.log(
            "Intervals raw activity count:",
            allActivities.length
        );


        // ====================================================
        // DEBUG FIRST RAW ACTIVITY
        // ====================================================

        if (
            allActivities.length > 0
        ) {

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
        // DEBUG ACTIVITY IDs + TYPES + FILE TYPES
        // ====================================================

        console.log(
            "Intervals activity summary:"
        );


        console.log(

            allActivities.map(
                activity => ({

                    id:
                        activity?.id,

                    type:
                        activity?.type,

                    name:
                        activity?.name,

                    start_date_local:
                        activity?.start_date_local,

                    start_date:
                        activity?.start_date,

                    file_type:
                        activity?.file_type

                })
            )

        );


        // ====================================================
        // 6. ACTIVITIES TO PROCESS
        // ====================================================
        //
        // DO NOT filter by type yet.
        //
        // Your previous logs showed type was undefined.
        // We first want to verify the real payload.
        //
        // Once confirmed, cycling-only filtering can be
        // added safely.
        //
        // ====================================================

        const activities =
            allActivities;


        console.log(
            `Intervals returned ${allActivities.length} total activities`
        );


        console.log(
            `ACTIVITIES WE WILL PROCESS: ${activities.length}`
        );


        // ====================================================
        // 7. NOTHING TO SYNC
        // ====================================================

        if (
            activities.length === 0
        ) {

            return res.status(200).json({

                message:
                    "No activities found for the requested date range.",

                fetched:
                    0,

                inserted:
                    0,

                fit_files_downloaded:
                    0

            });

        }


        // ====================================================
        // 8. INSERT / UPDATE ACTIVITIES
        // ====================================================

        let insertedCount =
            0;


        for (
            const activity of activities
        ) {

            if (
                !activity?.id
            ) {

                console.warn(
                    "Skipping activity without an ID."
                );

                continue;

            }


            // ------------------------------------------------
            // DATE
            // ------------------------------------------------

            const activityDate =

                activity.start_date_local ||

                activity.start_date ||

                activity.startDate ||

                null;


            // ------------------------------------------------
            // DISTANCE
            // ------------------------------------------------

            const distance =

                activity.distance ??

                activity.distance_km ??

                null;


            // ------------------------------------------------
            // MOVING TIME
            // ------------------------------------------------

            const movingTime =

                activity.moving_time ??

                activity.movingTime ??

                null;


            // ------------------------------------------------
            // ELAPSED TIME
            // ------------------------------------------------

            const elapsedTime =

                activity.elapsed_time ??

                activity.elapsedTime ??

                null;


            // ------------------------------------------------
            // SPEED
            // ------------------------------------------------

            const averageSpeed =

                activity.average_speed ??

                activity.averageSpeed ??

                null;


            // ------------------------------------------------
            // POWER
            // ------------------------------------------------

            const averagePower =

                activity.icu_average_watts ??

                activity.average_watts ??

                activity.average_power ??

                activity.averagePower ??

                null;


            // ------------------------------------------------
            // HEART RATE
            // ------------------------------------------------

            const averageHR =

                activity.average_heartrate ??

                activity.average_hr ??

                activity.averageHeartRate ??

                null;


            // ------------------------------------------------
            // MAX HEART RATE
            // ------------------------------------------------

            const maxHR =

                activity.max_heartrate ??

                activity.max_hr ??

                activity.maxHeartRate ??

                null;


            // ------------------------------------------------
            // CADENCE
            // ------------------------------------------------

            const averageCadence =

                activity.average_cadence ??

                activity.averageCadence ??

                null;


            // ------------------------------------------------
            // ELEVATION GAIN
            // ------------------------------------------------

            const elevationGain =

                activity.total_elevation_gain ??

                activity.elevation_gain ??

                activity.elevationGain ??

                null;


            // ------------------------------------------------
            // ELEVATION LOSS
            // ------------------------------------------------

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

                    String(
                        activity.id
                    ),

                    dateOrNull(
                        activityDate
                    ),

                    numberOrNull(
                        distance
                    ),

                    numberOrNull(
                        movingTime
                    ),

                    numberOrNull(
                        elapsedTime
                    ),

                    numberOrNull(
                        averageSpeed
                    ),

                    numberOrNull(
                        averagePower
                    ),

                    numberOrNull(
                        averageHR
                    ),

                    numberOrNull(
                        maxHR
                    ),

                    numberOrNull(
                        averageCadence
                    ),

                    numberOrNull(
                        elevationGain
                    ),

                    numberOrNull(
                        elevationLoss
                    ),

                    JSON.stringify(
                        activity
                    )

                ]

            );


            insertedCount++;

        }


        console.log(
            `Inserted/updated ${insertedCount} activities`
        );


        // ====================================================
        // 9. CREATE TEMP FOLDER
        // ====================================================

        tempFolder =
            path.join(
                process.cwd(),
                "temp",
                userID
            );


        await fs.mkdir(
            tempFolder,
            {
                recursive:
                    true
            }
        );


        console.log(
            `FIT temporary folder: ${tempFolder}`
        );


        // ====================================================
        // 10. DOWNLOAD FIT FILES
        // ====================================================

        let fitCount =
            0;


        for (
            const activity of activities
        ) {

            if (
                !activity?.id
            ) {

                continue;

            }


            const activityId =
                String(
                    activity.id
                );


            const fitPath =
                path.join(
                    tempFolder,
                    `${activityId}.fit`
                );


            try {

                await downloadFitFile(

                    activityId,

                    accessToken,

                    fitPath

                );


                fitCount++;


            } catch (error) {

                console.error(

                    `Could not obtain FIT for activity ${activityId}:`,

                    error.message

                );

            }

        }


        console.log(
            `Downloaded ${fitCount} FIT files`
        );


        // ====================================================
        // 11. NO FIT FILES
        // ====================================================

        if (
            fitCount === 0
        ) {

            console.warn(
                "No FIT files were downloaded."
            );


            console.warn(
                "Skipping Python ML pipeline."
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
        // 12. PREPROCESS
        // ====================================================

        const preprocessPath =
            path.join(
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
        // 13. FEATURES
        // ====================================================

        const featuresPath =
            path.join(
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
        // 14. FATIGUE
        // ====================================================

        const fatiguePath =
            path.join(
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
        // 15. CAPACITY
        // ====================================================

        const capacityPath =
            path.join(
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
        // 16. SEVERITY
        // ====================================================

        const severityPath =
            path.join(
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
        // 17. RECOMMENDATION
        // ====================================================

        const recommendationPath =
            path.join(
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
            "========================================"
        );

        console.log(
            "Activity sync and ML pipeline completed successfully."
        );

        console.log(
            "========================================"
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

        console.error(
            err
        );

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

        if (
            tempFolder
        ) {

            try {

                await fs.rm(
                    tempFolder,
                    {
                        recursive:
                            true,

                        force:
                            true
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


// ============================================================
// EXPORT
// ============================================================

export {
    syncActivities
};