import os
import functions_framework
from Game.Matches import game_launcher, generate_schedule_double_round
from Helpers.telegram_manager import send_log_message
from flask import Flask, jsonify, request

from Game.freshness_update import update_freshness_for_team
from Training.training import complete_training

app = Flask(__name__)


@app.route("/", methods=["POST"])
def LetscoachModel():
    """Cloud Function that runs the match algorithm"""
    try:
        send_log_message("Cloud function running now")
        # request_json = dict(match_id=259,away_team_id=67,home_team_id=74)
        request_json = request.get_json(silent=True)
        if request_json.get('type') == 'training':
            res = complete_training(request_json.get('training_id'))
        if request_json.get('type') == 'freshness_update':
            res = update_freshness_for_team(request_json.get('team_id'))
        else:
            away_team_id = request_json.get('away_team_id')
            home_team_id = request_json.get('home_team_id')
            match_id = request_json.get('match_id')

            res = game_launcher(dict(away_team_id=away_team_id, home_team_id=home_team_id, match_id=match_id))

        return jsonify({"message": res}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# LetscoachModel()
# generate_schedule_double_round(4,'11.03.2025', 1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
