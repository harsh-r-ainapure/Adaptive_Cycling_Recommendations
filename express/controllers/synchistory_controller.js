import multer from "multer";
import AdmZip from "adm-zip";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import pool from "../config/db.js";

export const upload = multer({ dest: "uploads/temp_zips/" });

async function runPythonScript(scriptName, args, batchInfo = "") {
    return new Promise((resolve, reject) => {
        const prefix = batchInfo ? `[${batchInfo}] [${scriptName}]` : `[${scriptName}]`;
        console.log(`${prefix} Starting execution...`);

        const py = spawn("python", [path.join("python", scriptName), ...args]);

        py.stdout.on("data", (data) => console.log(`${prefix} ${data.toString().trim()}`));
        py.stderr.on("data", (data) => {
            const msg = data.toString().trim();
            // pandas/SQLAlchemy UserWarnings are harmless; don't label them as errors
            const label = /Warning/.test(msg) && !/Traceback/.test(msg) ? "WARN" : "ERR";
            console.error(`${prefix} ${label}: ${msg}`);
        });

        py.on("error", (err) => reject(err));
        py.on("close", (code) => {
            if (code === 0) {
                console.log(`${prefix} Completed successfully.`);
                resolve();
            } else {
                reject(new Error(`${scriptName} exited with code ${code}`));
            }
        });
    });
}

export const handleHistoricalZipUpload = async (req, res) => {
    const userId = req.body.userId || req.user?.id;

    if (!userId) {
        if (req.file) fs.rmSync(req.file.path, { force: true });
        return res.status(400).json({ error: "User ID missing." });
    }

    try {
        const checkResult = await pool.query(
            "SELECT COUNT(*) FROM activities WHERE user_id = \$1",
            [userId]
        );

        if (parseInt(checkResult.rows[0].count, 10) > 0) {
            if (req.file) fs.rmSync(req.file.path, { force: true });
            return res.status(403).json({
                error: "Historical data already exists. Future rides sync automatically via Garmin webhooks."
            });
        }

        if (!req.file) {
            return res.status(400).json({ error: "First-time setup requires your Garmin history ZIP file." });
        }

        const zipPath = req.file.path;
        const extractDir = path.join("uploads", "extracted", userId);

        // 1. Unzip archive (and any nested zips) and delete the main zip to free disk space
        console.log(`[Setup] Extracting ZIP package for user: ${userId}`);
        const zip = new AdmZip(zipPath);
        zip.extractAllTo(extractDir, true);
        fs.rmSync(zipPath, { force: true });

        const extractNestedZips = (dir) => {
            fs.readdirSync(dir).forEach(file => {
                const filePath = path.join(dir, file);
                if (fs.statSync(filePath).isDirectory()) {
                    extractNestedZips(filePath);
                } else if (file.toLowerCase().endsWith(".zip")) {
                    try {
                        const nestedZip = new AdmZip(filePath);
                        const subDir = path.join(dir, path.basename(file, ".zip"));
                        fs.mkdirSync(subDir, { recursive: true });
                        nestedZip.extractAllTo(subDir, true);
                        fs.rmSync(filePath, { force: true });
                        extractNestedZips(subDir);
                    } catch (e) {
                        console.error(`[Setup] Skipping invalid nested zip: ${filePath}`);
                        fs.rmSync(filePath, { force: true });
                    }
                }
            });
        };
        extractNestedZips(extractDir);

        // 2. Respond immediately; cycling detection + ML pipeline run in the background
        res.status(202).json({
            message: "Upload received. Detecting cycling activities and processing in the background."
        });

        setImmediate(async () => {
            const BATCH_SIZE = 50;
            let pipelineOk = false;

            try {
                // Set status to processing
                await pool.query(
                    "UPDATE users SET historical_sync_status = 'processing' WHERE id = \$1",
                    [userId]
                ).catch(() => {}); // Fallback silently if users table schema varies

                // 3. Find cycling FIT files by CONTENT (sport + start time vs summarizedActivities.json).
                //    Garmin FIT filenames are upload IDs, NOT activityIds, so filename matching can't work.
                const matchFile = path.join(extractDir, "cycling_matches.json");
                await runPythonScript("match_fit.py", [extractDir, matchFile], "Filter");

                let matches = [];
                try {
                    matches = JSON.parse(fs.readFileSync(matchFile, "utf8"));
                } catch (e) {
                    throw new Error(`Could not read FIT match results: ${e.message}`);
                }

                console.log(`[Filter] Matched ${matches.length} cycling FIT files to summary rides.`);
                if (matches.length === 0) {
                    // Abort BEFORE touching the database so the user can re-upload (the 403 check stays clear).
                    throw new Error("No cycling FIT files matched any ride in summarizedActivities.json. Nothing imported.");
                }

                // Free disk: delete every FIT that was not selected
                const keep = new Set(matches.map(m => path.resolve(m.path)));
                const deleteUnselectedFits = (dir) => {
                    fs.readdirSync(dir).forEach(file => {
                        const p = path.join(dir, file);
                        if (fs.statSync(p).isDirectory()) {
                            deleteUnselectedFits(p);
                        } else if (file.toLowerCase().endsWith(".fit") && !keep.has(path.resolve(p))) {
                            fs.rmSync(p, { force: true });
                        }
                    });
                };
                deleteUnselectedFits(extractDir);

                // 4. Insert baseline activity rows from the summary JSON
                console.log(`[Pipeline] Initializing database baseline...`);
                await runPythonScript("preprocess.py", [extractDir, userId], "Global-Setup");

                // 5. Micro-batch feature extraction.
                //    Each FIT is renamed to <activityId>.fit. features.py uses the bare filename as
                //    "Activity ID" and joins it to activities.intervals_activity_id, so it must be exactly the activityId.
                const batches = [];
                for (let i = 0; i < matches.length; i += BATCH_SIZE) {
                    batches.push(matches.slice(i, i + BATCH_SIZE));
                }

                for (let idx = 0; idx < batches.length; idx++) {
                    const batch = batches[idx];
                    const batchLabel = `Batch ${idx + 1}/${batches.length}`;

                    const batchDir = path.join(extractDir, `batch_${idx}`);
                    fs.mkdirSync(batchDir, { recursive: true });

                    for (const m of batch) {
                        if (!fs.existsSync(m.path)) continue;
                        fs.renameSync(m.path, path.join(batchDir, `${m.activityId}.fit`));
                    }

                    console.log(`[${batchLabel}] Processing ${batch.length} files with features.py...`);
                    await runPythonScript("features.py", [batchDir, userId], batchLabel);

                    fs.rmSync(batchDir, { recursive: true, force: true });
                    console.log(`[${batchLabel}] Cleaned up batch directory.`);
                }

                // 6. Global models
                console.log(`[Pipeline] Running global post-processing models...`);
                await runPythonScript("fatigue.py", [userId], "Global-Finalize");
                await runPythonScript("capacities.py", [userId], "Global-Finalize");
                await runPythonScript("severity.py", [userId], "Global-Finalize");
                await runPythonScript("recommendation.py", [userId], "Global-Finalize");

                pipelineOk = true;
                
                // Update status to completed
                await pool.query(
                    "UPDATE users SET historical_sync_status = 'completed' WHERE id = \$1",
                    [userId]
                ).catch(() => {});

                console.log(`[Pipeline] SUCCESS: Imported ${matches.length} cycling rides and ran ML pipeline for user: ${userId}`);

            } catch (pyErr) {
                console.error("[Pipeline] ERROR:", pyErr.message || pyErr);
                
                // Update status to failed
                await pool.query(
                    "UPDATE users SET historical_sync_status = 'failed' WHERE id = \$1",
                    [userId]
                ).catch(() => {});
            } finally {
                try {
                    fs.rmSync(zipPath, { force: true });
                    fs.rmSync(extractDir, { recursive: true, force: true });
                    console.log(`[Cleanup] Temporary extraction directories removed.${pipelineOk ? "" : " (pipeline did NOT complete)"}`);
                } catch (cleanupErr) {
                    console.error("[Cleanup] Error clearing temporary files:", cleanupErr.message);
                }
            }
        });

    } catch (err) {
        console.error("Historical import failed:", err);
        if (req.file) fs.rmSync(req.file.path, { force: true });
        if (!res.headersSent) {
            res.status(500).json({ error: "Failed to process historical data package." });
        }
    }
};

// Optional status check endpoint helper
export const getSyncStatus = async (req, res) => {
    const userId = req.params.userId || req.user?.id;
    if (!userId) return res.status(400).json({ error: "User ID missing." });
    
    try {
        const result = await pool.query(
            "SELECT historical_sync_status FROM users WHERE id = \$1",
            [userId]
        );
        if (result.rows.length === 0) return res.json({ status: "idle" });
        res.json({ status: result.rows[0].historical_sync_status || "idle" });
    } catch (err) {
        res.status(500).json({ error: "Failed to fetch sync status." });
    }
};
