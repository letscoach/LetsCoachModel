try:
    from Game.Matches import game_launcher
except Exception as e:
    import traceback
    print(f"ERROR during imports: {e}")
    print(traceback.format_exc())

# Import with reload to ensure latest code is used
import importlib
import sys

try:
    # Reload SQL_db first (contains prize distribution function)
    from Helpers import SQL_db
    if 'Helpers.SQL_db' in sys.modules:
        importlib.reload(SQL_db)
        print("🔄 Reloaded Helpers.SQL_db")
    
    # Import modules
    from Competitions import dash100, dash5k, penalty_shootout
    
    # Reload modules to get latest code (important for long-running Flask server)
    if 'Competitions.dash100' in sys.modules:
        importlib.reload(dash100)
        print("🔄 Reloaded Competitions.dash100")
    if 'Competitions.dash5k' in sys.modules:
        importlib.reload(dash5k)
        print("🔄 Reloaded Competitions.dash5k")
    if 'Competitions.penalty_shootout' in sys.modules:
        importlib.reload(penalty_shootout)
        print("🔄 Reloaded Competitions.penalty_shootout")
    
    # Get classes
    Dash100 = dash100.Dash100
    Run5k = dash5k.Run5k
    PenaltyShootout = penalty_shootout.PenaltyShootout
    
    print("✅ All competition modules loaded and reloaded")
    
except Exception as e:
    import traceback
    print(f"ERROR importing competitions: {e}")
    print(traceback.format_exc())
    Dash100 = None
    Run5k = None
    PenaltyShootout = None


def match_handler(data):
    return game_launcher({
        'away_team_id': data.get('away_team_id'),
        'home_team_id': data.get('home_team_id'),
        'match_id': data.get('match_id'),
        'kind': data.get('kind', 'league'),
    })


def competition_handler(data):
    """Handle competition simulation requests"""
    competition_id = data.get('competition_id')
    competition_type_id = data.get('competition_type_id')
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Check if competition was already processed (race condition prevention)
        from Helpers.competition_lock import check_competition_already_running
        if check_competition_already_running(competition_id):
            msg = f"⚠️ Competition {competition_id} already running or just completed - skipping to prevent duplicate execution"
            logger.warning(msg)
            return msg
        
        if competition_type_id == 1:
            # Dash100 competition
            if Dash100:
                logger.info(f"Starting Dash100 competition {competition_id}")
                competition = Dash100(competition_id)
                results = competition.run_and_update()
                logger.info(f"Dash100 competition {competition_id} completed")
                return f"Dash100 competition {competition_id} completed with {len(results)} results"
            else:
                logger.error("Dash100 handler not loaded")
                return "Error: Dash100 handler not loaded"
        elif competition_type_id == 2:
            # Dash5k competition
            if Run5k:
                logger.info(f"Starting Dash5K competition {competition_id}")
                competition = Run5k(competition_id)
                results = competition.run_and_update()
                logger.info(f"Dash5K competition {competition_id} completed")
                return f"Dash5k competition {competition_id} completed with {len(results)} results"
            else:
                logger.error("Dash5K handler not loaded")
                return "Error: Dash5k handler not loaded"
        elif competition_type_id == 3:
            # Penalty Shooter competition
            if PenaltyShootout:
                logger.info(f"Starting Penalty Shooter competition {competition_id}")
                competition = PenaltyShootout(competition_id)
                results = competition.run_and_update()
                logger.info(f"Penalty Shooter competition {competition_id} completed")
                return f"Penalty Shooter competition {competition_id} completed"
            else:
                logger.error("PenaltyShootout handler not loaded")
                return "Error: PenaltyShootout handler not loaded"
        elif competition_type_id == 4:
            # Goalkeeper competition (same as Penalty Shooter but from GK perspective)
            if PenaltyShootout:
                logger.info(f"Starting Goalkeeper competition {competition_id}")
                competition = PenaltyShootout(competition_id)
                results = competition.run_and_update()
                logger.info(f"Goalkeeper competition {competition_id} completed")
                return f"Goalkeeper competition {competition_id} completed"
            else:
                logger.error("PenaltyShootout handler not loaded")
                return "Error: PenaltyShootout handler not loaded"
        else:
            logger.error(f"Unknown competition type {competition_type_id}")
            return f"Error: Unknown competition type {competition_type_id}"
    except Exception as e:
        logger.error(f"Error running competition {competition_id}: {str(e)}", exc_info=True)
        return f"Error running competition {competition_id}: {str(e)}"


def schedule_handler(data):
    """Handle schedule generation request"""
    try:
        from Game.Matches import generate_schedule_double_round
        
        league_id = data.get('league_id')
        start_date = data.get('start_date')
        start_time = data.get('start_time', '15:00')
        days_between = data.get('days_between', 7)
        
        if not league_id or not start_date:
            return "Error: Missing league_id or start_date"
            
        print(f"Generating schedule for league {league_id} starting {start_date}")
        schedule = generate_schedule_double_round(
            league_id, 
            start_date, 
            start_time_gmt=start_time, 
            days_between_matchdays=days_between
        )
        return f"Schedule generated with {len(schedule)} matches"
    except Exception as e:
        import traceback
        print(f"Error generating schedule: {e}")
        print(traceback.format_exc())
        return f"Error: {e}"


ACTION_MAP = {
    'match': match_handler,
    'competition': competition_handler,
    'generate_schedule': schedule_handler,
}