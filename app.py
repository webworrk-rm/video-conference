from flask import Flask, request, jsonify
import requests
from flask_pymongo import PyMongo
from bson import ObjectId
import os
from flask_cors import CORS

app = Flask(__name__)

# ✅ Corrected CORS setup (Allow all origins or restrict as needed)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ MongoDB Configuration (Using Render Environment Variables)
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb+srv://webworrkteam:<db_password>@cluster0.yr247.mongodb.net/video_conference?retryWrites=true&w=majority")
mongo = PyMongo(app)

# ✅ Define Database and Collection in Code
db = mongo.cx["video_conference"]
meetings_collection = db["meetings"]

# ✅ Daily.co API Configuration
dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

# ✅ API to create a meeting and store in MongoDB
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        response = requests.post(dailyco_base_url, headers=headers, json={"privacy": "private"})
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            meeting = {
                "url": data["url"],
                "waiting_list": []
            }
            meeting_id = meetings_collection.insert_one(meeting).inserted_id
            print(f"✅ Meeting stored in MongoDB: ID = {meeting_id}, URL = {data['url']}")

            # Retrieve and log stored meeting
            stored_meeting = meetings_collection.find_one({"_id": meeting_id})
            print(f"🔍 Stored Meeting Data: {stored_meeting}")

            return jsonify({"url": data["url"], "meeting_id": str(meeting_id)}), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500

    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ API to get all stored meetings from MongoDB
@app.route("/api/get-meetings", methods=["GET"])
def get_meetings():
    try:
        meetings = list(meetings_collection.find({}, {"_id": 1, "url": 1}))
        for meeting in meetings:
            meeting["_id"] = str(meeting["_id"])  # Convert ObjectId to string
        return jsonify({"meetings": meetings}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API to join a meeting (adds user to waiting list)
@app.route("/api/join-meeting", methods=["POST"])
def join_meeting():
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        user = {"id": str(ObjectId()), "user_name": data.get("user_name")}

        meetings_collection.update_one({"_id": ObjectId(meeting_id)}, {"$push": {"waiting_list": user}})
        return jsonify({"message": "User added to waiting list", "user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API to admit a participant from waiting list
@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        user_id = data.get("user_id")

        meeting = meetings_collection.find_one({"_id": ObjectId(meeting_id)})
        waiting_list = meeting.get("waiting_list", [])
        user = next((p for p in waiting_list if p["id"] == user_id), None)

        if user:
            meetings_collection.update_one({"_id": ObjectId(meeting_id)}, {"$pull": {"waiting_list": {"id": user_id}}})
            return jsonify({"message": "User admitted", "user": user}), 200
        else:
            return jsonify({"error": "User not found in waiting list"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
