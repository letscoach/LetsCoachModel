import logging
from typing import List, Dict, Tuple
import json
from Helpers import SQL_db as sql_db

# Set up basic logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define the position mappings
POSITION_MAPPING = {
    (0, 2): "GK",
    (1, 0): "Winger",
    (1, 1): "Centre-back",
    (1, 2): "Centre-back",
    (1, 3): "Centre-back",
    (1, 4): "Winger",
    (2, 0): "Wide Midfielder",
    (2, 1): "Central Midfielder",
    (2, 2): "Central Midfielder",
    (2, 3): "Central Midfielder",
    (2, 4): "Wide Midfielder",
    (3, 0): "Wide Midfielder",
    (3, 1): "Central Midfielder",
    (3, 2): "Central Midfielder",
    (3, 3): "Central Midfielder",
    (3, 4): "Wide Midfielder",
    (4, 0): "Forward",
    (4, 1): "Striker",
    (4, 2): "Striker",
    (4, 3): "Striker",
    (4, 4): "Forward",
    (5, 0): "Forward",
    (5, 1): "Striker",
    (5, 2): "Striker",
    (5, 3): "Striker",
    (5, 4): "Forward",
}


# Adapter function to convert the formation list into a Formation object
def ensure_list_of_lists(input_value):
    logger.debug(f"Received input for ensure_list_of_lists: {input_value}")

    if isinstance(input_value, str):  # Check if it's a string
        try:
            # Replace single quotes with double quotes to make it JSON compatible
            formatted_input = input_value.replace("'", '"')
            logger.debug(f"Formatted input for JSON decoding: {formatted_input}")

            # Convert the string into a list of lists
            result = json.loads(formatted_input)
            logger.debug(f"Decoded JSON result: {result}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            return None
    elif isinstance(input_value, list):  # If it's already a list
        logger.debug(f"Input is already a list: {input_value}")
        return input_value
    else:
        logger.error("Input must be a string or a list.")
        raise TypeError("Input must be a string or a list.")


def create_formation_from_list(formation_list):
    logger.debug(f"Creating formation from list: {formation_list}")
    players = []
    formation_list = ensure_list_of_lists(formation_list)

    for i, row in enumerate(formation_list):
        for j, player_id in enumerate(row):
            logger.debug(f"Processing player_id: {player_id} at position: ({i}, {j})")

            if player_id != "0" and (i, j) in POSITION_MAPPING:
                position = POSITION_MAPPING[(i, j)]
                logger.debug(f"Position mapped to: {position}")

                # Retrieve player data
                player_data = sql_db.get_player_by_token(player_id)
                logger.debug(f"Retrieved player data: {player_data}")

                # Create Player object with retrieved data
                player = Player(properties=player_data, position=position)
                players.append(player)
            else:
                logger.debug(f"Skipping player at position: ({i}, {j}) - either no player ID or invalid position")

    # Create and return Formation object
    formation = Formation(players=players)
    logger.debug(f"Formation created with {len(players)} players")
    return formation


# Define a Player as a dictionary with properties and a position
class Player:
    def __init__(self, properties: Dict[str, int], position: str):
        self.properties = properties
        self.position = position


# Define Formation as a list of Players
class Formation:
    def __init__(self, players: List[Player]):
        self.players = players


# Define primary score factors for each position
PRIMARY_FACTORS = {
    "GK": [2, 2, 3, 3, 2, 2, 2, 4, 4, 5, 30, 30, 30, 10, 0, 7],
    "Centre-back": [10, 0, 5, 5, 5, 14, 0, 9, 30, 25, 0, 0, 0, 9, 0, 24],
    "Winger": [15, 0, 12, 10, 12, 5, 0, 20, 23, 15, 0, 0, 0, 14, 0, 10],
    "Central Midfielder": [10, 0, 15, 15, 15, 5, 0, 23, 7, 16, 0, 0, 0, 20, 0, 10],
    "Wide Midfielder": [22, 0, 15, 15, 20, 5, 0, 25, 6, 6, 0, 0, 0, 12, 0, 10],
    "Striker": [15, 0, 30, 30, 15, 10, 0, 5, 3, 10, 0, 0, 0, 8, 0, 10],
    "Forward": [25, 0, 20, 20, 25, 5, 0, 20, 3, 3, 0, 0, 0, 10, 0, 5]
}

# Relevant properties for non-primary grades
OFFENSE_PROPERTIES = ["Speed", "Shoot_Precision", "Shoot_Power", "Dribble", "Heading", "Pass_Precision", "Game_vision",
                      "Leadership"]
MIDFIELD_PROPERTIES = ["Speed", "Dribble", "Pass_Precision", "Game_vision", "Leadership"]
DEFENSE_PROPERTIES = ["Speed", "Heading", "Tackle_Precision", "Aggression", "Leadership"]

# Position multipliers for each score type
POSITION_FACTORS = {
    "defense": [0.2, 0.25, 0.15, 0.007, 0.02, 0.002, 0.003],
    "midfield": [0.002, 0.01, 0.03, 0.3, 0.2, 0.005, 0.01],
    "offense": [0.0005, 0.003, 0.01, 0.007, 0.02, 0.5, 0.3]
}


# Extract the relevant values from the player data
def extract_values(player_data):
    logger.debug(f"Extracting values from player data: {player_data}")

    keys = [
        "Speed", "Endurance", "Shoot_Precision", "Shoot_Power", "Dribble",
        "Heading", "Injury_Risk", "Pass_Precision", "Tackle_Precision",
        "Aggression", "Diving", "GK_Kicking", "Reflexes", "Game_vision",
        "Leadership", "Physicality", "Freshness"
    ]

    logger.debug(f"Keys to extract: {keys}")

    extracted_values = []
    for key in keys:
        if key in player_data:
            extracted_values.append(player_data[key])
            logger.debug(f"Extracted {key}: {player_data[key]}")
        else:
            logger.debug(f"Key {key} not found in player data")

    logger.debug(f"Extracted values: {extracted_values}")

    return extracted_values


# Calculate personal grades for each player based on position and properties
def calculate_personal_grades(player: Player) -> Tuple[float, float, float]:
    logger.debug(f"Calculating personal grades for player at position: {player.position}")

    # Retrieve primary factors based on player's position
    primary_factors = PRIMARY_FACTORS[player.position]
    logger.debug(f"Primary factors for position {player.position}: {primary_factors}")

    # Extract the player's primary properties using the extract_values function
    primary_properties = extract_values(player.properties['properties'])
    logger.debug(f"Extracted primary properties for player {player.position}: {primary_properties}")

    # Compute the sum of the products (primary property * primary factor)
    product_values = []
    for p, f in zip(primary_properties, primary_factors):
        product = p * f
        product_values.append(product)
        logger.debug(f"Product of property {p} and factor {f}: {product}")

    sum_of_products = sum(product_values)
    sum_of_factors = sum(primary_factors)
    logger.debug(f"Sum of products: {sum_of_products}, Sum of primary factors: {sum_of_factors}")

    # Calculate the primary grade
    primary_grade = sum_of_products / sum_of_factors
    logger.debug(f"Calculated primary grade for player {player.position}: {primary_grade}")

    offense_grade = sum(player.properties['properties'][prop] for prop in OFFENSE_PROPERTIES) / len(OFFENSE_PROPERTIES)
    logger.debug(f"Calculated offense grade: {offense_grade}")

    midfield_grade = sum(player.properties['properties'][prop] for prop in MIDFIELD_PROPERTIES) / len(
        MIDFIELD_PROPERTIES)
    logger.debug(f"Calculated midfield grade: {midfield_grade}")

    defense_grade = sum(player.properties['properties'][prop] for prop in DEFENSE_PROPERTIES) / len(DEFENSE_PROPERTIES)
    logger.debug(f"Calculated defense grade: {defense_grade}")

    if player.position in ["GK", "Centre-back", "Winger"]:
        return primary_grade, midfield_grade, offense_grade
    elif player.position in ["Central Midfielder", "Wide Midfielder"]:
        return defense_grade, primary_grade, offense_grade
    else:  # Striker, Forward
        return defense_grade, midfield_grade, primary_grade


# Calculate team grade based on all players' personal grades and position factors
def calculate_team_grades(formation: Formation) -> Tuple[float, float, float]:
    logger.debug(f"Calculating team grades for formation with {len(formation.players)} players")

    defense_total = midfield_total = offense_total = 0
    position_order = ["GK", "Centre-back", "Winger", "Central Midfielder", "Wide Midfielder", "Striker", "Forward"]
    attack_players = ["Striker", "Forward"]
    attacker_count = 0
    midfield_players = ["Central Midfielder", "Wide Midfielder"]
    midfielder_count = 0
    deffense_players = ["Centre-back", "Winger"]
    deffenser_count = 0
    for player in formation.players:
        logger.debug(f"Processing player at position: {player.position}")

        if player.position in attack_players:
            attacker_count += 1
        elif player.position in midfield_players:
            midfielder_count += 1
        elif player.position in deffense_players:
            deffenser_count += 1

        defense_grade, midfield_grade, offense_grade = calculate_personal_grades(player)
        pos_index = position_order.index(player.position)

        logger.debug(f"Calculated personal grades for player {player.position}: "
                     f"Defense Grade: {defense_grade}, Midfield Grade: {midfield_grade}, Offense Grade: {offense_grade}")

        # Calculate freshness correction
        freshness_correction = player.properties["Freshness"] / 100
        logger.debug(f"Freshness for player {player.position}: {player.properties['Freshness']}, "
                     f"Freshness Correction: {freshness_correction}")

        # Calculate and log the product and updated totals for each category
        defense_product = freshness_correction * defense_grade * POSITION_FACTORS["defense"][pos_index]
        midfield_product = freshness_correction * midfield_grade * POSITION_FACTORS["midfield"][pos_index]
        offense_product = freshness_correction * offense_grade * POSITION_FACTORS["offense"][pos_index]


        logger.debug(f"Calculated product for defense: {defense_product}, "
                     f"midfield: {midfield_product}, offense: {offense_product}")

        # Log the total before and after adding the product
        defense_total += defense_product
        midfield_total += midfield_product
        offense_total += offense_product

    attack_factor = 1
    midfield_factor = 1
    deffense_factor = 1

    if attacker_count == 3:
        attack_factor = 1#0.9560
    elif attacker_count > 3:
        attack_factor = 0.731#0.7142#0.72

    if deffenser_count == 3:
        deffense_factor = 1#0.9560
    elif deffenser_count > 4:
        deffense_factor = 0.90#0.7142#0.72

    if midfielder_count == 2:
        midfield_factor = 1.31#0.9560
    elif midfielder_count > 4:
        midfield_factor = 0.9#0.7142#0.72

    offense_total *= attack_factor
    defense_total *= deffense_factor
    midfield_total *= midfield_factor
    # Log final team grades after all players have been processed
    logger.debug(f"Final team grades - Defense: {defense_total}, Midfield: {midfield_total}, Offense: {offense_total}")

    return defense_total, midfield_total, offense_total


# Example usage with the given list
def calc_grades(formation_list):
    logger.debug(f"Starting grade calculation for formation list: {formation_list}")

    # Create Formation
    formation = create_formation_from_list(formation_list)

    # Calculate team grades using the formation
    defense_grade, midfield_grade, offense_grade = calculate_team_grades(formation)

    logger.info(
        f"Final Grades - Defense: {defense_grade:.2f}, Midfield: {midfield_grade:.2f}, Offense: {offense_grade:.2f}")

    return dict(defense_score=defense_grade, midfield_score=midfield_grade, attack_score=offense_grade)
