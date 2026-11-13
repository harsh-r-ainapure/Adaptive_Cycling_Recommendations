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
        py.stderr.on("data", (data) => console.error(`${prefix} ERR: ${data.toString().trim()}`));
        
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
        return res.status(400).json({ error: "User ID missing." });
    }

    try {
        const checkResult = await pool.query(
            "SELECT COUNT(*) FROM activities WHERE user_id = $1",
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

        // 1. Unzip archive and delete main zip immediately to free disk space
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

        // 2. Parse summarizedActivities.json for 100% precise cycling filtering
        let validCyclingActivityIds = new Set();
        
        const findAndParseSummaries = (dir) => {
            fs.readdirSync(dir).forEach(file => {
                const filePath = path.join(dir, file);
                if (fs.statSync(filePath).isDirectory()) {
                    findAndParseSummaries(filePath);
                } else if (file.toLowerCase().includes("summarizedactivities.json")) {
                    try {
                        const rawData = fs.readFileSync(filePath, "utf8");
                        const parsed = JSON.parse(rawData);
                        
                        // Handle Garmin's [{"summarizedActivitiesExport": [...]}] wrapper
                        let list = [];
                        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].summarizedActivitiesExport) {
                            list = parsed[0].summarizedActivitiesExport;
                        } else if (Array.isArray(parsed)) {
                            list = parsed;
                        } else if (parsed && parsed.summarizedActivitiesExport) {
                            list = parsed.summarizedActivitiesExport;
                        } else if (parsed && parsed.summarizedActivities) {
                            list = parsed.summarizedActivities;
                        }
                        
                        list.forEach(act => {
                            if (!act || typeof act !== "object") return;
                            const type = (act.activityType || act.activityTypeId || "").toString().toLowerCase();
                            if (
                                type.includes("cycling") || 
                                type.includes("ride") || 
                                type.includes("biking")
                            ) {
                                if (act.activityId !== undefined && act.activityId !== null) {
                                    validCyclingActivityIds.add(act.activityId.toString().trim());
                                }
                            }
                        });
                    } catch (err) {
                        console.error("[Filter] Error parsing summarized activities JSON:", err);
                    }
                }
            });
        };
        findAndParseSummaries(extractDir);
        console.log(`[Filter] Found ${validCyclingActivityIds.size} valid cycling activity IDs in JSON summary.`);

        // 3. Collect all .fit files, filter by exact numeric ID, and DELETE non-cycling files immediately
        const walkSync = (dir, fileList = []) => {
            fs.readdirSync(dir).forEach(file => {
                const filePath = path.join(dir, file);
                if (fs.statSync(filePath).isDirectory()) {
                    fileList = walkSync(filePath, fileList);
                } else if (file.toLowerCase().endsWith(".fit")) {
                    fileList.push(filePath);
                }
            });
            return fileList;
        };

        const foundFitFiles = walkSync(extractDir);
        const cyclingFitFiles = [];

        for (const fitFile of foundFitFiles) {
            const base = path.basename(fitFile, path.extname(fitFile)); // e.g., mrudulaainapure0@gmail.com_203139416105
            const numericId = base.split("_").pop().split("-")[0].trim();

            if (validCyclingActivityIds.has(numericId)) {
                cyclingFitFiles.push(fitFile);
            } else {
                // Delete non-cycling FIT file immediately to free container RAM/disk
                fs.rmSync(fitFile, { force: true });
            }
        }

        console.log(`[Filter] Filtered down to ${cyclingFitFiles.length} cycling files out of ${foundFitFiles.length} total files.`);

        // 4. Respond instantly with HTTP 202
        res.status(202).json({ 
            message: `Filtered ${cyclingFitFiles.length} cycling activities. Micro-batch processing started in background.` 
        });

        // 5. Run ML pipeline asynchronously with detailed micro-batch logs
        setImmediate(async () => {
            const BATCH_SIZE = 50;
            const batches = [];
            for (let i = 0; i < cyclingFitFiles.length; i += BATCH_SIZE) {
                batches.push(cyclingFitFiles.slice(i, i + BATCH_SIZE));
            }

            try {
                console.log(`[Pipeline] Initializing database baseline...`);
                await runPythonScript("preprocess.py", [extractDir, userId], "Global-Setup");

                for (let idx = 0; idx < batches.length; idx++) {
                    const batch = batches[idx];
                    const batchNum = idx + 1;
                    const totalBatches = batches.length;
                    const batchLabel = `Batch ${batchNum}/${totalBatches}`;
                    
                    const batchDir = path.join(extractDir, `batch_${idx}`);
                    fs.mkdirSync(batchDir, { recursive: true });

                    for (const fitFile of batch) {
                        if (fs.existsSync(fitFile)) {
                            // Move instead of copy to avoid duplicating files in memory/disk
                            fs.renameSync(fitFile, path.join(batchDir, path.basename(fitFile)));
                        }
                    }

                    console.log(`[${batchLabel}] Processing ${batch.length} files with features.py...`);
                    await runPythonScript("features.py", [batchDir, userId], batchLabel);

                    // Clean up batch folder and generated CSVs immediately
                    fs.rmSync(batchDir, { recursive: true, force: true });
                    console.log(`[${batchLabel}] Cleaned up batch directory from RAM/disk.`);
                }

                console.log(`[Pipeline] Running global post-processing models...`);
                await runPythonScript("fatigue.py", [userId], "Global-Finalize");
                await runPythonScript("capacities.py", [userId], "Global-Finalize");
                await runPythonScript("severity.py", [userId], "Global-Finalize");
                await runPythonScript("recommendation.py", [userId], "Global-Finalize");
                
                console.log(`[Pipeline] SUCCESS: Historical import & ML pipeline fully completed for user: ${userId}`);

            } catch (pyErr) {
                console.error("[Pipeline] ERROR: Micro-batch processing failed:", pyErr);
            } finally {
                try {
                    fs.rmSync(zipPath, { force: true });
                    fs.rmSync(extractDir, { recursive: true, force: true });
                    console.log(`[Cleanup] Temporary extraction directories removed.`);
                } catch (cleanupErr) {
                    console.error("[Cleanup] Error clearing temporary files:", cleanupErr.message);
                }
            }
        });

    } catch (err) {
        console.error("Historical import failed:", err);
        if (!res.headersSent) {
            res.status(500).json({ error: "Failed to process historical data package." });
        }
    }
};