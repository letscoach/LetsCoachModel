try:
    from Game.Matches import game_launcher
except Exception as e:
    import traceback
    print(f"ERROR during imports: {e}")
    print(traceback.format_exc())

try:
    from Competitions.dash100 import run_dash100
    from Competitions.dash5k import run_dash5k
except Exception as e:
    import traceback
    print(f"ERROR importing competitions: {e}")
    print(traceback.format_exc())
    run_dash100 = None
    run_dash5k = None


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
    group_id = data.get('group_id')
    
    if competition_type_id == 1:
        # Dash100 competition
        if run_dash100:
            return run_dash100(competition_id, group_id)
        else:
            return "Error: Dash100 handler not loaded"
    elif competition_type_id == 2:
        # Dash5k competition
        if run_dash5k:
            return run_dash5k(competition_id, group_id)
        else:
            return "Error: Dash5k handler not loaded"
    else:
        return f"Error: Unknown competition type {competition_type_id}"


ACTION_MAP = {
    'match': match_handler,
    'competition': competition_handler,
}