import random
import logging
from typing import Dict, List, Tuple, Optional
from Game.formation_grader import *
from Helpers import SQL_db as db
from Helpers.telegram_manager import send_log_message
import Game.freshness_update as fu

logger = logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class GameManager:
    def __init__(self, game_id):
        self.game_id = game_id
        self.game_state = None

    def init_game(self, team1_id: str, team2_id: str, must_win=False, incremental=False) -> Dict:
        """
        Initialize the game, simulate the result, and update the DB.

        Args:
            team1_id: The ID of the first team
            team2_id: The ID of the second team
            must_win: Whether the game must have a winner
            incremental: If True, only initializes the game state without simulation

        Returns:
            Dictionary containing the result and player stories or initial state
        """
        send_log_message("2.Update Freshness")

        # Update freshness for both teams
        fu.update_freshness_for_team(team1_id)
        fu.update_freshness_for_team(team2_id)

        send_log_message("3.Get formation")

        # Retrieve formations
        team1_formation = self.get_team_formation(team1_id)
        team2_formation = self.get_team_formation(team2_id)

        send_log_message("4.Update formation")
        db.insert_opening_formations(self.game_id)

        send_log_message("5.Calc team grades")
        # Calculate grades for both teams
        team1_grades = self.calculate_team_grades(team1_formation)
        team2_grades = self.calculate_team_grades(team2_formation)

        # Add team_id to the grades
        team1_grades['team_id'] = team1_id
        team2_grades['team_id'] = team2_id

        if incremental:
            # Just initialize the game state for incremental simulation
            self.game_state = {
                'team1_id': team1_id,
                'team2_id': team2_id,
                'team1_formation': team1_formation,
                'team2_formation': team2_formation,
                'team1_grades': team1_grades,
                'team2_grades': team2_grades,
                'current_minute': 0,
                'team1_score': 0,
                'team2_score': 0,
                'events': [],
                'must_win': must_win,
                'extra_time': False,
                'penalties': False,
                'game_over': False
            }

            # NEW CODE: Run the full simulation automatically if incremental is True
            print("===== First Half =====")
            for i in range(9):  # 9 periods of 5 minutes = 45 minutes
                period_result = self.simulate_next_period(period_length=5)
                print(
                    f"Minute {period_result['current_minute']}: {period_result['team1_score']} - {period_result['team2_score']}")

            print("\n===== Second Half =====")
            for i in range(9):  # 9 periods of 5 minutes = 45 minutes
                period_result = self.simulate_next_period(period_length=5)
                print(
                    f"Minute {period_result['current_minute']}: {period_result['team1_score']} - {period_result['team2_score']}")

            # Handle extra time if needed (since must_win might be True)
            if not self.game_state['game_over']:
                print("\n===== Extra Time =====")
                while not self.game_state['game_over']:
                    period_result = self.simulate_next_period(period_length=5)
                    print(
                        f"Minute {period_result['current_minute']}: {period_result['team1_score']} - {period_result['team2_score']}")

            # Finalize the game to generate the complete game report
            final_result = self.finalize_game()
            print(f"\nFinal score: {final_result['result']['team1_score']} - {final_result['result']['team2_score']}")
            print(f"Man of the match: {final_result['man_of_the_match']}")

            return final_result
        else:
            # Full simulation
            send_log_message("6.Simulate the game")
            total_time, team1_score, team2_score, events = self.simulator.simulate_live_game(
                team1_grades, team2_grades, must_win=must_win)

            # Create player stories from the events
            player_stories = self._generate_player_stories_from_events(events, team1_id, team2_id, team1_score,
                                                                       team2_score)

            # Determine man of the match
            man_of_the_match = self._determine_man_of_the_match(player_stories)

            # Create the output structure
            output = {
                'result': {'team1_score': team1_score, 'team2_score': team2_score},
                'time_played_mins': total_time,
                'player_stories': player_stories,
                'man_of_the_match': man_of_the_match,
                'events': events
            }

            send_log_message("7.Insert into db all match data")

            db.insert_match_details(self.game_id, output.get('events', []))
            db.update_matche_result(self.game_id, f"{team1_score}-{team2_score}", output.get('time_played_mins'))

            try:
                db.insert_man_of_the_match(output['man_of_the_match'], self.game_id)
            except Exception as e:
                send_log_message(f"Error: {e}, continue running!")

            self.update_player_data_in_db(self.game_id, output['player_stories'])
            send_log_message("8.End game_hub")

            return output
    def simulate_next_period(self, period_length=5):
        """
        Simulates the next period of the game with recalculated team grades and freshness.

        Args:
            period_length: Length of period in minutes (default: 5)

        Returns:
            Dictionary with period events and updated game state
        """
        if self.game_state is None:
            raise ValueError("Game not initialized. Call init_game with incremental=True first.")

        if self.game_state['game_over']:
            return {'status': 'game_over', 'result': self._get_final_result()}

        current_minute = self.game_state['current_minute']
        team1_id = self.game_state['team1_id']
        team2_id = self.game_state['team2_id']

        # Recalculate freshness and team grades for accurate simulation
        send_log_message(f"Recalculating team stats at minute {current_minute}")

        # 1. Update player freshness
        self._update_player_freshness(team1_id, current_minute)
        self._update_player_freshness(team2_id, current_minute)

        # 2. Recalculate team formations (might change due to fatigue/injuries)
        team1_formation = self.get_team_formation(team1_id)
        team2_formation = self.get_team_formation(team2_id)

        # 3. Recalculate team grades with updated player stats
        team1_grades = self.calculate_team_grades(team1_formation)
        team2_grades = self.calculate_team_grades(team2_formation)

        team1_grades['team_id'] = team1_id
        team2_grades['team_id'] = team2_id

        # Update formations and grades in game state
        self.game_state['team1_formation'] = team1_formation
        self.game_state['team2_formation'] = team2_formation
        self.game_state['team1_grades'] = team1_grades
        self.game_state['team2_grades'] = team2_grades

        # Handle special cases (extra time, penalties)
        if current_minute >= 90 and not self.game_state['extra_time'] and not self.game_state['penalties']:
            # Regular time ended
            if self.game_state['must_win'] and self.game_state['team1_score'] == self.game_state['team2_score']:
                # Start extra time
                self.game_state['extra_time'] = True
                send_log_message("Starting extra time")
            else:
                # Game over
                self.game_state['game_over'] = True
                return {'status': 'game_over', 'result': self._get_final_result()}

        elif current_minute >= 120 and self.game_state['extra_time'] and not self.game_state['penalties']:
            # Extra time ended
            if self.game_state['must_win'] and self.game_state['team1_score'] == self.game_state['team2_score']:
                # Start penalties
                self.game_state['penalties'] = True
                penalty_events, team1_pens, team2_pens = self.simulator._simulate_penalty_shootout(
                    team1_grades, team2_grades, start_minute=current_minute
                )

                # Add penalty results
                if team1_pens > team2_pens:
                    self.game_state['team1_score'] += 0.1  # Fractional to indicate penalties
                else:
                    self.game_state['team2_score'] += 0.1

                # Add penalty events
                self.game_state['events'].extend(penalty_events)

                # Game over after penalties
                self.game_state['game_over'] = True
                return {
                    'status': 'penalties',
                    'events': penalty_events,
                    'result': self._get_final_result()
                }
            else:
                # Game over
                self.game_state['game_over'] = True
                return {'status': 'game_over', 'result': self._get_final_result()}

        # Simulate the next period
        period_end = current_minute + period_length

        # Check if we're in regular time or extra time
        if not self.game_state['extra_time']:
            period_end = min(period_end, 90)  # Don't exceed regular time
        else:
            period_end = min(period_end, 120)  # Don't exceed extra time

        # Calculate actual period length (might be shorter at end of regular/extra time)
        actual_period_length = period_end - current_minute

        # Simulate just this period
        period_events = self.simulator._simulate_game_periods(
            self.game_state['team1_grades'],
            self.game_state['team2_grades'],
            actual_period_length,
            actual_period_length,
            start_minute=current_minute
        )[0]

        # Update scores based on events
        for event in period_events:
            if event['action_id'] == 1:  # Goal event
                if event['team_id'] == team1_id:
                    self.game_state['team1_score'] += 1
                else:
                    self.game_state['team2_score'] += 1

        # Update game state
        self.game_state['current_minute'] = period_end
        self.game_state['events'].extend(period_events)

        # Return period results
        return {
            'status': 'in_progress',
            'current_minute': period_end,
            'team1_score': self.game_state['team1_score'],
            'team2_score': self.game_state['team2_score'],
            'events': period_events,
            'in_extra_time': self.game_state['extra_time']
        }

    def _update_player_freshness(self, team_id, current_minute):
        """
        Updates player freshness based on minutes played.

        Players lose freshness as the game progresses, affecting their performance.
        """
        # Get players for this team
        players = db.get_team_players(team_id)

        # Decrease freshness proportionally to minutes played
        for player_id, player_data in players.items():
            if 'properties' in player_data and 'Freshness' in player_data['properties']:
                # Calculate freshness loss
                # Players with higher endurance lose freshness more slowly
                endurance = player_data['properties'].get('Endurance', 50)
                freshness_loss = (current_minute / 90) * (35 - (endurance / 4))

                # Update freshness value
                current_freshness = player_data['properties']['Freshness']
                new_freshness = max(0, current_freshness - freshness_loss)

                # Store updated freshness
                player_data['properties']['Freshness'] = new_freshness

                # Update in database
                if current_minute != 0:
                    db.update_player_freshness(player_id, -freshness_loss)

    def _get_final_result(self):
        """Returns the final result of the game"""
        if self.game_state is None:
            return None

        return {
            'team1_score': self.game_state['team1_score'],
            'team2_score': self.game_state['team2_score'],
            'minutes_played': self.game_state['current_minute'],
            'penalties': self.game_state['penalties']
        }

    def finalize_game(self):
        """
        Finalizes the game, generates player stories, and updates the database.
        Call this after all periods have been simulated.

        Returns:
            Complete game result including player stories and man of the match
        """
        if self.game_state is None or not self.game_state['game_over']:
            raise ValueError("Game not finished. Complete simulation first.")

        team1_id = self.game_state['team1_id']
        team2_id = self.game_state['team2_id']
        team1_score = self.game_state['team1_score']
        team2_score = self.game_state['team2_score']
        total_time = self.game_state['current_minute']
        events = self.game_state['events']

        # Create player stories from the events
        player_stories = self._generate_player_stories_from_events(
            events, team1_id, team2_id, team1_score, team2_score)

        # Determine man of the match
        man_of_the_match = self._determine_man_of_the_match(player_stories)

        # Create the output structure
        output = {
            'result': {'team1_score': team1_score, 'team2_score': team2_score},
            'time_played_mins': total_time,
            'player_stories': player_stories,
            'man_of_the_match': man_of_the_match,
            'events': events
        }

        send_log_message("7.Insert into db all match data")

        db.insert_match_details(self.game_id, output.get('events', []))
        db.update_matche_result(self.game_id, f"{team1_score}-{team2_score}", output.get('time_played_mins'))

        try:
            db.insert_man_of_the_match(output['man_of_the_match'], self.game_id)
        except Exception as e:
            send_log_message(f"Error: {e}, continue running!")

        self.update_player_data_in_db(self.game_id, output['player_stories'])
        send_log_message("8.End game_hub")

        return output

    def _generate_player_stories_from_events(self, events, team1_id, team2_id, team1_score, team2_score):
        """
        Generates player stories based on the events that occurred during the game.
        """
        # Collect stats for each player
        player_stats = {}

        # Process all events to collect player stats
        for event in events:
            player_id = event.get('token')
            if not player_id:
                continue

            # Initialize player stats if not exists
            if player_id not in player_stats:
                player_stats[player_id] = {
                    'player_id': player_id,
                    'team_id': event['team_id'],
                    'scored_goal': 0,
                    'assist': 0,
                    'defense_action': 0,
                    'gk_saves': 0,
                    'cards': {'yellow': 0, 'red': 0},
                    'penalties': {'scored': 0, 'missed': 0, 'saved': 0}
                }

            # Update stats based on action type
            action_id = event['action_id']
            if action_id == 1:  # Goal
                player_stats[player_id]['scored_goal'] += 1
            elif action_id == 2:  # Assist
                player_stats[player_id]['assist'] += 1
            elif action_id == 4:  # Yellow card
                player_stats[player_id]['cards']['yellow'] += 1
            elif action_id == 5:  # Red card
                player_stats[player_id]['cards']['red'] += 1
            elif action_id == 7 or action_id == 8:  # Defensive action or GK save
                player_stats[player_id]['defense_action'] += 1
                if action_id == 8:  # GK save
                    player_stats[player_id]['gk_saves'] += 1
            elif action_id == 11:  # Penalty kick
                # The result of the penalty is in a separate event
                pass
            elif action_id == 14:  # Penalty shootout score
                player_stats[player_id]['penalties']['scored'] += 1
            elif action_id == 15:  # Penalty shootout miss
                player_stats[player_id]['penalties']['missed'] += 1

        # Generate player stories with performance calculations
        player_stories = []

        for player_id, stats in player_stats.items():
            # Get player data for current freshness
            player_data = db.get_player_by_token(player_id)
            properties = player_data.get('properties', {}) if player_data else {}

            # Determine if player's team won
            team_won = False
            if stats['team_id'] == team1_id:
                team_won = team1_score > team2_score
            else:
                team_won = team2_score > team1_score

            # Generate random attribute updates based on performance and team result
            attribute_updates = self._generate_attribute_updates(stats, team_won)

            # Calculate player score based on performance
            player_score = self._calculate_player_score(stats, team_won)

            # Calculate freshness delta - get current freshness and calculate total loss
            current_freshness = properties.get('Freshness', 100)
            freshness_delta = current_freshness - 100  # Negative value representing loss

            # Player name for output
            player_name = player_data.get('name', f"Player {player_id}") if player_data else f"Player {player_id}"

            player_stories.append({
                'player_id': player_id,
                'player_data': player_name,
                'performance': {
                    'overall_score': player_score,
                    'team_won': team_won,
                    'scored_goal': stats['scored_goal'],
                    'assist': stats['assist'],
                    'defense_action': stats['defense_action'],
                    'injured': False,  # We could add injury logic if desired
                    'punished': stats['cards']['yellow'] > 0 or stats['cards']['red'] > 0,
                    'attribute_deltas': attribute_updates,
                    'freshness_delta': freshness_delta,
                    'satisfaction_delta': self._calculate_satisfaction_delta(stats, team_won)
                }
            })

        return player_stories

    def _determine_man_of_the_match(self, player_stories):
        """Determines the man of the match based on player performances"""
        best_score = 0
        motm = None

        for player in player_stories:
            # Calculate a score based on key performance metrics
            performance = player['performance']
            score = (
                    performance['overall_score'] * 2 +
                    performance['scored_goal'] * 5 +
                    performance['assist'] * 3 +
                    performance['defense_action'] * 2
            )

            if score > best_score:
                best_score = score
                motm = player['player_id']

        return motm if motm else ""

    def _generate_attribute_updates(self, stats, team_won):
        """Generates random attribute updates based on player performance"""
        updates = {}
        # More likely to improve if team won and player performed well
        improvement_chance = 0.3
        if team_won:
            improvement_chance += 0.2
        if stats['scored_goal'] > 0 or stats['assist'] > 0 or stats['defense_action'] > 2:
            improvement_chance += 0.2

        # Random attributes that might improve
        possible_attributes = ["Speed", "Dribble", "Shoot_Precision", "Pass_Precision",
                               "Tackle_Precision", "Game_vision", "Physicality", "Endurance"]

        # Number of attributes to potentially improve
        num_attributes = random.randint(0, 3)
        selected_attributes = random.sample(possible_attributes, min(num_attributes, len(possible_attributes)))

        for attr in selected_attributes:
            if random.random() < improvement_chance:
                # Small improvement
                updates[attr] = random.uniform(0.005, 0.015)

        return updates

    def _calculate_player_score(self, stats, team_won):
        """Calculates the player's overall match score"""
        base_score = 3.0  # Average performance

        # Adjust for team result
        if team_won:
            base_score += 0.5

        # Adjust for goals and assists
        base_score += 0.4 * stats['scored_goal']
        base_score += 0.3 * stats['assist']
        base_score += 0.2 * stats['defense_action']

        # Adjust for negative actions
        if stats['cards']['yellow'] > 0:
            base_score -= 0.2
        if stats['cards']['red'] > 0:
            base_score -= 0.7

        # Ensure score is within bounds (0.5 to 5.0)
        return max(0.5, min(5.0, base_score))

    def _calculate_satisfaction_delta(self, stats, team_won):
        """Calculates the change in player satisfaction"""
        satisfaction_change = 0

        # Basic change based on team result
        if team_won:
            satisfaction_change += 4
        else:
            satisfaction_change -= 2

        # Performance factors
        if stats['scored_goal'] > 0:
            satisfaction_change += 2 * stats['scored_goal']
        if stats['assist'] > 0:
            satisfaction_change += 2 * stats['assist']
        if stats['defense_action'] > 2:
            satisfaction_change += 2

        # Negative factors
        if stats['cards']['yellow'] > 0:
            satisfaction_change -= 1
        if stats['cards']['red'] > 0:
            satisfaction_change -= 3

        return satisfaction_change

    def get_team_formation(self, team_id):
        """
        Retrieve the team formation from the database by team ID.
        - team_id: The ID of the team.
        - Returns: Formation list.
        """
        formation = db.get_team_default_formation(team_id)
        return formation

    def calculate_team_grades(self, formation_list):
        """
        Calculate team grades using the grading module.
        - formation_list: The team's formation as a list of player IDs.
        - Returns: Dictionary with defense, midfield, and offense grades.
        """
        from Game.formation_grader import calc_grades
        return calc_grades(formation_list)

    def update_player_data_in_db(self, match_id, player_stories):
        """
        Update the Players DB with new attributes and freshness in one bulk operation.
        - match_id: the match identifier for this update.
        - player_stories: List of dictionaries containing player updates.
        """
        logger.info("Starting update_player_data_in_db for match_id=%s", match_id)
        logger.debug("Received player_stories: %s", player_stories)

        # Perform the single bulk insert/update
        db.insert_player_attributes_game_effected(player_stories, match_id)

        logger.info("Bulk insert complete for match_id=%s.", match_id)
    # Example 3: Game with team formation/freshness changes during gameplay
    def run_tactical_game():
        # Create game manager with a game ID
        game_manager = GameManager(game_id="match_125")

        # Initialize the game state without simulation
        game_manager.init_game(team1_id="team1", team2_id="team2", must_win=False, incremental=True)

        # Simulate first half (45 minutes) in 5-minute chunks
        print("===== First Half =====")
        for i in range(9):  # 9 periods of 5 minutes = 45 minutes
            period_result = game_manager.simulate_next_period(period_length=5)
            print(
                f"Minute {period_result['current_minute']}: {period_result['team1_score']} - {period_result['team2_score']}")

        # Make tactical changes at half-time (this would update formations in the database)
        print("\n===== Half-Time Tactical Changes =====")
        print("Making substitutions and tactical changes...")
        # Example: In a real implementation, you'd call functions to update formations in the database
        # update_team_formation(team1_id, new_formation)

        # Simulate second half (45 minutes) in 5-minute chunks
        print("\n===== Second Half =====")
        for i in range(9):  # 9 periods of 5 minutes = 45 minutes
            period_result = game_manager.simulate_next_period(period_length=5)
            print(
                f"Minute {period_result['current_minute']}: {period_result['team1_score']} - {period_result['team2_score']}")

        # Finalize the game
        final_result = game_manager.finalize_game()
        print(f"\nFinal score: {final_result['result']['team1_score']} - {final_result['result']['team2_score']}")


game_manager = GameManager(game_id="444")

# Initialize the game for live simulation with must_win=True
game_state = game_manager.init_game(
    team1_id="99",  # home team ID
    team2_id="92",  # away team ID
    must_win=True,  # ensure there's a winner
    incremental=True  # for live simulation
)
