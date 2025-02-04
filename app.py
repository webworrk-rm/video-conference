from flask import Flask, request, jsonify
import requests
from flask_pymongo import PyMongo
from bson import ObjectId
import os
from flask_cors import CORS  # ✅ Import CORS

app = Flask(__name__)

# ✅ Corrected CORS setup
CORS(app, resources={r"/*": {"origins": "*"}})  # Allows all domains
# If you want to restrict it to Netlify only, use this:
# CORS(app, origins=["https://*.netlify.app"])  

# MongoDB Configuration
mongo_uri = os.getenv("MONGO_URI")

if not mongo_uri:
    print("⚠️ MONGO_URI is missing! Using default local database.")
    mongo_uri = "mongodb://localhost:27017/video_conference"

print(f"✅ Connected to MongoDB URI: {mongo_uri}")  # ✅ Debug Log
app.config["MONGO_URI"] = mongo_uri
mongo = PyMongo(app)


dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")  # Debug log

        # Check if Daily.co API key is set
        if not dailyco_api_key or dailyco_api_key == "YOUR_DAILY_CO_API_KEY":
            print("❌ ERROR: Daily.co API Key is missing or incorrect!")
            return jsonify({"error": "Daily.co API Key is missing!"}), 500

        # Send request to Daily.co
        response = requests.post(dailyco_base_url, headers=headers, json={"privacy": "private"})
        data = response.json()
        
        print("✅ Daily.co Response:", data)  # Debug log

        # Check if API response contains URL
        if "url" in data:
            meeting = {
                "url": data["url"],
                "waiting_list": []
            }
            meeting_id = mongo.db.meetings.insert_one(meeting).inserted_id
            print("✅ Meeting created with ID:", meeting_id)  # Debug log
            return jsonify({"url": data["url"], "meeting_id": str(meeting_id)}), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)  # Debug log
            return jsonify({"error": "Failed to create meeting", "details": data}), 500

    except Exception as e:
        print("❌ Create Meeting Error:", str(e))  # Debug log
        return jsonify({"error": str(e)}), 500


@app.route("/api/join-meeting", methods=["POST"])
def join_meeting():
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        user = {"id": str(ObjectId()), "user_name": data.get("user_name")}
        
        mongo.db.meetings.update_one({"_id": ObjectId(meeting_id)}, {"$push": {"waiting_list": user}})
        return jsonify({"message": "User added to waiting list", "user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        user_id = data.get("user_id")
        
        meeting = mongo.db.meetings.find_one({"_id": ObjectId(meeting_id)})
        waiting_list = meeting.get("waiting_list", [])
        user = next((p for p in waiting_list if p["id"] == user_id), None)
        
        if user:
            mongo.db.meetings.update_one({"_id": ObjectId(meeting_id)}, {"$pull": {"waiting_list": {"id": user_id}}})
            return jsonify({"message": "User admitted", "user": user}), 200
        else:
            return jsonify({"error": "User not found in waiting list"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
