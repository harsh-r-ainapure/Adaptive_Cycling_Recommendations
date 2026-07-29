import pg from "pg";
import dotenv from "dotenv";

dotenv.config();

const { Client } = pg;

const client = new Client({
    connectionString: process.env.SUPABASE_DB_URL,
    ssl: {
        rejectUnauthorized: false
    }
});

try {
    await client.connect();
    console.log("✅ Connected!");

    const result = await client.query("SELECT NOW()");
    console.log(result.rows);

    await client.end();
} catch (err) {
    console.error(err);
}