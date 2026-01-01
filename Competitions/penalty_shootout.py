import json
import random
from typing import List, Dict, Tuple, Optional
from Helpers import SQL_db as db


class PenaltyShootout:
    """
    Module for managing the Penalty Kicks (Scoring) competition.
    Handles player registration, goalkeeper selection, knockout simulation, and attribute updates.
    """

    # Constants for simulation
    SHOTS_PER_ROUND = 5  # Number of penalty kicks per player per round
    FRESHNESS_THRESHOLD = 10  # Minimum freshness to participate
    
    # Attribute weights for kicker score calculation
    KICKER_WEIGHTS = {
        "Shoot_Precision": 0.40,
        "Shoot_Power": 0.30,
        "Finishing": 0.20,
        "Satisfaction": 0.10
    }
    
    # Attribute weights for goalkeeper score calculation
    GK_WEIGHTS = {
        "Reflexes": 0.40,
        "Diving": 0.30,
        "Game_vision": 0.20,  # GK positioning/reading the game
        "Satisfaction": 0.10
    }
    
    # Random factor range for each kick
    RANDOM_RANGE = 5  # +/- 5 points
    
    # Advantage needed for kicker to score (goalkeeper has home advantage)
    KICKER_ADVANTAGE_NEEDED = 10

    def __init__(self, competition_id: str = None):
        """
        Initialize the Penalty Shootout competition module.

        Args:
            competition_id: Unique identifier for this competition instance
        """
        self.competition_id = competition_id
        self.participants = db.select_players_for_competition(competition_id)
        self.goalkeeper = self._select_goalkeeper()
        self.results = []
        self.rounds_data = []  # Store data for each round

    def _select_goalkeeper(self) -> Dict:
        """
        Select the goalkeeper for this competition.
        Currently selects a random GK from all available GKs.
        
        TODO: In future, select based on save statistics from matches.
        
        Returns:
            Goalkeeper player data dictionary
        """
        # For now, we'll select a random goalkeeper from the database
        # In production, this should query goalkeeper_statistics table
        try:
            # Query all goalkeepers (assuming position or role indicator exists)
            query = """
                SELECT p.*, pa.attribute_value as reflexes
                FROM players p
                LEFT JOIN player_attributes pa ON p.token = pa.token AND pa.attribute_id = 
                    (SELECT attribute_id FROM attributes WHERE attribute_name = 'Reflexes')
                WHERE p.position = 'GK' OR pa.attribute_value > 0
                ORDER BY RAND()
                LIMIT 1
            """
            # Fallback: just get a random player with good Reflexes
            gk_list = db.exec_select_query(query)
            if gk_list and len(gk_list) > 0:
                gk_token = gk_list[0]['token']
                goalkeeper = db.get_player_by_token(gk_token)
                return goalkeeper
            else:
                # Emergency fallback: use first player in participants as GK
                print("⚠️ Warning: No goalkeeper found, using fallback")
                return self.participants[0] if self.participants else None
        except Exception as e:
            print(f"❌ Error selecting goalkeeper: {e}")
            # Emergency fallback
            return self.participants[0] if self.participants else None

    def _calculate_player_score(self, player: Dict, is_kicker: bool = True) -> float:
        """
        Calculate a player's base score for penalty kick.

        Args:
            player: Player data dictionary with attributes
            is_kicker: True if calculating kicker score, False for goalkeeper

        Returns:
            Base score (0-100)
        """
        properties = player.get('properties', {})
        weights = self.KICKER_WEIGHTS if is_kicker else self.GK_WEIGHTS
        
        # Check freshness
        freshness = properties.get('Freshness', 100)
        if freshness < self.FRESHNESS_THRESHOLD:
            return 0  # Player too tired
        
        # Calculate core score
        core_score = 0
        for attr, weight in weights.items():
            attr_value = properties.get(attr, 50)  # Default to 50 if missing
            core_score += attr_value * weight
        
        # Adjust by freshness
        adjusted_score = core_score * (freshness / 100)
        
        return adjusted_score

    def _simulate_single_kick(self, kicker: Dict, goalkeeper: Dict) -> bool:
        """
        Simulate a single penalty kick.

        Args:
            kicker: Kicker player data
            goalkeeper: Goalkeeper player data

        Returns:
            True if goal scored, False if saved
        """
        # Calculate scores
        kicker_score = self._calculate_player_score(kicker, is_kicker=True)
        gk_score = self._calculate_player_score(goalkeeper, is_kicker=False)
        
        # Add random factors
        kicker_final = kicker_score + random.uniform(-self.RANDOM_RANGE, self.RANDOM_RANGE)
        gk_final = gk_score + random.uniform(-self.RANDOM_RANGE, self.RANDOM_RANGE)
        
        # Kicker needs advantage to score (GK has slight advantage)
        goal_scored = kicker_final > (gk_final + self.KICKER_ADVANTAGE_NEEDED)
        
        return goal_scored

    def _simulate_round(self, kickers: List[Dict]) -> List[Dict]:
        """
        Simulate one round of the competition.

        Args:
            kickers: List of players participating in this round

        Returns:
            List of results with goals scored per kicker
        """
        round_results = []
        
        for kicker in kickers:
            goals_scored = 0
            
            # Each kicker takes SHOTS_PER_ROUND kicks
            for shot_num in range(self.SHOTS_PER_ROUND):
                if self._simulate_single_kick(kicker, self.goalkeeper):
                    goals_scored += 1
            
            round_results.append({
                'token': kicker['token'],
                'goals_scored': goals_scored,
                'player_data': kicker
            })
        
        return round_results

    def _get_advancing_players(self, round_results: List[Dict]) -> List[Dict]:
        """
        Determine which players advance to the next round.

        Args:
            round_results: Results from current round

        Returns:
            List of player data for advancing players
        """
        if not round_results:
            return []
        
        # Find maximum goals scored in this round
        max_goals = max(r['goals_scored'] for r in round_results)
        
        # All players with max goals advance
        advancing = [
            r['player_data'] 
            for r in round_results 
            if r['goals_scored'] == max_goals
        ]
        
        return advancing

    def run_competition(self) -> List[Dict]:
        """
        Run the full knockout competition.

        Returns:
            Final results with rankings
        """
        if not self.participants:
            print("⚠️ No participants in competition")
            return []
        
        if not self.goalkeeper:
            print("❌ No goalkeeper available")
            return []
        
        print(f"\n🥅 Starting Penalty Shootout Competition!")
        print(f"   Goalkeeper: {self.goalkeeper.get('name', 'Unknown')}")
        print(f"   Participants: {len(self.participants)} kickers")
        
        current_kickers = self.participants.copy()
        round_number = 1
        all_eliminated = []  # Track elimination order
        gk_total_saves = 0
        
        while len(current_kickers) > 1:
            print(f"\n⚽ Round {round_number}: {len(current_kickers)} kickers")
            
            # Simulate round
            round_results = self._simulate_round(current_kickers)
            
            # Calculate saves for goalkeeper
            total_shots = len(current_kickers) * self.SHOTS_PER_ROUND
            total_goals = sum(r['goals_scored'] for r in round_results)
            round_saves = total_shots - total_goals
            gk_total_saves += round_saves
            
            # Store round data
            self.rounds_data.append({
                'round_number': round_number,
                'results': round_results,
                'saves': round_saves
            })
            
            # Get advancing players
            advancing = self._get_advancing_players(round_results)
            
            # Track eliminated players with their round and score
            eliminated_tokens = set(r['token'] for r in round_results) - set(p['token'] for p in advancing)
            for result in round_results:
                if result['token'] in eliminated_tokens:
                    all_eliminated.append({
                        'token': result['token'],
                        'elimination_round': round_number,
                        'goals_in_final_round': result['goals_scored']
                    })
            
            print(f"   {len(advancing)} kickers advance (scored max: {round_results[0]['goals_scored'] if round_results else 0})")
            
            current_kickers = advancing
            round_number += 1
            
            # Safety check: prevent infinite loops
            if round_number > 20:
                print("⚠️ Too many rounds, declaring all remaining as winners")
                break
        
        # Winner(s)
        if current_kickers:
            for winner in current_kickers:
                all_eliminated.append({
                    'token': winner['token'],
                    'elimination_round': round_number,  # Winner's round
                    'goals_in_final_round': self.SHOTS_PER_ROUND,  # Assume perfect round
                    'is_winner': True
                })
        
        # Build final results with rankings
        final_results = self._build_final_results(all_eliminated, gk_total_saves)
        
        self.results = final_results
        return final_results

    def _build_final_results(self, elimination_data: List[Dict], gk_saves: int) -> List[Dict]:
        """
        Build final results with proper rankings.

        Args:
            elimination_data: List of elimination info for each player
            gk_saves: Total saves made by goalkeeper

        Returns:
            Sorted list of results
        """
        # Sort by elimination round (desc) then by goals in final round (desc)
        sorted_data = sorted(
            elimination_data,
            key=lambda x: (x['elimination_round'], x['goals_in_final_round']),
            reverse=True
        )
        
        # Build results
        results = []
        for i, data in enumerate(sorted_data):
            results.append({
                'token': data['token'],
                'rank_position': i + 1,
                'elimination_round': data['elimination_round'],
                'goals_in_final_round': data['goals_in_final_round'],
                'is_winner': data.get('is_winner', False),
                'score': max(0, 100 - (i * 2))  # Score decreases by rank
            })
        
        # Add goalkeeper saves info (not part of results but useful)
        self.gk_saves = gk_saves
        
        return results

    def calculate_attribute_changes(self) -> Dict[str, Dict]:
        """
        Calculate attribute changes for participants based on competition results.

        Returns:
            Dictionary of player attribute changes
        """
        if not self.results:
            return {}
        
        formatted_changes = {}
        total_participants = len(self.results)
        
        for result in self.results:
            player_token = result['token']
            player = db.get_player_by_token(player_token)
            
            if not player:
                continue
            
            # Initialize player data
            player_data = {
                'token': player_token,
                'attributes': {},
                'rank_position': result['rank_position'],
                'score': result['score']
            }
            
            # Add is_winner for top 3
            if result['rank_position'] <= 3:
                player_data['is_winner'] = result['rank_position']
            
            # Calculate satisfaction based on quintiles
            percentile = (result['rank_position'] - 1) / max(1, total_participants - 1)
            
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
            
            # No freshness impact (as per PRD)
            # But small attribute improvements for top performers
            if result['rank_position'] <= 3:
                player_data['attributes']['Shoot_Precision'] = 0.02
                player_data['attributes']['Finishing'] = 0.01
            
            formatted_changes[player_token] = player_data
        
        return formatted_changes

    def get_goalkeeper_rewards(self) -> Dict:
        """
        Calculate rewards for the goalkeeper's team and owner.

        Returns:
            Dictionary with reward information
        """
        return {
            'goalkeeper_token': self.goalkeeper['token'] if self.goalkeeper else None,
            'goalkeeper_name': self.goalkeeper.get('name', 'Unknown') if self.goalkeeper else None,
            'total_saves': getattr(self, 'gk_saves', 0),
            'team_reward': 'BASE_PRIZE',  # Defined in BO
            'owner_reward_multiplier': getattr(self, 'gk_saves', 0)  # Scales with saves
        }

    def apply_attribute_changes(self) -> None:
        """
        Apply the calculated attribute changes to players in the database.
        """
        attribute_changes = self.calculate_attribute_changes()
        db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)

    def run_and_update(self):
        """
        Run the competition, calculate attribute changes and apply them.

        Returns:
            The competition results and goalkeeper info
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"🏁 Starting PenaltyShootout competition {self.competition_id}")
        results = self.run_competition()
        attribute_changes = self.calculate_attribute_changes()
        db.insert_player_attributes_competition_effected(attribute_changes, self.competition_id)
        
        # Get competition type from database to determine if Penalty Shooter (3) or Goalkeeper (4)
        comp_query = f"SELECT competition_type_id FROM competitions WHERE id = {self.competition_id}"
        comp_result = db.exec_select_query(comp_query)
        competition_type_id = comp_result[0][0] if comp_result else 3  # Default to 3 if not found
        
        # Distribute prizes to winners
        print(f"\n" + "="*70)
        print(f"💰 PENALTY: About to distribute prizes for competition {self.competition_id}, type {competition_type_id}")
        print(f"="*70)
        logger.info(f"💰 Distributing prizes for type {competition_type_id}...")
        try:
            prize_result = db.distribute_competition_prizes(self.competition_id, competition_type_id)
            print(f"🎉 PENALTY: Prize distribution result: {prize_result}")
            logger.info(f"🎉 Prize distribution result: {prize_result.get('status')}")
        except Exception as e:
            print(f"❌ PENALTY: Prize distribution FAILED: {e}")
            logger.error(f"❌ Prize distribution failed: {e}", exc_info=True)
            import traceback
            traceback.print_exc()
        print(f"="*70 + "\n")
        
        return {
            'results': results,
            'goalkeeper': self.get_goalkeeper_rewards(),
            'rounds': len(self.rounds_data)
        }


# Example usage
if __name__ == "__main__":
    # Test with competition_id from DB
    competition = PenaltyShootout(competition_id=1)
    output = competition.run_and_update()
    print("\n🏆 Competition Results:")
    print(json.dumps(output, indent=2))
