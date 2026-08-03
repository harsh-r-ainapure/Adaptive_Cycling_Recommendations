import pool from "../config/db.js";
import axios from "axios"
import jwt from "jsonwebtoken"


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


const signup_redirectt = async (req , res , next ) => {
 try{
   const authURL =
    "https://intervals.icu/oauth/authorize?" +
    new URLSearchParams({
        client_id: process.env.INTERVALS_CLIENT_ID,
        redirect_uri: process.env.INTERVALS_REDIRECT_URI,
        response_type: "code",
        scope: "ACTIVITY:READ"
    });
    res.redirect(authURL)
 }
 catch(err){
    console.log(err.response?.status);
    console.log(err.response?.headers);
    console.log(err.response?.data);

    return res.status(500).json({
        message: "Internal Server Error"
    });
 }

}

const signup_callback = async (req , res ,  next) => {
    try{

        const code = req.query.code;

        if(!code){
            return res.status(400).json({message:"Error occured"});
        }

       const response = await axios.post(
    "https://intervals.icu/api/oauth/token",
    new URLSearchParams({
        grant_type: "authorization_code",
        code,
        client_id: process.env.INTERVALS_CLIENT_ID,
        client_secret: process.env.INTERVALS_CLIENT_SECRET,
        redirect_uri: process.env.INTERVALS_REDIRECT_URI
    }),
    {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    }
);
   
const {
    access_token,
    athlete,
    scope 
} = response.data;

const interval_id = athlete.id;
const name = athlete.name;



const result = await pool.query(
    `
    INSERT INTO USERS (ACCESS_TOKEN,INTERVALS_ID,NAME,SCOPE) VALUES($1,$2,$3,$4 )

    ON CONFLICT (intervals_id)

DO UPDATE SET
    access_token = EXCLUDED.access_token,
    name = EXCLUDED.name,
    scope = EXCLUDED.scope,
    updated_at = NOW()

RETURNING id;
    `,[access_token,interval_id,name,scope]
)

const userId = result.rows[0].id;
const token = jwt.sign(
    {
        id:userId
    },
    process.env.JWT_SECRET,

    {
        expiresIn:"7d"
    }
)

res.redirect(`${process.env.FRONTEND_URL}?token=${token}`);
    }
    catch(err){
        console.log("The error is " ,err)
        return res.status(500).json({
    message: "Internal Server Error"
});
    }
}



export {
    signup_callback,
    signup_redirectt,
    saveProfile
};