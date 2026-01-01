import os
import sys
import traceback
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.info("🚀 Model service starting up...")

# הוסף את השורה הזו למצב development
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request

app = Flask(__name__)

# Import dependencies with error handling
try:
    from Helpers.telegram_manager import send_log_message
except Exception as e:
    print(f"Error importing telegram_manager: {e}")
    traceback.print_exc()
    def send_log_message(msg):
        print(f"[TELEGRAM] {msg}")

try:
    from types_handler import ACTION_MAP
except Exception as e:
    print(f"Error importing action handlers: {e}")
    traceback.print_exc()
    ACTION_MAP = {}

# Import scheduler lazily - only when needed
match_scheduler = None

def get_scheduler():
    global match_scheduler
    if match_scheduler is None:
        try:
            from scheduler import match_scheduler as sched
            match_scheduler = sched
        except Exception as e:
            print(f"Error importing scheduler: {e}")
            traceback.print_exc()
            class DummyScheduler:
                is_running = False
                def get_jobs(self):
                    return []
            match_scheduler = DummyScheduler()
    return match_scheduler

@app.route("/", methods=["POST"])
def LetscoachModel():
    """Cloud Function that runs the match algorithm"""
    try:
        logger.info("📥 Request received")
        data = request.get_json(silent=True) or {}
        action_type = data.get('type')
        logger.info(f"🎯 Action type: {action_type}, Data: {data}")

        # Reload types_handler to get latest code (important for development)
        import importlib
        import types_handler
        importlib.reload(types_handler)
        from types_handler import ACTION_MAP
        logger.info("🔄 Reloaded types_handler to get latest code")

        handler = ACTION_MAP.get(action_type)
        if handler:
            logger.info(f"✅ Handler found for {action_type}, executing...")
            result = handler(data)
            logger.info(f"✅ Handler completed: {result}")
            send_log_message(f"✅ {action_type} completed: {result}")
            return jsonify({"message": result}), 200
        else:
            logger.error(f"❌ Unknown type: {action_type}")
            send_log_message(f"Error : Unknown type: {action_type}")
            return jsonify({"error": f"Unknown type: {action_type}"}), 400

    except Exception as e:
        logger.error(f"❌ Error: {str(e)}", exc_info=True)
        send_log_message(f"Error : {str(e)}")
        return jsonify({"error": str(e)}), 200


# ===== Scheduler Routes =====

@app.route("/scheduler/start", methods=["POST"])
def start_scheduler():
    """התחל את ה-scheduler"""
    try:
        data = request.get_json(silent=True) or {}
        check_interval = data.get('check_interval_minutes', 5)
        
        get_scheduler().start(check_interval_minutes=check_interval)
        
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
        get_scheduler().stop()
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
        get_scheduler().pause()
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
        get_scheduler().resume()
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
        scheduler = get_scheduler()
        status = {
            "is_running": scheduler.is_running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": str(job.next_run_time)
                }
                for job in scheduler.get_jobs()
            ]
        }
        return jsonify(status), 200
    except Exception as e:
        error_msg = f"❌ שגיאה בקבלת סטטוס: {e}"
        return jsonify({"error": error_msg}), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
