import express from "express";
import auth from "../middleware/authmiddleware.js";
import { recommendation } from "../controllers/recommendation_controller.js";

const router = express.Router();

router.get(
    "/",
    auth,
    recommendation
);

export default router;