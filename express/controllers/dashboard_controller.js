import pool from "../config/db.js";

const get_dashboard = async (req, res) => {

    try {

        const userId = req.user.id;

        const result = await pool.query(
            `
            SELECT

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

                p.estimated_power,
                p.fatigue,
                p.cumulative_fatigue,
                p.baseline_power,
                p.baseline_hr,
                p.baseline_distance,
                p.baseline_elevation,
                p.current_capacity,
                p.capacity_deviation,
                p.variation,
                p.severity,
                p.percent_change

            FROM activities a

            INNER JOIN predictions p
                ON a.id = p.activity_id

            WHERE a.user_id = $1

            ORDER BY a.activity_date ASC;
            `,
            [userId]
        );

        return res.status(200).json(result.rows);

    }
    catch(err){

        console.log(err);

        return res.status(500).json({
            message:"Dashboard fetch failed"
        });

    }

};

export { get_dashboard };