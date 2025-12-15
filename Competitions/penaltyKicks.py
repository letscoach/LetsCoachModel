import random
from typing import List, Dict, Optional, Tuple
from Helpers import SQL_db as db  # Assume this exists for DB interaction


class PenaltyKicksCompetition:
    """
    Unified module for managing both Penalty Kicks (Scoring) and
    Penalty Kicks (Saving) competitions using a knockout format.
    """

    # --- Constants for Simulation & Attributes ---
    SHOTS_PER_ROUND = 5
    SATISFACTION_QUINTILES = {
        0.2: 10,
        0.4: 5,
        0.6: 0,
        0.8: -5,
        1.0: -10
    }
    # Placeholder for reward values (should come from BO)
    OPPONENT_TEAM_PRIZE = 100
    OPPONENT_OWNER_PRIZE_SCALE = {1: 10, 2: 25, 3: 50}  # Saves/Goals made: prize

    def __init__(self, competition_id: str, competition_type: str):
        """
        Initialize the competition module.

        Args:
            competition_id: Unique identifier for this competition instance.
            competition_type: Must be 'Scoring' (Kickers compete) or 'Saving' (GKs compete).
        """
        if competition_type not in ['Scoring', 'Saving']:
            raise ValueError("competition_type must be 'Scoring' or 'Saving'.")

        self.competition_id = competition_id
        self.competition_type = competition_type

        # Determine the role of the participating players and the advancement metric
        self.is_scoring_comp = (competition_type == 'Scoring')
        self.advancement_metric = 'goals' if self.is_scoring_comp else 'saves'

        # Fetch all registered participants (Kickers for Scoring, GKs for Saving)
        self.participants = db.select_players_for_competition(competition_id)

        # Select the static opponent (GK for Scoring, Kicker for Saving)
        self.opponent = self._select_opponent()

        self.opponent_total_score = 0  # Total goals conceded or saves made
        self.final_results = []
        self.opponent_rewarded = False

    def _select_opponent(self) -> Dict:
        """
        Selects the designated opponent (GK for Scoring, Kicker for Saving)
        based on global stats as per PRD.
        """
        if self.is_scoring_comp:
            # PRD: Select GK with highest number of saves across all leagues
            return db.get_top_goalkeeper(self.competition_id)
        else:
            # PRD: Select Kicker with highest number of goals scored across all leagues
            return db.get_top_kicker(self.competition_id)

    def _simulate_shots(self, participant: Dict, opponent: Dict) -> Tuple[int, int]:
        """
        Simulate SHOTS_PER_ROUND penalty kicks.
        (Uses placeholder logic, assumes opponent is the designated Kicker or GK)

        Returns:
            A tuple (saves, goals).
        """
        # --- PLACEHOLDER LOGIC FOR PENALTY ENGINE ---
        gk = opponent if self.is_scoring_comp else participant
        kicker = participant if self.is_scoring_comp else opponent

        gk_attrs = gk.get('attributes', {})
        kicker_attrs = kicker.get('attributes', {})

        # Example influence: (Reflexes + Handling) vs. (Shooting + Composure)
        gk_score = (gk_attrs.get('Reflexes', 50) * 0.4) + (gk_attrs.get('Handling', 50) * 0.6)
        kicker_score = (kicker_attrs.get('Shooting', 50) * 0.5) + (kicker_attrs.get('Penalties', 50) * 0.5)

        advantage = (gk_score - kicker_score) / 100
        saves = 0
        for _ in range(self.SHOTS_PER_ROUND):
            save_probability = 0.5 + (advantage * 0.2) + random.uniform(-0.1, 0.1)
            if random.random() < save_probability:
                saves += 1

        goals = self.SHOTS_PER_ROUND - saves
        # --- END PLACEHOLDER LOGIC ---
        return saves, goals

    def _rank_players(self, results: List[Dict]) -> List[Dict]:
        """
        Ranks participants for SATISFACTION update based on:
        1. Round Reached (Higher is better)
        2. Score (Goals/Saves) in Last Round (Higher is better)
        3. Total Score (Goals/Saves) (Higher is better)
        """
        # Sort results: Primary: round_reached (desc), Secondary: score_in_last_round (desc), Tertiary: total_score (desc)
        results.sort(key=lambda x: (
        x['round_reached'], x[f'{self.advancement_metric}_in_last_round'], x[f'total_{self.advancement_metric}']),
                     reverse=True)

        # Assign rank position
        for i, result in enumerate(results):
            result['rank_position'] = i + 1

        return results

    def run_competition(self) -> List[Dict]:
        """
        Simulate the knockout tournament round by round.

[Image of a single elimination tournament bracket]

        """
        current_participants: List[Dict] = self.participants
        participant_results: Dict[str, Dict] = {
            p['token']: {
                'token': p['token'],
                'team_id': p['team_id'],
                'round_reached': 0,
                f'total_{self.advancement_metric}': 0,
                f'{self.advancement_metric}_in_last_round': 0,
                'is_winner': False
            } for p in self.participants
        }

        round_number = 1
        self.opponent_total_score = 0

        # 1. Edge Case: Check for a single participant (automatic winner)
        if len(current_participants) == 1:
            token = current_participants[0]['token']
            participant_results[token]['is_winner'] = True
            participant_results[token]['round_reached'] = 1
            # Still need to run 1 round for stats/rewards
            saves, goals = self._simulate_shots(current_participants[0], self.opponent)
            self.opponent_total_score = saves if self.is_scoring_comp else goals
            participant_results[token][f'total_{self.advancement_metric}'] = goals if self.is_scoring_comp else saves

            self.final_results = self._rank_players(list(participant_results.values()))
            self._reward_opponent()
            return self.final_results

        # 2. Run Knockout Rounds
        while len(current_participants) > 1 and round_number < 10:
            round_scores = []
            max_score_in_round = -1

            # Simulate shots for all participants in the current round
            for p in current_participants:
                saves, goals = self._simulate_shots(p, self.opponent)

                # Update opponent's total score (Saves for Scoring, Goals for Saving)
                self.opponent_total_score += saves if self.is_scoring_comp else goals

                current_score = goals if self.is_scoring_comp else saves
                token = p['token']

                # Update individual participant's stats
                participant_results[token]['round_reached'] = round_number
                participant_results[token][f'total_{self.advancement_metric}'] += current_score
                participant_results[token][f'{self.advancement_metric}_in_last_round'] = current_score

                round_scores.append({'token': token, 'score': current_score})

                max_score_in_round = max(max_score_in_round, current_score)

            # Determine who advances (highest score advances)

            # Tokens of players who achieved the highest score in this round
            advancing_tokens = {r['token'] for r in round_scores if r['score'] == max_score_in_round}

            # Scenario 1: Only ONE participant achieved the highest score (outright winner of the ROUND)
            if len(advancing_tokens) == 1 and max_score_in_round > -1:
                winner_token = list(advancing_tokens)[0]
                participant_results[winner_token]['is_winner'] = True
                current_participants = []  # End the competition
                break

            # Scenario 2: Multiple participants tied for the highest score - ALL advance
            # Filter the current participants list to create the next round's list
            current_participants = [p for p in current_participants if p['token'] in advancing_tokens]

            # Scenario 3: Competition ends if only one participant is left after filtering
            if len(current_participants) == 1:
                winner_token = current_participants[0]['token']
                participant_results[winner_token]['is_winner'] = True
                break

            # Continue to next round
            round_number += 1

        # 3. Finalize results, reward opponent, and store stats
        self.final_results = self._rank_players(list(participant_results.values()))
        self._reward_opponent()

        return self.final_results

    def _reward_opponent(self):
        """
        Calculates and applies the participation and performance rewards for the designated opponent.
        """
        if self.opponent and not self.opponent_rewarded:
            team_id = self.opponent['team_id']

            # 1. Team Participation Prize
            db.reward_team(team_id, self.OPPONENT_TEAM_PRIZE,
                           f"Opponent participation reward for Competition {self.competition_id}")

            # 2. Owner Performance Prize (based on total score)
            # Find the reward tier based on total goals/saves
            # Example: 1 save/goal: $10, 5 saves/goals: $50

            # This logic is simplified; a proper scaling based on performance is required per PRD.
            # Using opponent_total_score as the basis for performance reward.
            performance_reward = self.opponent_total_score * 5  # Example: $5 per goal/save

            db.reward_user(self.opponent['user_id'], performance_reward,
                           f"Opponent performance reward for Competition {self.competition_id}")

            self.opponent_rewarded = True

    def calculate_attribute_changes(self) -> Dict[str, Dict]:
        """
        Calculate SATISFACTION changes for participants based on their final ranking/quintile.
        FRESHNESS is explicitly stated as 'no impact'.
        """
        # Filter results that participated
        valid_results = [r for r in self.final_results if r['round_reached'] > 0]
        total_valid = len(valid_results)

        formatted_changes = {}

        for result in self.final_results:
            player_token = result['token']
            player_data = {
                'token': player_token,
                'attributes': {},
                'rank_position': result.get('rank_position', 0),
            }

            # Only apply SATISFACTION change if the player participated
            if result.get('round_reached', 0) > 0 and total_valid > 0:
                rank = result['rank_position']

                # Calculate percentile (0 to 1, where 0 is best)
                percentile = (rank - 1) / total_valid

                # Determine satisfaction change based on quintile
                satisfaction_change = 0
                for threshold, change in self.SATISFACTION_QUINTILES.items():
                    if percentile < threshold:
                        satisfaction_change = change
                        break

                player_data['attributes']['Satisfaction'] = satisfaction_change

                # Apply a bonus to the winner's key attributes (Optional addition)
                if result.get('is_winner', False):
                    # Kicker gets Shooting/Penalties bonus, GK gets Reflexes/Handling bonus
                    if self.is_scoring_comp:
                        player_data['attributes']['Shooting'] = 0.05
                        player_data['attributes']['Penalties'] = 0.03
                    else:
                        player_data['attributes']['Reflexes'] = 0.05
                        player_data['attributes']['Handling'] = 0.03

            # FRESHNESS change is 0 (as per PRD Section 7)
            player_data['attributes']['Freshness'] = 0

            formatted_changes[player_token] = player_data

        return formatted_changes

    def run_and_update(self):
        """
        Run the competition, calculate attribute changes, and apply them.
        """
        results = self.run_competition()
        attribute_changes = self.calculate_attribute_changes()

        # Store results and apply attributes
        db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)

        # Store competition-specific results
        db.store_penalty_kick_results(
            results,
            self.competition_id,
            self.opponent['token'],
            self.opponent_total_score,
            self.competition_type
        )

        return {
            "results": results,
            "opponent_token": self.opponent['token'],
            "opponent_total_score": self.opponent_total_score
        }