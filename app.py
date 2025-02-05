from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Daily.co API Configuration
dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"
token_api_url = "https://api.daily.co/v1/meeting-tokens"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

waiting_list = {}  # Store participant join requests

@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

# ✅ API to Create a Meeting with Controlled Access
@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        print("✅ Received request to create a meeting")

        # Set meeting expiration (1 hour from now)
        future_timestamp = int(time.time()) + 3600

        # ✅ Create a Private Meeting with Knocking (Host Approval Required)
        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "properties": {
                "enable_knocking": True,  # ✅ Participants must request to join
                "exp": future_timestamp,
                "start_audio_off": True,
                "start_video_off": True,
                "enable_chat": True,
                "enable_network_ui": True,
                "max_participants": 20
            }
        })
        data = response.json()
        print("✅ Daily.co Response:", data)

        if "url" in data:
            meeting_url = data["url"]
            room_name = data["name"]

            # ✅ Generate Host & Participant Tokens
            host_token = generate_token(room_name, is_owner=True)
            participant_token = generate_token(room_name, is_owner=False)

            if host_token and participant_token:
                host_url = f"{meeting_url}?t={host_token}"
                participant_url = f"{meeting_url}?t={participant_token}"
                waiting_list[room_name] = []  # Initialize waiting list

                print(f"✅ Meeting created: Host URL = {host_url}, Participant URL = {participant_url}")
                return jsonify({
                    "host_url": host_url,
                    "participant_url": participant_url
                }), 201
            else:
                return jsonify({"error": "Failed to generate meeting tokens"}), 500
        else:
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        print("❌ Create Meeting Error:", str(e))
        return jsonify({"error": str(e)}), 500

# ✅ Function to Generate Secure Meeting Tokens
def generate_token(room_name, is_owner=False):
    try:
        print(f"🔍 Generating token for room: {room_name}, is_owner: {is_owner}")

        response = requests.post(token_api_url, headers=headers, json={
            "properties": {
                "room_name": room_name,
                "is_owner": is_owner,  # ✅ Hosts have control; participants require approval
                "exp": int(time.time()) + 3600  # ✅ Token expires in 1 hour
            }
        })
        token_data = response.json()
        print("✅ Token API Response:", token_data)
        return token_data.get("token")
    except Exception as e:
        print(f"❌ Token Generation Failed: {e}")
        return None

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

        # Remove participant from waiting list
        waiting_list[room_name] = [p for p in waiting_list[room_name] if p["user_name"] != user_name]

        # ✅ Approve participant in Daily.co
        approve_participant(room_name, user_name)

        print(f"✅ {user_name} admitted to {room_name}")
        return jsonify({"message": "User admitted", "user_name": user_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Function to Approve Participant in Daily.co
def approve_participant(room_name, user_name):
    try:
        # Daily.co API endpoint to approve a participant
        approve_url = f"https://api.daily.co/v1/rooms/{room_name}/participants/{user_name}/approve"
        response = requests.post(approve_url, headers=headers)
        if response.status_code == 200:
            print(f"✅ Approved {user_name} in Daily.co")
        else:
            print(f"❌ Failed to approve {user_name}: {response.json()}")
    except Exception as e:
        print(f"❌ Approval Error: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
