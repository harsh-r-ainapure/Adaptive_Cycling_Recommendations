import pool from "../config/db";
import axios from "axios"


const signup_redirectt = async (req , res , next ) => {
 try{
    const authURL =
    `https://intervals.icu/oauth/authorize` +
    `?client_id=${process.env.INTERVALS_CLIENT_ID}` +
    `&redirect_uri=${encodeURIComponent(process.env.INTERVALS_REDIRECT_URI)}` +
    `&response_type=code`;

    res.redirect(authURL)
 }
 catch(err){
    console.log("The error is " , err)
 }

}

const signup_callback = async (req , res ,  next) => {
    try{

        const code = req.query.code;

        if(!code){
            return res.status(400).json({message:"Error occured"});
        }

        const response = await axios.post(
    "https://intervals.icu/oauth/token",
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



await pool.query(
    `
    INSERT INTO USERS (ACCESS_TOKEN,INTERVALS_ID,NAME,SCOPE) VALUES($1,$2,$3,$4 )

    ON CONFLICT (intervals_id)

DO UPDATE SET
    access_token = EXCLUDED.access_token,
    name = EXCLUDED.name,
    scope = EXCLUDED.scope,
    updated_at = NOW();
    `,[access_token,interval_idid,name,scope]
)
    }
    catch(err){
        console.log("The error is " ,err)
    }
}

export {
    signup_callback,
    signup_redirectt
};