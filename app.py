from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")  # Replace with your actual API key
dailyco_base_url = "https://api.daily.co/v1/rooms"
token_api_url = "https://api.daily.co/v1/meeting-tokens"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

waiting_list = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

@app.route("/api/create-meeting", methods=["POST"])


# ✅ API for Participants to Request to Join (Sent to Host)
@app.route("/api/request-join", methods=["POST"])
def request_join():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        waiting_list[room_name].append({"user_name": user_name})
        print(f"🔔 Join request received: {user_name} for {room_name}")

        return jsonify({"message": "Request sent to host", "room_name": room_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for Host to View Waiting List
@app.route("/api/waiting-list/<room_name>", methods=["GET"])
def get_waiting_list(room_name):
    try:
        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        return jsonify({"waiting_list": waiting_list[room_name]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for Host to Admit a Participant
@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        waiting_list[room_name] = [p for p in waiting_list[room_name] if p["user_name"] != user_name]

        print(f"✅ {user_name} admitted to {room_name}")
        return jsonify({"message": "User admitted", "user_name": user_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
