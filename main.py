import os
import functions_framework
from Game.Matches import game_launcher
from Helpers.telegram_manager import send_log_message
from flask import Flask, jsonify, request

app = Flask(__name__)


@app.route("/", methods=["POST"])
def LetscoachModel():
    """Cloud Function that runs the match algorithm"""
    try:
        send_log_message("Cloud function running now")
        request_json = request.get_json(silent=True)

        away_team_id = request_json.get('away_team_id')
        home_team_id = request_json.get('home_team_id')
        match_id = request_json.get('match_id')

        res = game_launcher(dict(away_team_id=away_team_id, home_team_id=home_team_id, match_id=match_id))

        return jsonify({"message": res}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
