from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os

app = Flask(__name__)

# ✅ Corrected CORS setup (Allow all origins or restrict as needed)
CORS(app, resources={r"/*": {"origins": "*"}})

# ✅ Daily.co API Configuration
dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

# In-memory waiting list
waiting_list = {}

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

# ✅ API to create a meeting (Private with host controls)
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        # Create a meeting with **private** access and knocking feature enabled
        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "exp": 3600,  # Meeting valid for 1 hour
            "properties": {
                "enable_knocking": True  # Forces participants to wait for approval
            }
        })
        data = response.json()

        print("✅ Daily.co Response:", data)

        if "url" in data:
            room_name = data["name"]
            waiting_list[room_name] = []  # Initialize waiting list for this room

            host_url = f"{data['url']}?t=host"
            participant_url = f"{data['url']}?t=participant"
            print(f"✅ Meeting created: Host URL = {host_url}, Participant URL = {participant_url}")
            return jsonify({
                "url": participant_url,  # Participants get this link
                "host_url": host_url,     # Host gets this link
                "room_name": room_name
            }), 201
        else:
            print("❌ ERROR: Daily.co API failed", data)
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ API to request to join a meeting (Participant requests admission)
@app.route("/api/request-join", methods=["POST"])
def request_join():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        user_request = {"user_name": user_name}
        waiting_list[room_name].append(user_request)

        print(f"🔔 Join request received: {user_name} for {room_name}")

        return jsonify({"message": "Request sent to host", "room_name": room_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for host to get waiting list
@app.route("/api/waiting-list/<room_name>", methods=["GET"])
def get_waiting_list(room_name):
    try:
        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        return jsonify({"waiting_list": waiting_list[room_name]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ API for host to admit participant
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
