from datetime import datetime, timedelta
from random import choice, sample
from backend import SQL_db  as sql_db
import logging
import ast
# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_training_attributes(training_type):
    # Define training types and their corresponding attributes
    training_attributes = {
        "Attack Training": ["Shoot Precision", "Shoot Power", "Heading"],
        "Defense Training": ["Heading", "Aggression", "Tackle Precision"],
        "Midfield Training": ["Dribble", "Game Vision", "Pass Precision"],
        "Personal Skills Training": ["Speed", "Endurance", "Leadership", "Physicality", "Injury Risk"],
        "Recovery Training": ["Freshness"],
    }

    # Return the attributes for the given training type
    return training_attributes.get(training_type, [])


#def start_training(team_id, training_type, intensity_level):
    #training_durations = {'Light': 6, 'Medium': 8, 'Intense': 10}
    #recovery_times = {'Light': 18, 'Medium': 16, 'Intense': 14}

    #now = datetime.now()
    #start_time = now
    #end_time = now + timedelta(hours=training_durations[intensity_level])
    #recovery_end_time = end_time + timedelta(hours=recovery_times[intensity_level])

    # Enforce rules: Check if training is allowed based on match timing
    #DB:
    #last_game_time = get_last_game_time(team_id)  # Fetch last game time from DB
    #DB:
    #required_cooldown = 10 if last_game_type(team_id) == "home" else 12
    #if now < last_game_time + timedelta(hours=required_cooldown):
    #    return {"error": "Training cannot start yet. Wait for the cooldown period."}

    # Insert training session into the database
    # DB:
    #session_id = insert_training_session(team_id, training_type, intensity_level, start_time, end_time, recovery_end_time)
    #return {"session_id": session_id, "message": "Training started successfully"}

def complete_training(session_id):
    logging.info(f"Starting training session {session_id}")

    # Fetch training session details from DB
    session = sql_db.get_team_training_by_id(session_id)
    team_id = session[0]['team_id']
    training_type = session[0]['training_name']
    intensity_level = session[0]['intensity_name']
    logging.info(f"Training session {session_id}: Team {team_id}, Type {training_type}, Intensity {intensity_level}")

    # Fetch affected players and attributes
    players_str = session[0]['participating_players']
    players = ast.literal_eval(players_str)
    affected_attributes = get_training_attributes(training_type)

    # Dictionary to store improvements for each player
    players_data = {}

    for player in players:
        impacted_attributes = sample(affected_attributes, k=choice([1, 2]))
        properties = {}
        player_data = sql_db.get_player_by_token(player)
        attr_str = player_data['attributes']

        # Convert to dictionary - AMICHAi - can you return a doctionary?
        attr_dict = {key.strip(): float(value.strip()) for key, value in
                     (item.split(":") for item in attr_str.split(","))}
        base_improvement = {"Light": 0.005, "Medium": 0.008, "Intense": 0.012}[intensity_level]
        actual_improvement = base_improvement * (attr_dict["Trainability"] / 100) * (player_data["Freshness"] / 100)

        for attribute in impacted_attributes:
            properties[attribute] = actual_improvement

        # Reduce fatigue
        fatigue_reduction = 25 - (attr_dict['Endurance'] / 4) + {"Light": 0, "Medium": 2, "Intense": 5}[intensity_level]
        properties["Freshness"] = -fatigue_reduction #min(100, player["Freshness"] - fatigue_reduction)

        players_data[player] = {
            "player_id": player,
            "properties": properties
        }

        logging.info(f"Player {player} updated attributes: {properties}")

    # Insert training effects into the DB
    try:
        sql_db.insert_player_attributes_training_effected(players_data, session_id)
        logging.info(f"Training effects successfully inserted for session {session_id}")
        return {'status' : 'success'}
    except Exception as e:
        logging.error(f"Error inserting training effects for session {session_id}: {e}")
        return {"error": "Database update failed"}

    # Mark session as completed
#    try:
#        update_training_session_status(session_id, "Completed")
#        logging.info(f"Training session {session_id} marked as completed")
#    except Exception as e:
#        logging.error(f"Error updating training session status for session {session_id}: {e}")
#        return {"error": "Failed to update training session status"}

#    return {"message": "Training completed and attributes updated"}


def get_fatigue_reduction(endurance, intensity):
    intensity_bonus = {"Light": 0, "Medium": 2, "Intense": 5}
    return 25 - (endurance / 4) + intensity_bonus[intensity]


#if freshness > 80:
#    injury_probability -= 0.076 / 100
#elif 60 <= freshness <= 80:
#    injury_probability *= 2
#elif 40 <= freshness < 60:
#    injury_probability *= 3
#else:
#    injury_probability *= 4
#complete_training(13)