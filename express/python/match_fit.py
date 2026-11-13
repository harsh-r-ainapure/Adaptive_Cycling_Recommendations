"""
match_fit.py <extract_dir> <out_json>

Finds the cycling FIT files in a Garmin export by CONTENT (not filename) and links
each one to its activityId in summarizedActivities.json.

Garmin names FIT files after an upload ID, which is NOT the activityId, so filename
matching never works. Instead:
  1. file_id.type must be 'activity' and session.sport must be cycling
  2. session.start_time must be within TOL_SECONDS of a cycling summary ride's start
  3. one FIT per ride (largest file wins; duplicates are uploads of the same ride)

Writes [{"path": ..., "activityId": ...}, ...] to <out_json>.
"""
import os, sys, json, datetime
from fitparse import FitFile

TOL_SECONDS = 300
CYCLING_WORDS = ("cycling", "biking", "ride")


def load_summary_rides(root):
    rides = {}  # activityId -> start epoch seconds (UTC)
    for dp, _, files in os.walk(root):
        for f in files:
            if "summarizedactivities.json" not in f.lower():
                continue
            try:
                with open(os.path.join(dp, f), "r", encoding="utf-8") as fh:
                    data = json.load(fh)
            except Exception as e:
                print(f"[match_fit] Cannot read {f}: {e}")
                continue
            if isinstance(data, list) and data and isinstance(data[0], dict) and "summarizedActivitiesExport" in data[0]:
                acts = data[0]["summarizedActivitiesExport"]
            elif isinstance(data, dict):
                acts = data.get("summarizedActivitiesExport", data.get("summarizedActivities", []))
            elif isinstance(data, list):
                acts = data
            else:
                acts = []
            for a in acts:
                if not isinstance(a, dict) or a.get("activityId") is None:
                    continue
                t = str(a.get("activityType", a.get("activityTypeId", ""))).lower()
                if not any(w in t for w in CYCLING_WORDS):
                    continue
                ts = a.get("startTimeGmt") or a.get("beginTimestamp")
                if ts is None:
                    continue
                rides[str(a["activityId"]).strip()] = float(ts) / 1000.0
    return rides


def is_cycling(sport, sub_sport):
    s = f"{sport or ''} {sub_sport or ''}".lower()
    return any(w in s for w in CYCLING_WORDS)


def inspect_fit(path):
    """Return (sport, sub_sport, start_epoch) for activity FITs, else None. Exits early on non-activity files."""
    ff = FitFile(path)
    fid = next(iter(ff.get_messages("file_id")), None)
    if fid is None:
        return None
    ftype = {x.name: x.value for x in fid}.get("type")
    if str(ftype).lower() not in ("activity", "4"):
        return None
    ses = next(iter(ff.get_messages("session")), None)
    if ses is None:
        return None
    d = {x.name: x.value for x in ses}
    st = d.get("start_time")
    if st is None:
        return None
    epoch = st.replace(tzinfo=datetime.timezone.utc).timestamp()
    return d.get("sport"), d.get("sub_sport"), epoch


def main():
    root, out_json = sys.argv[1], sys.argv[2]
    rides = load_summary_rides(root)
    print(f"[match_fit] {len(rides)} cycling rides in summary.")

    fits = []
    for dp, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(".fit"):
                fits.append(os.path.join(dp, f))
    print(f"[match_fit] Inspecting {len(fits)} FIT files...")

    best = {}  # activityId -> (size, path)
    cyc_fit = unmatched = errors = 0
    for p in fits:
        try:
            info = inspect_fit(p)
        except Exception:
            errors += 1
            continue
        if not info:
            continue
        sport, sub, epoch = info
        if not is_cycling(sport, sub):
            continue
        cyc_fit += 1
        aid = min(rides, key=lambda k: abs(rides[k] - epoch), default=None)
        if aid is None or abs(rides[aid] - epoch) > TOL_SECONDS:
            unmatched += 1
            print(f"[match_fit] Cycling FIT with no summary ride: {os.path.basename(p)}")
            continue
        size = os.path.getsize(p)
        if aid not in best or size > best[aid][0]:
            best[aid] = (size, p)

    result = [{"path": p, "activityId": aid} for aid, (_, p) in best.items()]
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(result, fh)
    print(f"[match_fit] cycling FITs={cyc_fit}, unreadable={errors}, unmatched={unmatched}, rides matched={len(result)}/{len(rides)}")


if __name__ == "__main__":
    main()
