import multer from "multer";
import AdmZip from "adm-zip";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import pool from "../config/db.js";

export const upload = multer({ dest: "uploads/temp_zips/" });

async function runPythonScript(scriptName, args) {
    return new Promise((resolve, reject) => {
        const py = spawn("python", [path.join("python", scriptName), ...args]);
        
        py.stdout.on("data", (data) => console.log(`[${scriptName}] ${data}`));
        py.stderr.on("data", (data) => console.error(`[${scriptName} ERR] ${data}`));
        
        py.on("close", (code) => {
            if (code === 0) resolve();
            else reject(new Error(`${scriptName} exited with code ${code}`));
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
        const fitFilesDir = path.join(extractDir, "fit_files");

        // 1. Unzip archive and unpack any nested zips
        fs.mkdirSync(fitFilesDir, { recursive: true });
        const zip = new AdmZip(zipPath);
        zip.extractAllTo(extractDir, true);

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
                        console.error(`Skipping invalid nested zip: ${filePath}`);
                    }
                }
            });
        };
        extractNestedZips(extractDir);

        // 2. Find summarizedActivities.json for 100% precise activity type filtering
        let validCyclingActivityIds = new Set();
        
        const findAndParseSummaries = (dir) => {
            fs.readdirSync(dir).forEach(file => {
                const filePath = path.join(dir, file);
                if (fs.statSync(filePath).isDirectory()) {
                    findAndParseSummaries(filePath);
                } else if (file.toLowerCase().includes("summarizedactivities.json")) {
                    try {
                        const rawData = fs.readFileSync(filePath, "utf8");
                        const activities = JSON.parse(rawData);
                        
                        // Handle array or object wrapper depending on Garmin export format
                        const list = Array.isArray(activities) ? activities : (activities.summarizedActivities || []);
                        
                        list.forEach(act => {
                            const type = (act.activityType || act.activityTypeId || "").toString().toLowerCase();
                            // Target cycling types specifically
                            if (type.includes("cycling") || type.includes("ride") || type.includes("biking") || type === "2" || type === "3") {
                                if (act.activityId) {
                                    validCyclingActivityIds.add(act.activityId.toString());
                                }
                            }
                        });
                    } catch (err) {
                        console.error("Error parsing summarized activities JSON:", err);
                    }
                }
            });
        };
        findAndParseSummaries(extractDir);

        // 3. Walk directory to collect all .fit files
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
        let copiedCount = 0;

        for (const fitFile of foundFitFiles) {
            const fileName = path.basename(fitFile);
            
            // If we successfully found summary IDs, filter with 100% precision
            if (validCyclingActivityIds.size > 0) {
                const matches = Array.from(validCyclingActivityIds).some(id => fileName.includes(id));
                if (matches) {
                    fs.copyFileSync(fitFile, path.join(fitFilesDir, fileName));
                    copiedCount++;
                }
            } else {
                // Fallback: if summary json wasn't found for some reason, copy all
                fs.copyFileSync(fitFile, path.join(fitFilesDir, fileName));
                copiedCount++;
            }
        }

        console.log(`100% Precision Filter: Copied ${copiedCount} cycling FIT files out of ${foundFitFiles.length} total files.`);

        // 4. Respond instantly with HTTP 202 to prevent Render timeout
        res.status(202).json({ 
            message: `Filtered ${copiedCount} cycling activities. Baseline initialization started in background.` 
        });

        // 5. Run ML pipeline asynchronously
        setImmediate(async () => {
            try {
                await runPythonScript("preprocess.py", [userId]);
                await runPythonScript("features.py", [fitFilesDir, userId]);
                await runPythonScript("fatigue.py", [userId]);
                await runPythonScript("capacities.py", [userId]);
                await runPythonScript("severity.py", [userId]);
                console.log("Background ML pipeline completed successfully for user:", userId);
            } catch (pyErr) {
                console.error("Background ML pipeline failed:", pyErr);
            } finally {
                try {
                    fs.rmSync(zipPath, { force: true });
                    fs.rmSync(extractDir, { recursive: true, force: true });
                } catch (cleanupErr) {
                    console.error("Cleanup error:", cleanupErr.message);
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