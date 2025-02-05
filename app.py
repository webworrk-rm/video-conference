from flask import Flask, request, jsonify
import requests
from flask_cors import CORS
import os
import time
import json  # For working with JSON data in app_data

# For WebSockets (you'll need to install: pip install websockets)
import asyncio
import websockets

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

dailyco_api_key = os.getenv("DAILY_CO_API_KEY", "YOUR_DAILY_CO_API_KEY")
dailyco_base_url = "https://api.daily.co/v1/rooms"
token_api_url = "https://api.daily.co/v1/meeting-tokens"

headers = {
    "Authorization": f"Bearer {dailyco_api_key}",
    "Content-Type": "application/json"
}

waiting_list = {}  # Store participant join requests (now with more info)

# WebSocket setup
connected_clients = {}  # Store connected WebSocket clients

async def handle_websocket(websocket, path):
    connected_clients[path] = websocket  # Store the client
    try:
        while True:  # Keep the connection open
            message = await websocket.recv() # Expecting message from Client
            # Handle messages from the client if needed
            # For example, client can send a message to server.
            print(f"Received message from client: {message}")
            # You can process messages from clients here if you want to add more features.
            # For example, you could have a chat feature or other interactive elements.
    except websockets.exceptions.ConnectionClosedError:
        pass # Handle client disconnect
    finally:
        del connected_clients[path]  # Remove the client when disconnected


async def start_websocket_server():
    async with websockets.serve(handle_websocket, "0.0.0.0", 8765): # running on port 8765
        await asyncio.Future()  # Run forever

# Start the WebSocket server in a separate thread
import threading
def start_server_thread():
    asyncio.run(start_websocket_server())

websocket_thread = threading.Thread(target=start_server_thread)
websocket_thread.daemon = True  # Allow the main thread to exit
websocket_thread.start()


@app.route("/", methods=["GET"])
def home():
    return jsonify({"message": "API is running!"}), 200

@app.route("/api/create-meeting", methods=["POST"])
def create_meeting():
    try:
        # ... (room creation code)

        if "url" in data:
            meeting_url = data["url"]
            room_name = data["name"]

            host_token = generate_token(room_name, is_owner=True)
            participant_token = generate_token(room_name, is_owner=False)  # Generate participant token

            host_url = f"{meeting_url}?t={host_token}"
            participant_url = f"{meeting_url}?t={participant_token}" # Construct participant URL

            print(f"Host URL: {host_url}")
            print(f"Participant URL: {participant_url}") # Print participant URL

            return jsonify({
                "host_url": host_url,
                "room_name": room_name,
                "participant_url": participant_url  # Include participant URL in the response
            }), 201
        else:
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_token(room_name, is_owner=False, user_name=None):
    try:
        properties = {
            "room_name": room_name,
            "is_owner": is_owner,
            "exp": int(time.time()) + 3600
        }
        if user_name:
            properties["app_data"] = json.dumps({"user_name": user_name})  # Stringify JSON

        response = requests.post(token_api_url, headers=headers, json={"properties": properties})
        token_data = response.json()
        return token_data.get("token")
    except Exception as e:
        return None


@app.route("/api/participant-token", methods=["POST"])
def get_participant_token():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        participant_token = generate_token(room_name, is_owner=False, user_name=user_name)

        if participant_token:
            waiting_list[room_name] = waiting_list.get(room_name, [])
            waiting_list[room_name].append({"user_name": user_name, "approved": False})

            # Notify connected host clients for this room.
            for path, client in connected_clients.items():
                if path.startswith(f"/{room_name}"): # Check if client is for the same room
                    try:
                        asyncio.run(client.send(json.dumps({"type": "join_request", "user_name": user_name, "room_name": room_name}))) # Send JSON message
                    except Exception as e:
                        print(f"Error sending message to client: {e}")

            return jsonify({"token": participant_token}), 200
        else:
            return jsonify({"error": "Failed to generate token"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/waiting-list/<room_name>", methods=["GET"])
def get_waiting_list(room_name):
    try:
       return jsonify({"waiting_list": waiting_list.get(room_name, [])}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admit-participant", methods=["POST"])
def admit_participant():
    try:
        data = request.json
        room_name = data.get("room_name")
        user_name = data.get("user_name")

        if room_name not in waiting_list:
            return jsonify({"error": "Room not found"}), 404

        # Update waiting list and notify clients
        for i, participant in enumerate(waiting_list[room_name]):
            if participant["user_name"] == user_name:
                waiting_list[room_name][i]["approved"] = True
                # Notify all clients (including the admitted participant)
                for path, client in connected_clients.items():
                    if path.startswith(f"/{room_name}"):
                         try:
                             asyncio.run(client.send(json.dumps({"type": "user_admitted", "user_name": user_name, "room_name": room_name})))
                         except Exception as e:
                            print(f"Error sending message to client: {e}")
                break # Exit after finding and updating user

        return jsonify({"message": "User admitted", "user_name": user_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
