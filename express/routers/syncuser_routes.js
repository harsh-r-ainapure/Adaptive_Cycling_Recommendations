import express from "express";
import authenticate from "../middleware/authmiddleware.js";
import {
    signup_redirectt,
    signup_callback,
    saveProfile
} from "../controllers/syncuser_controller.js";

const router = express.Router();

// Route to initiate Garmin OAuth flow
router.get("/signup", signup_redirectt);

// Garmin OAuth callback route (matches your registered Garmin Developer portal URL)
router.get("/callback", signup_callback);

// Save user profile settings (power meter preferences, etc.)
router.post(
    "/profile",
    authenticate,
    saveProfile
);

export default router;