try:
    from Game.Matches import game_launcher
    from Game.freshness_update import update_freshness_for_team
    from Game.update_satisfaction import update_satisfaction_for_team
    from Training.training import complete_training
    from Competitions.dash5k import Run5k
    from Competitions.dash100 import Run100
except Exception as e:
    import traceback
    print(f"ERROR during imports: {e}")
    print(traceback.format_exc())

def complete_training_handler(data):
    return complete_training(data.get('training_id'))


def freshness_update_handler(data):
    team_id = data.get('team_id')
    update_freshness_for_team(team_id)
    return update_satisfaction_for_team(team_id)


def match_handler(data):
    return game_launcher({
        'away_team_id': data.get('away_team_id'),
        'home_team_id': data.get('home_team_id'),
        'match_id': data.get('match_id'),
    })

def competition_handler(data):
    competition_type = data.get('competition_type')
    if competition_type == 2:
        comp = Run5k(data)
        return comp.run_and_update()
    elif competition_type == 1:
        comp = Run100(data)
        return comp.run_and_update()
    else:
        raise ValueError(f"Unknown competition type: {competition_type}")

def competition_handler(data):
    pass


ACTION_MAP = {
    'training': complete_training_handler,
    'freshness_update': freshness_update_handler,
    'match': match_handler,
    "competition": competition_handler
}