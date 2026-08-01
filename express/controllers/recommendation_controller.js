import path from "path";
import { spawn } from "child_process";
import pool from "../config/db.js";
import axios from "axios";
import fs from "fs/promises";

function runPython(scriptPath, userId) {
    return new Promise((resolve, reject) => {

        const pythonProcess = spawn(
            process.platform === "win32" ? "py" : "python",
            [scriptPath, userId]
        );

        pythonProcess.stdout.on("data", data => {
            console.log(data.toString());
        });

        pythonProcess.stderr.on("data", data => {
            console.error(data.toString());
        });

        pythonProcess.on("close", code => {
            if (code === 0)
                resolve();
            else
                reject(new Error(`${scriptPath} exited with code ${code}`));
        });

        pythonProcess.on("error", reject);
    });
}

const recommendation = async (req, res, next) => {
    try {

        const userId = req.user.id;

        
           

      
       const result = await pool.query(
    `
    SELECT
    r.*,
    p.baseline_distance,
    p.baseline_elevation,
    p.baseline_hr
FROM recommendations r
JOIN activities a
    ON r.activity_id = a.id
JOIN predictions p
    ON p.activity_id = a.id
WHERE a.user_id = $1
ORDER BY a.activity_date DESC
LIMIT 1;
    `,
    [userId]
);


        return res.status(200).json({
    recommendation: result.rows[0],
    message: "Recommendations generated successfully."
});

 

    } catch (err) {
        next(err);
    }
};

export {
    recommendation
};