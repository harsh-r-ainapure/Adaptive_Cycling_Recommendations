import pandas as pd
import os
import sys
import json
from dotenv import load_dotenv
import psycopg2

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("Error: SUPABASE_DB_URL environment variable is not set.")
    sys.exit(1)

try:
    conn = psycopg2.connect(db_url)
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)

temp_folder = sys.argv[1]
user_id = sys.argv[2]

print(f"[preprocess.py] Scanning {temp_folder} for summarized activities...")

cursor = conn.cursor()
inserted_count = 0

def process_summaries(dir_path):
    global inserted_count
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if "summarizedactivities.json" in file.lower():
                json_path = os.path.join(root, file)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        list_acts = data if isinstance(data, list) else data.get("summarizedActivities", [])
                        
                        for act in list_acts:
                            activity_id = str(act.get("activityId", ""))
                            if not activity_id:
                                continue
                            
                            activity_type = str(act.get("activityType", act.get("activityTypeId", "cycling"))).lower()
                            if not any(t in activity_type for t in ["cycling", "ride", "biking", "2", "3"]):
                                continue

                            activity_date = act.get("startTimeLocal", act.get("beginTimestamp"))
                            distance = float(act.get("distance", 0.0))
                            moving_time = float(act.get("duration", act.get("movingTime", 0.0)))
                            elapsed_time = float(act.get("elapsedTime", moving_time))
                            avg_speed = float(act.get("averageSpeed", 0.0))
                            avg_hr = float(act.get("averageHR", 0.0))
                            max_hr = float(act.get("maxHR", 0.0))
                            avg_cadence = float(act.get("averageBikingCadence", act.get("averageCadence", 0.0)))
                            avg_power = float(act.get("averagePower", 0.0))
                            elevation_gain = float(act.get("elevationGain", 0.0))

                            insert_query = """
                            INSERT INTO activities (
                                id, user_id, intervals_activity_id, activity_date, distance, 
                                moving_time, elapsed_time, average_speed, average_hr, max_hr, 
                                average_cadence, average_power, elevation_gain
                            )
                            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING;
                            """
                            
                            cursor.execute(
                                insert_query,
                                (
                                    user_id, activity_id, activity_date, distance,
                                    moving_time, elapsed_time, avg_speed, avg_hr, max_hr,
                                    avg_cadence, avg_power, elevation_gain
                                )
                            )
                            inserted_count += 1
                except Exception as e:
                    print(f"Error parsing summary JSON {json_path}: {e}")

process_summaries(temp_folder)
conn.commit()
cursor.close()
conn.close()

print(f"[preprocess.py] Successfully synced {inserted_count} activity records into database baseline.")