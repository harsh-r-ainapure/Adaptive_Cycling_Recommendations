import express from "express";
import {
    signup_redirectt,
    signup_callback
} from "../controllers/syncuser_controller.js";

const router = express.Router();

router.get("/signup", signup_redirectt);

router.get("/callback", signup_callback);

export default router;