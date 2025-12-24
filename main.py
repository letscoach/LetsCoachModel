import os
import sys
from Helpers.telegram_manager import send_log_message
from flask import Flask, jsonify, request

# הוסף את השורה הזו למצב development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from types_handler import ACTION_MAP
from scheduler import match_scheduler

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


# ===== Scheduler Routes =====

@app.route("/scheduler/start", methods=["POST"])
def start_scheduler():
    """התחל את ה-scheduler"""
    try:
        data = request.get_json(silent=True) or {}
        check_interval = data.get('check_interval_minutes', 5)
        
        match_scheduler.start(check_interval_minutes=check_interval)
        
        msg = f"✅ Scheduler התחיל - בדיקה כל {check_interval} דקות"
        send_log_message(msg)
        return jsonify({"message": msg}), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בהתחלת Scheduler: {e}"
        send_log_message(error_msg)
        return jsonify({"error": error_msg}), 400


@app.route("/scheduler/stop", methods=["POST"])
def stop_scheduler():
    """עצור את ה-scheduler"""
    try:
        match_scheduler.stop()
        send_log_message("⏹️ Scheduler עוצר")
        return jsonify({"message": "Scheduler עוצר"}), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בעצירת Scheduler: {e}"
        send_log_message(error_msg)
        return jsonify({"error": error_msg}), 400


@app.route("/scheduler/pause", methods=["POST"])
def pause_scheduler():
    """השהה את ה-scheduler"""
    try:
        match_scheduler.pause()
        send_log_message("⏸️ Scheduler משהוי")
        return jsonify({"message": "Scheduler משהוי"}), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בהשהיית Scheduler: {e}"
        send_log_message(error_msg)
        return jsonify({"error": error_msg}), 400


@app.route("/scheduler/resume", methods=["POST"])
def resume_scheduler():
    """המשך את ה-scheduler"""
    try:
        match_scheduler.resume()
        send_log_message("▶️ Scheduler מתחדש")
        return jsonify({"message": "Scheduler מתחדש"}), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בהמשך Scheduler: {e}"
        send_log_message(error_msg)
        return jsonify({"error": error_msg}), 400


@app.route("/scheduler/status", methods=["GET"])
def scheduler_status():
    """קבל את סטטוס ה-scheduler"""
    try:
        status = {
            "is_running": match_scheduler.is_running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time)
                }
                for job in match_scheduler.get_jobs()
            ]
        }
        return jsonify(status), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בקבלת סטטוס: {e}"
        return jsonify({"error": error_msg}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
