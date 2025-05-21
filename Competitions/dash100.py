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
        "SPEED": 0.60,
        "PHYSICALITY": 0.25,
        "ENDURANCE": 0.10,
        "SATISFACTION": 0.05
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
        self.participants = []
        self.results = []

    def verify_player_eligibility(self, player_token: str, team_id: int, competition_time: datetime) -> Tuple[
        bool, str]:
        """
        Verify if a player is eligible to participate in the 100m Dash competition.

        Args:
            player_token: Player's unique identifier
            team_id: Team's ID
            competition_time: Scheduled start time of the competition

        Returns:
            Tuple of (is_eligible, reason_if_not_eligible)
        """
        # Check 1: Player exists and has required attributes
        player = db.get_player_by_token(player_token)
        if not player:
            return False, "Player not found"

        # Extract player's properties
        player_props = player.get('properties', {})
        if 'Freshness' not in player_props:
            return False, "Player missing required attributes"

        # Check 2: Freshness threshold
        if player_props.get('Freshness', 0) < self.FRESHNESS_THRESHOLD:
            return False, f"Player's freshness is too low ({player_props.get('Freshness', 0)})"

        # Check 3: Team official match conflict (within 5 hours)
        match_conflict = self._check_team_official_match(team_id, competition_time)
        if match_conflict:
            return False, "Team has an official match within 5 hours of the competition"

        # Check 4: Player training conflict
        training_conflict, end_time = self._check_player_training(player_token, team_id, competition_time)
        if training_conflict:
            return False, f"Player is in training until {end_time.strftime('%H:%M')}"

        # Check 5: Team already has a participant
        if self._check_team_already_registered(team_id):
            return False, "Another player from this team is already registered"

        # Check 6: Weekly participation limit
        if self._check_weekly_participation(player_token):
            return False, "Player has already participated in the 100m dash this week"

        # Check 7: Player registered for another competition
        other_comp = self._check_other_competition(player_token, competition_time)
        if other_comp:
            return False, f"Player is already registered for {other_comp}"

        # All checks passed
        return True, "Eligible"

    def _check_team_official_match(self, team_id: int, competition_time: datetime) -> bool:
        """Check if team has an official match within 5 hours of competition time."""
        # Use existing next_time_match function to check upcoming matches
        next_match = db.get_next_time_match(team_id)

        if next_match:
            # Convert relative time to absolute time
            match_time_delta = timedelta(
                days=next_match.get('days', 0),
                hours=next_match.get('hours', 0),
                minutes=next_match.get('minutes', 0)
            )

            # If match is within 5 hours of competition, return conflict
            hours_until_match = match_time_delta.total_seconds() / 3600
            if hours_until_match <= 5:
                return True

        return False

    def _check_player_training(self, player_token: str, team_id: int, competition_time: datetime) -> Tuple[
        bool, Optional[datetime]]:
        """Check if player is in training that conflicts with competition time."""
        # Get team trainings
        trainings = db.get_team_training(team_id)

        for training in trainings:
            # Parse participating players
            try:
                participating_players = json.loads(training.get('participating_players', '[]'))

                # Check if player is part of this training
                if player_token in participating_players:
                    # Check if training ends after competition starts
                    end_date = training.get('end_date')
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")

                    if end_date and end_date > competition_time:
                        return True, end_date
            except:
                # If error parsing JSON, continue to next training
                continue

        return False, None

    def _check_team_already_registered(self, team_id: int) -> bool:
        """Check if another player from this team is already registered."""
        # For now, check in memory list of participants
        for participant in self.participants:
            if participant.get('team_id') == team_id:
                return True
        return False

    def _check_weekly_participation(self, player_token: str) -> bool:
        """Check if player has already participated in 100m dash this week."""
        # This could be expanded with a DB query if needed
        trainings = db.get_player_competition(player_token)
        # For now, return False (no previous participation)
        return False

    def _check_other_competition(self, player_token: str, competition_time: datetime) -> Optional[str]:
        """Check if player is registered for another daily competition."""
        # This could be expanded with a DB query if needed
        trainings = db.get_player_competition(player_token)
        # For now, return None (no other competitions)
        return None

    def register_player(self, player_token: str, team_id: int, competition_time: datetime) -> Tuple[bool, str]:
        """
        Register a player for the competition after verifying eligibility.

        Args:
            player_token: Player's unique identifier
            team_id: Team's ID
            competition_time: Scheduled competition time

        Returns:
            Tuple of (success, message)
        """
        # Verify eligibility
        is_eligible, reason = self.verify_player_eligibility(player_token, team_id, competition_time)
        if not is_eligible:
            return False, reason

        # Get player data
        player = db.get_player_by_token(player_token)
        if not player:
            return False, "Player not found"

        # Get team data
        team = db.get_team_by_id(team_id)
        team_name = team.get('team_name', 'Unknown Team') if team else 'Unknown Team'

        # Add to participants list
        self.participants.append({
            'player_id': player_token,
            'player_name': player.get('name', 'Unknown Player'),
            'team_id': team_id,
            'team_name': team_name,
            'registration_time': datetime.now()
        })

        return True, f"Player {player.get('name', 'Unknown')} successfully registered for 100m Dash"

    def calculate_race_time(self, player: Dict) -> float:
        """
        Calculate a player's race time based on their attributes.

        Args:
            player: Player data dictionary with properties

        Returns:
            Race time in seconds (or DNF_TIME if below freshness threshold)
        """
        # Get player properties
        properties = player.get('properties', {})

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
            player_id = participant['player_id']

            # Get full player data from database
            player = db.get_player_by_token(player_id)

            # Calculate race time
            race_time = self.calculate_race_time(player)

            # Add to results
            results.append({
                'player_id': player_id,
                'player_name': participant['player_name'],
                'team_id': participant['team_id'],
                'team_name': participant['team_name'],
                'race_time': race_time,
                'dnf': race_time >= self.DNF_TIME
            })

        # Sort by race time (fastest first)
        results.sort(key=lambda x: x['race_time'])

        # Add ranking
        for i, result in enumerate(results):
            result['rank'] = i + 1

        # Store results for later use
        self.results = results

        return results

    def calculate_attribute_changes(self) -> List[Dict]:
        """
        Calculate attribute changes for participants based on competition results.

        Returns:
            List of player performance objects compatible with SQL_db.insert_player_attributes_game_effected
        """
        attribute_changes = []

        # Filter out DNF results for quintile calculations
        valid_results = [r for r in self.results if not r.get('dnf', False)]
        total_valid = len(valid_results)

        # Calculate changes for all participants (including DNF)
        for result in self.results:
            player_id = result['player_id']
            player = db.get_player_by_token(player_id)

            # Initialize performance object
            performance = {
                'attribute_deltas': {},
                'overall_score': 0,
                'team_won': False  # Not applicable for race
            }

            # Calculate satisfaction change based on quintiles for valid results
            if not result.get('dnf', False) and total_valid > 0:
                # Find participant's position in the results (0-indexed)
                position = next((i for i, r in enumerate(valid_results) if r['player_id'] == player_id), -1)

                # Calculate percentile (0 to 1, where 0 is best)
                percentile = position / total_valid if position >= 0 else 1.0

                # Determine satisfaction change based on quintile
                if percentile < 0.2:  # Top 20%
                    satisfaction_delta = 10
                elif percentile < 0.4:  # 20-40%
                    satisfaction_delta = 5
                elif percentile < 0.6:  # 40-60%
                    satisfaction_delta = 0
                elif percentile < 0.8:  # 60-80%
                    satisfaction_delta = -5
                else:  # Bottom 20%
                    satisfaction_delta = -10

                performance['satisfaction_delta'] = satisfaction_delta

            # Calculate freshness decrease - 10% of full match fatigue
            # Adapt calculation from post_game.py
            properties = player.get('properties', {})
            endurance = properties.get('Endurance', 50)

            # Similar formula as in post_game.py but reduced to 10%
            full_match_fatigue = 35 - (endurance / 4)
            freshness_decrease = full_match_fatigue * 0.1  # 10% of full match

            performance['freshness_delta'] = -freshness_decrease  # Negative for decrease

            # Add to attribute changes list in format compatible with insert_player_attributes_game_effected
            attribute_changes.append({
                'player_id': player_id,
                'performance': performance
            })

        return attribute_changes

    def apply_attribute_changes(self) -> None:
        """
        Apply the calculated attribute changes to players in the database.
        Uses the existing insert_player_attributes_game_effected function.
        """
        # Calculate attribute changes
        attribute_changes = self.calculate_attribute_changes()

        # Use existing DB function to apply changes
        db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)

 def run_and_update(self):
        self.run_competition()
        self.calculate_attribute_changes()
        self.apply_attribute_changes()