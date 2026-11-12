import express from "express";
import path from "path";
import bodyParser from "body-parser";
import cookieParser from "cookie-parser";
import helmet from "helmet";
import compression from "compression";
import cors from "cors";
import dotenv from "dotenv";
import pool from "./config/db.js";
import { fileURLToPath } from "url";
import syncUserRoutes from "./routers/syncuser_routes.js";
import syncActiveRoutes from "./routers/syncactive_routes.js";
import syncHistoryRoutes from "./routers/synchistory_routes.js"; // Added historical router
import recommendationRouter from "./routers/recommendation_router.js";
import dashboardRouter from "./routers/dashboard_router.js";

dotenv.config();

const app = express();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(
  helmet({
    crossOriginResourcePolicy: { policy: "cross-origin" },
  })
);
app.use(compression());
app.use(cors());

// Serve static files from the 'public' folder (for logo.png, etc.)
app.use(express.static(path.join(__dirname, "public")));
app.use(express.static("public"));

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(cookieParser());

// Garmin Auth Routes (matches https://app.harshainapure.dev/api/auth/garmin/callback)
app.use("/api/auth/garmin", syncUserRoutes);

// Garmin Webhook & Activity Routes
app.use("/api/sync", syncActiveRoutes);

// First-time Historical ZIP Upload Route (accessible at POST /api/history/upload-history)
app.use("/api/history", syncHistoryRoutes);

app.use("/recommendation", recommendationRouter);

app.use("/dashboard", dashboardRouter);

const port = process.env.PORT || 3003;

async function testDB() {
    try {
        const client = await pool.connect();
        const result = await client.query("SELECT version();");
        client.release();
    } catch (err) {
        console.error(err);
    }
}

testDB();

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
