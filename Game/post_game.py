import json
import random
from Game.formation_grader import *
from Helpers import SQL_db as db

def round_up_to_half(score):
    return round((score * 2 + 1) // 1) / 2


class EventLogger:
    def __init__(self):
        self.events = []

    def log_event(self, minute, second,token, team_id, action_id, description):
        self.events.append({"minute": minute,
                            "second": second,
                            "description": description,
                            "token": token,
                            "team_id": team_id,
                            "action_timestamp" : f"{minute:02}:{second:02}",
                            "action_id": action_id})

    def get_events(self):
        return sorted(self.events, key=lambda x: (x["minute"], x["second"]))


class SatisfactionCalculator:
    @staticmethod
    def calculate_satisfaction_changes(results, team1_score, team2_score):
        """
        Calculates the satisfaction change for each player based on playing time, match result, and personal performance.
        """
        satisfaction_changes = {}
        team_won = team1_score > team2_score
        team_lost = team1_score < team2_score
        is_draw = team1_score == team2_score
        goal_difference = abs(team1_score - team2_score)

        for player_result in results:
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
            #if player_result["performance"].get("man_of_the_match", False):
            #    satisfaction_change += 4
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
            player_result["satisfaction_delta"] = satisfaction_change



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
        formation_list = ensure_list_of_lists(formation)
        for i, row in enumerate(formation_list):
            for j, player_id in enumerate(row):
                if player_id != "0" and (i, j) in POSITION_MAPPING:
                    position = POSITION_MAPPING[(i, j)]
                    player_data = db.get_player_by_token(player_id)
                    player_data['position'] = position
                    player_data['defense_action'] = 0
                    player_data['assist'] = 0
                    player_data['scored_goal'] = 0
                    player_data['properties'] = player_data.get('properties', {})
                    players.append(player_data)
        return players


    def assign_defense_actions(self, players, event_logger):
        """
        Assigns defensive actions such as blocks and goalkeeper saves,
        ensuring attackers and defenders are randomly assigned per attack event.

        :param players: List of all players (both teams).
        :param event_logger: Event logging object.
        """

        # Group players by team
        team1 = [p for p in players if p["team_id"] == players[0]["team_id"]]
        team2 = [p for p in players if p["team_id"] != players[0]["team_id"]]

        position_weights_defense = {
            "GK": 0.9,
            "Centre-back": 0.7,
            "Wide Midfielder": 0.2,
            "Winger": 0.1
        }

        position_weights_attack = {
            "Striker": 0.4,
            "Forward": 0.3,
            "Winger": 0.15,
            "Wide Midfielder": 0.1,
            "Centre-back": 0.04,
            "GK": 0.005
        }

        defensive_actions = []

        for minute in range(5, 91, 15):
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
                    team_id = attacker["team_id"],
                    action_id=6,  # Shot attempt action
                    description=f"Player {attacker['player_id']} attempted a shot"
                )
                attacker["shots"] = attacker.get("shots", 0) + 1

                if goalkeeper and random.random() < 0.4:  # 40% chance GK makes a save
                    event_logger.log_event(
                        minute=minute,
                        second=second,
                        token=goalkeeper["player_id"],
                        team_id =goalkeeper["team_id"],
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
                        team_id =defender["team_id"],
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

    def assign_goals_and_assists(self, players, team_score, event_logger):
        scorers = []
        if team_score > 0:
            position_weights = {
                "Striker": 0.4,
                "Forward": 0.3,
                "Winger": 0.15,
                "Wide Midfielder": 0.1,
                "Centre-back": 0.04,
                "GK": 0.005
            }

            weighted_players = []
            for player in players:
                weight = position_weights.get(player.get("position", "Wide Midfielder"), 0.1)
                weighted_players.extend([player] * int(weight * 100))

            for _ in range(team_score):
                scorer = random.choice(weighted_players)
                scorer['scored_goal'] += 1
                minute = random.randint(1, 90)
                second = random.randint(0, 59)

                assister = None
                if random.random() < 0.6:
                    plausible_assisters = [
                        p for p in players
                        if p['player_id'] != scorer['player_id'] and p["position"] in ["Forward", "Winger",
                                                                                       "Wide Midfielder"] and p[
                               "position"] != "GK"
                    ]
                    if plausible_assisters:
                        assister = random.choice(plausible_assisters)
                        assister['assist'] += 1

                self.log_goal_with_assist(event_logger, minute, second, scorer, assister)
                scorers.append({"player": scorer, "minute": minute, "second": second, "assister": assister})

        return scorers
    def log_goal_with_assist(self, event_logger, goal_minute, goal_second, scorer, assister=None):
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
                token = assister['player_id'],
                team_id = scorer['team_id'],
                action_id = 2,
                description=f"Player {assister['player_id']} provided an assist for Player {scorer['player_id']}"
            )

        event_logger.log_event(
            minute=goal_minute,
            second=goal_second,
            token=scorer['player_id'],
            team_id = scorer['team_id'],
            action_id=1,
            description=f"Player {scorer['player_id']} scored a goal"
        )

    def calculate_freshness_drop(self, endurance, min_played=90):
        """
        Calculate the drop in 'Freshness' based on the player's 'Endurance'.
        """
        return (35 - (endurance / 4)) * (min_played / 90)

    def random_attribute_updates(self, player, team_won):
        updates = {}
        total_updates = random.randint(1, 3) if team_won else random.randint(0, 2)
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

        team1_players = self.fetch_player_data(team1_formation)
        team2_players = self.fetch_player_data(team2_formation)

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
                "performance": {
                    "overall_score": calculate_player_score(
                        player, story,
                        team_score=team1_score if player in team1_players else team2_score,
                        opponent_score=team2_score if player in team1_players else team1_score,
                        team_won=team_won
                    ),
                    "scored_goal": story.get("scored_goal", 0),
                    "assist": story.get("assist", 0),
                    "defense_action": story.get("defense_action", 0),
                    "injured": story.get("injured", False),
                    "punished": story.get("punished", False),
                    "attribute_deltas": attribute_updates,
                    "freshness_delta": -self.calculate_freshness_drop(player['properties']['Endurance']),
                }
            })
        SatisfactionCalculator.calculate_satisfaction_changes(results, team1_score, team2_score)

        return {
            "result": {"team1_score": team1_score, "team2_score": team2_score},
            "time_played_mins": 90,
            "player_stories": results,
            "events": event_logger.get_events()
        }
