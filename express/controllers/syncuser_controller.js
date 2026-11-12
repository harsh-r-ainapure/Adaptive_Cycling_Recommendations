import pool from "../config/db.js";
import axios from "axios";
import jwt from "jsonwebtoken";
import crypto from "crypto";

const saveProfile = async (req, res) => {
    try {
        const userId = req.user.id;
        const {
            name,
            has_power_meter,
            power_meter_month,
            power_meter_year
        } = req.body;

        await pool.query(
            `
            UPDATE users
            SET
                name = $1,
                has_power_meter = $2,
                power_meter_month = $3,
                power_meter_year = $4
            WHERE id = $5
            `,
            [
                name,
                has_power_meter,
                power_meter_month,
                power_meter_year,
                userId
            ]
        );

        return res.json({
            message: "Profile saved successfully."
        });
    } catch (err) {
        console.error(err);
        return res.status(500).json({
            message: "Unable to save profile."
        });
    }
};

// Helper functions for PKCE (S256)
const generateCodeVerifier = () => {
    return crypto.randomBytes(32).toString('base64url');
};

const generateCodeChallenge = (codeVerifier) => {
    return crypto
        .createHash('sha256')
        .update(codeVerifier)
        .digest('base64url');
};

const signup_redirectt = async (req, res, next) => {
    try {
        // 1. Generate PKCE verifier and challenge
        const codeVerifier = generateCodeVerifier();
        const codeChallenge = generateCodeChallenge(codeVerifier);

        // 2. Temporarily store the code_verifier in a secure cookie (expires in 5 minutes)
        res.cookie('garmin_code_verifier', codeVerifier, {
            httpOnly: true,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'lax',
            maxAge: 5 * 60 * 1000 
        });

        // 3. Build Garmin OAuth2 confirmation URL
        const authURL =
            "https://connect.garmin.com/oauth2Confirm?" +
            new URLSearchParams({
                client_id: process.env.GARMIN_CONSUMER_KEY,
                redirect_uri: process.env.GARMIN_REDIRECT_URI,
                response_type: "code",
                code_challenge: codeChallenge,
                code_challenge_method: "S256"
            });

        res.redirect(authURL);
    } catch (err) {
        console.error("Garmin redirect error:", err);
        return res.status(500).json({
            message: "Internal Server Error"
        });
    }
};

const signup_callback = async (req, res, next) => {
    try {
        const code = req.query.code;
        const codeVerifier = req.cookies?.garmin_code_verifier;

        if (!code || !codeVerifier) {
            return res.status(400).json({ message: "Authorization code or PKCE verifier missing." });
        }

        // 1. Exchange authorization code for tokens
        const tokenResponse = await axios.post(
            "https://diauth.garmin.com/di-oauth2-service/oauth/token",
            new URLSearchParams({
                grant_type: "authorization_code",
                code,
                client_id: process.env.GARMIN_CONSUMER_KEY,
                client_secret: process.env.GARMIN_CONSUMER_SECRET,
                code_verifier: codeVerifier,
                redirect_uri: process.env.GARMIN_REDIRECT_URI
            }),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            }
        );

        const { access_token, refresh_token } = tokenResponse.data;

        // 2. Fetch the Garmin User ID using the access token
        const userResponse = await axios.get(
            "https://apis.garmin.com/wellness-api/rest/user/id",
            {
                headers: {
                    "Authorization": `Bearer ${access_token}`
                }
            }
        );

        const garmin_id = userResponse.data.userId;

        // 3. Upsert user into database
        const result = await pool.query(
            `
            INSERT INTO USERS (ACCESS_TOKEN, REFRESH_TOKEN, GARMIN_ID) 
            VALUES ($1, $2, $3)
            ON CONFLICT (garmin_id)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                updated_at = NOW()
            RETURNING id;
            `,
            [access_token, refresh_token, garmin_id]
        );

        const userId = result.rows[0].id;
        const token = jwt.sign(
            { id: userId },
            process.env.JWT_SECRET,
            { expiresIn: "7d" }
        );

        // Clear the verifier cookie
        res.clearCookie('garmin_code_verifier');

        res.redirect(`${process.env.FRONTEND_URL}?token=${token}`);
    } catch (err) {
        console.error("Garmin callback error:", err.response?.data || err);
        return res.status(500).json({
            message: "Internal Server Error"
        });
    }
};

export {
    signup_callback,
    signup_redirectt,
    saveProfile
};