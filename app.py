from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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

# In-memory storage for waiting lists
waiting_list = {}

@app.route("/", methods=["GET"])
def home():
    """Health check endpoint"""
    return jsonify({"message": "API is running!", "status": "healthy"}), 200

@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    """Create a new meeting with host controls"""
    try:
        # Set meeting expiration (1 hour from now)
        expiration = int(time.time()) + 3600

        # Create a private meeting room with knocking enabled
        response = requests.post(
            dailyco_base_url,
            headers=headers,
            json={
                "privacy": "private",
                "properties": {
                    "enable_knocking": True,
                    "exp": expiration,
                    "start_audio_off": True,
                    "start_video_off": True,
                    "enable_chat": True,
                    "enable_network_ui": True,
                    "max_participants": 20
                }
            }
        )
        
        data = response.json()
        
        if "url" not in data:
            return jsonify({
                "error": "Failed to create meeting",
                "details": data
            }), 500

        meeting_url = data["url"]
        room_name = data["name"]

        # Generate tokens for host and participants
        host_token = generate_token(room_name, is_owner=True)
        participant_token = generate_token(room_name, is_owner=False)

        if not (host_token and participant_token):
            return jsonify({
                "error": "Failed to generate meeting tokens"
            }), 500

        # Create full URLs with tokens
        host_url = f"{meeting_url}?t={host_token}"
        participant_url = f"{meeting_url}?t={participant_token}"
        
        # Initialize waiting list for this room
        waiting_list[room_name] = []

        return jsonify({
            "host_url": host_url,
            "participant_url": participant_url,
            "room_name": room_name
        }), 201

    except Exception as e:
        return jsonify({
            "error": "Failed to create meeting",
            "details": str(e)
        }), 500

def generate_token(room_name, is_owner=False):
    """Generate a secure meeting token"""
    try:
        response = requests.post(
            token_api_url,
            headers=headers,
            json={
                "properties": {
                    "room_name": room_name,
                    "is_owner": is_owner,
                    "exp": int(time.time()) + 3600
                }
            }
        )
        
        token_data = response.json()
        return token_data.get("token")
        
    except Exception as e:
        print(f"Token generation failed: {e}")
        return None

@app.route("/api/request-join", methods=["POST"])
def request_join():
    """Handle participant join requests"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400

        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if not (room_name and user_name):
            return jsonify({
                "error": "Missing required fields"
            }), 400

        if room_name not in waiting_list:
            return jsonify({
                "error": "Room not found"
            }), 404

        # Add user to waiting list
        waiting_list[room_name].append({
            "user_name": user_name,
            "request_time": time.time()
        })

        return jsonify({
            "message": "Join request sent to host",
            "room_name": room_name,
            "position": len(waiting_list[room_name])
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to process join request",
            "details": str(e)
        }), 500

@app.route("/api/waiting-list/<room_name>", methods=["GET"])
def get_waiting_list(room_name):
    """Retrieve waiting list for a specific room"""
    try:
        if room_name not in waiting_list:
            return jsonify({
                "error": "Room not found"
            }), 404

        return jsonify({
            "waiting_list": waiting_list[room_name],
            "count": len(waiting_list[room_name])
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to retrieve waiting list",
            "details": str(e)
        }), 500

@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    """Admit a participant from the waiting list"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400

        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if not (room_name and user_name):
            return jsonify({
                "error": "Missing required fields"
            }), 400

        if room_name not in waiting_list:
            return jsonify({
                "error": "Room not found"
            }), 404

        # Remove participant from waiting list
        waiting_list[room_name] = [
            p for p in waiting_list[room_name]
            if p["user_name"] != user_name
        ]

        return jsonify({
            "message": "Participant admitted successfully",
            "user_name": user_name,
            "remaining_participants": len(waiting_list[room_name])
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to admit participant",
            "details": str(e)
        }), 500

@app.route("/api/remove-participant", methods=["POST"])
def remove_participant():
    """Remove a participant from the waiting list"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided"
            }), 400

        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if not (room_name and user_name):
            return jsonify({
                "error": "Missing required fields"
            }), 400

        if room_name not in waiting_list:
            return jsonify({
                "error": "Room not found"
            }), 404

        # Remove participant from waiting list
        waiting_list[room_name] = [
            p for p in waiting_list[room_name]
            if p["user_name"] != user_name
        ]

        return jsonify({
            "message": "Participant removed successfully",
            "user_name": user_name,
            "remaining_participants": len(waiting_list[room_name])
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to remove participant",
            "details": str(e)
        }), 500

@app.route("/api/clear-room/<room_name>", methods=["POST"])
def clear_room(room_name):
    """Clear all participants from a room's waiting list"""
    try:
        if room_name not in waiting_list:
            return jsonify({
                "error": "Room not found"
            }), 404

        waiting_list[room_name] = []

        return jsonify({
            "message": "Room cleared successfully",
            "room_name": room_name
        }), 200

    except Exception as e:
        return jsonify({
            "error": "Failed to clear room",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    # Get port from environment variable or default to 5000
    port = int(os.getenv("PORT", 5000))
    
    # Run the application
    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("FLASK_DEBUG", "true").lower() == "true"
    )
