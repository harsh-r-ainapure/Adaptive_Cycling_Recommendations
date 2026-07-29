import express from "express";
import { syncActivities } from "../controllers/syncactive_controller.js";
import authenticate from "../middleware/authmiddleware.js";

const router = express.Router();

router.post(
    "/activities",
    authenticate,
    syncActivities
);

export default router;