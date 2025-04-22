import json
import random
import formation_grader
from Helpers import SQL_db as db


def round_up_to_half(score):
    return round((score * 2 + 1) // 1) / 2

def calc_man_of_the_match(results):
    man_of_the_match = ''
    highest_score = 0
    for player_result in results:
        player_score = 0
        player_id = player_result["player_id"]
        if (player_result['performance']["team_won"]):
            player_score += 100

        player_score += player_result["performance"]['overall_score'] * 50 + 5 * player_result["performance"]["scored_goal"] +  3 * player_result["performance"]["assist"] + 3 * player_result["performance"]["defense_action"]

        if (player_score > highest_score):
            highest_score = player_score
            man_of_the_match = player_id

    return man_of_the_match

class EventLogger:
    def __init__(self):
        self.events = []

    def log_event(self, minute, second, token, team_id, action_id, description):
        self.events.append({"minute": minute,
                            "second": second,
                            "description": description,
                            "token": token,
                            "team_id": team_id,
                            "action_timestamp": f"{minute:02}:{second:02}",
                            "action_id": action_id})

    def get_events(self):
        return sorted(self.events, key=lambda x: (x["minute"], x["second"]))


class SatisfactionCalculator:
    @staticmethod
    def calculate_satisfaction_changes(results, team1_score, team2_score, man_of_the_match):
        """
        Calculates the satisfaction change for each player based on playing time, match result, and personal performance.
        """
        satisfaction_changes = {}
        is_draw = team1_score == team2_score
        goal_difference = abs(team1_score - team2_score)

        for player_result in results:
            if (player_result['performance']["team_won"]):
                team_won = True
                team_lost = False
            else:
                team_won = False
                team_lost = True
            #player = player_result["player_data"]
            player_id = player_result["player_id"]
            minutes_played = 90#player_result.get("minutes_played", 0)
            satisfaction_change = 0

            # Playing Time Impact
            if minutes_played >= 72:  # 80% of 90 minutes
                satisfaction_change += 4
            elif 36 <= minutes_played < 72:  # 40%-79%
                satisfaction_change += 2
            elif 1 <= minutes_played < 36:  # 1%-39%
                satisfaction_change += 0
            elif minutes_played == 0:  # Did not play
                satisfaction_change -= 2

            # Match Result Impact
            if team_won:
                if minutes_played > 45:
                    satisfaction_change += 4
                else:
                    satisfaction_change += 2
            elif is_draw:
                if minutes_played > 45:
                    satisfaction_change += 2
            elif team_lost:
                if minutes_played > 45:
                    satisfaction_change -= 4
                else:
                    satisfaction_change -= 2

            # Special Adjustments: Win/Loss by 3+ goals
            if team_won and goal_difference >= 3:
                if minutes_played > 0:
                    satisfaction_change += 2
            elif team_lost and goal_difference >= 3:
                if minutes_played > 0:
                    satisfaction_change -= 2

            # Performance Impact
            if player_id == "man_of_the_match":
                satisfaction_change += 4
            if player_result["performance"].get("scored_goal", 0) > 0:
                satisfaction_change += 2 * player_result["performance"]["scored_goal"]
            if player_result["performance"].get("assist", 0) > 0:
                satisfaction_change += 2 * player_result["performance"]["assist"]
            #if player_result["performance"].get("punished", False):
            #    satisfaction_change -= 2
            #if player_result["performance"].get("conceded_penalty", False):
            #    satisfaction_change -= 2

            # Training and Improvement Impact
            if player_result["performance"].get("attribute_deltas", False):
                satisfaction_change += 4
            #todo: calculate stagnation...
            #if player_result["performance"].get("stagnation", False):
            #    satisfaction_change -= 2

            # Apply changes to player
            player_result['performance']["satisfaction_delta"] = satisfaction_change

    @staticmethod
    def satisfaction_change_for_non_players(non_players):
        non_players_satisfaction_change = 2
        for player in non_players:
            db.set_player_satisfaction(non_players_satisfaction_change, '-',player)


def calculate_player_score(player, player_story, team_score, opponent_score, team_won):
    baseline_score = random.uniform(2.5, 3.5)

    if team_won:
        baseline_score += 0.5

    if player["position"] in ["Centre-back", "GK"] and opponent_score <= 1:
        baseline_score += 0.5

    if player["position"] in ["Striker", "Forward", "Wide Midfielder", "Winger"] and team_score > 2:
        baseline_score += 0.5

    baseline_score += 0.4 * player_story.get("scored_goal", 0)
    baseline_score += 0.2 * player_story.get("assist", 0)
    baseline_score += 0.3 * player_story.get("defense_action", 0)

    if player_story.get("punished", False):
        baseline_score -= 0.3

    clamped_score = max(0, min(5, baseline_score))
    return round_up_to_half(clamped_score)


def calculate_event_bonus(player_story):
    event_bonus = 0
    event_bonus += 20 * player_story.get("scored_goal", 0)
    event_bonus += 10 * int(player_story.get("assist", False))
    event_bonus += 5 * player_story.get("defense_action", 0)
    event_bonus += -15 * int(player_story.get("punished", False))
    event_bonus += -10 if not player_story.get("scored_goal") and not player_story.get("assist") and not player_story.get("defense_action") else 0
    return event_bonus


def map_score_to_5_point_scale(overall_score):
    normalized_score = (overall_score - 30) / (80 - 30)
    scaled_score = normalized_score * 5
    return round(max(0.5, min(5, scaled_score)) * 2) / 2


class PostGameProcessor:
    def __init__(self, position_weights):
        self.position_weights = position_weights

    def get_team_formation(self, team_id):
        return db.get_team_default_formation(team_id)

    def fetch_player_data(self, formation):
        players = []
        formation_list = formation#ensure_list_of_lists(formation)
        for i, row in enumerate(formation_list):
            for j, player_id in enumerate(row):
                if player_id != "0" and (i, j) in formation_grader.POSITION_MAPPING:
                    position = formation_grader.POSITION_MAPPING[(i, j)]
                    player_data = db.get_player_by_token(player_id)
                    player_data['position'] = position
                    player_data['defense_action'] = 0
                    player_data['assist'] = 0
                    player_data['scored_goal'] = 0
                    player_data['properties'] = player_data.get('properties', {})
                    players.append(player_data)
        return players

    def assign_defense_actions(self, players, event_logger, time_period=(0, 90), fatigue_factor=1.0):
        """
        Assigns defensive actions such as blocks and goalkeeper saves,
        ensuring attackers and defenders are randomly assigned per attack event.

        :param players: List of all players (both teams).
        :param event_logger: Event logging object.
        :param time_period: Tuple indicating the (start, end) minute range for this period
        :param fatigue_factor: Multiplier to account for player fatigue (< 1.0 means more mistakes)
        """
        start_min, end_min = time_period

        # Group players by team
        team1 = [p for p in players if p["team_id"] == players[0]["team_id"]]
        team2 = [p for p in players if p["team_id"] != players[0]["team_id"]]

        position_weights_defense = {
            "GK": 0.9 * fatigue_factor,
            "Centre-back": 0.7 * fatigue_factor,
            "Wide Midfielder": 0.2 * fatigue_factor,
            "Winger": 0.1 * fatigue_factor
        }

        position_weights_attack = {
            "Striker": 0.4 * fatigue_factor,
            "Forward": 0.3 * fatigue_factor,
            "Winger": 0.15 * fatigue_factor,
            "Wide Midfielder": 0.1 * fatigue_factor,
            "Centre-back": 0.04 * fatigue_factor,
            "GK": 0.005 * fatigue_factor
        }

        defensive_actions = []

        # Calculate adjusted attack frequency for the time period
        period_length = end_min - start_min
        num_attacks = max(1, int(period_length / 90 * 6))  # Scale attacks proportional to period length

        attack_minutes = sorted(random.sample(range(start_min, end_min), num_attacks))

        for minute in attack_minutes:
            if random.random() < 0.25:  # 25% chance an attack event occurs
                # Randomly decide which team is attacking and which is defending for this attack
                if random.random() < 0.5:
                    attacking_team, defending_team = team1, team2
                else:
                    attacking_team, defending_team = team2, team1

                # Generate weighted lists for selection
                weighted_defenders = [
                    player for player in defending_team
                    for _ in range(int(position_weights_defense.get(player.get("position"), 0) * 100))
                ]

                weighted_attackers = [
                    player for player in attacking_team
                    for _ in range(int(position_weights_attack.get(player.get("position"), 0) * 100))
                ]

                # Ensure goalkeeper selection is correct
                goalkeeper = next((p for p in defending_team if p.get("position") == "GK"), None)

                if not weighted_attackers or not weighted_defenders:
                    continue  # Ensure valid players exist

                # Select attacker (from attacking team)
                attacker = random.choice(weighted_attackers)
                second = random.randint(0, 59)
                # Log shot event for attacker
                event_logger.log_event(
                    minute=minute,
                    second=second,
                    token=attacker["player_id"],
                    team_id=attacker["team_id"],
                    action_id=6,  # Shot attempt action
                    description=f"Player {attacker['player_id']} attempted a shot"
                )
                attacker["shots"] = attacker.get("shots", 0) + 1

                # With fatigue, GK saves are less likely in extra time
                if goalkeeper and random.random() < (0.4 * fatigue_factor):  # scaled by fatigue
                    event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=goalkeeper["player_id"],
                        team_id=goalkeeper["team_id"],
                        action_id=8,  # GK save action
                        description=f"Goalkeeper {goalkeeper['player_id']} saved a shot from {attacker['player_id']}"
                    )
                    goalkeeper["gk_saves"] = goalkeeper.get("gk_saves", 0) + 1
                    defensive_actions.append({
                        "player": goalkeeper,
                        "minute": minute,
                        "second": second,
                        "attacker": attacker
                    })
                else:
                    # Select a defender if GK didn't save
                    defender = random.choice(weighted_defenders)
                    event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=defender["player_id"],
                        team_id=defender["team_id"],
                        action_id=7,  # Blocked shot
                        description=f"Player {defender['player_id']} blocked a shot from {attacker['player_id']}"
                    )
                    defender["defense_action"] = defender.get("defense_action", 0) + 1
                    defensive_actions.append({
                        "player": defender,
                        "minute": minute,
                        "second": second,
                        "attacker": attacker
                    })

        return defensive_actions

    def assign_goals_and_assists(self, players, team_score, event_logger, time_period=(0, 90), fatigue_factor=1.0):
        """
        Assigns goals and assists to players based on their positions and the team's score.

        :param players: List of players in the team
        :param team_score: Number of goals to assign
        :param event_logger: Event logging object
        :param time_period: Tuple of (start_minute, end_minute) for this period
        :param fatigue_factor: Factor to account for player fatigue (< 1.0 means decreased performance)
        """
        start_min, end_min = time_period
        scorers = []

        if team_score > 0:
            # Apply fatigue factor to position weights
            position_weights = {
                "Striker": 0.4 * fatigue_factor,
                "Forward": 0.3 * fatigue_factor,
                "Winger": 0.15 * fatigue_factor,
                "Wide Midfielder": 0.1 * fatigue_factor,
                "Centre-back": 0.04 * fatigue_factor,
                "GK": 0.005 * fatigue_factor
            }

            weighted_players = []
            for player in players:
                weight = position_weights.get(player.get("position", "Wide Midfielder"), 0.1)
                weighted_players.extend([player] * int(weight * 100))

            for _ in range(team_score):
                scorer = random.choice(weighted_players)
                scorer['scored_goal'] += 1
                minute = random.randint(start_min, end_min)
                second = random.randint(0, 59)

                # In extra time, assists are less common due to fatigue
                assister = None
                if random.random() < (0.6 * fatigue_factor):
                    plausible_assisters = [
                        p for p in players
                        if p['player_id'] != scorer['player_id'] and p["position"] in ["Forward", "Winger",
                                                                                       "Wide Midfielder"] and p[
                               "position"] != "GK"
                    ]
                    if plausible_assisters:
                        assister = random.choice(plausible_assisters)
                        assister['assist'] += 1

                period_name = ""
                if minute > 90 and minute <= 105:
                    period_name = " (First Extra Time)"
                elif minute > 105:
                    period_name = " (Second Extra Time)"

                self.log_goal_with_assist(event_logger, minute, second, scorer, assister, period_name)
                scorers.append({"player": scorer, "minute": minute, "second": second, "assister": assister})

        return scorers

    def log_goal_with_assist(self, event_logger, goal_minute, goal_second, scorer, assister=None, period_suffix=""):
        if assister and assister['player_id'] != scorer['player_id']:
            # Assuming we know goal_minute and goal_second
            assist_minute = goal_minute
            assist_second = goal_second - random.randint(2, 6)

            # Handle the case where assist_second becomes negative
            if assist_second < 0:
                assist_minute = max(0, goal_minute - 1)  # Go to previous minute, but not below 1
                assist_second = 60 + assist_second  # Add to 60 (e.g., -3 becomes 57)

            event_logger.log_event(
                minute=assist_minute,
                second=assist_second,
                token=assister['player_id'],
                team_id=scorer['team_id'],
                action_id=2,
                description=f"Player {assister['player_id']} provided an assist for Player {scorer['player_id']}{period_suffix}"
            )

        event_logger.log_event(
            minute=goal_minute,
            second=goal_second,
            token=scorer['player_id'],
            team_id=scorer['team_id'],
            action_id=1,
            description=f"Player {scorer['player_id']} scored a goal{period_suffix}"
        )

    def calculate_freshness_drop(self, endurance, min_played=90, is_extra_time=False):
        """
        Calculate the drop in 'Freshness' based on the player's 'Endurance'.
        In extra time, fatigue increases more rapidly.

        :param endurance: Player's endurance attribute
        :param min_played: Minutes played
        :param is_extra_time: Whether this is during extra time (increased fatigue)
        """
        # Extra time fatigue penalty - fatigue increases faster after 90 minutes
        extra_time_factor = 1.5 if is_extra_time else 1.0

        return (35 - (endurance / 4)) * (min_played / 90) * extra_time_factor

    def random_attribute_updates(self, player, team_won, is_extra_time=False):
        """
        Generate random attribute updates for a player

        :param player: Player data dictionary
        :param team_won: Whether player's team won
        :param is_extra_time: Whether in extra time (affects update amount)
        """
        updates = {}
        total_updates = random.randint(1, 3) if team_won else random.randint(0, 2)

        # Extra time can provide more development opportunities
        if is_extra_time:
            # Extra time boosts attribute gains slightly
            update_value = 0.015 if team_won else 0.008
            # Players in extra time have chance for additional attribute update
            if random.random() < 0.3:  # 30% chance
                total_updates += 1
        else:
            update_value = 0.01 if team_won else 0.005

        attributes = list(player["properties"].keys())
        random.shuffle(attributes)
        for attr in attributes[:total_updates]:
            updates[attr] = update_value
        return updates

    def generate_player_stories(self, all_players):
        player_stories = []
        for player in all_players:
            player_stories.append({
                "player_id": player['player_id'],
                "scored_goal": player.get("scored_goal", 0),
                "assist": player.get("assist", 0),
                "defense_action": player.get("defense_action", 0),
                "injured": False,
                "punished": player.get("punished", False)
            })
        return player_stories

    def process_post_game(self, team1_id, team2_id, team1_score, team2_score):
        team1_formation = self.get_team_formation(team1_id)
        team2_formation = self.get_team_formation(team2_id)

        team1_total = db.get_team_players(team1_id)
        team2_total = db.get_team_players(team2_id)


        team1_players = self.fetch_player_data(team1_formation)
        team2_players = self.fetch_player_data(team2_formation)

        # Extract player IDs from the dictionary keys
        team1_total_keys = set(team1_total.keys())
        team2_total_keys = set(team2_total.keys())

        # Extract player IDs from the list
        team1_player_ids = set(player['player_id'] for player in team1_players)
        team2_player_ids = set(player['player_id'] for player in team2_players)

        # Find player IDs that are in the dictionary but not in the list
        team1_non_players = list(team1_total_keys - team1_player_ids)
        team2_non_players = list(team2_total_keys - team2_player_ids)

        non_players = team1_non_players + team2_non_players

        list(map(lambda x: x.update({'team_id': team1_id}), team1_players))
        list(map(lambda x: x.update({'team_id': team2_id}), team2_players))

        all_players = team1_players + team2_players
        event_logger = EventLogger()

        self.assign_defense_actions(all_players, event_logger)

        self.assign_goals_and_assists(
            [player for player in all_players if player['team_id'] == team1_id],
            team1_score,
            event_logger
        )
        self.assign_goals_and_assists(
            [player for player in all_players if player['team_id'] == team2_id],
            team2_score,
            event_logger
        )

        player_stories = self.generate_player_stories(all_players)

        results = []
        for player, story in zip(all_players, player_stories):
            team_won = (player in team1_players and team1_score > team2_score) or (
                    player in team2_players and team2_score > team1_score
            )

            attribute_updates = self.random_attribute_updates(player, team_won)

            results.append({
                "player_id": player["player_id"],
                "player_data": player["name"],
                "player_team_id": player["team_id"],
                "player_properties": player['properties'],
                "player_position": player['position'],
                "performance": {
                    "overall_score": calculate_player_score(
                        player, story,
                        team_score=team1_score if player in team1_players else team2_score,
                        opponent_score=team2_score if player in team1_players else team1_score,
                        team_won=team_won
                    ),
                    "team_won": team_won,
                    "scored_goal": story.get("scored_goal", 0),
                    "assist": story.get("assist", 0),
                    "defense_action": story.get("defense_action", 0),
                    "injured": story.get("injured", False),
                    "punished": story.get("punished", False),
                    "attribute_deltas": attribute_updates,
                    "freshness_delta": -self.calculate_freshness_drop(player['properties']['Endurance']),
                }
            })

        man_of_the_match = calc_man_of_the_match(results)
        SatisfactionCalculator.calculate_satisfaction_changes(results, team1_score, team2_score, man_of_the_match)

        SatisfactionCalculator.satisfaction_change_for_non_players(non_players)
        return {
            "result": {"team1_score": team1_score, "team2_score": team2_score},
            "time_played_mins": 90,
            "player_stories": results,
            "man_of_the_match": man_of_the_match,
            "events": event_logger.get_events()
        }

    def process_extra_time(self, team1_id, team2_id, all_players, prev_time_played, is_first_extra_time=True):
        """
        Process an extra time period (either 91-105 or 106-120 minutes).

        :param team1_id: ID of first team
        :param team2_id: ID of second team
        :param all_players: All players with updated stats from previous periods
        :param prev_time_played: Minutes already played (90 or 105)
        :param is_first_extra_time: Whether this is the first (True) or second (False) extra time
        :return: Tuple of (game_result, player_stories)
        """
        # Set time period
        if is_first_extra_time:
            period_start, period_end = prev_time_played, prev_time_played + 15  # 90-105
            period_name = "First Extra Time"
        else:
            period_start, period_end = prev_time_played, prev_time_played + 15  # 105-120
            period_name = "Second Extra Time"

        # Calculate fatigue factor - players are more tired now
        fatigue_factor = 0.8 if is_first_extra_time else 0.7

        # Group players by team
        team1_players = [p for p in all_players if p['team_id'] == team1_id]
        team2_players = [p for p in all_players if p['team_id'] == team2_id]

        event_logger = EventLogger()

        # Add period start event
        event_logger.log_event(
            minute=period_start,
            second=0,
            token="system",
            team_id=None,
            action_id=10,  # Special system event
            description=f"{period_name} begins"
        )

        # Simulate defensive actions with fatigue factor
        self.assign_defense_actions(
            all_players,
            event_logger,
            time_period=(period_start, period_end),
            fatigue_factor=fatigue_factor
        )

        # Generate goal probabilities - fewer goals in extra time due to caution
        # Teams play more defensively in extra time
        team1_goal_prob = random.random() * 0.6 * fatigue_factor  # Reduced scoring probability
        team2_goal_prob = random.random() * 0.6 * fatigue_factor

        team1_score = 1 if team1_goal_prob > 0.4 else 0
        team2_score = 1 if team2_goal_prob > 0.4 else 0

        # Assign goals and assists
        self.assign_goals_and_assists(
            team1_players,
            team1_score,
            event_logger,
            time_period=(period_start, period_end),
            fatigue_factor=fatigue_factor
        )

        self.assign_goals_and_assists(
            team2_players,
            team2_score,
            event_logger,
            time_period=(period_start, period_end),
            fatigue_factor=fatigue_factor
        )

        # Generate player stories for this period
        player_stories = self.generate_player_stories(all_players)

        results = []
        for player, story in zip(all_players, player_stories):
            team_won = (player['team_id'] == team1_id and team1_score > team2_score) or (
                    player['team_id'] == team2_id and team2_score > team1_score
            )

            # Extra time attribute updates
            attribute_updates = self.random_attribute_updates(player, team_won, is_extra_time=True)

            # Calculate increased fatigue for extra time
            extra_time_freshness_drop = -self.calculate_freshness_drop(
                player['properties']['Endurance'],
                min_played=15,  # Only playing 15 minutes, but with extra fatigue factor
                is_extra_time=True
            )

            results.append({
                "player_id": player["player_id"],
                "player_data": player["name"],
                "performance": {
                    "overall_score": calculate_player_score(
                        player, story,
                        team_score=team1_score if player['team_id'] == team1_id else team2_score,
                        opponent_score=team2_score if player['team_id'] == team1_id else team1_score,
                        team_won=team_won
                    ),
                    "scored_goal": story.get("scored_goal", 0),
                    "assist": story.get("assist", 0),
                    "defense_action": story.get("defense_action", 0),
                    "injured": story.get("injured", False),
                    "punished": story.get("punished", False),
                    "attribute_deltas": attribute_updates,
                    "freshness_delta": extra_time_freshness_drop,
                }
            })

        return {
            "result": {"team1_score": team1_score, "team2_score": team2_score},
            "time_played_mins": 15,  # Just this period
            "player_stories": results,
            "events": event_logger.get_events()
        }

    def simulate_penalty_shootout(self, team1_id, team2_id, all_players):
        """
        Simulate penalty shootout to decide the winner when the game remains tied
        after extra time.

        :param team1_id: ID of first team
        :param team2_id: ID of second team
        :param all_players: All players
        :return: Dictionary with penalty shootout results
        """
        # Group players by team
        team1_players = [p for p in all_players if p['team_id'] == team1_id]
        team2_players = [p for p in all_players if p['team_id'] == team2_id]

        # Find goalkeepers for each team
        team1_gk = next((p for p in team1_players if p.get("position") == "GK"), team1_players[0])
        team2_gk = next((p for p in team2_players if p.get("position") == "GK"), team2_players[0])

        # Define penalty takers based on positions and properties
        def select_penalty_takers(team_players):
            # Sort players by suitability for penalties
            sorted_players = sorted(
                team_players,
                key=lambda p: (
                    # Prefer strikers and forwards
                    -1 if p.get("position") in ["Striker", "Forward"] else 0,
                    # Use Shooting skill if available
                    p.get("properties", {}).get("Shooting", 50),
                    # Use Composure if available
                    p.get("properties", {}).get("Composure", 50)
                ),
                reverse=True
            )

            # Return top 5 players
            return sorted_players[:5]

        team1_takers = select_penalty_takers(team1_players)
        team2_takers = select_penalty_takers(team2_players)

        event_logger = EventLogger()

        # Log start of penalty shootout
        event_logger.log_event(
            minute=120,
            second=0,
            token="system",
            team_id=None,
            action_id=11,  # Special system event
            description="Penalty shootout begins"
        )

        # Function to simulate a penalty kick
        def simulate_penalty(taker, goalkeeper):
            # Base probability of scoring
            score_probability = 0.75

            # Adjust based on taker's shooting/composure if available
            if "properties" in taker:
                props = taker["properties"]
                shooting = props.get("Shooting", 50)
                composure = props.get("Composure", 50)
                score_probability += (shooting - 50) / 200  # +/- 0.125 maximum
                score_probability += (composure - 50) / 200  # +/- 0.125 maximum

            # Adjust based on goalkeeper abilities
            if "properties" in goalkeeper:
                reflexes = goalkeeper["properties"].get("Reflexes", 50)
                penalty_stopping = goalkeeper["properties"].get("Penalty Stopping", 50)
                score_probability -= (reflexes - 50) / 200  # +/- 0.125 maximum
                score_probability -= (penalty_stopping - 50) / 200  # +/- 0.125 maximum

            # Clamp probability
            score_probability = max(0.5, min(0.95, score_probability))

            # Determine outcome
            scored = random.random() < score_probability
            return scored

        # Perform the initial 5 rounds of penalties
        team1_score = 0
        team2_score = 0
        penalty_results = []

        # First 5 penalties per team
        for round_idx in range(5):
            # Team 1 penalty
            team1_taker = team1_takers[round_idx % team1_takers.__sizeof__()]
            team1_scored = simulate_penalty(team1_taker, team2_gk)
            if team1_scored:
                team1_score += 1

            event_logger.log_event(
                minute=120,
                second=round_idx * 2,
                token=team1_taker["player_id"],
                team_id=team1_id,
                action_id=12,  # Penalty kick
                description=f"Penalty by Player {team1_taker['player_id']}: {'SCORED' if team1_scored else 'MISSED'}"
            )

            penalty_results.append({
                "round": round_idx + 1,
                "team_id": team1_id,
                "player_id": team1_taker["player_id"],
                "scored": team1_scored
            })

            # Team 2 penalty
            team2_taker = team2_takers[round_idx % team2_takers.__sizeof__()]
            team2_scored = simulate_penalty(team2_taker, team1_gk)
            if team2_scored:
                team2_score += 1

            event_logger.log_event(
                minute=120,
                second=round_idx * 2 + 1,
                token=team2_taker["player_id"],
                team_id=team2_id,
                action_id=12,  # Penalty kick
                description=f"Penalty by Player {team2_taker['player_id']}: {'SCORED' if team2_scored else 'MISSED'}"
            )

            penalty_results.append({
                "round": round_idx + 1,
                "team_id": team2_id,
                "player_id": team2_taker["player_id"],
                "scored": team2_scored
            })

            # Early termination check (mathematical impossibility for other team to win)
            remaining_rounds = 5 - (round_idx + 1)
            if (team1_score > team2_score + remaining_rounds) or (team2_score > team1_score + remaining_rounds):
                break

        # If still tied, continue with sudden death
        if team1_score == team2_score:
            round_idx = 5
            sudden_death_takers1 = [p for p in team1_players if p not in team1_takers]
            sudden_death_takers2 = [p for p in team2_players if p not in team2_takers]

            # If we need more takers than available, start over from beginning
            if not sudden_death_takers1:
                sudden_death_takers1 = team1_players
            if not sudden_death_takers2:
                sudden_death_takers2 = team2_players

            # Keep going until someone wins
            while team1_score == team2_score:
                # Team 1 penalty
                team1_taker = sudden_death_takers1[round_idx % len(sudden_death_takers1)]
                team1_scored = simulate_penalty(team1_taker, team2_gk)
                if team1_scored:
                    team1_score += 1

                event_logger.log_event(
                    minute=120,
                    second=30 + round_idx,
                    token=team1_taker["player_id"],
                    team_id=team1_id,
                    action_id=12,  # Penalty kick
                    description=f"Sudden death penalty by Player {team1_taker['player_id']}: {'SCORED' if team1_scored else 'MISSED'}"
                )

                penalty_results.append({
                    "round": "SD" + str(round_idx - 4),
                    "team_id": team1_id,
                    "player_id": team1_taker["player_id"],
                    "scored": team1_scored
                })

                # Team 2 penalty
                team2_taker = sudden_death_takers2[round_idx % len(sudden_death_takers2)]
                team2_scored = simulate_penalty(team2_taker, team1_gk)
                if team2_scored:
                    team2_score += 1

                event_logger.log_event(
                    minute=120,
                    second=31 + round_idx,
                    token=team2_taker["player_id"],
                    team_id=team2_id,
                    action_id=12,  # Penalty kick
                    description=f"Sudden death penalty by Player {team2_taker['player_id']}: {'SCORED' if team2_scored else 'MISSED'}"
                )

                penalty_results.append({
                    "round": "SD" + str(round_idx - 4),
                    "team_id": team2_id,
                    "player_id": team2_taker["player_id"],
                    "scored": team2_scored
                })

                round_idx += 1

                # In sudden death, we check after each pair of penalties
                if team1_score != team2_score:
                    break

        # Determine winner and update players
        team1_won = team1_score > team2_score
        team2_won = team2_score > team1_score

        # Log final result
        event_logger.log_event(
            minute=120,
            second=59,
            token="system",
            team_id=None,
            action_id=13,  # Final result
            description=f"Penalty shootout result: Team {team1_id} {team1_score} - {team2_score} Team {team2_id}"
        )

        # Update player stories with penalty information
        penalty_takers = [result["player_id"] for result in penalty_results]
        penalty_scorers = [result["player_id"] for result in penalty_results if result["scored"]]

        player_stories = []
        for player in all_players:
            # Special bonuses for penalty takers
            took_penalty = player["player_id"] in penalty_takers
            scored_penalty = player["player_id"] in penalty_scorers
            team_won_shootout = (player['team_id'] == team1_id and team1_won) or (
                    player['team_id'] == team2_id and team2_won)

            # Boost or reduce composure based on penalty performance
            attribute_deltas = {}
            if took_penalty:
                if scored_penalty:
                    attribute_deltas["Composure"] = 0.02
                    if "Penalty Taking" in player.get("properties", {}):
                        attribute_deltas["Penalty Taking"] = 0.03
                else:
                    attribute_deltas["Composure"] = -0.01

            # Goalkeepers who saved penalties get boosts
            if player.get("position") == "GK":
                saves = sum(1 for result in penalty_results
                            if not result["scored"] and result["team_id"] != player['team_id'])
                if saves > 0:
                    attribute_deltas["Reflexes"] = 0.02
                    if "Penalty Stopping" in player.get("properties", {}):
                        attribute_deltas["Penalty Stopping"] = saves * 0.02

            player_stories.append({
                "player_id": player["player_id"],
                "player_data": player["name"],
                "performance": {
                    "overall_score": 3.0 + (0.5 if team_won_shootout else 0) +
                                     (0.5 if scored_penalty else 0) -
                                     (0.5 if took_penalty and not scored_penalty else 0),
                    "scored_goal": 0,
                    "assist": 0,
                    "defense_action": 0,
                    "penalty_taken": took_penalty,
                    "penalty_scored": scored_penalty,
                    "injured": False,
                    "punished": False,
                    "attribute_deltas": attribute_deltas,
                    "freshness_delta": -5.0  # Penalty shootouts are mentally draining
                }
            })

        return {
            "result": {
                "team1_score": team1_score,
                "team2_score": team2_score,
                "winner_id": team1_id if team1_score > team2_score else team2_id
            },
            "time_played_mins": 0,  # No additional match time
            "player_stories": player_stories,
            "events": event_logger.get_events(),
            "penalty_details": penalty_results
        }

    def process_must_win_game(self, team1_id, team2_id, team1_score=None, team2_score=None):
        """
        Process a "must win" game where there must be a winner.
        If tied after 90 minutes, the game goes to extra time.
        If still tied after extra time, goes to penalties.

        :param team1_id: ID of first team
        :param team2_id: ID of second team
        :param team1_score: Optional preset score for team1 (for testing)
        :param team2_score: Optional preset score for team2 (for testing)
        :return: Combined match result including all periods and possible shootout
        """
        # Step 1: Simulate regular 90 minute game
        regular_time = self.process_post_game(team1_id, team2_id,
                                              team1_score if team1_score is not None else random.randint(0, 3),
                                              team2_score if team2_score is not None else random.randint(0, 3))

        # Extract the scores
        t1_score = regular_time["result"]["team1_score"]
        t2_score = regular_time["result"]["team2_score"]

        # Check if the game is tied
        if t1_score == t2_score:
            # Add a message to the event log that the game is going to extra time
            regular_time["events"].append({
                "minute": 90,
                "second": 0,
                "description": "Regular time ended with a draw. Match proceeds to extra time.",
                "token": "system",
                "team_id": None,
                "action_timestamp": "90:00",
                "action_id": 9  # Special action ID for period transitions
            })

            # Get player data from regular time
            player_data = {}
            for player_story in regular_time["player_stories"]:
                pid = player_story["player_id"]
                player_data[pid] = {
                    "player_id": pid,
                    "name": player_story["player_data"],
                    "team_id": player_story["player_team_id"],
                    "properties": player_story['player_properties'],  # This would need to be populated from your database
                    "position": player_story['player_position'],  # This would need to be populated
                    "scored_goal": player_story['performance']['scored_goal'],
                    "assist": player_story['performance']['assist'],
                    "defense_action": player_story['performance']['defense_action']
                }

            # We need to get their properties back from the database
            # This is a placeholder - you would need to implement this
            for pid in player_data:
                db_player = db.get_player_by_token(pid)
                if db_player:
                    player_data[pid]["properties"] = db_player.get("properties", {})
                    player_data[pid]["position"] = db_player.get("position", "")

            all_players = list(player_data.values())

            # Step 2: Simulate first extra time (91-105)
            first_extra_time = self.process_extra_time(
                team1_id, team2_id, all_players, 90, is_first_extra_time=True
            )

            # Update scores
            t1_score += first_extra_time["result"]["team1_score"]
            t2_score += first_extra_time["result"]["team2_score"]

            # Merge the results
            combined_result = self.merge_partial_outputs(regular_time, first_extra_time)

            # Check if still tied after first extra time
            if t1_score == t2_score:
                # Step 3: Simulate second extra time (106-120)
                second_extra_time = self.process_extra_time(
                    team1_id, team2_id, all_players, 105, is_first_extra_time=False
                )

                # Update scores
                t1_score += second_extra_time["result"]["team1_score"]
                t2_score += second_extra_time["result"]["team2_score"]

                # Merge results again
                combined_result = self.merge_partial_outputs(combined_result, second_extra_time)

                # Check if still tied after second extra time
                if t1_score == t2_score:
                    # Step 4: Simulate penalty shootout
                    penalty_shootout = self.simulate_penalty_shootout(team1_id, team2_id, all_players)

                    # Merge penalty shootout results
                    # Note: Penalties don't add to the main scoreline but determine the winner
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

    def adapt_output_to_partial(self, full_output, team1_id, team2_id, min_start, min_end):
        """
        Helper method to filter events and rescale performance metrics based on
        only the portion of time [min_start, min_end].
        """
        import copy

        # Deep-copy so we do not modify the original result
        partial_output = copy.deepcopy(full_output)

        # Calculate partial duration
        partial_duration = min_end - min_start
        if partial_duration <= 0:
            # If the time window is invalid or zero-length, just return no events & zero stats
            partial_output["time_played_mins"] = 0
            partial_output["events"] = []
            partial_output["result"]["team1_score"] = 0
            partial_output["result"]["team2_score"] = 0
            partial_output["player_stories"] = []
            return partial_output

        # 1) Filter events to those within [min_start, min_end].
        all_events = full_output.get("events", [])
        partial_events = [
            e for e in all_events
            if min_start <= e.get("minute", 0) <= min_end
        ]

        partial_output["events"] = partial_events
        partial_output["time_played_mins"] = partial_duration

        # 2) Recompute scoreboard for this partial window (if desired).
        #    E.g. count how many "goal" events each team scored in that window.
        #    (Adjust logic if your event logger uses different type strings.)
        team1_partial_goals = sum(
            1 for e in partial_events
            if e.get("action_id") == 1 and e.get("team_id") == team1_id
        )
        team2_partial_goals = sum(
            1 for e in partial_events
            if e.get("action_id") == 1 and e.get("team_id") == team2_id
        )

        partial_output["result"]["team1_score"] = team1_partial_goals
        partial_output["result"]["team2_score"] = team2_partial_goals

        # 3) Adapt each player's performance metrics
        new_player_stories = []
        fraction_of_match = partial_duration / 90.0

        for player_story in full_output.get("player_stories", []):
            p_id = player_story.get("player_id")
            performance = player_story.get("performance", {})

            # Filter the partial events for this specific player
            player_events = [
                e for e in partial_events
                if e.get("token") == p_id
            ]

            # Re-count goals, assists, defense actions, injuries, punishments from partial events
            partial_goals = sum(1 for e in player_events if e.get("action_id") == 1)
            partial_assists = sum(1 for e in player_events if e.get("action_id") == 2)
            partial_def_actions = sum(1 for e in player_events if e.get("action_id") in [7, 8])
            partial_injured = any(e.get("action_id") == 9 for e in player_events)
            partial_punished = any(e.get("action_id") == 10 for e in player_events)

            # Scale overall_score, attribute_deltas, and freshness_delta by fraction_of_match
            old_overall_score = performance.get("overall_score", 0)
            scaled_overall_score = old_overall_score * fraction_of_match

            old_attr_deltas = performance.get("attribute_deltas", {})
            scaled_attr_deltas = {
                attr: delta * fraction_of_match
                for attr, delta in old_attr_deltas.items()
            }

            old_freshness_delta = performance.get("freshness_delta", 0)
            scaled_freshness_delta = old_freshness_delta * fraction_of_match

            new_player_stories.append({
                "player_id": p_id,
                "player_data": player_story.get("player_data", ""),
                "performance": {
                    "overall_score": scaled_overall_score,
                    "scored_goal": partial_goals,
                    "assist": partial_assists,
                    "defense_action": partial_def_actions,
                    "injured": partial_injured,
                    "punished": partial_punished,
                    "attribute_deltas": scaled_attr_deltas,
                    "freshness_delta": scaled_freshness_delta
                }
            })

        partial_output["player_stories"] = new_player_stories

        return partial_output

    def merge_partial_outputs(self, partial_output1, partial_output2):
        """
        Merges two partial outputs (each of which has the same structure as
        the result of process_post_game_live or _adapt_output_to_partial).

        Returns a new dictionary representing the combined partial output.
        """

        import copy

        # 1) Start with a deep copy of partial_output1
        merged = copy.deepcopy(partial_output1)

        # 2) Sum up the final score (assuming these partial outputs are disjoint).
        merged["result"]["team1_score"] += partial_output2["result"]["team1_score"]
        merged["result"]["team2_score"] += partial_output2["result"]["team2_score"]

        # 3) Add time played (again, assuming disjoint segments).
        merged["time_played_mins"] += partial_output2["time_played_mins"]

        # 4) Concatenate and sort events
        merged["events"].extend(partial_output2.get("events", []))
        merged["events"].sort(key=lambda e: (e.get("minute", 0), e.get("second", 0)))

        # 5) Merge player stories
        #    Build a dict keyed by player_id from partial_output1
        merged_player_dict = {
            ps["player_id"]: ps for ps in merged.get("player_stories", [])
        }

        # Go through partial_output2 player stories and merge
        for ps2 in partial_output2.get("player_stories", []):
            pid = ps2["player_id"]
            if pid not in merged_player_dict:
                # If this player wasn't in the first partial, just copy them
                merged_player_dict[pid] = copy.deepcopy(ps2)
            else:
                # Merge with existing player data
                ps1 = merged_player_dict[pid]
                merged_player_dict[pid] = self.merge_player_stories(ps1, ps2)

        # Finally, replace merged["player_stories"] with the merged data
        merged["player_stories"] = list(merged_player_dict.values())

        return merged

    def merge_player_stories(self, ps1, ps2):
        """
        Merge two player_stories dictionaries (ps1, ps2) into one.
        Both have the form:
          {
            "player_id": int,
            "player_data": str,
            "performance": {
                "overall_score": float,
                "scored_goal": int,
                "assist": int,
                "defense_action": int,
                "injured": bool,
                "punished": bool,
                "attribute_deltas": dict,
                "freshness_delta": float
            }
          }

        Returns a new dict with combined performance.
        """

        import copy
        merged_ps = copy.deepcopy(ps1)

        perf1 = ps1.get("performance", {})
        perf2 = ps2.get("performance", {})

        # Sum numeric fields; OR boolean fields
        merged_ps["performance"]["overall_score"] = perf1.get("overall_score", 0) + perf2.get("overall_score", 0)
        merged_ps["performance"]["scored_goal"] = perf1.get("scored_goal", 0) + perf2.get("scored_goal", 0)
        merged_ps["performance"]["assist"] = perf1.get("assist", 0) + perf2.get("assist", 0)
        merged_ps["performance"]["defense_action"] = perf1.get("defense_action", 0) + perf2.get("defense_action", 0)

        merged_ps["performance"]["injured"] = perf1.get("injured", False) or perf2.get("injured", False)
        merged_ps["performance"]["punished"] = perf1.get("punished", False) or perf2.get("punished", False)

        # Merge attribute deltas by adding them
        attr_deltas_1 = perf1.get("attribute_deltas", {})
        attr_deltas_2 = perf2.get("attribute_deltas", {})
        merged_attr_deltas = {}

        all_attrs = set(attr_deltas_1.keys()) | set(attr_deltas_2.keys())
        for attr in all_attrs:
            merged_attr_deltas[attr] = attr_deltas_1.get(attr, 0) + attr_deltas_2.get(attr, 0)

        merged_ps["performance"]["attribute_deltas"] = merged_attr_deltas

        # Sum freshness delta
        merged_ps["performance"]["freshness_delta"] = perf1.get("freshness_delta", 0) + perf2.get("freshness_delta", 0)

        # Handle special fields like penalty_taken and penalty_scored if they exist
        for special_field in ["penalty_taken", "penalty_scored"]:
            if special_field in perf1 or special_field in perf2:
                merged_ps["performance"][special_field] = perf1.get(special_field, False) or perf2.get(special_field,
                                                                                                       False)

        return merged_ps

    def process_post_game_live(self, team1_id, team2_id, team1_score, team2_score, min_start, min_end):
        output = self.process_post_game(team1_id, team2_id, team1_score, team2_score)
        partial_output = self.adapt_output_to_partial(output, team1_id, team2_id, min_start, min_end)
        return partial_output

    def process_must_win_game_live(self, team1_id, team2_id, min_start, min_end):
        """
        Process a live segment of a must-win game

        :param team1_id: ID of first team
        :param team2_id: ID of second team
        :param min_start: Starting minute of the segment
        :param min_end: Ending minute of the segment
        :return: Partial match result for the specified time window
        """
        # First, simulate the entire match
        full_match = self.process_must_win_game(team1_id, team2_id)

        # Then extract just the portion requested
        partial_result = self.adapt_output_to_partial(full_match, team1_id, team2_id, min_start, min_end)

        return partial_result