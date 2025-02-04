from flask import Flask, request, jsonify
import requests
from flask_pymongo import PyMongo
from bson import ObjectId
import os

app = Flask(__name__)

# MongoDB Configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI", "mongodb://localhost:27017/video_conference")
mongo = PyMongo(app)

dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        response = requests.post(dailyco_base_url, headers=headers, json={"privacy": "private"})
        data = response.json()
        if "url" in data:
            meeting = {
                "url": data["url"],
                "waiting_list": []
            }
            meeting_id = mongo.db.meetings.insert_one(meeting).inserted_id
            return jsonify({"url": data["url"], "meeting_id": str(meeting_id)}), 201
        else:
            return jsonify({"error": "Failed to create meeting"}), 500
    except Exception as e:
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
