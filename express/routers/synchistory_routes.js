import express from "express";
import { upload, handleHistoricalZipUpload, getSyncStatus } from "../controllers/synchistory_controller.js";
import authenticate from "../middleware/authmiddleware.js";

const router = express.Router();

router.post(
    "/upload-history", 
    authenticate,                  // Uses your existing middleware
    upload.single("zipFile"),      // Handles the multipart ZIP file upload
    handleHistoricalZipUpload      // Runs the ML pipeline
);

// New status polling route to track background sync progress
router.get(
    "/sync-status/:userId",
    authenticate,
    getSyncStatus
);

export default router;
