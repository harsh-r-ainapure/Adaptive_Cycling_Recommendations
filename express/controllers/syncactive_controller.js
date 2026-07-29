import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";
import path from "path";
import { spawn } from "child_process";

const syncActivities = async (req, res) => {

    try {

        const userID = req.user.id;

        // Get access token
        const tokenResult = await pool.query(
            `
            SELECT access_token
            FROM users
            WHERE id = $1
            `,
            [userID]
        );

        const access_token = tokenResult.rows[0].access_token;

        const today = new Date().toISOString().split("T")[0];

        // Check if activities already exist
        const activityCountResult = await pool.query(
            `
            SELECT COUNT(*) AS count
            FROM activities
            WHERE user_id = $1
            `,
            [userID]
        );

        const activityCount = Number(activityCountResult.rows[0].count);

        let oldest;

        if (activityCount === 0) {

            oldest = "2020-11-19";

        } else {

            const latestResult = await pool.query(
                `
                SELECT MAX(activity_date) AS latest
                FROM activities
                WHERE user_id = $1
                `,
                [userID]
            );

            oldest = latestResult.rows[0].latest
    .toISOString()
    .split("T")[0];

        }

        // Download summaries
        const summaryResponse = await axios.get(
            "https://intervals.icu/api/v1/athlete/0/activities",
            {
                headers: {
                    Authorization: `Bearer ${access_token}`
                },
                params: {
                    oldest,
                    newest: today
                }
            }
        );

        const activities = summaryResponse.data;

        console.log(
    `Fetched ${activities.length} activities`
);

        for (const activity of activities) {

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
    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14
)
ON CONFLICT (user_id, intervals_activity_id)
DO UPDATE SET
    activity_date = EXCLUDED.activity_date,
    distance = EXCLUDED.distance,
    moving_time = EXCLUDED.moving_time,
    elapsed_time = EXCLUDED.elapsed_time,
    average_speed = EXCLUDED.average_speed,
    average_power = EXCLUDED.average_power,
    average_hr = EXCLUDED.average_hr,
    max_hr = EXCLUDED.max_hr,
    average_cadence = EXCLUDED.average_cadence,
    elevation_gain = EXCLUDED.elevation_gain,
    elevation_loss = EXCLUDED.elevation_loss,
    raw_data = EXCLUDED.raw_data;
        `,
        [
            userID,
            activity.id,
            activity.start_date,
            activity.distance,
            activity.moving_time,
            activity.elapsed_time,
            activity.average_speed,
            activity.icu_average_watts,
            activity.average_heartrate,
            activity.max_heartrate,
            activity.average_cadence,
            activity.total_elevation_gain,
            activity.total_elevation_loss,
            JSON.stringify(activity)
        ]
    );

}
        // Check whether features already exist
       

        if (activities.length === 0) {

    return res.json({
        message: "Already up to date."
    });

} 

        // Create temp folder
        const tempFolder = path.join("temp", userID);

        await fs.mkdir(tempFolder, {
            recursive: true
        });

        // Download FIT files
        for (const activity of activities) {

            const fitResponse = await axios.get(
                `https://intervals.icu/api/v1/activity/${activity.id}/file`,
                {
                    headers: {
                        Authorization: `Bearer ${access_token}`
                    },
                    responseType: "arraybuffer"
                }
            );

            console.log(fitResponse.headers["content-type"]);
console.log(fitResponse.data.length);

            const fitPath = path.join(
                tempFolder,
                `${activity.id}.fit`
            );

            await fs.writeFile(
                fitPath,
                fitResponse.data
            );

           console.log("Saved:", fitPath);

        }

        const scriptPath = path.join(
    process.cwd(),
    "python",
    "features.py"
);

const python = spawn(
    process.platform === "win32" ? "py" : "python",
    [
        scriptPath,
        tempFolder,
        userID
    ]
);

python.stdout.on("data", (data) => {
    console.log(data.toString());
});

python.stderr.on("data", (data) => {
    console.error(data.toString());
});

python.on("error", (err) => {
    console.error(err);
});

await new Promise((resolve, reject) => {

    python.on("close", (code) => {

        if (code === 0)
            resolve();

        else
            reject(new Error(`Python exited with code ${code}`));

    });

});



                // Delete temp folder
        await fs.rm(tempFolder, {
            recursive: true,
            force: true
        });

        res.json({
            message: "Sync completed successfully."
        });

    } catch (err) {

        console.error(err);

        res.status(500).json({
            message: "Sync failed."
        });

    } 

};

export {
    syncActivities
};