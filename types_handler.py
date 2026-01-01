try:
    from Game.Matches import game_launcher
except Exception as e:
    import traceback
    print(f"ERROR during imports: {e}")
    print(traceback.format_exc())

try:
    from Competitions.dash100 import Dash100
    from Competitions.dash5k import Run5k
except Exception as e:
    import traceback
    print(f"ERROR importing competitions: {e}")
    print(traceback.format_exc())
    Dash100 = None
    Dash5K = None


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
        else:
            logger.error(f"Unknown competition type {competition_type_id}")
            return f"Error: Unknown competition type {competition_type_id}"
    except Exception as e:
        logger.error(f"Error running competition {competition_id}: {str(e)}", exc_info=True)
        return f"Error running competition {competition_id}: {str(e)}"


ACTION_MAP = {
    'match': match_handler,
    'competition': competition_handler,
}