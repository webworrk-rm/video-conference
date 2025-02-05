from flask import Flask, request, jsonify
import requests
from flask_pymongo import PyMongo
import os
from flask_cors import CORS

app = Flask(__name__)

# ✅ Corrected CORS setup (Allow all origins or restrict as needed)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/video_conference")
mongo = PyMongo(app)
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

# ✅ API to create a meeting (Host URL & Participant URL)
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        response = requests.post(dailyco_base_url, headers=headers, json={"privacy": "public"})
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            host_url = f"{data['url']}?t=host"
            participant_url = f"{data['url']}?t=participant"
            print(f"✅ Meeting created: Host URL = {host_url}, Participant URL = {participant_url}")
            return jsonify({
                "host_url": host_url,
                "participant_url": participant_url
            }), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ API to join a meeting (Participants must wait for approval)
@app.route("/api/join-meeting", methods=["POST"])
def join_meeting():
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        user = {"id": str(ObjectId()), "user_name": data.get("user_name"), "status": "pending"}

        meetings_collection.update_one({"_id": ObjectId(meeting_id)}, {"$push": {"waiting_list": user}})
        return jsonify({"message": "User is waiting for approval", "user": user}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API to admit a participant from the waiting list
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
            user["status"] = "approved"
            meetings_collection.update_one(
                {"_id": ObjectId(meeting_id)},
                {"$pull": {"waiting_list": {"id": user_id}}}
            )
            return jsonify({"message": "User admitted", "user": user}), 200
        else:
            return jsonify({"error": "User not found in waiting list"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
