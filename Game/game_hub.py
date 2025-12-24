import json
from typing import List, Dict, Tuple
import logging
from Helpers import SQL_db as db
from Game.game_model import simulate_football_match
from Game.formation_grader import calc_grades, create_formation_from_list
from Game.post_game import PostGameProcessor
import Game.freshness_update as fu

from Helpers.telegram_manager import send_log_message
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GameDefinition:
    midfield_score = 'midfield_score'
    defense_score='defense_score'
    attack_score='attack_score'

class GameProcessor:
    # Fixed position weights
    POSITION_WEIGHTS = {
        "GK": {"Diving": 30, "GK_Kicking": 30, "Reflexes": 30, "Game_vision": 10},
        "Centre-back": {
            "Tackle_Precision": 30,
            "Aggression": 25,
            "Physicality": 24,
            "Heading": 14,
            "Pass_Precision": 9,
            "Game_vision": 9,
        },
        "Winger": {
            "Speed": 15,
            "Dribble": 12,
            "Shoot_Precision": 12,
            "Pass_Precision": 20,
            "Tackle_Precision": 23,
            "Game_vision": 14,
            "Aggression": 15,
            "Physicality": 10,
        },
        "Central Midfielder": {
            "Speed": 10,
            "Dribble": 15,
            "Shoot_Precision": 15,
            "Pass_Precision": 23,
            "Game_vision": 20,
            "Aggression": 16,
            "Physicality": 10,
        },
        "Wide Midfielder": {
            "Speed": 22,
            "Dribble": 20,
            "Shoot_Precision": 15,
            "Pass_Precision": 25,
            "Tackle_Precision": 6,
            "Game_vision": 12,
            "Physicality": 10,
        },
        "Striker": {
            "Speed": 15,
            "Dribble": 15,
            "Shoot_Precision": 30,
            "Shoot_Power": 30,
            "Heading": 10,
            "Aggression": 10,
            "Game_vision": 8,
            "Physicality": 10,
        },
        "Forward": {
            "Speed": 25,
            "Dribble": 25,
            "Shoot_Precision": 20,
            "Shoot_Power": 20,
            "Pass_Precision": 20,
            "Game_vision": 10,
            "Physicality": 5,
        },
    }

    def __init__(self, game_id, game_type):
        """
        Initialize the GameProcessor with fixed position weights and PostGameProcessor.
        """
        self.post_game_processor = PostGameProcessor(self.POSITION_WEIGHTS)
        self.game_id = game_id
        self.game_type = game_type
    def get_team_formation(self, team_id: str) -> List[List[str]]:
        """
        Retrieve the team formation from the database by team ID.
        - team_id: The ID of the team.
        - Returns: Formation list.
        """
        #team_data = db.get_document('Teams','team_id', team_id) #db.get_team(team_id)
        formation = db.get_team_default_formation(team_id)
        return formation

    def calculate_team_grades(self, formation_list: List[List[str]]) -> Dict[str, float]:
        """
        Calculate team grades using the grading module.
        - formation_list: The team's formation as a list of player IDs.
        - Returns: Dictionary with defense, midfield, and offense grades.
        """
        return calc_grades(formation_list)

    def simulate_game(self, team1_grades: Dict[str, float], team2_grades: Dict[str, float]) -> Tuple[int, int]:
        """
        Simulate the game and calculate the result.
        - team1_grades: Team 1 grades as a dictionary.
        - team2_grades: Team 2 grades as a dictionary.
        - Returns: Tuple with the scores of team 1 and team 2.
        """
        team1 = {
            "attack": team1_grades[GameDefinition.attack_score],
            "defense": team1_grades[GameDefinition.defense_score],
            "midfield": team1_grades[GameDefinition.midfield_score],
        }
        team2 = {
            "attack": team2_grades[GameDefinition.attack_score],
            "defense": team2_grades[GameDefinition.defense_score],
            "midfield": team2_grades[GameDefinition.midfield_score],
        }
        return simulate_football_match(team1, team2)

    def update_player_data_in_db(self, match_id: int, player_stories: List[Dict]):
        """
        Update the Players DB with new attributes and freshness in one bulk operation.
        - match_id: the match identifier for this update.
        - player_stories: List of dictionaries containing player updates.
          Each dictionary has:
            - "player_id"
            - "attribute_deltas"
            - "freshness_delta"
        """
        logger.info("Starting update_player_data_in_db for match_id=%s", match_id)
        logger.debug("Received player_stories: %s", player_stories)

        # Prepare a local data structure for collecting updates before bulk insert
 #       players_data = {}

#        for story in player_stories:
#            player_id = story["player_id"]
#            attribute_deltas = story["attribute_deltas"]
#            freshness_delta = story["freshness_delta"]
#            players_data[player_id]["attribute_deltas"] = attribute_deltas
#            players_data[player_id]["freshness_delta"] = freshness_delta
#            logger.debug(
#                "Processing story for player_id=%s with attribute_deltas=%s, freshness_delta=%s",
#                player_id, attribute_deltas, freshness_delta
#            )

#        logger.info("Finished gathering all changes. Performing bulk attribute insertion now.")

        # Perform the single bulk insert/update
        db.insert_player_attributes_game_effected(player_stories, match_id)

        logger.info("Bulk insert complete for match_id=%s.", match_id)
    def init_game(self, team1_id: str, team2_id: str) -> Dict:
        """
        Initialize the game, simulate the result, process post-game data, and update the DB.
        - team1_id: The ID of the first team.
        - team2_id: The ID of the second team.
        - Returns: Dictionary containing the result and player stories.
        """
        send_log_message("2.Update Freshness")

        fu.update_freshness_for_team(team1_id)
        fu.update_freshness_for_team(team2_id)
        send_log_message("3.Get formation")
        # Step 1: Retrieve formations
        team1_formation = self.get_team_formation(team1_id)
        team2_formation = self.get_team_formation(team2_id)
        send_log_message("4.Update formation")
        db.insert_opening_formations(self.game_id)

        send_log_message("5.Calc team grades")
        # Step 2: Calculate grades for both teams
        team1_grades = self.calculate_team_grades(team1_formation)
        team2_grades = self.calculate_team_grades(team2_formation)
        send_log_message("6.Simulate the game")
        # Step 3: Simulate the game
        team1_score, team2_score = self.simulate_game(team1_grades, team2_grades)

        # Step 4: Process post-game data using PostGameProcessor
        output = {}
        if self.game_type == 11:
            output = self.post_game_processor.process_post_game(team1_id, team2_id, team1_score, team2_score)
        elif self.game_type == 12:
            output = self.post_game_processor.process_must_win_game(team1_id, team2_id, team1_score, team2_score)
        else:
            # Default to regular post-game processing for other game types (e.g., 'league')
            send_log_message(f"Game type {self.game_type} not explicitly handled, using default post-game processing")
            output = self.post_game_processor.process_post_game(team1_id, team2_id, team1_score, team2_score)
        send_log_message("7.Insert into db all match data")

        db.insert_match_details(self.game_id, output.get('events', []))
        db.update_matche_result(self.game_id, f"{team1_score}-{team2_score}",output.get('time_played_mins'))
        try:
            db.insert_man_of_the_match(output['man_of_the_match'], self.game_id)
        except Exception as e:
            send_log_message(f"Error : {e}, continue running!")
        self.update_player_data_in_db(self.game_id, output['player_stories'])
        send_log_message("8.End game_hub")

        # Step 6: Return the result and player stories
        return output


def test_game_processor():
    # Initialize the mock database
    db.init_mock_db()

    # Create GameProcessor instance
    game_processor = GameProcessor()

    # Retrieve random team IDs from the mock database
    teams = db.get_all_documents("Teams")
    if len(teams) < 2:
        raise ValueError("Not enough teams in the database to run the test.")

    team1_id = teams[0]["team_id"]
    team2_id = teams[1]["team_id"]

    # Simulate a game
    result = game_processor.init_game(team1_id, team2_id)

    # Validate the output
    print(json.dumps(result, indent=4))

    # Example assertions
    assert "team1_score" in result
    assert "team2_score" in result
    assert isinstance(result["player_stories"], list)


# Example Usage
if __name__ == "__main__":
    # Initialize the GameProcessor
    test_game_processor()

