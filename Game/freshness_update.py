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
    from Helpers.telegram_manager import send_log_message
    from datetime import datetime
    
    login_time = datetime.utcnow()
    logger.info(f"🔐 LOGIN FRESHNESS UPDATE - START at {login_time}")
    logger.info(f"🎯 Processing {len(player_ids)} players")
    send_log_message(f"🔐 LOGIN FRESHNESS START - {len(player_ids)} players at {login_time}")
    
    for player_id in player_ids:
        try:
            last_update_str, current_freshness, endurance = fetch_player_data(player_id)
            freshness_update = 0

            # Parse the last_update timestamp
            last_update_parsed = parse_custom_datetime(last_update_str)
            
            # Calculate hours passed
            hours_passed = (datetime.utcnow() - last_update_parsed).total_seconds() / 3600
            
            # Calculate freshness recovery based on hours since last_update
            freshness_update = calculate_freshness_update(last_update_parsed, endurance)
            new_freshness_total = min(current_freshness + freshness_update, 100)
            new_freshness_delta = new_freshness_total - current_freshness

            # Detailed logging
            log_msg = (
                f"👤 Player {player_id}:\n"
                f"   ⏰ Last Update: {last_update_str}\n"
                f"   ⏱️  Hours Passed: {hours_passed:.2f}h\n"
                f"   💪 Endurance: {endurance}\n"
                f"   📊 Current Freshness: {current_freshness:.2f}\n"
                f"   ⬆️  Calculated Gain: {freshness_update:.2f}\n"
                f"   ✨ New Freshness: {new_freshness_total:.2f}"
            )
            logger.info(log_msg)
            print(log_msg)
            
            if freshness_update > 0:
                send_log_message(log_msg)
                update_player_freshness(player_id, new_freshness_delta)
                logger.info(f"   ✅ Updated DB with delta: {new_freshness_delta:.2f}")
            else:
                logger.info(f"   ℹ️  No update needed (gain <= 0)")
                
        except Exception as e:
            logger.error(f"❌ Error updating player {player_id}: {e}", exc_info=True)
            send_log_message(f"❌ Error updating player {player_id}: {e}")
    
    logger.info(f"✅ FRESHNESS UPDATE COMPLETED at {datetime.utcnow()}")
    send_log_message(f"✅ LOGIN FRESHNESS UPDATE COMPLETED")


#    print("Freshness update completed for all players.")

def update_freshness_for_team(team_id):
    from Helpers.telegram_manager import send_log_message
    
    logger.info(f"🎯 UPDATE_FRESHNESS_FOR_TEAM - Starting for team {team_id}")
    print(f"🎯 UPDATE_FRESHNESS_FOR_TEAM - Starting for team {team_id}")
    team_players_list = sql_db.get_team_players(team_id)
    logger.info(f"   Found {len(team_players_list)} players for team {team_id}")
    print(f"   Found {len(team_players_list)} players for team {team_id}")
    send_log_message(f"🎯 Updating freshness for team {team_id}: {len(team_players_list)} players")
    update_freshness_for_players(team_players_list)

# update_freshness_for_team(67)