import time
from datetime import datetime, timedelta
import Helpers.SQL_db as sql_db  # Importing the module for database interactions


def parse_custom_datetime(dt_str: str) -> datetime:
    if dt_str == '0000-00-00 00:00:00':
        # Return a default date/time—e.g., Unix epoch
        return datetime(1970, 1, 1, 0, 0, 0)
    else:
        # Parse normally. Adjust the format string as needed
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')


def update_player_satisfaction(player_id, new_satisfaction_delta):
    """
    Updates the player's freshness value in the database.
    """
    sql_db.set_player_satisfaction(new_satisfaction_delta,'-', player_id)

def update_satisfaction_for_players(player_ids, training_history):
    now = datetime.utcnow()

    for player_id in player_ids:
        for training_player_data in training_history:
            if training_player_data['token'] == player_id:
                last_training_time = training_player_data['last_training_date']
                time_diff = now - last_training_time
                days = round(time_diff.total_seconds() / (3600 * 24))  # Convert time difference full days

                if days > 1 and days % 7 == 0:
                    satisfaction_reduction = 2
                    update_player_satisfaction(player_id, satisfaction_reduction)

def update_satisfaction_for_team(team_id):
    team_players_list = sql_db.get_team_players(team_id)
    training_history = sql_db.get_training_history_by_team_id(team_id)
    update_satisfaction_for_players(team_players_list, training_history)


#update_satisfaction_for_team(68)
