import pandas as pd
import os
import sys
import json
from datetime import datetime
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

def safe_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

def process_summaries(dir_path):
    global inserted_count
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if "summarizedactivities.json" in file.lower():
                json_path = os.path.join(root, file)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # Unpack Garmin's nested [{"summarizedActivitiesExport": [...]}] structure
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict) and "summarizedActivitiesExport" in data[0]:
                            list_acts = data[0]["summarizedActivitiesExport"]
                        elif isinstance(data, dict):
                            list_acts = data.get("summarizedActivitiesExport", data.get("summarizedActivities", []))
                        elif isinstance(data, list):
                            list_acts = data
                        else:
                            list_acts = []
                        
                        for act in list_acts:
                            if not isinstance(act, dict):
                                continue

                            raw_id = act.get("activityId")
                            if raw_id is None:
                                continue
                            activity_id = str(raw_id).strip()
                            
                            activity_type = str(act.get("activityType", act.get("activityTypeId", ""))).lower()
                            if not any(t in activity_type for t in ["cycling", "ride", "biking", "virtual_ride", "indoor_cycling", "road_biking"]):
                                continue

                            # Convert epoch milliseconds to ISO timestamp string
                            raw_ts = act.get("startTimeLocal", act.get("beginTimestamp"))
                            if isinstance(raw_ts, (int, float)):
                                activity_date = pd.to_datetime(raw_ts, unit="ms").isoformat()
                            elif raw_ts:
                                activity_date = str(raw_ts)
                            else:
                                continue

                            distance = safe_float(act.get("distance"))
                            moving_time = safe_float(act.get("movingDuration", act.get("duration", act.get("movingTime"))))
                            elapsed_time = safe_float(act.get("elapsedDuration", act.get("elapsedTime", moving_time)))
                            avg_speed = safe_float(act.get("avgSpeed", act.get("averageSpeed")))
                            avg_hr = safe_float(act.get("avgHr", act.get("averageHR")))
                            max_hr = safe_float(act.get("maxHr", act.get("maxHR")))
                            avg_cadence = safe_float(act.get("avgBikeCadence", act.get("averageBikingCadence", act.get("averageCadence"))))
                            avg_power = safe_float(act.get("avgPower", act.get("averagePower")))
                            elevation_gain = safe_float(act.get("elevationGain"))

                            # Avoid duplicates even if intervals_activity_id has no UNIQUE constraint
                            insert_query = """
                            INSERT INTO activities (
                                id, user_id, intervals_activity_id, activity_date, distance, 
                                moving_time, elapsed_time, average_speed, average_hr, max_hr, 
                                average_cadence, average_power, elevation_gain
                            )
                            SELECT gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            WHERE NOT EXISTS (
                                SELECT 1 FROM activities WHERE user_id = %s AND intervals_activity_id = %s
                            );
                            """
                            
                            cursor.execute(
                                insert_query,
                                (
                                    user_id, activity_id, activity_date, distance,
                                    moving_time, elapsed_time, avg_speed, avg_hr, max_hr,
                                    avg_cadence, avg_power, elevation_gain,
                                    user_id, activity_id
                                )
                            )
                            inserted_count += cursor.rowcount
                except Exception as e:
                    print(f"Error parsing summary JSON {json_path}: {e}")
                    conn.rollback()

process_summaries(temp_folder)
conn.commit()

# --- POWER METER DATE FILTERING ---
try:
    cursor.execute(
        "SELECT power_meter, power_meter_install_date, power_meter_month, power_meter_year FROM users WHERE id = %s",
        (user_id,)
    )
    user_row = cursor.fetchone()
    if user_row:
        has_power_meter, install_date, pm_month, pm_year = user_row
        cutoff_datetime = None
        if str(has_power_meter).lower() in ["true", "yes", "1"]:
            if install_date:
                cutoff_datetime = pd.to_datetime(install_date)
            elif pm_month and pm_year:
                try:
                    if isinstance(pm_month, str):
                        month_num = datetime.strptime(pm_month[:3], "%b").month
                    else:
                        month_num = int(pm_month)
                    cutoff_datetime = pd.Timestamp(year=int(pm_year), month=month_num, day=1)
                except Exception as e:
                    print(f"[preprocess.py] Could not parse power meter month/year: {e}")

        if cutoff_datetime is not None:
            print(f"[preprocess.py] Filtering out activities prior to power meter installation date: {cutoff_datetime.strftime('%Y-%m-%d')}")
            delete_query = "DELETE FROM activities WHERE user_id = %s AND activity_date < %s;"
            cursor.execute(delete_query, (user_id, cutoff_datetime))
            deleted_count = cursor.rowcount
            conn.commit()
            print(f"[preprocess.py] Discarded {deleted_count} pre-power-meter activities.")
except Exception as e:
    print(f"[preprocess.py] Power meter calibration check skipped or failed: {e}")

cursor.close()
conn.close()

print(f"[preprocess.py] Successfully synced {inserted_count} cycling activity records into database baseline.")
