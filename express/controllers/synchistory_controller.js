import multer from "multer";
import AdmZip from "adm-zip";
import path from "path";
import fs from "fs";
import { spawn } from "child_process";
import pool from "../config/db.js";

// Export upload so routers can use it as middleware (e.g., upload.single('zipFile'))
export const upload = multer({ dest: "uploads/temp_zips/" });

// Helper to run python scripts sequentially
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
        // 1. Check if user already has historical data in the database
        const checkResult = await pool.query(
            "SELECT COUNT(*) FROM activities WHERE user_id = $1",
            [userId]
        );
        
        const activityCount = parseInt(checkResult.rows[0].count, 10);

        if (activityCount > 0) {
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

        // 2. Unzip and flatten .fit files
        fs.mkdirSync(fitFilesDir, { recursive: true });
        const zip = new AdmZip(zipPath);
        zip.extractAllTo(extractDir, true);

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
        for (const fitFile of foundFitFiles) {
            const fileName = path.basename(fitFile);
            fs.copyFileSync(fitFile, path.join(fitFilesDir, fileName));
        }

        // 3. Run the ML pipeline sequentially for baseline creation
        await runPythonScript("preprocess.py", [userId]);
        await runPythonScript("features.py", [fitFilesDir, userId]);
        await runPythonScript("fatigue.py", [userId]);
        await runPythonScript("capacities.py", [userId]);
        await runPythonScript("severity.py", [userId]);

        // 4. Cleanup temporary files
        fs.rmSync(zipPath, { force: true });
        fs.rmSync(extractDir, { recursive: true, force: true });

        res.json({ message: "First-time historical import completed. Baseline models initialized successfully." });

    } catch (err) {
        console.error("Historical import failed:", err);
        res.status(500).json({ error: "Failed to process historical data package." });
    }
};