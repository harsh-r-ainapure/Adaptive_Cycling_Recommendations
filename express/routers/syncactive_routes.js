import express from "express";
import { verifyGarminWebhook, handleGarminWebhook } from "../controllers/syncactive_controller.js";

const router = express.Router();

// GET route for Garmin webhook domain/challenge verification
router.get("/activities", verifyGarminWebhook);

// POST route for incoming Garmin activity push webhooks
router.post("/activities", handleGarminWebhook);

export default router;