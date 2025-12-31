import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from Helpers import SQL_db as db


class Dash100:
    """
    Module for managing the 100m Dash competition.
    Handles player verification, competition simulation, and attribute updates.
    """

    # Constants from PRD for simulation
    MIN_TIME = 9.5  # Theoretical minimum time in seconds
    MAX_TIME = 15.0  # Maximum time for a slow/tired player
    FRESHNESS_THRESHOLD = 10  # Minimum freshness to participate
    DNF_TIME = 100.0  # Time assigned to disqualified players
    RANDOM_RANGE = 0.15  # Range for random factor in seconds

    # Attribute weights for core score calculation
    ATTRIBUTE_WEIGHTS = {
        "Speed": 0.60,
        "Physicality": 0.25,
        "Endurance": 0.10,
        "Satisfaction": 0.05
    }

    # Exponent for non-linear formula
    SCORE_EXPONENT = 1.5

    def __init__(self, competition_id: str = None):
        """
        Initialize the 100m Dash competition module.

        Args:
            competition_id: Unique identifier for this competition instance
        """
        self.competition_id = competition_id
        self.participants = db.select_players_for_competition(competition_id)
        self.results = []

    def calculate_race_time(self, player: Dict) -> float:
        """
        Calculate a player's race time based on their attributes.

        Args:
            player: Player data dictionary with properties

        Returns:
            Race time in seconds (or DNF_TIME if below freshness threshold)
        """
        # Get player properties
        properties = player.get('attributes', {})

        # Check FRESHNESS threshold
        freshness = properties.get('Freshness', 0)
        if freshness < self.FRESHNESS_THRESHOLD:
            return self.DNF_TIME

        # Calculate CoreScore
        core_score = 0
        for attr, weight in self.ATTRIBUTE_WEIGHTS.items():
            core_score += properties.get(attr, 50) * weight

        # Adjust score by freshness
        adjusted_score = core_score * (freshness / 100)

        # Convert to base time (non-linear)
        time_range = self.MAX_TIME - self.MIN_TIME
        score_ratio = adjusted_score / 100
        base_time = self.MIN_TIME + time_range * (1 - score_ratio) ** self.SCORE_EXPONENT

        # Add random factor
        random_factor = random.uniform(-self.RANDOM_RANGE, self.RANDOM_RANGE)
        final_time = base_time + random_factor

        return final_time

    def run_competition(self) -> List[Dict]:
        """
        Simulate the race for all participants and return results.

        Returns:
            List of race results, sorted by finish time
        """
        results = []

        # Calculate race time for each participant
        for participant in self.participants:
          # Calculate race time
            race_time = self.calculate_race_time(participant)

            # Add to results
            results.append({
                'token': participant['token'],
                'race_time': race_time,
                'dnf': race_time >= self.DNF_TIME
            })

        # Sort by race time (fastest first)
        results.sort(key=lambda x: x['race_time'])

        # Add ranking and score
        for i, result in enumerate(results):
            result['rank_position'] = i + 1  # Changed from rank to rank_position

            # Calculate score based on race time (inverted and normalized to 0-100)
            if result.get('dnf', False):
                result['score'] = 0
            else:
                # For 100m dash, lower time is better - normalize to 0-100 scale
                time_range = self.MAX_TIME - self.MIN_TIME
                normalized_time = max(0, min(1, (self.MAX_TIME - result['race_time']) / time_range))
                result['score'] = round(normalized_time * 100)

        # Store results for later use
        self.results = results

        return results

    def calculate_attribute_changes(self) -> Dict[str, Dict]:
        """
        Calculate attribute changes for participants based on competition results.

        Returns:
            Dictionary of player attribute changes formatted for insert_player_attributes_competition_effected
        """
        # Initialize dictionary to store formatted attribute changes
        formatted_changes = {}

        # Filter out DNF results for quintile calculations
        valid_results = [r for r in self.results if not r.get('dnf', False)]
        total_valid = len(valid_results)

        # Calculate changes for all participants (including DNF)
        for result in self.results:
            player_token = result['token']
            player = db.get_player_by_token(player_token)

            # Initialize player data with required structure
            player_data = {
                'token': player_token,
                'attributes': {},
                'rank_position': result.get('rank_position', 0),
                'score': result.get('score', 0)
            }

            # Add is_winner field for top 3 finishers (1=winner, 0=not winner)
            if result.get('rank_position', 0) <= 3 and not result.get('dnf', False):
                player_data['is_winner'] = 1
            else:
                player_data['is_winner'] = 0

            # Calculate satisfaction change based on quintiles for valid results
            if not result.get('dnf', False) and total_valid > 0:
                # Find participant's position in the results (0-indexed)
                position = next((i for i, r in enumerate(valid_results) if r['token'] == player_token), -1)

                # Calculate percentile (0 to 1, where 0 is best)
                percentile = position / total_valid if position >= 0 else 1.0

                # Determine satisfaction change based on quintile
                if percentile < 0.2:  # Top 20%
                    player_data['attributes']['Satisfaction'] = 10
                elif percentile < 0.4:  # 20-40%
                    player_data['attributes']['Satisfaction'] = 5
                elif percentile < 0.6:  # 40-60%
                    player_data['attributes']['Satisfaction'] = 0
                elif percentile < 0.8:  # 60-80%
                    player_data['attributes']['Satisfaction'] = -5
                else:  # Bottom 20%
                    player_data['attributes']['Satisfaction'] = -10
            else:
                # DNF players get a satisfaction penalty
                player_data['attributes']['Satisfaction'] = -15

            # Calculate freshness decrease - 10% of full match fatigue (100m dash is less tiring)
            properties = player.get('properties', {})
            endurance = properties.get('Endurance', 50)

            # Similar formula as in post_game.py but reduced to 10%
            full_match_fatigue = 35 - (endurance / 4)
            freshness_decrease = full_match_fatigue * 0.1  # 10% of full match

            player_data['attributes']['Freshness'] = -freshness_decrease  # Negative for decrease

            # Add small attribute improvements for top performers
            if not result.get('dnf', False) and result.get('rank_position', 0) <= 3:
                player_data['attributes']['Speed'] = 0.02  # Sprinters get speed boost
                player_data['attributes']['Physicality'] = 0.01

            # Add player to the formatted changes dictionary
            formatted_changes[player_token] = player_data

        return formatted_changes

    def apply_attribute_changes(self) -> None:
        """
        Apply the calculated attribute changes to players in the database.
        Uses the existing insert_player_attributes_competition_effected function.
        """
        # Calculate attribute changes in the required format
        attribute_changes = self.calculate_attribute_changes()

        # Use existing DB function to apply changes
        db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)

    def run_and_update(self):
        """
        Run the competition, calculate attribute changes and apply them.

        Returns:
            The competition results
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🏁 Starting Dash100 competition {self.competition_id}")
        self.run_competition()
        logger.info(f"✅ Competition simulated, calculating attribute changes...")
        
        attribute_changes = self.calculate_attribute_changes()
        logger.info(f"📊 Calculated changes for {len(attribute_changes)} players")
        
        logger.info(f"💾 Inserting results to database...")
        success, errors = db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)
        logger.info(f"✅ Database insertion complete: {success} succeeded, {errors} failed")

        return self.results


# Example usage
#if __name__ == "__main__":
#    competition = Dash100(3)
#    results = competition.run_and_update()
#    print("Competition results:", results)