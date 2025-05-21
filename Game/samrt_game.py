import random
import json
from collections import defaultdict
import Helpers.SQL_db as db
import post_game as pg


class SoccerAttackOpportunitySystem:
    """
    Implementation of the Soccer Attack Opportunity Probability System as defined in the PRD.
    This system calculates the likelihood of creating dangerous attacking opportunities
    based on player positions, attributes, and field zones.
    """

    # Zone definitions based on the PRD
    ZONES = {
        1: "Left attacking",
        2: "Middle attacking",
        3: "Right attacking",
        4: "Right defensive",
        5: "Middle defensive",
        6: "Left defensive"
    }

    # Position types
    POSITIONS = [
        "GK", "Centre-back", "Full Back", "Wing Back",
        "Central Midfielder", "Wide Midfielder", "Winger",
        "Striker", "Forward"
    ]

    # Map position to simplified position for attribute weighting
    POSITION_MAPPING = {
        "GK": "GK",
        "Centre-back": "Center Back",
        "Full Back": "Full Back",
        "Wing Back": "Full Back",
        "Central Midfielder": "Central Midfielder",
        "Wide Midfielder": "Central Midfielder",
        "Winger": "Winger",
        "Striker": "Center Forward",
        "Forward": "Forward"
    }

    # Supported formations
    FORMATIONS = ["3-4-3", "3-5-2", "4-2-4", "4-3-3", "4-4-2", "5-3-2"]

    def __init__(self, formation_weights=None, attribute_weights=None):
        """
        Initialize the system with position weights by zone and attribute weights by position.

        Args:
            formation_weights: Dictionary of formation weights by zone, defaults to values from PRD
            attribute_weights: Dictionary of attribute weights by position, defaults to values from PRD
        """
        # Load default weights from PRD if not provided
        self.formation_weights = formation_weights or self._load_formation_weights()
        self.attribute_weights = attribute_weights or self._load_attribute_weights()

    def _load_formation_weights(self):
        """Load formation zone weights from default values in the PRD"""
        # This would typically load from a JSON or database
        # For now, we'll include a simplified version based on the PRD

        weights = {}

        # Example for 4-3-3 formation, zone 1 (Left Attacking)
        weights["4-3-3"] = {
            1: {  # Left Attacking
                "Left Winger": 0.30,
                "Full Back": 0.25,
                "Central Midfielder": 0.20,
                "Striker": 0.15,
                "Centre-back": 0.09,
                "GK": 0.01
            },
            2: {  # Middle Attacking
                "Central Midfielder": 0.35,
                "Striker": 0.27,
                "Left Winger": 0.15,
                "Right Winger": 0.15,
                "Wide Midfielder": 0.07,
                "GK": 0.01
            },
            3: {  # Right Attacking
                "Right Winger": 0.30,
                "Full Back": 0.25,
                "Central Midfielder": 0.20,
                "Striker": 0.15,
                "Centre-back": 0.09,
                "GK": 0.01
            },
            4: {  # Right Defensive
                "Centre-back": 0.35,
                "Full Back": 0.30,
                "Central Midfielder": 0.15,
                "GK": 0.10,
                "Winger": 0.10
            },
            5: {  # Middle Defensive
                "Centre-back": 0.60,  # Combining left and right CB
                "GK": 0.25,
                "Central Midfielder": 0.15
            },
            6: {  # Left Defensive
                "Centre-back": 0.35,
                "Full Back": 0.30,
                "Central Midfielder": 0.15,
                "GK": 0.10,
                "Winger": 0.10
            }
        }

        # Simplified versions for other formations
        for formation in ["3-4-3", "3-5-2", "4-2-4", "4-4-2", "5-3-2"]:
            weights[formation] = weights["4-3-3"].copy()

        return weights

    def _load_attribute_weights(self):
        """Load attribute weights by position from default values in the PRD"""
        # This would typically load from a JSON or database
        # For now, we'll include the values from the PRD

        return {
            "GK": {
                "Game_vision": 0.50,
                "GK_Kicking": 0.30,
                "Pass_Precision": 0.20
            },
            "Center Back": {
                "Pass_Precision": 0.40,
                "Game_vision": 0.30,
                "Heading": 0.15,
                "Physicality": 0.15
            },
            "Full Back": {
                "Speed": 0.25,
                "Pass_Precision": 0.25,
                "Dribble": 0.25,
                "Game_vision": 0.15,
                "Endurance": 0.10
            },
            "Central Midfielder": {
                "Game_vision": 0.35,
                "Pass_Precision": 0.35,
                "Dribble": 0.15,
                "Speed": 0.10,
                "Physicality": 0.05
            },
            "Winger": {
                "Dribble": 0.35,
                "Speed": 0.30,
                "Pass_Precision": 0.20,
                "Game_vision": 0.15
            },
            "Center Forward": {
                "Game_vision": 0.25,
                "Dribble": 0.25,
                "Speed": 0.20,
                "Pass_Precision": 0.15,
                "Physicality": 0.10,
                "Heading": 0.05
            },
            "Forward": {
                "Dribble": 0.30,
                "Speed": 0.25,
                "Game_vision": 0.20,
                "Pass_Precision": 0.20,
                "Physicality": 0.05
            }
        }

    def calculate_zone_attack_opportunity(self, players, formation, zone):
        """
        Calculate the attack opportunity probability for a specific zone.

        Args:
            players: List of player objects with position and attributes
            formation: Team formation (e.g., "4-3-3")
            zone: Zone number (1-6)

        Returns:
            Zone attack opportunity score (0-100)
        """
        if formation not in self.formation_weights:
            # Default to 4-3-3 if formation not found
            formation = "4-3-3"

        zone_weights = self.formation_weights[formation].get(zone, {})

        total_opportunity = 0

        for player in players:
            position = player.get("position")
            # Skip if player position is not in weights for this zone
            if position not in zone_weights:
                continue

            # Get position weight for this zone
            position_weight = zone_weights[position]

            # Calculate player attack rating based on attributes
            player_attack_rating = self.calculate_player_attack_rating(player)

            # Add to total opportunity
            total_opportunity += position_weight * player_attack_rating

        # Scale to 0-100 range for easier interpretation
        return total_opportunity * 100

    def calculate_player_attack_rating(self, player):
        """
        Calculate a player's attack contribution rating based on their position and attributes.

        Args:
            player: Player object with position and attributes

        Returns:
            Player attack rating (0-1 scale)
        """
        position = player.get("position")
        attributes = player.get("properties", {})

        # Map position to simplified position for attribute weighting
        mapped_position = self.POSITION_MAPPING.get(position, "Central Midfielder")

        # Get attribute weights for this position
        attribute_weights = self.attribute_weights.get(mapped_position, {})

        # Calculate weighted attribute score
        total_score = 0
        total_weight = 0

        for attr, weight in attribute_weights.items():
            # Get attribute value (default to 50 if not found)
            attr_value = attributes.get(attr, 50)
            total_score += attr_value * weight
            total_weight += weight

        # Normalize result to 0-1 scale
        if total_weight > 0:
            return total_score / (total_weight * 100)
        else:
            return 0.5  # Default to average if no weights

    def get_attack_danger_distribution(self, attack_zone_rating, defense_zone_rating):
        """
        Calculate the probability distribution for attack danger levels.

        Args:
            attack_zone_rating: Rating of the attacking zone (0-100)
            defense_zone_rating: Rating of the defending zone (0-100)

        Returns:
            Dictionary of probabilities for each danger level (1-5)
        """
        # Baseline distribution from PRD
        baseline = {
            1: 0.55,  # Least dangerous
            2: 0.20,
            3: 0.15,
            4: 0.07,
            5: 0.03  # Most dangerous
        }

        # Calculate attack advantage percentage
        scale_factor = 50  # Scaling factor to convert rating difference to percentage
        attack_advantage = (attack_zone_rating - defense_zone_rating) / scale_factor

        # Adjust distribution based on advantage
        adjusted = {}

        # If advantage is positive, increase higher danger levels
        # If negative, increase lower danger levels
        if attack_advantage > 0:
            # Reduce levels 1-2, increase levels 3-5
            adjustment = min(attack_advantage, 0.25)  # Cap the maximum adjustment

            adjusted[1] = max(0.30, baseline[1] - adjustment * 0.9)
            adjusted[2] = max(0.15, baseline[2] - adjustment * 0.3)
            adjusted[3] = min(0.25, baseline[3] + adjustment * 0.5)
            adjusted[4] = min(0.15, baseline[4] + adjustment * 0.3)
            adjusted[5] = min(0.15, baseline[5] + adjustment * 0.4)
        else:
            # Increase levels 1-2, reduce levels 3-5
            adjustment = min(abs(attack_advantage), 0.25)  # Cap the maximum adjustment

            adjusted[1] = min(0.75, baseline[1] + adjustment * 0.9)
            adjusted[2] = min(0.25, baseline[2] + adjustment * 0.3)
            adjusted[3] = max(0.05, baseline[3] - adjustment * 0.5)
            adjusted[4] = max(0.02, baseline[4] - adjustment * 0.3)
            adjusted[5] = max(0.01, baseline[5] - adjustment * 0.4)

        # Normalize to ensure probabilities sum to 1
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}


class MatchSimulator:
    """
    Enhanced football match simulator that integrates the Soccer Attack Opportunity System
    and player action assignments.
    """

    def __init__(self):
        """Initialize the match simulator with the attack opportunity system"""
        self.attack_system = SoccerAttackOpportunitySystem()
        self.event_logger = EventLogger()

    def simulate_football_match(self, team1, team2):
        """
        Simulate a football match between two teams.

        Args:
            team1: First team data (with players, formation, etc.)
            team2: Second team data

        Returns:
            Tuple of (team1_score, team2_score, match_events, player_performances)
        """
        # Initialize match data
        team1_score = 0
        team2_score = 0
        team1_id = team1.get("id", "team1")
        team2_id = team2.get("id", "team2")

        # Get team formations
        team1_formation = team1.get("formation", "4-3-3")
        team2_formation = team2.get("formation", "4-3-3")

        # Get players
        team1_players = team1.get("players", [])
        team2_players = team2.get("players", [])

        # Track player performance
        player_performances = self._initialize_player_performances(team1_players, team2_players)

        # Calculate attacking zone ratings for each team
        team1_zone_ratings = self._calculate_team_zone_ratings(team1_players, team1_formation)
        team2_zone_ratings = self._calculate_team_zone_ratings(team2_players, team2_formation)

        # Total number of attacks in a match
        total_attacks = 200

        # Attacking zone pairs (attacking zone vs defending zone)
        zone_pairs = [
            (1, 4),  # Left attack vs Right defense
            (2, 5),  # Middle attack vs Middle defense
            (3, 6)  # Right attack vs Left defense
        ]

        # Calculate overall midfield strength (affects possession)
        team1_midfield = self._calculate_midfield_strength(team1_players)
        team2_midfield = self._calculate_midfield_strength(team2_players)

        # Calculate possession based on midfield strength
        total_midfield = team1_midfield + team2_midfield
        team1_possession = team1_midfield / total_midfield if total_midfield > 0 else 0.5

        # Simulate attacks
        for attack_num in range(total_attacks):
            # Determine attacking team based on possession
            if random.random() < team1_possession:
                attacking_team_id = team1_id
                defending_team_id = team2_id
                attacking_players = team1_players
                defending_players = team2_players
                attacking_formation = team1_formation
                defending_formation = team2_formation
                attacking_zone_ratings = team1_zone_ratings
                defending_zone_ratings = team2_zone_ratings
            else:
                attacking_team_id = team2_id
                defending_team_id = team1_id
                attacking_players = team2_players
                defending_players = team1_players
                attacking_formation = team2_formation
                defending_formation = team1_formation
                attacking_zone_ratings = team2_zone_ratings
                defending_zone_ratings = team1_zone_ratings

            # Choose attacking zone
            attack_zone_chances = {
                1: attacking_zone_ratings[1] / sum(attacking_zone_ratings.values()),
                2: attacking_zone_ratings[2] / sum(attacking_zone_ratings.values()),
                3: attacking_zone_ratings[3] / sum(attacking_zone_ratings.values())
            }

            attack_zone = self._weighted_choice(attack_zone_chances)

            # Get corresponding defense zone
            defense_zone = zone_pairs[attack_zone - 1][1]

            # Get zone ratings
            attack_rating = attacking_zone_ratings[attack_zone]
            defense_rating = defending_zone_ratings[defense_zone]

            # Get danger level distribution
            danger_distribution = self.attack_system.get_attack_danger_distribution(
                attack_rating, defense_rating
            )

            # Choose danger level based on distribution
            danger_level = self._weighted_choice(danger_distribution)

            # For higher danger levels, determine if a goal was scored
            if danger_level >= 4:
                # Generate random minute for the attack (1-90)
                minute = random.randint(1, 90)
                second = random.randint(0, 59)

                # Choose attacking player based on position weights for that zone
                attacker = self._choose_player_for_attack(attacking_players, attack_zone, attacking_formation)

                if attacker:
                    # Log shot attempt
                    self.event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=attacker["player_id"],
                        team_id=attacking_team_id,
                        action_id=6,  # Shot attempt
                        description=f"Player {attacker['player_id']} attempted a shot"
                    )

                    # Update player performance
                    player_performances[attacker["player_id"]]["shots"] = player_performances[
                                                                              attacker["player_id"]].get("shots", 0) + 1

                    # Danger level 5 has higher goal probability
                    goal_probability = 0.30 if danger_level == 5 else 0.10

                    # Calculate if goal is scored
                    if random.random() < goal_probability:
                        # Goal scored!
                        if attacking_team_id == team1_id:
                            team1_score += 1
                        else:
                            team2_score += 1

                        # Identify possible assister (20% of goals have assists)
                        if random.random() < 0.60:
                            assister = self._choose_player_for_assist(attacking_players, attack_zone,
                                                                      attacking_formation,
                                                                      exclude_id=attacker["player_id"])
                        else:
                            assister = None

                        # Log goal event
                        self._log_goal_with_assist(minute, second, attacker, assister, attacking_team_id)

                        # Update player performances
                        player_performances[attacker["player_id"]]["scored_goal"] = player_performances[
                                                                                        attacker["player_id"]].get(
                            "scored_goal", 0) + 1

                        if assister:
                            player_performances[assister["player_id"]]["assist"] = player_performances[
                                                                                       assister["player_id"]].get(
                                "assist", 0) + 1
                    else:
                        # Shot saved/blocked
                        if random.random() < 0.5:
                            # GK save
                            goalkeeper = next((p for p in defending_players if p.get("position") == "GK"), None)
                            if goalkeeper:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=goalkeeper["player_id"],
                                    team_id=defending_team_id,
                                    action_id=8,  # GK save
                                    description=f"Goalkeeper {goalkeeper['player_id']} saved a shot from {attacker['player_id']}"
                                )
                                player_performances[goalkeeper["player_id"]]["defense_action"] = player_performances[
                                                                                                     goalkeeper[
                                                                                                         "player_id"]].get(
                                    "defense_action", 0) + 1
                        else:
                            # Defender block
                            defender = self._choose_defender_for_block(defending_players, defense_zone,
                                                                       defending_formation)
                            if defender:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=defender["player_id"],
                                    team_id=defending_team_id,
                                    action_id=7,  # Blocked shot
                                    description=f"Player {defender['player_id']} blocked a shot from {attacker['player_id']}"
                                )
                                player_performances[defender["player_id"]]["defense_action"] = player_performances[
                                                                                                   defender[
                                                                                                       "player_id"]].get(
                                    "defense_action", 0) + 1

        # Calculate player ratings
        player_stories = self._generate_player_stories(player_performances, team1_id, team2_id, team1_score,
                                                       team2_score)

        # Calculate man of the match
        man_of_the_match = self._calculate_man_of_the_match(player_stories)

        # Calculate satisfaction changes
        self._calculate_satisfaction_changes(player_stories, team1_score, team2_score, man_of_the_match)

        # Return match results and events
        return {
            "result": {"team1_score": team1_score, "team2_score": team2_score},
            "time_played_mins": 90,
            "player_stories": player_stories,
            "man_of_the_match": man_of_the_match,
            "events": self.event_logger.get_events()
        }

    def _initialize_player_performances(self, team1_players, team2_players):
        """Initialize performance tracking for all players"""
        performances = {}

        for player in team1_players + team2_players:
            performances[player["player_id"]] = {
                "player_id": player["player_id"],
                "player_data": player.get("name", "Player " + str(player["player_id"])),
                "player_team_id": player.get("team_id", "unknown"),
                "player_properties": player.get("properties", {}),
                "player_position": player.get("position", "Unknown"),
                "scored_goal": 0,
                "assist": 0,
                "defense_action": 0,
                "shots": 0,
                "punished": False,
                "injured": False
            }

        return performances

    def _calculate_team_zone_ratings(self, players, formation):
        """Calculate attack opportunity ratings for each zone"""
        ratings = {}

        # Calculate for attacking zones (1-3)
        for zone in [1, 2, 3]:
            ratings[zone] = self.attack_system.calculate_zone_attack_opportunity(players, formation, zone)

        # Calculate for defensive zones (4-6)
        for zone in [4, 5, 6]:
            ratings[zone] = self.attack_system.calculate_zone_attack_opportunity(players, formation, zone)

        return ratings

    def _calculate_midfield_strength(self, players):
        """Calculate overall midfield strength based on midfielders' attributes"""
        midfield_strength = 0
        midfielder_count = 0

        for player in players:
            position = player.get("position", "")
            if "Midfielder" in position or position in ["Central Midfielder", "Wide Midfielder"]:
                # Get key midfielder attributes
                attributes = player.get("properties", {})

                # Calculate weighted score based on key midfield attributes
                attribute_score = (
                        attributes.get("Game_vision", 50) * 0.4 +
                        attributes.get("Pass_Precision", 50) * 0.3 +
                        attributes.get("Dribble", 50) * 0.2 +
                        attributes.get("Endurance", 50) * 0.1
                )

                midfield_strength += attribute_score
                midfielder_count += 1

        # Return average midfield strength, defaulting to 50 if no midfielders
        return midfield_strength / midfielder_count if midfielder_count > 0 else 50

    def _weighted_choice(self, choices):
        """Choose a random item based on weights"""
        total = sum(choices.values())
        r = random.uniform(0, total)
        upto = 0

        for choice, weight in choices.items():
            upto += weight
            if upto > r:
                return choice

        # Fallback to first choice if something goes wrong
        return list(choices.keys())[0]

    def _choose_player_for_attack(self, players, attack_zone, formation):
        """Choose a player to lead an attack based on zone weights"""
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(attack_zone, {})

        # Filter players by position and create weighted selection
        candidates = []

        for player in players:
            position = player.get("position")
            if position in zone_weights:
                # Add player to candidates with weight based on position and attributes
                position_weight = zone_weights[position]

                # Get attack rating
                attack_rating = self.attack_system.calculate_player_attack_rating(player)

                # Final weight is position weight * attack rating
                weight = position_weight * attack_rating

                candidates.append((player, weight))

        # Return random player weighted by contribution
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return random player
        return random.choice(players) if players else None

    def _choose_player_for_assist(self, players, attack_zone, formation, exclude_id=None):
        """
        Choose a player to provide an assist based on performance metrics,
        position relevance to the zone, and actual passing attributes.
        """
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(attack_zone, {})

        # Filter players for assist
        candidates = []

        for player in players:
            # Exclude goal scorer
            if exclude_id and player.get("player_id") == exclude_id:
                continue

            position = player.get("position")

            # Only consider players in appropriate positions for assists
            if position in ["Striker", "Forward", "Winger", "Wide Midfielder", "Central Midfielder"]:
                # Base weight from zone contribution
                position_weight = zone_weights.get(position, 0.05)

                # Get key attributes for assists
                attributes = player.get("properties", {})
                pass_precision = attributes.get("Pass_Precision", 50) / 100
                game_vision = attributes.get("Game_vision", 50) / 100
                dribble = attributes.get("Dribble", 50) / 100
                speed = attributes.get("Speed", 50) / 100

                # Calculate passing ability score (weighted combination of relevant attributes)
                passing_ability = (
                        pass_precision * 0.40 +  # Precision is most important
                        game_vision * 0.35 +  # Vision is critical for assists
                        dribble * 0.15 +  # Ability to beat opponents before passing
                        speed * 0.10  # Speed to get into assist positions
                )

                # Calculate position-specific bonus based on the attacking zone
                position_zone_bonus = 1.0

                # Left-sided players have advantage in left attack zone
                if attack_zone == 1 and position in ["Wide Midfielder", "Winger"] and "Left" in player.get(
                        "position_detail", ""):
                    position_zone_bonus = 1.5
                # Right-sided players have advantage in right attack zone
                elif attack_zone == 3 and position in ["Wide Midfielder", "Winger"] and "Right" in player.get(
                        "position_detail", ""):
                    position_zone_bonus = 1.5
                # Central players have advantage in central attack zone
                elif attack_zone == 2 and position in ["Central Midfielder", "Striker"]:
                    position_zone_bonus = 1.3

                # Final weight calculation
                final_weight = position_weight * passing_ability * position_zone_bonus

                # Add player with calculated weight
                candidates.append((player, final_weight))

        # Return weighted random selection
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            if total_weight <= 0:
                return None

            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return None
        return None

    def _choose_defender_for_block(self, players, defense_zone, formation):
        """Choose a defensive player to block a shot"""
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(defense_zone, {})

        # Filter players for defensive actions
        candidates = []

        for player in players:
            position = player.get("position")

            # Prefer defenders and defensive midfielders
            if position in ["Centre-back", "Full Back", "Wing Back", "Central Midfielder"]:
                # Add player to candidates with weight
                weight = zone_weights.get(position, 0.05)

                # Increase weight for players with good defensive attributes
                attributes = player.get("properties", {})
                physicality = attributes.get("Physicality", 50) / 100

                # Final weight is position weight * defensive ability
                weight = weight * physicality

                candidates.append((player, weight))

        # Return random player weighted by contribution
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            if total_weight <= 0:
                return random.choice(players) if players else None

            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return random player
        return random.choice(players) if players else None

    def _log_goal_with_assist(self, goal_minute, goal_second, scorer, assister=None, team_id=None):
        """
        Log goal and assist events with realistic timing and descriptions based on player attributes.

        This improved version creates more realistic event descriptions based on:
        1. Player positions and attributes
        2. Timing characteristics of different types of goals/assists
        3. Dynamic event descriptions based on scenario
        """
        goal_description = ""
        assist_description = ""

        # Generate descriptive goal event based on scorer's attributes and position
        if scorer:
            position = scorer.get("position", "")
            attributes = scorer.get("properties", {})

            # Different types of goal descriptions based on player position and attributes
            if position in ["Striker", "Forward"]:
                if attributes.get("Shooting", 50) > 70:
                    goal_types = [
                        f"unleashed a powerful shot into the net",
                        f"finished clinically from inside the box",
                        f"beat the goalkeeper with a precise finish"
                    ]
                else:
                    goal_types = [
                        f"managed to put the ball in the net",
                        f"scored from close range",
                        f"found the back of the net"
                    ]
            elif position in ["Winger", "Wide Midfielder"]:
                if attributes.get("Dribble", 50) > 70:
                    goal_types = [
                        f"cut inside and fired into the far corner",
                        f"dribbled past defenders to score",
                        f"scored after a brilliant solo run"
                    ]
                else:
                    goal_types = [
                        f"found space to shoot and scored",
                        f"took a chance from the wing and scored",
                        f"got on the scoresheet"
                    ]
            elif position in ["Central Midfielder"]:
                goal_types = [
                    f"scored from outside the box",
                    f"found the net with a well-placed shot",
                    f"capitalized on the opportunity to score"
                ]
            else:
                goal_types = [
                    f"scored a goal",
                    f"found the back of the net",
                    f"got on the scoresheet"
                ]

            goal_description = f"Player {scorer['player_id']} {random.choice(goal_types)}"

        # Generate assist description based on assister's position and attributes
        if assister and assister['player_id'] != scorer['player_id']:
            position = assister.get("position", "")
            attributes = assister.get("properties", {})

            # Different types of assist descriptions based on player position and attributes
            if position in ["Winger", "Wide Midfielder"]:
                if attributes.get("Pass_Precision", 50) > 70:
                    assist_types = [
                        f"delivered a perfect cross",
                        f"whipped in a dangerous ball",
                        f"found space on the wing and crossed"
                    ]
                else:
                    assist_types = [
                        f"sent in a cross",
                        f"put the ball into the box",
                        f"delivered a cross"
                    ]
            elif position in ["Central Midfielder"]:
                if attributes.get("Game_vision", 50) > 70:
                    assist_types = [
                        f"played a defense-splitting pass",
                        f"threaded a brilliant through ball",
                        f"spotted the run and delivered a perfect pass"
                    ]
                else:
                    assist_types = [
                        f"found a teammate with a pass",
                        f"played it forward",
                        f"provided the pass"
                    ]
            elif position in ["Striker", "Forward"]:
                assist_types = [
                    f"laid it off",
                    f"headed it down",
                    f"flicked the ball on"
                ]
            else:
                assist_types = [
                    f"provided the assist",
                    f"set up the goal",
                    f"created the chance"
                ]

            assist_description = f"Player {assister['player_id']} {random.choice(assist_types)} for Player {scorer['player_id']}"

            # Timing: assist happens a few seconds before the goal
            assist_minute = goal_minute
            assist_second = goal_second - random.randint(2, 6)

            # Handle the case where assist_second becomes negative
            if assist_second < 0:
                assist_minute = max(1, goal_minute - 1)
                assist_second = 60 + assist_second

            # Log the assist event
            self.event_logger.log_event(
                minute=assist_minute,
                second=assist_second,
                token=assister['player_id'],
                team_id=team_id,
                action_id=2,  # Assist
                description=assist_description
            )

        # Add assist information to goal description if available
        if assister and assister['player_id'] != scorer['player_id']:
            goal_description += f" from {assister['player_id']}'s assist"

        # Log the goal event
        self.event_logger.log_event(
            minute=goal_minute,
            second=goal_second,
            token=scorer['player_id'],
            team_id=team_id,
            action_id=1,  # Goal
            description=goal_description
        )

    def _generate_player_stories(self, player_performances, team1_id, team2_id, team1_score, team2_score):
        """Generate player stories from performance data"""
        player_stories = []

        for player_id, performance in player_performances.items():
            team_won = (performance["player_team_id"] == team1_id and team1_score > team2_score) or \
                       (performance["player_team_id"] == team2_id and team2_score > team1_score)

            team_score = team1_score if performance["player_team_id"] == team1_id else team2_score
            opponent_score = team2_score if performance["player_team_id"] == team1_id else team1_score

            # Calculate overall score
            overall_score = self._calculate_player_score(
                performance,
                team_score,
                opponent_score,
                team_won
            )

            # Random attribute updates
            attribute_updates = self._random_attribute_updates(performance, team_won)

            # Calculate freshness drop
            freshness_delta = -self._calculate_freshness_drop(
                performance.get("player_properties", {}).get("Endurance", 50)
            )

            player_stories.append({
                "player_id": player_id,
                "player_data": performance["player_data"],
                "player_team_id": performance["player_team_id"],
                "player_properties": performance["player_properties"],
                "player_position": performance["player_position"],
                "performance": {
                    "overall_score": overall_score,
                    "team_won": team_won,
                    "scored_goal": performance.get("scored_goal", 0),
                    "assist": performance.get("assist", 0),
                    "defense_action": performance.get("defense_action", 0),
                    "injured": performance.get("injured", False),
                    "punished": performance.get("punished", False),
                    "attribute_deltas": attribute_updates,
                    "freshness_delta": freshness_delta
                }})

    def process_must_win_game(self, team1, team2, team1_score=None, team2_score=None):
        """
        Process a "must win" game where there must be a winner.
        If tied after 90 minutes, the game goes to extra time.
        If still tied after extra time, goes to penalties.

        Args:
            team1: First team data
            team2: Second team data
            team1_score: Optional preset score for team1 (for testing)
            team2_score: Optional preset score for team2 (for testing)

        Returns:
            Combined match result including all periods and possible shootout
        """
        team1_id = team1.get("id", "team1")
        team2_id = team2.get("id", "team2")

        # Step 1: Simulate regular 90 minute game
        regular_time = self.simulate_football_match(team1, team2)

        # Extract the scores (or use preset scores for testing)
        t1_score = team1_score if team1_score is not None else regular_time["result"]["team1_score"]
        t2_score = team2_score if team2_score is not None else regular_time["result"]["team2_score"]

        # Update result with actual scores
        regular_time["result"]["team1_score"] = t1_score
        regular_time["result"]["team2_score"] = t2_score

        # Check if the game is tied after regular time
        if t1_score == t2_score:
            # Add a message to the event log that the game is going to extra time
            self.event_logger.log_event(
                minute=90,
                second=0,
                token="system",
                team_id=None,
                action_id=9,  # Special action for period transitions
                description="Regular time ended with a draw. Match proceeds to extra time."
            )

            # Step 2: Simulate first extra time (91-105)
            first_extra_time = self._simulate_extra_time(
                team1, team2,
                regular_time["player_stories"],
                90,
                is_first_extra_time=True
            )

            # Update scores
            t1_score += first_extra_time["result"]["team1_score"]
            t2_score += first_extra_time["result"]["team2_score"]

            # Merge the results
            combined_result = self._merge_match_periods(regular_time, first_extra_time)

            # Check if still tied after first extra time
            if t1_score == t2_score:
                # Step 3: Simulate second extra time (106-120)
                second_extra_time = self._simulate_extra_time(
                    team1, team2,
                    combined_result["player_stories"],
                    105,
                    is_first_extra_time=False
                )

                # Update scores
                t1_score += second_extra_time["result"]["team1_score"]
                t2_score += second_extra_time["result"]["team2_score"]

                # Merge results again
                combined_result = self._merge_match_periods(combined_result, second_extra_time)

                # Check if still tied after second extra time
                if t1_score == t2_score:
                    # Step 4: Simulate penalty shootout
                    penalty_shootout = self._simulate_penalty_shootout(
                        team1, team2,
                        combined_result["player_stories"]
                    )

                    # Merge penalty shootout results
                    combined_result["events"].extend(penalty_shootout["events"])
                    combined_result["penalty_details"] = penalty_shootout["penalty_details"]
                    combined_result["winner_id"] = penalty_shootout["result"]["winner_id"]

                    # Add special flag to indicate the match was decided by penalties
                    combined_result["decided_by"] = "penalties"
                else:
                    # Match decided in second extra time
                    combined_result["winner_id"] = team1_id if t1_score > t2_score else team2_id
                    combined_result["decided_by"] = "second_extra_time"
            else:
                # Match decided in first extra time
                combined_result["winner_id"] = team1_id if t1_score > t2_score else team2_id
                combined_result["decided_by"] = "first_extra_time"
        else:
            # Match decided in regular time
            combined_result = regular_time
            combined_result["winner_id"] = team1_id if t1_score > t2_score else team2_id
            combined_result["decided_by"] = "regular_time"

        # Update the final score in combined result
        combined_result["result"]["team1_score"] = t1_score
        combined_result["result"]["team2_score"] = t2_score

        return combined_result

    def _simulate_extra_time(self, team1, team2, previous_player_stories, prev_time_played, is_first_extra_time=True):
        """
        Simulate an extra time period (either 91-105 or 106-120 minutes).

        Args:
            team1: First team data
            team2: Second team data
            previous_player_stories: Player performances from previous periods
            prev_time_played: Minutes already played (90 or 105)
            is_first_extra_time: Whether this is the first (True) or second (False) extra time

        Returns:
            Match results for this extra time period
        """
        team1_id = team1.get("id", "team1")
        team2_id = team2.get("id", "team2")

        # Set time period
        if is_first_extra_time:
            period_start, period_end = prev_time_played, prev_time_played + 15  # 90-105
            period_name = "First Extra Time"
        else:
            period_start, period_end = prev_time_played, prev_time_played + 15  # 105-120
            period_name = "Second Extra Time"

        # Calculate fatigue factor - players are more tired now
        fatigue_factor = 0.8 if is_first_extra_time else 0.7

        # Log start of extra time period
        self.event_logger.log_event(
            minute=period_start,
            second=0,
            token="system",
            team_id=None,
            action_id=10,  # Special system event
            description=f"{period_name} begins"
        )

        # Recreate player objects from player stories (just the key fields needed for simulation)
        team1_players = []
        team2_players = []

        for player_story in previous_player_stories:
            player_obj = {
                "player_id": player_story["player_id"],
                "name": player_story["player_data"],
                "team_id": player_story["player_team_id"],
                "position": player_story["player_position"],
                "properties": player_story["player_properties"]
            }

            # Apply fatigue to player attributes
            fatigue_impact = random.uniform(0.05, 0.15) * (2 - fatigue_factor)
            for attr in player_obj["properties"]:
                if attr in ["Endurance", "Speed", "Dribble"]:
                    # These attributes are most affected by fatigue
                    player_obj["properties"][attr] = max(40, player_obj["properties"][attr] * (1 - fatigue_impact))

            # Add to appropriate team
            if player_story["player_team_id"] == team1_id:
                team1_players.append(player_obj)
            else:
                team2_players.append(player_obj)

        # Update team objects with fatigued players
        team1_for_extra = team1.copy()
        team1_for_extra["players"] = team1_players

        team2_for_extra = team2.copy()
        team2_for_extra["players"] = team2_players

        # Calculate zone ratings for extra time (affected by fatigue)
        team1_zone_ratings = self._calculate_team_zone_ratings(team1_players, team1.get("formation", "4-3-3"))
        team2_zone_ratings = self._calculate_team_zone_ratings(team2_players, team2.get("formation", "4-3-3"))

        # Calculate possession for extra time (affected by fatigue and previous period)
        team1_midfield = self._calculate_midfield_strength(team1_players) * fatigue_factor
        team2_midfield = self._calculate_midfield_strength(team2_players) * fatigue_factor

        total_midfield = team1_midfield + team2_midfield
        team1_possession = team1_midfield / total_midfield if total_midfield > 0 else 0.5

        # Reduced number of attacks in extra time
        total_attacks = 30  # Fewer attacks in 15 minutes of extra time

        # Initialize extra time results
        team1_score = 0
        team2_score = 0
        player_performances = self._initialize_player_performances(team1_players, team2_players)

        # Attacking zone pairs
        zone_pairs = [
            (1, 4),  # Left attack vs Right defense
            (2, 5),  # Middle attack vs Middle defense
            (3, 6)  # Right attack vs Left defense
        ]

        # Simulate attacks in extra time
        for attack_num in range(total_attacks):
            # Extra time is more cautious - higher threshold for dangerous attacks
            caution_factor = 0.7

            # Determine attacking team based on possession
            if random.random() < team1_possession:
                attacking_team_id = team1_id
                defending_team_id = team2_id
                attacking_players = team1_players
                defending_players = team2_players
                attacking_formation = team1.get("formation", "4-3-3")
                defending_formation = team2.get("formation", "4-3-3")
                attacking_zone_ratings = team1_zone_ratings
                defending_zone_ratings = team2_zone_ratings
            else:
                attacking_team_id = team2_id
                defending_team_id = team1_id
                attacking_players = team2_players
                defending_players = team1_players
                attacking_formation = team2.get("formation", "4-3-3")
                defending_formation = team1.get("formation", "4-3-3")
                attacking_zone_ratings = team2_zone_ratings
                defending_zone_ratings = team1_zone_ratings

            # Choose attacking zone
            attack_zone_chances = {
                1: attacking_zone_ratings[1] / sum(attacking_zone_ratings.values()),
                2: attacking_zone_ratings[2] / sum(attacking_zone_ratings.values()),
                3: attacking_zone_ratings[3] / sum(attacking_zone_ratings.values())
            }

            attack_zone = self._weighted_choice(attack_zone_chances)

            # Get corresponding defense zone
            defense_zone = zone_pairs[attack_zone - 1][1]

            # Get zone ratings
            attack_rating = attacking_zone_ratings[attack_zone] * fatigue_factor
            defense_rating = defending_zone_ratings[defense_zone] * fatigue_factor

            # Get danger level distribution (adjusted for extra time caution)
            base_danger_distribution = self.attack_system.get_attack_danger_distribution(
                attack_rating, defense_rating
            )

            # Make extra time more cautious - reduce probability of high danger levels
            cautious_danger_distribution = {
                1: base_danger_distribution[1] * 1.2,  # Increase low-danger attacks
                2: base_danger_distribution[2] * 1.1,
                3: base_danger_distribution[3] * 0.9,
                4: base_danger_distribution[4] * 0.8,
                5: base_danger_distribution[5] * 0.6  # Significant reduction in high-danger attacks
            }

            # Normalize distribution
            total_prob = sum(cautious_danger_distribution.values())
            cautious_danger_distribution = {k: v / total_prob for k, v in cautious_danger_distribution.items()}

            # Choose danger level based on distribution
            danger_level = self._weighted_choice(cautious_danger_distribution)

            # For higher danger levels, determine if a goal was scored
            if danger_level >= 4:
                # Generate random minute for the attack (within extra time period)
                minute = random.randint(period_start, period_end)
                second = random.randint(0, 59)

                # Choose attacking player based on position weights for that zone
                attacker = self._choose_player_for_attack(attacking_players, attack_zone, attacking_formation)

                if attacker:
                    # Log shot attempt
                    self.event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=attacker["player_id"],
                        team_id=attacking_team_id,
                        action_id=6,  # Shot attempt
                        description=f"Player {attacker['player_id']} attempted a shot in {period_name}"
                    )

                    # Update player performance
                    player_performances[attacker["player_id"]]["shots"] = player_performances[
                                                                              attacker["player_id"]].get("shots", 0) + 1

                    # Lower goal probability in extra time due to fatigue
                    base_goal_probability = 0.20 if danger_level == 5 else 0.08
                    goal_probability = base_goal_probability * fatigue_factor

                    # Calculate if goal is scored
                    if random.random() < goal_probability:
                        # Goal scored!
                        if attacking_team_id == team1_id:
                            team1_score += 1
                        else:
                            team2_score += 1

                        # Less likely to have assists in extra time due to fatigue
                        assist_probability = 0.4 * fatigue_factor
                        if random.random() < assist_probability:
                            assister = self._choose_player_for_assist(attacking_players, attack_zone,
                                                                      attacking_formation,
                                                                      exclude_id=attacker["player_id"])
                        else:
                            assister = None

                        # Log goal event
                        period_suffix = f" in {period_name}"
                        self._log_goal_with_assist(minute, second, attacker, assister, attacking_team_id)

                        # Update player performances
                        player_performances[attacker["player_id"]]["scored_goal"] = player_performances[
                                                                                        attacker["player_id"]].get(
                            "scored_goal", 0) + 1

                        if assister:
                            player_performances[assister["player_id"]]["assist"] = player_performances[
                                                                                       assister["player_id"]].get(
                                "assist", 0) + 1
                    else:
                        # Shot saved/blocked
                        if random.random() < 0.5:
                            # GK save
                            goalkeeper = next((p for p in defending_players if p.get("position") == "GK"), None)
                            if goalkeeper:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=goalkeeper["player_id"],
                                    team_id=defending_team_id,
                                    action_id=8,  # GK save
                                    description=f"Goalkeeper {goalkeeper['player_id']} saved a shot from {attacker['player_id']} in {period_name}"
                                )
                                player_performances[goalkeeper["player_id"]]["defense_action"] = player_performances[
                                                                                                     goalkeeper[
                                                                                                         "player_id"]].get(
                                    "defense_action", 0) + 1
                        else:
                            # Defender block
                            defender = self._choose_defender_for_block(defending_players, defense_zone,
                                                                       defending_formation)
                            if defender:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=defender["player_id"],
                                    team_id=defending_team_id,
                                    action_id=7,  # Blocked shot
                                    description=f"Player {defender['player_id']} blocked a shot from {attacker['player_id']} in {period_name}"
                                )
                                player_performances[defender["player_id"]]["defense_action"] = player_performances[
                                                                                                   defender[
                                                                                                       "player_id"]].get(
                                    "defense_action", 0) + 1

        # Generate player stories for this period
        player_stories = []
        for player_id, perf in player_performances.items():
            team_won = (perf["player_team_id"] == team1_id and team1_score > team2_score) or \
                       (perf["player_team_id"] == team2_id and team2_score > team1_score)

            team_score = team1_score if perf["player_team_id"] == team1_id else team2_score
            opponent_score = team2_score if perf["player_team_id"] == team1_id else team1_score

            # Extra time attribute updates (smaller changes due to shorter period)
            attribute_updates = {}
            if random.random() < 0.3:  # Only 30% chance of attribute changes in extra time
                attr_keys = list(perf.get("player_properties", {}).keys())
                if attr_keys:
                    random_attr = random.choice(attr_keys)
                    update_value = 0.005 if team_won else 0.003
                    attribute_updates[random_attr] = update_value

            # Calculate extra time player score (lower baseline due to fatigue)
            baseline_score = random.uniform(2.0, 3.0) * fatigue_factor

            # Adjust based on performance
            baseline_score += 0.4 * perf.get("scored_goal", 0)
            baseline_score += 0.2 * perf.get("assist", 0)
            baseline_score += 0.2 * perf.get("defense_action", 0)

            if team_won:
                baseline_score += 0.3

            if perf.get("punished", False):
                baseline_score -= 0.3

            # Calculate freshness drop for extra time (more severe)
            endurance = perf.get("player_properties", {}).get("Endurance", 50)
            freshness_delta = -(35 - (endurance / 4)) * (15 / 90) * (1.5 if not is_first_extra_time else 1.3)

            # Round score to nearest 0.5
            overall_score = max(0, min(5, round(baseline_score * 2) / 2))

            player_stories.append({
                "player_id": player_id,
                "player_data": perf["player_data"],
                "player_team_id": perf["team_id"],
                "player_properties": perf["player_properties"],
                "player_position": perf["player_position"]})

import random
import json
from collections import defaultdict


class SoccerAttackOpportunitySystem:
    """
    Implementation of the Soccer Attack Opportunity Probability System as defined in the PRD.
    This system calculates the likelihood of creating dangerous attacking opportunities
    based on player positions, attributes, and field zones.
    """

    # Zone definitions based on the PRD
    ZONES = {
        1: "Left attacking",
        2: "Middle attacking",
        3: "Right attacking",
        4: "Right defensive",
        5: "Middle defensive",
        6: "Left defensive"
    }

    # Position types
    POSITIONS = [
        "GK", "Centre-back", "Full Back", "Wing Back",
        "Central Midfielder", "Wide Midfielder", "Winger",
        "Striker", "Forward"
    ]

    # Map position to simplified position for attribute weighting
    POSITION_MAPPING = {
        "GK": "GK",
        "Centre-back": "Center Back",
        "Full Back": "Full Back",
        "Wing Back": "Full Back",
        "Central Midfielder": "Central Midfielder",
        "Wide Midfielder": "Central Midfielder",
        "Winger": "Winger",
        "Striker": "Center Forward",
        "Forward": "Forward"
    }

    # Supported formations
    FORMATIONS = ["3-4-3", "3-5-2", "4-2-4", "4-3-3", "4-4-2", "5-3-2"]

    def __init__(self, formation_weights=None, attribute_weights=None):
        """
        Initialize the system with position weights by zone and attribute weights by position.

        Args:
            formation_weights: Dictionary of formation weights by zone, defaults to values from PRD
            attribute_weights: Dictionary of attribute weights by position, defaults to values from PRD
        """
        # Load default weights from PRD if not provided
        self.formation_weights = formation_weights or self._load_formation_weights()
        self.attribute_weights = attribute_weights or self._load_attribute_weights()

    def _load_formation_weights(self):
        """Load formation zone weights from default values in the PRD"""
        # This would typically load from a JSON or database
        # For now, we'll include a simplified version based on the PRD

        weights = {}

        # Example for 4-3-3 formation, zone 1 (Left Attacking)
        weights["4-3-3"] = {
            1: {  # Left Attacking
                "Left Winger": 0.30,
                "Full Back": 0.25,
                "Central Midfielder": 0.20,
                "Striker": 0.15,
                "Centre-back": 0.09,
                "GK": 0.01
            },
            2: {  # Middle Attacking
                "Central Midfielder": 0.35,
                "Striker": 0.27,
                "Left Winger": 0.15,
                "Right Winger": 0.15,
                "Wide Midfielder": 0.07,
                "GK": 0.01
            },
            3: {  # Right Attacking
                "Right Winger": 0.30,
                "Full Back": 0.25,
                "Central Midfielder": 0.20,
                "Striker": 0.15,
                "Centre-back": 0.09,
                "GK": 0.01
            },
            4: {  # Right Defensive
                "Centre-back": 0.35,
                "Full Back": 0.30,
                "Central Midfielder": 0.15,
                "GK": 0.10,
                "Winger": 0.10
            },
            5: {  # Middle Defensive
                "Centre-back": 0.60,  # Combining left and right CB
                "GK": 0.25,
                "Central Midfielder": 0.15
            },
            6: {  # Left Defensive
                "Centre-back": 0.35,
                "Full Back": 0.30,
                "Central Midfielder": 0.15,
                "GK": 0.10,
                "Winger": 0.10
            }
        }

        # Simplified versions for other formations
        for formation in ["3-4-3", "3-5-2", "4-2-4", "4-4-2", "5-3-2"]:
            weights[formation] = weights["4-3-3"].copy()

        return weights

    def _load_attribute_weights(self):
        """Load attribute weights by position from default values in the PRD"""
        # This would typically load from a JSON or database
        # For now, we'll include the values from the PRD

        return {
            "GK": {
                "Game_vision": 0.50,
                "GK_Kicking": 0.30,
                "Pass_Precision": 0.20
            },
            "Center Back": {
                "Pass_Precision": 0.40,
                "Game_vision": 0.30,
                "Heading": 0.15,
                "Physicality": 0.15
            },
            "Full Back": {
                "Speed": 0.25,
                "Pass_Precision": 0.25,
                "Dribble": 0.25,
                "Game_vision": 0.15,
                "Endurance": 0.10
            },
            "Central Midfielder": {
                "Game_vision": 0.35,
                "Pass_Precision": 0.35,
                "Dribble": 0.15,
                "Speed": 0.10,
                "Physicality": 0.05
            },
            "Winger": {
                "Dribble": 0.35,
                "Speed": 0.30,
                "Pass_Precision": 0.20,
                "Game_vision": 0.15
            },
            "Center Forward": {
                "Game_vision": 0.25,
                "Dribble": 0.25,
                "Speed": 0.20,
                "Pass_Precision": 0.15,
                "Physicality": 0.10,
                "Heading": 0.05
            },
            "Forward": {
                "Dribble": 0.30,
                "Speed": 0.25,
                "Game_vision": 0.20,
                "Pass_Precision": 0.20,
                "Physicality": 0.05
            }
        }

    def calculate_zone_attack_opportunity(self, players, formation, zone):
        """
        Calculate the attack opportunity probability for a specific zone.

        Args:
            players: List of player objects with position and attributes
            formation: Team formation (e.g., "4-3-3")
            zone: Zone number (1-6)

        Returns:
            Zone attack opportunity score (0-100)
        """
        if formation not in self.formation_weights:
            # Default to 4-3-3 if formation not found
            formation = "4-3-3"

        zone_weights = self.formation_weights[formation].get(zone, {})

        total_opportunity = 0

        for player in players:
            position = player.get("position")
            # Skip if player position is not in weights for this zone
            if position not in zone_weights:
                continue

            # Get position weight for this zone
            position_weight = zone_weights[position]

            # Calculate player attack rating based on attributes
            player_attack_rating = self.calculate_player_attack_rating(player)

            # Add to total opportunity
            total_opportunity += position_weight * player_attack_rating

        # Scale to 0-100 range for easier interpretation
        return total_opportunity * 100

    def calculate_player_attack_rating(self, player):
        """
        Calculate a player's attack contribution rating based on their position and attributes.

        Args:
            player: Player object with position and attributes

        Returns:
            Player attack rating (0-1 scale)
        """
        position = player.get("position")
        attributes = player.get("properties", {})

        # Map position to simplified position for attribute weighting
        mapped_position = self.POSITION_MAPPING.get(position, "Central Midfielder")

        # Get attribute weights for this position
        attribute_weights = self.attribute_weights.get(mapped_position, {})

        # Calculate weighted attribute score
        total_score = 0
        total_weight = 0

        for attr, weight in attribute_weights.items():
            # Get attribute value (default to 50 if not found)
            attr_value = attributes.get(attr, 50)
            total_score += attr_value * weight
            total_weight += weight

        # Normalize result to 0-1 scale
        if total_weight > 0:
            return total_score / (total_weight * 100)
        else:
            return 0.5  # Default to average if no weights

    def get_attack_danger_distribution(self, attack_zone_rating, defense_zone_rating):
        """
        Calculate the probability distribution for attack danger levels.

        Args:
            attack_zone_rating: Rating of the attacking zone (0-100)
            defense_zone_rating: Rating of the defending zone (0-100)

        Returns:
            Dictionary of probabilities for each danger level (1-5)
        """
        # Baseline distribution from PRD
        baseline = {
            1: 0.55,  # Least dangerous
            2: 0.20,
            3: 0.15,
            4: 0.07,
            5: 0.03  # Most dangerous
        }

        # Calculate attack advantage percentage
        scale_factor = 50  # Scaling factor to convert rating difference to percentage
        attack_advantage = (attack_zone_rating - defense_zone_rating) / scale_factor

        # Adjust distribution based on advantage
        adjusted = {}

        # If advantage is positive, increase higher danger levels
        # If negative, increase lower danger levels
        if attack_advantage > 0:
            # Reduce levels 1-2, increase levels 3-5
            adjustment = min(attack_advantage, 0.25)  # Cap the maximum adjustment

            adjusted[1] = max(0.30, baseline[1] - adjustment * 0.9)
            adjusted[2] = max(0.15, baseline[2] - adjustment * 0.3)
            adjusted[3] = min(0.25, baseline[3] + adjustment * 0.5)
            adjusted[4] = min(0.15, baseline[4] + adjustment * 0.3)
            adjusted[5] = min(0.15, baseline[5] + adjustment * 0.4)
        else:
            # Increase levels 1-2, reduce levels 3-5
            adjustment = min(abs(attack_advantage), 0.25)  # Cap the maximum adjustment

            adjusted[1] = min(0.75, baseline[1] + adjustment * 0.9)
            adjusted[2] = min(0.25, baseline[2] + adjustment * 0.3)
            adjusted[3] = max(0.05, baseline[3] - adjustment * 0.5)
            adjusted[4] = max(0.02, baseline[4] - adjustment * 0.3)
            adjusted[5] = max(0.01, baseline[5] - adjustment * 0.4)

        # Normalize to ensure probabilities sum to 1
        total = sum(adjusted.values())
        return {k: v / total for k, v in adjusted.items()}


class MatchSimulator:
    """
    Enhanced football match simulator that integrates the Soccer Attack Opportunity System
    and player action assignments.
    """

    def __init__(self):
        """Initialize the match simulator with the attack opportunity system"""
        self.attack_system = SoccerAttackOpportunitySystem()
        self.event_logger = pg.EventLogger()

    def simulate_football_match(self, match_id):
        """
        Simulate a football match between two teams.

        Args:
            team1: First team data (with players, formation, etc.)
            team2: Second team data

        Returns:
            Tuple of (team1_score, team2_score, match_events, player_performances)
        """
        # Initialize match data
        team1_score = 0
        team2_score = 0
        match_events = []
        match_details = db.get_match_details(match_id)
        team1_id = match_details["home_team_details"]["team_id"]
        team2_id = match_details["away_team_details"]["team_id"]

        # Get team formations
        team1_formation_name = match_details["home_team_details"]["formation_name"]
        team2_formation_name = match_details["away_team_details"]["formation_name"]

        # Get players
        team1_players = match_details["home_team_details"]["players"]
        team2_players = match_details["away_team_details"]["players"]

        # Track player performance
        player_performances = self._initialize_player_performances(team1_players, team2_players)

        # Calculate attacking zone ratings for each team
        team1_zone_ratings = self._calculate_team_zone_ratings(team1_players, team1_formation)
        team2_zone_ratings = self._calculate_team_zone_ratings(team2_players, team2_formation)

        # Total number of attacks in a match
        total_attacks = 200

        # Attacking zone pairs (attacking zone vs defending zone)
        zone_pairs = [
            (1, 4),  # Left attack vs Right defense
            (2, 5),  # Middle attack vs Middle defense
            (3, 6)  # Right attack vs Left defense
        ]

        # Calculate overall midfield strength (affects possession)
        team1_midfield = self._calculate_midfield_strength(team1_players)
        team2_midfield = self._calculate_midfield_strength(team2_players)

        # Calculate possession based on midfield strength
        total_midfield = team1_midfield + team2_midfield
        team1_possession = team1_midfield / total_midfield if total_midfield > 0 else 0.5

        # Simulate attacks
        for attack_num in range(total_attacks):
            # Determine attacking team based on possession
            if random.random() < team1_possession:
                attacking_team_id = team1_id
                defending_team_id = team2_id
                attacking_players = team1_players
                defending_players = team2_players
                attacking_formation = team1_formation
                defending_formation = team2_formation
                attacking_zone_ratings = team1_zone_ratings
                defending_zone_ratings = team2_zone_ratings
            else:
                attacking_team_id = team2_id
                defending_team_id = team1_id
                attacking_players = team2_players
                defending_players = team1_players
                attacking_formation = team2_formation
                defending_formation = team1_formation
                attacking_zone_ratings = team2_zone_ratings
                defending_zone_ratings = team1_zone_ratings

            # Choose attacking zone
            attack_zone_chances = {
                1: attacking_zone_ratings[1] / sum(attacking_zone_ratings.values()),
                2: attacking_zone_ratings[2] / sum(attacking_zone_ratings.values()),
                3: attacking_zone_ratings[3] / sum(attacking_zone_ratings.values())
            }

            attack_zone = self._weighted_choice(attack_zone_chances)

            # Get corresponding defense zone
            defense_zone = zone_pairs[attack_zone - 1][1]

            # Get zone ratings
            attack_rating = attacking_zone_ratings[attack_zone]
            defense_rating = defending_zone_ratings[defense_zone]

            # Get danger level distribution
            danger_distribution = self.attack_system.get_attack_danger_distribution(
                attack_rating, defense_rating
            )

            # Choose danger level based on distribution
            danger_level = self._weighted_choice(danger_distribution)

            # For higher danger levels, determine if a goal was scored
            if danger_level >= 4:
                # Generate random minute for the attack (1-90)
                minute = random.randint(1, 90)
                second = random.randint(0, 59)

                # Choose attacking player based on position weights for that zone
                attacker = self._choose_player_for_attack(attacking_players, attack_zone, attacking_formation)

                if attacker:
                    # Log shot attempt
                    self.event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=attacker["player_id"],
                        team_id=attacking_team_id,
                        action_id=6,  # Shot attempt
                        description=f"Player {attacker['player_id']} attempted a shot"
                    )

                    # Update player performance
                    player_performances[attacker["player_id"]]["shots"] = player_performances[
                                                                              attacker["player_id"]].get("shots", 0) + 1

                    # Danger level 5 has higher goal probability
                    goal_probability = 0.30 if danger_level == 5 else 0.10

                    # Calculate if goal is scored
                    if random.random() < goal_probability:
                        # Goal scored!
                        if attacking_team_id == team1_id:
                            team1_score += 1
                        else:
                            team2_score += 1

                        # Identify possible assister (20% of goals have assists)
                        if random.random() < 0.60:
                            assister = self._choose_player_for_assist(attacking_players, attack_zone,
                                                                      attacking_formation,
                                                                      exclude_id=attacker["player_id"])
                        else:
                            assister = None

                        # Log goal event
                        self._log_goal_with_assist(minute, second, attacker, assister, attacking_team_id)

                        # Update player performances
                        player_performances[attacker["player_id"]]["scored_goal"] = player_performances[
                                                                                        attacker["player_id"]].get(
                            "scored_goal", 0) + 1

                        if assister:
                            player_performances[assister["player_id"]]["assist"] = player_performances[
                                                                                       assister["player_id"]].get(
                                "assist", 0) + 1
                    else:
                        # Shot saved/blocked
                        if random.random() < 0.5:
                            # GK save
                            goalkeeper = next((p for p in defending_players if p.get("position") == "GK"), None)
                            if goalkeeper:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=goalkeeper["player_id"],
                                    team_id=defending_team_id,
                                    action_id=8,  # GK save
                                    description=f"Goalkeeper {goalkeeper['player_id']} saved a shot from {attacker['player_id']}"
                                )
                                player_performances[goalkeeper["player_id"]]["defense_action"] = player_performances[
                                                                                                     goalkeeper[
                                                                                                         "player_id"]].get(
                                    "defense_action", 0) + 1
                        else:
                            # Defender block
                            defender = self._choose_defender_for_block(defending_players, defense_zone,
                                                                       defending_formation)
                            if defender:
                                self.event_logger.log_event(
                                    minute=minute,
                                    second=second,
                                    token=defender["player_id"],
                                    team_id=defending_team_id,
                                    action_id=7,  # Blocked shot
                                    description=f"Player {defender['player_id']} blocked a shot from {attacker['player_id']}"
                                )
                                player_performances[defender["player_id"]]["defense_action"] = player_performances[
                                                                                                   defender[
                                                                                                       "player_id"]].get(
                                    "defense_action", 0) + 1

        # Calculate player ratings
        player_stories = self._generate_player_stories(player_performances, team1_id, team2_id, team1_score,
                                                       team2_score)

        # Calculate man of the match
        man_of_the_match = self._calculate_man_of_the_match(player_stories)

        # Calculate satisfaction changes
        self._calculate_satisfaction_changes(player_stories, team1_score, team2_score, man_of_the_match)

        # Return match results and events
        return {
            "result": {"team1_score": team1_score, "team2_score": team2_score},
            "time_played_mins": 90,
            "player_stories": player_stories,
            "man_of_the_match": man_of_the_match,
            "events": self.event_logger.get_events()
        }

    def _initialize_player_performances(self, team1_players, team1_formation, team2_players, team2_formation):
        """Initialize performance tracking for all players"""
        for player in team1_players + team2_players:
            performances[player["player_id"]] = {
                "player_id": player["player_id"],
                "player_data": player.get("name", "Player " + str(player["player_id"])),
                "player_team_id": player.get("team_id", "unknown"),
                "player_properties": db.get_player_by_token(player["player_id"]).get("properties", {}),
                "player_position": extract_player_position(team1_players, team1_formation, team2_players, team2_formation),
                "scored_goal": 0,
                "assist": 0,
                "defense_action": 0,
                "shots": 0,
                "punished": False,
                "injured": False
            }

            for i, row in enumerate(team1_formation):
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

        return performances

    def _calculate_team_zone_ratings(self, players, formation):
        """Calculate attack opportunity ratings for each zone"""
        ratings = {}

        # Calculate for attacking zones (1-3)
        for zone in [1, 2, 3]:
            ratings[zone] = self.attack_system.calculate_zone_attack_opportunity(players, formation, zone)

        # Calculate for defensive zones (4-6)
        for zone in [4, 5, 6]:
            ratings[zone] = self.attack_system.calculate_zone_attack_opportunity(players, formation, zone)

        return ratings

    def _calculate_midfield_strength(self, players):
        """Calculate overall midfield strength based on midfielders' attributes"""
        midfield_strength = 0
        midfielder_count = 0

        for player in players:
            position = player.get("position", "")
            if "Midfielder" in position or position in ["Central Midfielder", "Wide Midfielder"]:
                # Get key midfielder attributes
                attributes = player.get("properties", {})

                # Calculate weighted score based on key midfield attributes
                attribute_score = (
                        attributes.get("Game_vision", 50) * 0.4 +
                        attributes.get("Pass_Precision", 50) * 0.3 +
                        attributes.get("Dribble", 50) * 0.2 +
                        attributes.get("Endurance", 50) * 0.1
                )

                midfield_strength += attribute_score
                midfielder_count += 1

        # Return average midfield strength, defaulting to 50 if no midfielders
        return midfield_strength / midfielder_count if midfielder_count > 0 else 50

    def _weighted_choice(self, choices):
        """Choose a random item based on weights"""
        total = sum(choices.values())
        r = random.uniform(0, total)
        upto = 0

        for choice, weight in choices.items():
            upto += weight
            if upto > r:
                return choice

        # Fallback to first choice if something goes wrong
        return list(choices.keys())[0]

    def _choose_player_for_attack(self, players, attack_zone, formation):
        """Choose a player to lead an attack based on zone weights"""
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(attack_zone, {})

        # Filter players by position and create weighted selection
        candidates = []

        for player in players:
            position = player.get("position")
            if position in zone_weights:
                # Add player to candidates with weight based on position and attributes
                position_weight = zone_weights[position]

                # Get attack rating
                attack_rating = self.attack_system.calculate_player_attack_rating(player)

                # Final weight is position weight * attack rating
                weight = position_weight * attack_rating

                candidates.append((player, weight))

        # Return random player weighted by contribution
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return random player
        return random.choice(players) if players else None

    def _choose_player_for_assist(self, players, attack_zone, formation, exclude_id=None):
        """
        Choose a player to provide an assist based on performance metrics,
        position relevance to the zone, and actual passing attributes.
        """
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(attack_zone, {})

        # Filter players for assist
        candidates = []

        for player in players:
            # Exclude goal scorer
            if exclude_id and player.get("player_id") == exclude_id:
                continue

            position = player.get("position")

            # Only consider players in appropriate positions for assists
            if position in ["Striker", "Forward", "Winger", "Wide Midfielder", "Central Midfielder"]:
                # Base weight from zone contribution
                position_weight = zone_weights.get(position, 0.05)

                # Get key attributes for assists
                attributes = player.get("properties", {})
                pass_precision = attributes.get("Pass_Precision", 50) / 100
                game_vision = attributes.get("Game_vision", 50) / 100
                dribble = attributes.get("Dribble", 50) / 100
                speed = attributes.get("Speed", 50) / 100

                # Calculate passing ability score (weighted combination of relevant attributes)
                passing_ability = (
                        pass_precision * 0.40 +  # Precision is most important
                        game_vision * 0.35 +  # Vision is critical for assists
                        dribble * 0.15 +  # Ability to beat opponents before passing
                        speed * 0.10  # Speed to get into assist positions
                )

                # Calculate position-specific bonus based on the attacking zone
                position_zone_bonus = 1.0

                # Left-sided players have advantage in left attack zone
                if attack_zone == 1 and position in ["Wide Midfielder", "Winger"] and "Left" in player.get(
                        "position_detail", ""):
                    position_zone_bonus = 1.5
                # Right-sided players have advantage in right attack zone
                elif attack_zone == 3 and position in ["Wide Midfielder", "Winger"] and "Right" in player.get(
                        "position_detail", ""):
                    position_zone_bonus = 1.5
                # Central players have advantage in central attack zone
                elif attack_zone == 2 and position in ["Central Midfielder", "Striker"]:
                    position_zone_bonus = 1.3

                # Final weight calculation
                final_weight = position_weight * passing_ability * position_zone_bonus

                # Add player with calculated weight
                candidates.append((player, final_weight))

        # Return weighted random selection
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            if total_weight <= 0:
                return None

            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return None
        return None

    def _choose_defender_for_block(self, players, defense_zone, formation):
        """Choose a defensive player to block a shot"""
        zone_weights = self.attack_system.formation_weights.get(formation, {}).get(defense_zone, {})

        # Filter players for defensive actions
        candidates = []

        for player in players:
            position = player.get("position")

            # Prefer defenders and defensive midfielders
            if position in ["Centre-back", "Full Back", "Wing Back", "Central Midfielder"]:
                # Add player to candidates with weight
                weight = zone_weights.get(position, 0.05)

                # Increase weight for players with good defensive attributes
                attributes = player.get("properties", {})
                physicality = attributes.get("Physicality", 50) / 100

                # Final weight is position weight * defensive ability
                weight = weight * physicality

                candidates.append((player, weight))

        # Return random player weighted by contribution
        if candidates:
            total_weight = sum(weight for _, weight in candidates)
            if total_weight <= 0:
                return random.choice(players) if players else None

            r = random.uniform(0, total_weight)

            upto = 0
            for player, weight in candidates:
                upto += weight
                if upto > r:
                    return player

            # Fallback to first player
            return candidates[0][0]

        # If no suitable candidates, return random player
        return random.choice(players) if players else None

    def _log_goal_with_assist(self, goal_minute, goal_second, scorer, assister=None, team_id=None):
        """
        Log goal and assist events with realistic timing and descriptions based on player attributes.

        This improved version creates more realistic event descriptions based on:
        1. Player positions and attributes
        2. Timing characteristics of different types of goals/assists
        3. Dynamic event descriptions based on scenario
        """
        goal_description = ""
        assist_description = ""

        # Generate descriptive goal event based on scorer's attributes and position
        if scorer:
            position = scorer.get("position", "")
            attributes = scorer.get("properties", {})

            # Different types of goal descriptions based on player position and attributes
            if position in ["Striker", "Forward"]:
                if attributes.get("Shooting", 50) > 70:
                    goal_types = [
                        f"unleashed a powerful shot into the net",
                        f"finished clinically from inside the box",
                        f"beat the goalkeeper with a precise finish"
                    ]
                else:
                    goal_types = [
                        f"managed to put the ball in the net",
                        f"scored from close range",
                        f"found the back of the net"
                    ]
            elif position in ["Winger", "Wide Midfielder"]:
                if attributes.get("Dribble", 50) > 70:
                    goal_types = [
                        f"cut inside and fired into the far corner",
                        f"dribbled past defenders to score",
                        f"scored after a brilliant solo run"
                    ]
                else:
                    goal_types = [
                        f"found space to shoot and scored",
                        f"took a chance from the wing and scored",
                        f"got on the scoresheet"
                    ]
            elif position in ["Central Midfielder"]:
                goal_types = [
                    f"scored from outside the box",
                    f"found the net with a well-placed shot",
                    f"capitalized on the opportunity to score"
                ]
            else:
                goal_types = [
                    f"scored a goal",
                    f"found the back of the net",
                    f"got on the scoresheet"
                ]

            goal_description = f"Player {scorer['player_id']} {random.choice(goal_types)}"

        # Generate assist description based on assister's position and attributes
        if assister and assister['player_id'] != scorer['player_id']:
            position = assister.get("position", "")
            attributes = assister.get("properties", {})

            # Different types of assist descriptions based on player position and attributes
            if position in ["Winger", "Wide Midfielder"]:
                if attributes.get("Pass_Precision", 50) > 70:
                    assist_types = [
                        f"delivered a perfect cross",
                        f"whipped in a dangerous ball",
                        f"found space on the wing and crossed"
                    ]
                else:
                    assist_types = [
                        f"sent in a cross",
                        f"put the ball into the box",
                        f"delivered a cross"
                    ]
            elif position in ["Central Midfielder"]:
                if attributes.get("Game_vision", 50) > 70:
                    assist_types = [
                        f"played a defense-splitting pass",
                        f"threaded a brilliant through ball",
                        f"spotted the run and delivered a perfect pass"
                    ]
                else:
                    assist_types = [
                        f"found a teammate with a pass",
                        f"played it forward",
                        f"provided the pass"
                    ]
            elif position in ["Striker", "Forward"]:
                assist_types = [
                    f"laid it off",
                    f"headed it down",
                    f"flicked the ball on"
                ]
            else:
                assist_types = [
                    f"provided the assist",
                    f"set up the goal",
                    f"created the chance"
                ]

            assist_description = f"Player {assister['player_id']} {random.choice(assist_types)} for Player {scorer['player_id']}"

            # Timing: assist happens a few seconds before the goal
            assist_minute = goal_minute
            assist_second = goal_second - random.randint(2, 6)

            # Handle the case where assist_second becomes negative
            if assist_second < 0:
                assist_minute = max(1, goal_minute - 1)
                assist_second = 60 + assist_second

            # Log the assist event
            self.event_logger.log_event(
                minute=assist_minute,
                second=assist_second,
                token=assister['player_id'],
                team_id=team_id,
                action_id=2,  # Assist
                description=assist_description
            )

        # Add assist information to goal description if available
        if assister and assister['player_id'] != scorer['player_id']:
            goal_description += f" from {assister['player_id']}'s assist"

        # Log the goal event
        self.event_logger.log_event(
            minute=goal_minute,
            second=goal_second,
            token=scorer['player_id'],
            team_id=team_id,
            action_id=1,  # Goal
            description=goal_description
        )

    def _generate_player_stories(self, player_performances, team1_id, team2_id, team1_score, team2_score):
        """Generate player stories from performance data"""
        player_stories = []

        for player_id, performance in player_performances.items():
            team_won = (performance["player_team_id"] == team1_id and team1_score > team2_score) or \
                       (performance["player_team_id"] == team2_id and team2_score > team1_score)

            team_score = team1_score if performance["player_team_id"] == team1_id else team2_score
            opponent_score = team2_score if performance["player_team_id"] == team1_id else team1_score

            # Calculate overall score
            overall_score = self._calculate_player_score(
                performance,
                team_score,
                opponent_score,
                team_won
            )

            # Random attribute updates
            attribute_updates = self._random_attribute_updates(performance, team_won)

            # Calculate freshness drop
            freshness_delta = -self._calculate_freshness_drop(
                performance.get("player_properties", {}).get("Endurance", 50)
            )

            player_stories.append({
                "player_id": player_id,
                "player_data": performance["player_data"],
                "player_team_id": performance["player_team_id"],
                "player_properties": performance["player_properties"],
                "player_position": performance["player_position"],
                "performance": {
                    "overall_score": overall_score,
                    "team_won": team_won,
                    "scored_goal": performance.get("scored_goal", 0),
                    "assist": performance.get("assist", 0),
                    "defense_action": performance.get("defense_action", 0),
                    "injured": performance.get("injured", False),
                    "punished": performance.get("punished", False),
                    "attribute_deltas": attribute_updates,
                    "freshness_delta": freshness_delta,
                }})