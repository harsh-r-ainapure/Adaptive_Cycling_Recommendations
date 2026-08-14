import pool from "../config/db.js";

const get_dashboard = async (req, res) => {

    try {

        const userId = req.user.id;

        const result = await pool.query(
            `
            SELECT

                /* =========================
                   ACTIVITY DATA
                   ========================= */

                a.id AS activity_id,
                a.intervals_activity_id,
                a.activity_date,
                a.distance,
                a.moving_time,
                a.elapsed_time,
                a.average_speed,
                a.average_power,
                a.average_hr,
                a.max_hr,
                a.average_cadence,
                a.elevation_gain,
                a.elevation_loss,


                /* =========================
                   ACTIVITY FEATURES
                   ========================= */

                f.gradient,
                f.rel_speed,
                f.hr_sd,
                f.hr_recovery_slope,
                f.rolling_percent,
                f.stopping_percent,
                f.power_zone_percent,
                f.recovery_zone_percent,
                f.baseline_hr AS feature_baseline_hr,

                f.vam,
                f.ele_sd,
                f.cadence_sd,
                f.cadence_drift,
                f.stop_hr_recovery_percent,
                f.cadence_ratio,
                f.heart_ratio,
                f.ele_ratio,


                /* =========================
                   PREDICTIONS
                   ========================= */

                p.estimated_power,
                p.fatigue,
                p.cumulative_fatigue,
                p.baseline_power,

                p.baseline_hr AS prediction_baseline_hr,

                p.baseline_distance,
                p.baseline_elevation,
                p.current_capacity,
                p.capacity_deviation,
                p.variation,
                p.severity,
                p.percent_change,


                /* =========================
                   RECOMMENDATIONS
                   ========================= */

                r.recommended_distance,
                r.recommended_elevation,
                r.recommended_hr

            FROM activities a

            /* Prediction must exist for dashboard entry */
            INNER JOIN predictions p
                ON a.id = p.activity_id

            /* Features may not exist for every activity */
            LEFT JOIN activity_features f
                ON a.id = f.activity_id

            /* Recommendation may not exist for every activity */
            LEFT JOIN recommendations r
                ON a.id = r.activity_id

            WHERE a.user_id = $1

            ORDER BY a.activity_date ASC;
            `,
            [userId]
        );

        return res.status(200).json(result.rows);

    }
    catch (err) {

        console.error("Dashboard fetch failed:", err);

        return res.status(500).json({
            message: "Dashboard fetch failed"
        });

    }

};

export { get_dashboard };