import express from "express";
import authenticate from "../middleware/authmiddleware.js";
import { verifyGarminWebhook, handleGarminWebhook, syncRecentRides } from "../controllers/syncactive_controller.js";

const router = express.Router();

// GET route for Garmin webhook domain/challenge verification
router.get("/activities", verifyGarminWebhook);

// POST route for incoming Garmin activity push webhooks
router.post("/activities", handleGarminWebhook);

// POST route for manual recent rides synchronization triggered via frontend button
router.post("/recent", authenticate, syncRecentRides);

export default router;