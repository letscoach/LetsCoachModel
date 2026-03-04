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
        
    def get_team_formation(self, team_id: str) -> Tuple[List[List[str]], str]:
        """
        Retrieve the team formation from the database by team ID.
        - team_id: The ID of the team.
        - Returns: Tuple of (Formation list, captain_token).
        """
        #team_data = db.get_document('Teams','team_id', team_id) #db.get_team(team_id)
        formation, captain_token = db.get_team_default_formation(team_id)
        return formation, captain_token

    def calculate_team_grades(self, formation_list: List[List[str]], captain_token: str = None) -> Dict[str, float]:
        """
        Calculate team grades using the grading module.
        - formation_list: The team's formation as a list of player IDs.
        - captain_token: Token of the team captain (gets bonus).
        - Returns: Dictionary with defense, midfield, and offense grades.
        """
        return calc_grades(formation_list, captain_token)

    def simulate_game(self, team1_grades: Dict[str, float], team2_grades: Dict[str, float], home_advantage: bool = False) -> Tuple[int, int]:
        """
        Simulate the game and calculate the result.
        - team1_grades: Team 1 grades as a dictionary (HOME team if home_advantage=True).
        - team2_grades: Team 2 grades as a dictionary (AWAY team if home_advantage=True).
        - home_advantage: If True, team1 gets home advantage bonuses.
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
        return simulate_football_match(team1, team2, home_advantage=home_advantage)

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
        from datetime import datetime
        
        logger.info("Starting update_player_data_in_db for match_id=%s", match_id)
        logger.debug("Received player_stories: %s", player_stories)

        # Use match end time (now) for freshness last_update timestamp
        # This prevents instant freshness recovery when player refreshes the page
        match_end_time = datetime.now()

        # Perform the single bulk insert/update
        db.insert_player_attributes_game_effected(player_stories, match_id, match_end_time)

        logger.info("Bulk insert complete for match_id=%s.", match_id)
    def init_game(self, team1_id: str, team2_id: str) -> Dict:
        """
        Initialize the game, simulate the result, process post-game data, and update the DB.
        - team1_id: The ID of the first team (HOME team).
        - team2_id: The ID of the second team (AWAY team).
        - Returns: Dictionary containing the result and player stories.
        """
        send_log_message("2.Update Freshness")

        fu.update_freshness_for_team(team1_id)
        fu.update_freshness_for_team(team2_id)
        send_log_message("3.Get formation")
        # Step 1: Retrieve formations (including captain tokens)
        team1_formation, team1_captain = self.get_team_formation(team1_id)
        team2_formation, team2_captain = self.get_team_formation(team2_id)
        send_log_message("4.Update formation")
        db.insert_opening_formations(self.game_id)

        send_log_message("5.Calc team grades")
        # Step 2: Calculate grades for both teams (with captain bonus)
        team1_grades = self.calculate_team_grades(team1_formation, team1_captain)
        team2_grades = self.calculate_team_grades(team2_formation, team2_captain)
        
        # Determine if home advantage applies (kind=1 is League matches with home/away)
        # League matches have home advantage since they are part of round-robin with home/away games
        home_advantage = (self.game_type == 1)  # Enable home advantage for league matches
        
        send_log_message(f"6.Simulate the game (home_advantage={home_advantage})")
        # Step 3: Simulate the game
        team1_score, team2_score = self.simulate_game(team1_grades, team2_grades, home_advantage=home_advantage)

        # Step 4: Process post-game data using PostGameProcessor
        send_log_message(f"Game type {self.game_type}, processing post-game")
        output = self.post_game_processor.process_post_game(team1_id, team2_id, team1_score, team2_score, match_kind=self.game_type)
        send_log_message("7.Insert into db all match data")

        db.insert_match_details(self.game_id, output.get('events', []))
        db.update_matche_result(self.game_id, f"{team1_score}-{team2_score}",output.get('time_played_mins'))
        try:
            db.insert_man_of_the_match(output['man_of_the_match'], self.game_id)
        except Exception as e:
            send_log_message(f"Error : {e}, continue running!")
        self.update_player_data_in_db(self.game_id, output['player_stories'])
        
        # Process betting payout for friendly matches (kind=2)
        if self.game_type == 2:
            try:
                betting_result = db.process_friendly_match_betting(self.game_id, team1_score, team2_score)
                send_log_message(f"Betting processed: {betting_result.get('status')}")
            except Exception as e:
                send_log_message(f"Betting error: {e}")
        
        # Check end-of-league for league matches (kind=1)
        if self.game_type == 1:
            try:
                # Get league_id from the match
                match_info = db.exec_select_query(
                    f"SELECT league_id FROM matches WHERE match_id = {self.game_id}"
                )
                if match_info and match_info[0].get('league_id'):
                    league_id = match_info[0]['league_id']
                    end_result = db.process_end_of_league(league_id, self.game_id)
                    if end_result:
                        send_log_message(
                            f"🏆 League {league_id} ended! "
                            f"Champion: {end_result['champion']['team_name'] if end_result.get('champion') else 'N/A'}, "
                            f"Top Scorer: {end_result['top_scorer']['player_name'] if end_result.get('top_scorer') else 'N/A'}"
                        )
            except Exception as e:
                send_log_message(f"End-of-league check error: {e}")
        
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

