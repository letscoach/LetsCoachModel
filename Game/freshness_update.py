from datetime import datetime, timedelta
import Helpers.SQL_db as sql_db  # Importing the module for database interactions


def fetch_player_data(player_id):
    """
    Fetches the last freshness update time and endurance for a given player.
    Returns (last_update, current_freshness, endurance).
    """
    freshness = sql_db.select_player_freshness(player_id)
    last_update = sql_db.get_freshness_last_effort(player_id)
    current_freshness = freshness['attribute_value']
    data = sql_db.get_player_by_token(player_id)
    attr_dict = data['properties']
    # DONE Convert to dictionary - AMICHAY - can you return a doctionary?
    # attr_dict = {key.strip(): float(value.strip()) for key, value in
    #              (item.split(":") for item in attr_str.split(","))}
    endurance = attr_dict['Endurance']
    return last_update, current_freshness, endurance

def parse_custom_datetime(dt_str: str) -> datetime:
    if dt_str == '0000-00-00 00:00:00':
        # Return a default date/time—e.g., Unix epoch
        return datetime(1970, 1, 1, 0, 0, 0)
    else:
        # Parse normally. Adjust the format string as needed
        return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')


def calculate_freshness_update(last_update, endurance):
    """
    Calculates the freshness update based on the time elapsed since the last update
    and the player's endurance level.

    - Full recovery from 0 to 70 freshness in 24 hours with endurance = 100.
    - Recovery is proportional to both time and endurance.
    """
    if last_update is None or endurance is None:
        return 0  # No update if data is missing

    now = datetime.utcnow()
    time_diff = now - last_update
    hours_passed = time_diff.total_seconds() / 3600  # Convert time difference to hours

    # Calculate freshness gain: with endurance 100, it reaches 70 in 24 hours
    freshness_gain = hours_passed * (0.65625 + 2.5 * (endurance / 2400))
    # delta_freshness = min(freshness_gain, 70)  # Limit maximum recovery to 70
    delta_freshness = freshness_gain
    return delta_freshness


def update_player_freshness(player_id, new_freshness_delta):
    """
    Updates the player's freshness value in the database.
    """
    sql_db.set_player_freshness(new_freshness_delta,'+', player_id)


def update_freshness_for_players(player_ids):
    """
    API function that updates freshness for all players in the given list.
    - Fetches player data.
    - Calculates freshness update.
    - Updates the new freshness in the database.
    """
    for player_id in player_ids:
        last_update_data, current_freshness, endurance = fetch_player_data(player_id)
        freshness_update = 0

        if last_update_data['status'] == 'last_effort':
            freshness_update = calculate_freshness_update(parse_custom_datetime(last_update_data['last_effort_time']), endurance)

        if freshness_update > 0:
            new_freshness_delta = min(current_freshness + freshness_update, 100) - current_freshness  # Ensure max freshness is 100
            update_player_freshness(player_id, new_freshness_delta)


#    print("Freshness update completed for all players.")

def update_freshness_for_team(team_id):
    team_players_list = sql_db.get_team_players(team_id)
    update_freshness_for_players(team_players_list)

# update_freshness_for_team(67)