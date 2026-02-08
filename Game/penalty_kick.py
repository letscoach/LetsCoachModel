"""
Penalty Kick Module

Shared penalty kick logic for:
1. In-game penalty kicks (fouls in the box)
2. Penalty shootouts (match deciding)
3. Penalty competitions

Based on realistic football statistics:
- Average penalty conversion rate: 76-78%
- Goalkeeper save rate: ~17%
- Missed target: ~5-7%
"""

import random
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class PenaltyKick:
    """
    Handles individual penalty kick simulation with realistic outcomes.
    """
    
    # Attribute weights for kicker score calculation
    KICKER_WEIGHTS = {
        "Shoot_Precision": 0.35,
        "Shoot_Power": 0.25,
        "Finishing": 0.25,
        "Satisfaction": 0.10,
        "Freshness": 0.05
    }
    
    # Attribute weights for goalkeeper score calculation
    GK_WEIGHTS = {
        "Reflexes": 0.35,
        "Diving": 0.30,
        "Game_Vision": 0.20,  # Reading the kicker
        "Satisfaction": 0.10,
        "Freshness": 0.05
    }
    
    # Random factor range for each kick (+/- points)
    RANDOM_RANGE = 8
    
    # Base conversion rate (before adjustments)
    BASE_CONVERSION_RATE = 0.76
    
    # Outcome types
    OUTCOME_GOAL = "goal"
    OUTCOME_SAVED = "saved"
    OUTCOME_MISSED = "missed"  # Hit post/crossbar or completely missed
    OUTCOME_RESAVE = "saved_rebound"  # Saved but dramatic
    
    @classmethod
    def calculate_kicker_score(cls, player: Dict) -> float:
        """
        Calculate kicker's penalty taking ability score.
        
        Args:
            player: Player data with properties
            
        Returns:
            Score from 0-100
        """
        properties = player.get('properties', {})
        
        score = 0
        for attr, weight in cls.KICKER_WEIGHTS.items():
            attr_value = properties.get(attr, 50)
            score += attr_value * weight
        
        return score
    
    @classmethod
    def calculate_gk_score(cls, goalkeeper: Dict) -> float:
        """
        Calculate goalkeeper's penalty saving ability score.
        
        Args:
            goalkeeper: Goalkeeper data with properties
            
        Returns:
            Score from 0-100
        """
        properties = goalkeeper.get('properties', {})
        
        score = 0
        for attr, weight in cls.GK_WEIGHTS.items():
            attr_value = properties.get(attr, 50)
            score += attr_value * weight
        
        return score
    
    @classmethod
    def simulate_kick(
        cls,
        kicker: Dict,
        goalkeeper: Dict,
        pressure_factor: float = 1.0,
        is_shootout: bool = False,
        shootout_round: int = 0
    ) -> Tuple[str, Dict]:
        """
        Simulate a single penalty kick.
        
        Args:
            kicker: Kicker player data
            goalkeeper: Goalkeeper player data
            pressure_factor: Multiplier for pressure (higher = more pressure)
            is_shootout: Whether this is a shootout penalty
            shootout_round: Round number in shootout (affects pressure)
            
        Returns:
            Tuple of (outcome, details_dict)
        """
        # Calculate base scores
        kicker_score = cls.calculate_kicker_score(kicker)
        gk_score = cls.calculate_gk_score(goalkeeper)
        
        # Add random factors
        kicker_random = random.uniform(-cls.RANDOM_RANGE, cls.RANDOM_RANGE)
        gk_random = random.uniform(-cls.RANDOM_RANGE, cls.RANDOM_RANGE)
        
        # Apply pressure factor (reduces kicker effectiveness in high-pressure situations)
        if is_shootout and shootout_round >= 5:
            # Sudden death - maximum pressure
            pressure_factor *= 1.3
        elif is_shootout:
            # Regular shootout - increasing pressure each round
            pressure_factor *= (1.0 + shootout_round * 0.05)
        
        # Pressure affects kicker more than goalkeeper
        kicker_final = kicker_score + kicker_random - (pressure_factor - 1.0) * 10
        gk_final = gk_score + gk_random + (pressure_factor - 1.0) * 5
        
        # Calculate conversion probability
        # Base rate adjusted by kicker vs goalkeeper differential
        differential = kicker_final - gk_final
        
        # Convert differential to probability adjustment
        # +20 differential = +10% conversion, -20 = -10%
        prob_adjustment = differential / 200
        
        conversion_prob = cls.BASE_CONVERSION_RATE + prob_adjustment
        conversion_prob = max(0.50, min(0.92, conversion_prob))  # Clamp between 50-92%
        
        # Determine outcome
        roll = random.random()
        
        if roll < conversion_prob:
            outcome = cls.OUTCOME_GOAL
        else:
            # Determine if saved or missed
            # About 70% of non-goals are saves, 30% are misses
            if random.random() < 0.70:
                outcome = cls.OUTCOME_SAVED
            else:
                outcome = cls.OUTCOME_MISSED
        
        # Build details
        details = {
            "kicker_id": kicker.get("player_id") or kicker.get("token"),
            "kicker_name": kicker.get("name", "Unknown"),
            "goalkeeper_id": goalkeeper.get("player_id") or goalkeeper.get("token"),
            "goalkeeper_name": goalkeeper.get("name", "Unknown"),
            "kicker_score": round(kicker_final, 1),
            "gk_score": round(gk_final, 1),
            "conversion_prob": round(conversion_prob, 3),
            "outcome": outcome,
            "pressure_factor": round(pressure_factor, 2)
        }
        
        logger.debug(f"Penalty: {details['kicker_name']} vs {details['goalkeeper_name']} - {outcome} (prob: {conversion_prob:.1%})")
        
        return outcome, details


class PenaltyShootoutSimulator:
    """
    Simulates a full penalty shootout between two teams.
    """
    
    def __init__(self, team1_players: list, team2_players: list, team1_id: str, team2_id: str):
        """
        Initialize shootout simulator.
        
        Args:
            team1_players: List of team 1 players
            team2_players: List of team 2 players
            team1_id: Team 1 ID
            team2_id: Team 2 ID
        """
        self.team1_players = team1_players
        self.team2_players = team2_players
        self.team1_id = team1_id
        self.team2_id = team2_id
        
        # Find goalkeepers
        self.team1_gk = self._find_goalkeeper(team1_players, team1_players[0])
        self.team2_gk = self._find_goalkeeper(team2_players, team2_players[0])
        
        # Select penalty takers
        self.team1_takers = self._select_penalty_takers(team1_players)
        self.team2_takers = self._select_penalty_takers(team2_players)
    
    def _find_goalkeeper(self, players: list, fallback) -> Dict:
        """Find the goalkeeper in the team."""
        for p in players:
            if p.get("position") == "GK":
                return p
        return fallback
    
    def _select_penalty_takers(self, players: list) -> list:
        """
        Select and order penalty takers based on ability.
        
        Returns:
            Ordered list of penalty takers (best first for rounds 1-5)
        """
        # Filter out goalkeeper
        outfield = [p for p in players if p.get("position") != "GK"]
        
        # Sort by penalty taking ability
        sorted_players = sorted(
            outfield,
            key=lambda p: PenaltyKick.calculate_kicker_score(p),
            reverse=True
        )
        
        return sorted_players
    
    def simulate(self) -> Dict:
        """
        Simulate the full penalty shootout.
        
        Returns:
            Dictionary with results:
            {
                "winner_id": str,
                "team1_score": int,
                "team2_score": int,
                "kicks": list of kick details,
                "events": list of events for logging
            }
        """
        team1_score = 0
        team2_score = 0
        kicks = []
        events = []
        
        current_round = 0
        
        # First 5 rounds
        for round_idx in range(5):
            current_round = round_idx + 1
            
            # Team 1 kicks
            taker1 = self.team1_takers[round_idx % len(self.team1_takers)]
            outcome1, details1 = PenaltyKick.simulate_kick(
                taker1, self.team2_gk,
                is_shootout=True, shootout_round=current_round
            )
            
            if outcome1 == PenaltyKick.OUTCOME_GOAL:
                team1_score += 1
            
            kicks.append({
                "round": current_round,
                "team_id": self.team1_id,
                **details1
            })
            
            events.append({
                "minute": 120,
                "second": round_idx * 2,
                "token": details1["kicker_id"],
                "team_id": self.team1_id,
                "action_id": 14 if outcome1 == PenaltyKick.OUTCOME_GOAL else 15,
                "description": f"Penalty {'SCORED' if outcome1 == PenaltyKick.OUTCOME_GOAL else outcome1.upper()} by {details1['kicker_name']}"
            })
            
            # Team 2 kicks
            taker2 = self.team2_takers[round_idx % len(self.team2_takers)]
            outcome2, details2 = PenaltyKick.simulate_kick(
                taker2, self.team1_gk,
                is_shootout=True, shootout_round=current_round
            )
            
            if outcome2 == PenaltyKick.OUTCOME_GOAL:
                team2_score += 1
            
            kicks.append({
                "round": current_round,
                "team_id": self.team2_id,
                **details2
            })
            
            events.append({
                "minute": 120,
                "second": round_idx * 2 + 1,
                "token": details2["kicker_id"],
                "team_id": self.team2_id,
                "action_id": 14 if outcome2 == PenaltyKick.OUTCOME_GOAL else 15,
                "description": f"Penalty {'SCORED' if outcome2 == PenaltyKick.OUTCOME_GOAL else outcome2.upper()} by {details2['kicker_name']}"
            })
            
            # Check for early termination
            remaining = 5 - current_round
            if team1_score > team2_score + remaining:
                break  # Team 1 wins mathematically
            if team2_score > team1_score + remaining:
                break  # Team 2 wins mathematically
        
        # Sudden death if still tied
        while team1_score == team2_score:
            current_round += 1
            
            # Team 1 kicks
            taker1_idx = (current_round - 1) % len(self.team1_takers)
            taker1 = self.team1_takers[taker1_idx]
            outcome1, details1 = PenaltyKick.simulate_kick(
                taker1, self.team2_gk,
                is_shootout=True, shootout_round=current_round
            )
            
            if outcome1 == PenaltyKick.OUTCOME_GOAL:
                team1_score += 1
            
            kicks.append({
                "round": current_round,
                "team_id": self.team1_id,
                **details1
            })
            
            events.append({
                "minute": 120,
                "second": (current_round - 1) * 2,
                "token": details1["kicker_id"],
                "team_id": self.team1_id,
                "action_id": 14 if outcome1 == PenaltyKick.OUTCOME_GOAL else 15,
                "description": f"Sudden death: {'SCORED' if outcome1 == PenaltyKick.OUTCOME_GOAL else outcome1.upper()} by {details1['kicker_name']}"
            })
            
            # Team 2 kicks
            taker2_idx = (current_round - 1) % len(self.team2_takers)
            taker2 = self.team2_takers[taker2_idx]
            outcome2, details2 = PenaltyKick.simulate_kick(
                taker2, self.team1_gk,
                is_shootout=True, shootout_round=current_round
            )
            
            if outcome2 == PenaltyKick.OUTCOME_GOAL:
                team2_score += 1
            
            kicks.append({
                "round": current_round,
                "team_id": self.team2_id,
                **details2
            })
            
            events.append({
                "minute": 120,
                "second": (current_round - 1) * 2 + 1,
                "token": details2["kicker_id"],
                "team_id": self.team2_id,
                "action_id": 14 if outcome2 == PenaltyKick.OUTCOME_GOAL else 15,
                "description": f"Sudden death: {'SCORED' if outcome2 == PenaltyKick.OUTCOME_GOAL else outcome2.upper()} by {details2['kicker_name']}"
            })
            
            # Safety valve - prevent infinite loops
            if current_round > 20:
                logger.warning("Shootout exceeded 20 rounds - forcing winner")
                if random.random() < 0.5:
                    team1_score += 1
                else:
                    team2_score += 1
        
        # Determine winner
        winner_id = self.team1_id if team1_score > team2_score else self.team2_id
        
        return {
            "winner_id": winner_id,
            "team1_score": team1_score,
            "team2_score": team2_score,
            "total_rounds": current_round,
            "kicks": kicks,
            "events": events
        }


class InGamePenalty:
    """
    Handles in-game penalty situations (fouls in the box).
    """
    
    # Probability of penalty being awarded given a dangerous situation in the box
    # In real football, ~0.4 penalties per game on average
    PENALTY_BASE_PROBABILITY = 0.025  # Per dangerous attack in the box
    
    # Factors that increase penalty probability
    DANGER_LEVEL_MULTIPLIERS = {
        4: 0.8,   # Level 4 attack - reduced chance
        5: 1.5    # Level 5 attack - increased chance
    }
    
    @classmethod
    def check_penalty_awarded(
        cls,
        danger_level: int,
        attack_rating: float,
        defense_rating: float,
        defender_aggression: float = 50
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Check if a penalty should be awarded during an attack.
        
        Args:
            danger_level: Attack danger level (4 or 5 for penalty consideration)
            attack_rating: Attacking team's zone rating
            defense_rating: Defending team's zone rating
            defender_aggression: Average aggression of defenders (affects foul likelihood)
            
        Returns:
            Tuple of (penalty_awarded: bool, foul_details: Optional[Dict])
        """
        # Only level 4-5 attacks can result in penalties
        if danger_level < 4:
            return False, None
        
        # Base probability
        prob = cls.PENALTY_BASE_PROBABILITY
        
        # Apply danger level multiplier
        prob *= cls.DANGER_LEVEL_MULTIPLIERS.get(danger_level, 1.0)
        
        # Higher attack rating = more likely to get into penalty situations
        prob *= (attack_rating / 50)  # Normalize around 50
        
        # Higher defender aggression = more likely to foul
        prob *= (defender_aggression / 50)
        
        # Clamp probability
        prob = min(0.15, prob)  # Max 15% per dangerous attack
        
        # Roll for penalty
        if random.random() < prob:
            foul_details = {
                "danger_level": danger_level,
                "probability_used": round(prob, 4)
            }
            return True, foul_details
        
        return False, None
    
    @classmethod
    def select_penalty_taker(cls, team_players: list) -> Dict:
        """
        Select the best penalty taker from the team.
        
        Args:
            team_players: List of team players
            
        Returns:
            Best penalty taker
        """
        # Filter out goalkeeper
        outfield = [p for p in team_players if p.get("position") != "GK"]
        
        if not outfield:
            outfield = team_players
        
        # Find best penalty taker
        best_taker = max(
            outfield,
            key=lambda p: PenaltyKick.calculate_kicker_score(p)
        )
        
        return best_taker
    
    @classmethod
    def simulate_in_game_penalty(
        cls,
        attacking_team_players: list,
        defending_goalkeeper: Dict,
        minute: int
    ) -> Tuple[bool, Dict]:
        """
        Simulate an in-game penalty kick.
        
        Args:
            attacking_team_players: List of attacking team players
            defending_goalkeeper: Defending team's goalkeeper
            minute: Current match minute
            
        Returns:
            Tuple of (goal_scored: bool, details: Dict)
        """
        # Select penalty taker
        taker = cls.select_penalty_taker(attacking_team_players)
        
        # Calculate pressure factor based on match situation
        # Late game penalties are more pressured
        if minute >= 85:
            pressure_factor = 1.2
        elif minute >= 75:
            pressure_factor = 1.1
        else:
            pressure_factor = 1.0
        
        # Simulate the kick
        outcome, details = PenaltyKick.simulate_kick(
            taker,
            defending_goalkeeper,
            pressure_factor=pressure_factor,
            is_shootout=False
        )
        
        details["minute"] = minute
        details["is_in_game"] = True
        
        goal_scored = outcome == PenaltyKick.OUTCOME_GOAL
        
        return goal_scored, details
