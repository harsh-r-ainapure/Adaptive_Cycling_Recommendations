import express from "express";
import { upload, handleHistoricalZipUpload } from "../controllers/synchistory_controller.js";
import authenticate from "../middleware/authmiddleware.js";

const router = express.Router();

router.post(
    "/upload-history", 
    authenticate,                  // Uses your existing middleware
    upload.single("zipFile"),      // Handles the multipart ZIP file upload
    handleHistoricalZipUpload      // Runs the ML pipeline
);

export default router;