def create_meeting():
    try:
        future_timestamp = int(time.time()) + 3600

        response = requests.post(dailyco_base_url, headers=headers, json={
            "privacy": "private",
            "properties": {
                "enable_knocking": True,
                "exp": future_timestamp,
                "start_audio_off": True,
                "start_video_off": True,
                "enable_chat": True,
                "enable_network_ui": True,
                "max_participants": 20
            }
        })
        data = response.json()

        if "url" in data:
            meeting_url = data["url"]
            room_name = data["name"]

            host_token = generate_token(room_name, is_owner=True)
            participant_token = generate_token(room_name, is_owner=False)

            if host_token and participant_token:
                host_url = f"{meeting_url}?t={host_token}"
                participant_url = f"{meeting_url}?t={participant_token}"

                waiting_list[room_name] = []

                print(f"Host URL: {host_url}")  # Print the host URL
                print(f"Participant URL: {participant_url}")  # Print the participant URL

                return jsonify({
                    "host_url": host_url,
                    "participant_url": participant_url
                }), 201
            else:
                return jsonify({"error": "Failed to generate meeting tokens"}), 500
        else:
            return jsonify({"error": "Failed to create meeting", "details": data}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def generate_token(room_name, is_owner=False):
    try:
        response = requests.post(token_api_url, headers=headers, json={
            "properties": {
                "room_name": room_name,
                "is_owner": is_owner,
                "exp": int(time.time()) + 3600
            }
        })
        token_data = response.json()
        return token_data.get("token")
    except Exception as e:
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

        waiting_list[room_name] = [p for p in waiting_list[room_name] if p["user_name"] != user_name]

        print(f"✅ {user_name} admitted to {room_name}")
        return jsonify({"message": "User admitted", "user_name": user_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
