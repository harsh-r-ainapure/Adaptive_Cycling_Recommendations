import express from "express";

import authenticate from "../middleware/authmiddleware.js";
import { get_dashboard } from "../controllers/dashboard_controller.js";

const router = express.Router();

router.get("/", authenticate, get_dashboard);

export default router;