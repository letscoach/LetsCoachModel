from datetime import datetime, timedelta
import Helpers.SQL_db as sql_db  # Importing the module for database interactions
import logging

logger = logging.getLogger(__name__)


def fetch_player_data(player_id):
    """
    Fetches the last freshness update time and endurance for a given player.
    Returns (last_update_str, current_freshness, endurance).
    
    Gets last_update directly from player_dynamic_attributes table (attribute_id=15)
    """
    freshness = sql_db.select_player_freshness(player_id)
    last_update_result = sql_db.get_freshness_last_effort(player_id)
    current_freshness = freshness['attribute_value']
    data = sql_db.get_player_by_token(player_id)
    attr_dict = data['properties']
    endurance = attr_dict['Endurance']
    
    # Extract last_update from the query result
    # get_freshness_last_effort now returns the last_update timestamp directly from player_dynamic_attributes
    if last_update_result and 'last_effort_time' in last_update_result:
        last_update_str = last_update_result['last_effort_time']
    else:
        # Fallback if no record found (shouldn't happen, but be safe)
        logger.warning(f"⚠️ No freshness record found for player {player_id}")
        last_update_str = '0000-00-00 00:00:00'
    
    return last_update_str, current_freshness, endurance

def parse_custom_datetime(dt_input) -> datetime:
    """
    Parse datetime from either string or datetime object.
    Handles cases where DB returns datetime object directly.
    """
    # If it's already a datetime object, return it
    if isinstance(dt_input, datetime):
        return dt_input
    
    # If it's a string
    if dt_input == '0000-00-00 00:00:00':
        # Return a default date/time—e.g., Unix epoch
        return datetime(1970, 1, 1, 0, 0, 0)
    else:
        # Parse normally. Adjust the format string as needed
        return datetime.strptime(dt_input, '%Y-%m-%d %H:%M:%S')


def calculate_freshness_update(last_update, endurance):
    """
    Calculates the freshness update based on the time elapsed since the last update
    and the player's endurance level.

    - Full recovery from 0 to 70 freshness in 24 hours with endurance = 100.
    - Recovery is proportional to both time and endurance.
    """
    if last_update is None or endurance is None:
        return 0  # No update if data is missing

    # ✅ FIX: Use local time instead of UTC to match DB NOW()
    now = datetime.now()  # Changed from datetime.utcnow()
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
    - Fetches player data from player_dynamic_attributes (attribute_id=15 for freshness)
    - Calculates freshness update based on time elapsed since last_update
    - Updates the new freshness in the database
    """
    for player_id in player_ids:
        last_update_str, current_freshness, endurance = fetch_player_data(player_id)
        freshness_update = 0

        # Parse the last_update timestamp
        last_update_parsed = parse_custom_datetime(last_update_str)
        logger.info(f"🔍 DEBUG - Player {player_id}: last_update_raw={last_update_str}, parsed={last_update_parsed}")
        
        # Calculate freshness recovery based on hours since last_update
        freshness_update = calculate_freshness_update(last_update_parsed, endurance)

        if freshness_update > 0:
            new_freshness_delta = min(current_freshness + freshness_update, 100) - current_freshness  # Ensure max freshness is 100
            logger.info(f"🔄 Update Freshness - Player {player_id}: current={current_freshness:.2f}, calculated_gain={freshness_update:.2f}, capped_delta={new_freshness_delta:.2f}, new_total={current_freshness + new_freshness_delta:.2f}")
            print(f"🔄 Update Freshness - Player {player_id}: current={current_freshness:.2f}, gain={freshness_update:.2f}, delta={new_freshness_delta:.2f}, new={current_freshness + new_freshness_delta:.2f}")
            update_player_freshness(player_id, new_freshness_delta)


#    print("Freshness update completed for all players.")

def update_freshness_for_team(team_id):
    team_players_list = sql_db.get_team_players(team_id)
    update_freshness_for_players(team_players_list)

# update_freshness_for_team(67)