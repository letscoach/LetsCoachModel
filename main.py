import os
import sys
# DEBUG: Force rebuild for git update
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


# ===== Live Match Routes =====

# In-memory storage for active live matches (use Redis in production)
ACTIVE_LIVE_MATCHES = {}

@app.route("/live_match/init", methods=["POST"])
def init_live_match():
    """Initialize a new live match session"""
    try:
        from Game.live_match_api import live_match_simulator
        
        data = request.get_json(silent=True) or {}
        match_id = data.get('match_id')
        team1_id = data.get('team1_id')
        team2_id = data.get('team2_id')
        must_win = data.get('must_win', False)
        
        if not all([match_id, team1_id, team2_id]):
            return jsonify({"error": "Missing required fields"}), 400
        
        logger.info(f"🏟️ Initializing live match {match_id}: {team1_id} vs {team2_id}")
        
        match_state = live_match_simulator.initialize_match(
            match_id, team1_id, team2_id, must_win)
        
        ACTIVE_LIVE_MATCHES[match_id] = match_state
        
        return jsonify({
            "match_id": match_id,
            "team1_id": team1_id,
            "team2_id": team2_id,
            "zone_ratings": match_state['zone_ratings'],
            "interventions_left": match_state['interventions_left'],
            "status": "initialized"
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error initializing live match: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/live_match/simulate_period", methods=["POST"])
def simulate_period():
    """Simulate the next period of the match (10 game minutes)"""
    try:
        from Game.live_match_api import live_match_simulator
        
        data = request.get_json(silent=True) or {}
        match_id = data.get('match_id')
        period_minutes = data.get('period_minutes', 10)
        
        if not match_id:
            return jsonify({"error": "Missing match_id"}), 400
        
        match_state = ACTIVE_LIVE_MATCHES.get(match_id)
        if not match_state:
            return jsonify({"error": "Match not found"}), 404
        
        logger.info(f"⚽ Simulating period for match {match_id} (minute {match_state['current_minute']})")
        
        result = live_match_simulator.simulate_period(match_state, period_minutes)
        
        # Update stored state
        ACTIVE_LIVE_MATCHES[match_id] = match_state
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error simulating period: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/live_match/intervene", methods=["POST"])
def live_match_intervene():
    """Process a coaching intervention"""
    try:
        from Game.live_match_api import live_match_simulator
        
        data = request.get_json(silent=True) or {}
        match_id = data.get('match_id')
        team_id = data.get('team_id')
        action_type = data.get('action_type')  # 'substitution', 'formation', 'attitude'
        action_data = data.get('action_data', {})
        
        if not all([match_id, team_id, action_type]):
            return jsonify({"error": "Missing required fields"}), 400
        
        match_state = ACTIVE_LIVE_MATCHES.get(match_id)
        if not match_state:
            return jsonify({"error": "Match not found"}), 404
        
        logger.info(f"🔄 Intervention for match {match_id}: {action_type}")
        
        result = live_match_simulator.process_intervention(
            match_state, team_id, action_type, action_data)
        
        # Update stored state
        ACTIVE_LIVE_MATCHES[match_id] = match_state
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing intervention: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/live_match/state/<match_id>", methods=["GET"])
def get_live_match_state(match_id):
    """Get current state of a live match"""
    try:
        match_state = ACTIVE_LIVE_MATCHES.get(match_id)
        if not match_state:
            return jsonify({"error": "Match not found"}), 404
        
        # Return sanitized state (without internal data)
        return jsonify({
            "match_id": match_id,
            "team1_score": match_state['team1_score'],
            "team2_score": match_state['team2_score'],
            "current_minute": match_state['current_minute'],
            "current_period": match_state['current_period'],
            "interventions_left": match_state['interventions_left'],
            "stats": match_state['stats'],
            "events": match_state['events'][-20:],  # Last 20 events
            "game_over": match_state['game_over'],
            "extra_time": match_state['extra_time'],
            "penalties": match_state['penalties'],
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting match state: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/live_match/finalize", methods=["POST"])
def finalize_live_match():
    """Finalize a match and save results"""
    try:
        from Game.live_match_api import live_match_simulator
        
        data = request.get_json(silent=True) or {}
        match_id = data.get('match_id')
        
        if not match_id:
            return jsonify({"error": "Missing match_id"}), 400
        
        match_state = ACTIVE_LIVE_MATCHES.get(match_id)
        if not match_state:
            return jsonify({"error": "Match not found"}), 404
        
        logger.info(f"🏁 Finalizing match {match_id}")
        
        # Handle penalty shootout if needed
        penalty_result = None
        if match_state.get('penalties') and match_state.get('must_win'):
            penalty_result = live_match_simulator.simulate_penalty_shootout(match_state)
        
        result = live_match_simulator.finalize_match(match_state)
        
        if penalty_result:
            result['penalty_result'] = penalty_result
        
        # Clean up from memory
        del ACTIVE_LIVE_MATCHES[match_id]
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error finalizing match: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/live_match/penalties", methods=["POST"])
def simulate_penalties():
    """Simulate penalty shootout for a tied match"""
    try:
        from Game.live_match_api import live_match_simulator
        
        data = request.get_json(silent=True) or {}
        match_id = data.get('match_id')
        
        if not match_id:
            return jsonify({"error": "Missing match_id"}), 400
        
        match_state = ACTIVE_LIVE_MATCHES.get(match_id)
        if not match_state:
            return jsonify({"error": "Match not found"}), 404
        
        logger.info(f"🥅 Simulating penalties for match {match_id}")
        
        result = live_match_simulator.simulate_penalty_shootout(match_state)
        
        # Update stored state
        ACTIVE_LIVE_MATCHES[match_id] = match_state
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error simulating penalties: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
