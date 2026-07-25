import express from "express";
import path from "path";
import bodyParser from "body-parser";
import helmet from "helmet";
import compression from "compression";
import cors from "cors";
import dotenv from "dotenv";
import pool from "./config/db.js";
import { fileURLToPath } from "url";

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

const port = process.env.PORT || 3003;

async function testDB() {
    try {
        const result = await pool.query("SELECT NOW()");
        console.log("Database Time:", result.rows[0].now);
    } catch (err) {
        console.error(err);
    }
}

testDB();

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});