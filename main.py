import os
from Helpers.telegram_manager import send_log_message
from flask import Flask, jsonify, request

from LetsCoachModel.types_handler import ACTION_MAP

app = Flask(__name__)

@app.route("/", methods=["POST"])
def LetscoachModel():
    """Cloud Function that runs the match algorithm"""
    try:
        send_log_message("Cloud function running now")
        data = request.get_json(silent=True) or {}
        action_type = data.get('type')

        handler = ACTION_MAP.get(action_type)
        if handler:
            result = handler(data)
            return jsonify({"message": result}), 200
        else:
            send_log_message(f"Error : Unknown type: {action_type}")
            return jsonify({"error": f"Unknown type: {action_type}"}), 400

    except Exception as e:
        send_log_message(f"Error : {str(e)}")
        return jsonify({"error": str(e)}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
