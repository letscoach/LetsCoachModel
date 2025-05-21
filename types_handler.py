from LetsCoachModel.Game.Matches import game_launcher
from LetsCoachModel.Game.freshness_update import update_freshness_for_team
from LetsCoachModel.Game.update_satisfaction import update_satisfaction_for_team
from LetsCoachModel.Training.training import complete_training


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
    pass


ACTION_MAP = {
    'training': complete_training_handler,
    'freshness_update': freshness_update_handler,
    'match': match_handler,
    "competition": competition_handler
}