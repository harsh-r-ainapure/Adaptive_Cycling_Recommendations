import express from "express";
import path from "path";
import bodyParser from "body-parser";
import helmet from "helmet";
import compression from "compression";
import cors from "cors";
import dotenv from "dotenv";
import pool from "./config/db.js";
import { fileURLToPath } from "url";
import syncUserRoutes from "./routers/syncuser_routes.js";
import syncActiveRoutes from "./routers/syncactive_routes.js";
import recommendationRouter from "./routers/recommendation_router.js";

dotenv.config();

const app = express();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(helmet());
app.use(compression());

app.use(express.static(path.join(__dirname, "public")));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

app.use(cors());

app.use("/api/user", syncUserRoutes);

app.use("/api/sync", syncActiveRoutes);

app.use("/recommendation", recommendationRouter);

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