import express from "express";

import authenticate from "../middleware/authmiddleware.js";

import {
    signup_redirectt,
    signup_callback,
    saveProfile
} from "../controllers/syncuser_controller.js";

const router = express.Router();

router.get("/signup", signup_redirectt);

router.get("/callback", signup_callback);

router.post(
    "/profile",
    authenticate,
    saveProfile
);

export default router;