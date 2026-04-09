"""
Live Match Simulation Module for Backend API Integration

This module provides the simulation logic that the Backend API calls.
It uses the existing samrt_game.py MatchSimulator but exposes period-based
simulation for real-time live match experience.

Based on PRD v2.0:
- 6-zone field analysis
- 200 attacks per game (~22 per 10-minute period)
- Danger levels 1-5
- Coaching interventions support
"""

import random
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Import existing game logic
from Game.samrt_game import MatchSimulator, SoccerAttackOpportunitySystem
from Game.formation_grader import calculate_team_grades
from Game.penalty_kick import PenaltyShootoutSimulator
import Helpers.SQL_db as db


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS (from PRD)
# ═══════════════════════════════════════════════════════════════════════════════

TOTAL_ATTACKS_PER_MATCH = 200
ATTACKS_PER_PERIOD = 22  # ~200 attacks / 9 periods of 10 min each
MAX_INTERVENTIONS = 3
MAX_SUBSTITUTIONS = 5

# Danger level distribution (PRD Section 4.2)
DANGER_LEVEL_BASE = {
    1: 0.55,  # Harmless - no duel
    2: 0.20,  # Low risk
    3: 0.15,  # Moderate risk (10% duel chance)
    4: 0.07,  # Dangerous (60% duel chance)
    5: 0.03,  # Critical (100% duel chance)
}

# Zone matchups (PRD Section 2.1)
ZONE_PAIRS = [
    (1, 4),  # Left attack vs Right defense
    (2, 5),  # Middle attack vs Middle defense
    (3, 6),  # Right attack vs Left defense
]

# Attitude modifiers
ATTITUDE_MODIFIERS = {
    'ultra-defensive': {'attack': 0.8, 'defense': 1.2},
    'defensive': {'attack': 0.9, 'defense': 1.1},
    'balanced': {'attack': 1.0, 'defense': 1.0},
    'attacking': {'attack': 1.1, 'defense': 0.9},
    'ultra-attacking': {'attack': 1.2, 'defense': 0.8},
}


class LiveMatchSimulator:
    """
    Handles live match simulation with period-based progression.
    Integrates with the existing MatchSimulator but adds:
    - Period-based simulation (10 min game time = 3 min real time)
    - Intervention support (formation, substitution, attitude changes)
    - Real-time event generation
    """

    def __init__(self):
        self.match_simulator = MatchSimulator()
        self.attack_system = SoccerAttackOpportunitySystem()

    def initialize_match(self, match_id: str, team1_id: str, team2_id: str, 
                         must_win: bool = False) -> Dict:
        """
        Initialize a live match session.
        
        Args:
            match_id: Unique match identifier
            team1_id: Home team ID
            team2_id: Away team ID
            must_win: If True, match goes to extra time/penalties if tied
            
        Returns:
            Initial match state dictionary
        """
        # Get team data from database
        team1_data = self._get_team_data(team1_id)
        team2_data = self._get_team_data(team2_id)
        
        # Calculate zone ratings
        team1_zone_ratings = self._calculate_zone_ratings(
            team1_data['players'], team1_data['formation'])
        team2_zone_ratings = self._calculate_zone_ratings(
            team2_data['players'], team2_data['formation'])
        
        # Initialize match state
        match_state = {
            'match_id': match_id,
            'team1_id': team1_id,
            'team2_id': team2_id,
            'team1_score': 0,
            'team2_score': 0,
            'current_minute': 0,
            'current_period': 0,
            'total_attacks': 0,
            'events': [],
            'interventions_left': MAX_INTERVENTIONS,
            'substitutions_used': {'team1': 0, 'team2': 0},
            'must_win': must_win,
            'extra_time': False,
            'penalties': False,
            'game_over': False,
            'created_at': datetime.now().isoformat(),
            
            # Team data
            'team1_data': team1_data,
            'team2_data': team2_data,
            'team1_formation': team1_data['formation'],
            'team2_formation': team2_data['formation'],
            'team1_attitude': 'balanced',
            'team2_attitude': 'balanced',
            
            # Zone ratings
            'zone_ratings': {
                'team1': team1_zone_ratings,
                'team2': team2_zone_ratings
            },
            
            # Stats
            'stats': {
                'team1': self._init_team_stats(),
                'team2': self._init_team_stats()
            },
            
            # Player fatigue
            'player_fatigue': {},
            
            # Player performances
            'player_performances': self._initialize_player_performances(
                team1_data['players'], team2_data['players']
            )
        }
        
        return match_state

    def simulate_period(self, match_state: Dict, period_minutes: int = 10) -> Dict:
        """
        Simulate the next period of the match.
        
        Args:
            match_state: Current match state
            period_minutes: Duration of period in game minutes (default 10)
            
        Returns:
            Dictionary with period events and updated state
        """
        if match_state['game_over']:
            return {
                'status': 'game_over',
                'events': [],
                'scores': {
                    'team1': match_state['team1_score'],
                    'team2': match_state['team2_score']
                }
            }
        
        start_minute = match_state['current_minute']
        end_minute = start_minute + period_minutes
        
        # Check for end of regular/extra time
        if not match_state['extra_time']:
            end_minute = min(end_minute, 90)
        else:
            end_minute = min(end_minute, 120)
        
        actual_period_minutes = end_minute - start_minute
        
        # Calculate attacks for this period
        num_attacks = int(ATTACKS_PER_PERIOD * (actual_period_minutes / 10))
        
        # Simulate attacks
        period_events = self._simulate_attacks(
            match_state, num_attacks, start_minute, end_minute)
        
        # Update state
        match_state['events'].extend(period_events)
        match_state['total_attacks'] += num_attacks
        match_state['current_minute'] = end_minute
        match_state['current_period'] += 1
        
        # Update fatigue
        self._update_fatigue(match_state, actual_period_minutes)
        
        # Check for end of match
        if end_minute >= 90 and not match_state['extra_time']:
            if match_state['must_win'] and match_state['team1_score'] == match_state['team2_score']:
                match_state['extra_time'] = True
            else:
                match_state['game_over'] = True
        elif end_minute >= 120 and match_state['extra_time']:
            if match_state['team1_score'] == match_state['team2_score']:
                match_state['penalties'] = True
            match_state['game_over'] = True
        
        return {
            'status': 'in_progress' if not match_state['game_over'] else 'game_over',
            'events': period_events,
            'current_minute': match_state['current_minute'],
            'current_period': match_state['current_period'],
            'scores': {
                'team1': match_state['team1_score'],
                'team2': match_state['team2_score']
            },
            'stats': match_state['stats'],
            'extra_time': match_state['extra_time'],
            'penalties': match_state['penalties'],
            'game_over': match_state['game_over']
        }

    def process_intervention(self, match_state: Dict, team_id: str, 
                            action_type: str, action_data: Dict) -> Dict:
        """
        Process a coaching intervention.
        
        Args:
            match_state: Current match state
            team_id: ID of the team making the intervention
            action_type: 'substitution', 'formation', or 'attitude'
            action_data: Intervention-specific data
            
        Returns:
            Result of the intervention
        """
        if match_state['interventions_left'] <= 0:
            return {'success': False, 'error': 'No interventions remaining'}
        
        team_key = 'team1' if team_id == match_state['team1_id'] else 'team2'
        events = []
        
        if action_type == 'substitution':
            result = self._process_substitution(match_state, team_key, action_data)
            events = result.get('events', [])
            
        elif action_type == 'formation':
            result = self._process_formation_change(match_state, team_key, action_data)
            events = result.get('events', [])
            
        elif action_type == 'attitude':
            result = self._process_attitude_change(match_state, team_key, action_data)
            events = result.get('events', [])
        
        # Consume intervention
        match_state['interventions_left'] -= 1
        match_state['events'].extend(events)
        
        return {
            'success': True,
            'interventions_left': match_state['interventions_left'],
            'events': events,
            'zone_ratings': match_state['zone_ratings'][team_key]
        }

    def simulate_penalty_shootout(self, match_state: Dict) -> Dict:
        """
        Simulate penalty shootout if match ended in draw with must_win=True.
        
        Args:
            match_state: Current match state
            
        Returns:
            Penalty shootout results
        """
        team1_players = match_state['team1_data']['players']
        team2_players = match_state['team2_data']['players']
        
        simulator = PenaltyShootoutSimulator(
            team1_players, team2_players,
            match_state['team1_id'], match_state['team2_id']
        )
        
        result = simulator.simulate()
        
        # Update match state
        match_state['events'].extend(result['events'])
        
        return {
            'team1_penalties': result['team1_score'],
            'team2_penalties': result['team2_score'],
            'winner_id': result['winner_id'],
            'events': result['events']
        }

    def finalize_match(self, match_state: Dict) -> Dict:
        """
        Finalize match and save results to database.
        
        Args:
            match_state: Final match state
            
        Returns:
            Final match results
        """
        match_id = match_state['match_id']
        team1_score = match_state['team1_score']
        team2_score = match_state['team2_score']
        
        # Generate player stories
        player_stories = self._generate_player_stories(match_state)
        
        # Determine man of the match
        man_of_the_match = self._determine_man_of_the_match(player_stories)
        
        # Save to database
        try:
            db.insert_match_details(match_id, match_state['events'])
            db.update_matche_result(
                match_id, 
                f"{team1_score}-{team2_score}", 
                match_state['current_minute']
            )
            if man_of_the_match:
                db.insert_man_of_the_match(man_of_the_match, match_id)
            saved_to_db = True
        except Exception as e:
            print(f"Error saving to database: {e}")
            saved_to_db = False
        
        return {
            'final_score': {
                'team1': team1_score,
                'team2': team2_score
            },
            'stats': match_state['stats'],
            'player_stories': player_stories,
            'man_of_the_match': man_of_the_match,
            'total_events': len(match_state['events']),
            'saved_to_db': saved_to_db
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    def _get_team_data(self, team_id: str) -> Dict:
        """Get team data from database"""
        try:
            formation_data = db.get_team_formation(team_id)
            players = db.get_team_players_with_properties(team_id)
            
            return {
                'team_id': team_id,
                'formation': formation_data.get('formation', '4-3-3'),
                'players': players if players else [],
                'captain_id': formation_data.get('captain_token'),
            }
        except Exception as e:
            print(f"Error getting team data: {e}")
            return {
                'team_id': team_id,
                'formation': '4-3-3',
                'players': [],
                'captain_id': None,
            }

    def _calculate_zone_ratings(self, players: List, formation: str) -> Dict:
        """Calculate zone ratings for a team"""
        ratings = {}
        
        for zone in range(1, 7):
            ratings[zone] = self.attack_system.calculate_zone_attack_opportunity(
                players, formation, zone
            )
        
        # Ensure minimum rating
        for zone in ratings:
            ratings[zone] = max(30, min(90, ratings[zone]))
        
        return ratings

    def _init_team_stats(self) -> Dict:
        """Initialize team statistics"""
        return {
            'possession': 50,
            'shots': 0,
            'shots_on_target': 0,
            'fouls': 0,
            'corners': 0,
            'yellow_cards': 0,
            'red_cards': 0,
            'passes': 0,
        }

    def _initialize_player_performances(self, team1_players: List, 
                                         team2_players: List) -> Dict:
        """Initialize performance tracking for all players"""
        performances = {}
        
        for player in team1_players + team2_players:
            player_id = player.get('player_id') or player.get('id')
            if player_id:
                performances[player_id] = {
                    'player_id': player_id,
                    'team_id': player.get('team_id'),
                    'scored_goal': 0,
                    'assist': 0,
                    'defense_action': 0,
                    'shots': 0,
                    'yellow_cards': 0,
                    'red_cards': 0,
                }
        
        return performances

    def _simulate_attacks(self, match_state: Dict, num_attacks: int,
                          start_minute: int, end_minute: int) -> List:
        """Simulate a batch of attacks"""
        events = []
        
        team1_id = match_state['team1_id']
        team2_id = match_state['team2_id']
        
        # Calculate possession
        team1_mid = match_state['zone_ratings']['team1'].get(2, 50)
        team2_mid = match_state['zone_ratings']['team2'].get(2, 50)
        
        # Apply attitude modifiers
        team1_att_mod = ATTITUDE_MODIFIERS.get(
            match_state['team1_attitude'], {'attack': 1, 'defense': 1})
        team2_att_mod = ATTITUDE_MODIFIERS.get(
            match_state['team2_attitude'], {'attack': 1, 'defense': 1})
        
        team1_possession = team1_mid / (team1_mid + team2_mid)
        
        for i in range(num_attacks):
            # Determine attacking team
            if random.random() < team1_possession:
                attacking = 'team1'
                defending = 'team2'
                attacking_id = team1_id
                defending_id = team2_id
                att_mod = team1_att_mod
                def_mod = team2_att_mod
            else:
                attacking = 'team2'
                defending = 'team1'
                attacking_id = team2_id
                defending_id = team1_id
                att_mod = team2_att_mod
                def_mod = team1_att_mod
            
            # Choose attack zone
            attack_zone = random.choice([1, 2, 3])
            defense_zone = ZONE_PAIRS[attack_zone - 1][1]
            
            # Get modified zone ratings
            attack_rating = match_state['zone_ratings'][attacking][attack_zone] * att_mod['attack']
            defense_rating = match_state['zone_ratings'][defending][defense_zone] * def_mod['defense']
            
            # Calculate danger level
            danger_level = self._get_danger_level(attack_rating, defense_rating)
            
            # Calculate minute for this attack
            attack_minute = start_minute + int((end_minute - start_minute) * i / max(num_attacks, 1))
            
            # Generate event
            event = self._generate_event(
                attack_minute, attacking_id, defending_id,
                attack_zone, danger_level, match_state
            )
            
            if event:
                events.append(event)
                
                # Update scores
                if event['type'] == 'goal':
                    if attacking == 'team1':
                        match_state['team1_score'] += 1
                    else:
                        match_state['team2_score'] += 1
                
                # Update stats
                self._update_stats(match_state['stats'][attacking], event)
        
        return events

    def _get_danger_level(self, attack_rating: float, defense_rating: float) -> int:
        """Determine danger level based on zone matchup"""
        advantage = (attack_rating - defense_rating) / 100
        
        probs = DANGER_LEVEL_BASE.copy()
        if advantage > 0:
            probs[1] = max(0.30, probs[1] - advantage * 0.5)
            probs[4] = min(0.15, probs[4] + advantage * 0.2)
            probs[5] = min(0.10, probs[5] + advantage * 0.15)
        else:
            probs[1] = min(0.70, probs[1] - advantage * 0.5)
            probs[4] = max(0.03, probs[4] + advantage * 0.2)
            probs[5] = max(0.01, probs[5] + advantage * 0.1)
        
        total = sum(probs.values())
        probs = {k: v/total for k, v in probs.items()}
        
        r = random.random()
        cumulative = 0
        for level, prob in sorted(probs.items()):
            cumulative += prob
            if r <= cumulative:
                return level
        return 1

    def _generate_event(self, minute: int, attacking_id: str, defending_id: str,
                        zone: int, danger_level: int, match_state: Dict) -> Optional[Dict]:
        """Generate an event based on attack danger level"""
        event_id = len(match_state['events']) + 1
        team = 'home' if attacking_id == match_state['team1_id'] else 'away'
        
        # Level 1-2: Just possession
        if danger_level <= 2:
            return {
                'id': event_id,
                'minute': minute,
                'type': 'attack',
                'team': team,
                'team_id': attacking_id,
                'zone': zone,
                'danger_level': danger_level,
                'description': f"Building attack in zone {zone}" if danger_level == 2 else f"Possession in zone {zone}",
            }
        
        # Level 3: Shot from distance
        if danger_level == 3:
            if random.random() < 0.10:  # 10% duel
                return self._generate_duel_event(
                    minute, attacking_id, defending_id, zone, danger_level, event_id, match_state)
            return {
                'id': event_id,
                'minute': minute,
                'type': 'shot',
                'team': team,
                'team_id': attacking_id,
                'zone': zone,
                'danger_level': danger_level,
                'description': "Shot from distance — wide!",
            }
        
        # Level 4-5: Dangerous attack
        if danger_level >= 4:
            duel_chance = 0.60 if danger_level == 4 else 1.0
            
            if random.random() < duel_chance:
                duel_event = self._generate_duel_event(
                    minute, attacking_id, defending_id, zone, danger_level, event_id, match_state)
                if duel_event['type'] in ['foul', 'card']:
                    return duel_event
            
            # Goal chance
            goal_prob = 0.15 if danger_level == 4 else 0.40
            
            if random.random() < goal_prob:
                return {
                    'id': event_id,
                    'minute': minute,
                    'type': 'goal',
                    'team': team,
                    'team_id': attacking_id,
                    'zone': zone,
                    'danger_level': danger_level,
                    'description': "⚽ GOAL!" if danger_level == 5 else "⚽ GOAL! Clinical finish!",
                }
            else:
                return {
                    'id': event_id,
                    'minute': minute,
                    'type': 'save',
                    'team': 'home' if defending_id == match_state['team1_id'] else 'away',
                    'team_id': defending_id,
                    'zone': zone,
                    'danger_level': danger_level,
                    'description': "Great save by the keeper!",
                }
        
        return None

    def _generate_duel_event(self, minute: int, attacking_id: str, defending_id: str,
                             zone: int, danger_level: int, event_id: int, 
                             match_state: Dict) -> Dict:
        """Generate duel outcome (fouls, cards)"""
        def_team = 'home' if defending_id == match_state['team1_id'] else 'away'
        
        # Calculate severity (PRD formula)
        severity = (50 + (100 - 60) + (match_state['total_attacks'] / 4)) / 3
        
        if severity > 85:
            return {
                'id': event_id,
                'minute': minute,
                'type': 'card',
                'card_type': 'red',
                'team': def_team,
                'team_id': defending_id,
                'zone': zone,
                'danger_level': danger_level,
                'description': "🟥 RED CARD! Dangerous tackle!",
            }
        
        if severity > 60:
            return {
                'id': event_id,
                'minute': minute,
                'type': 'card',
                'card_type': 'yellow',
                'team': def_team,
                'team_id': defending_id,
                'zone': zone,
                'danger_level': danger_level,
                'description': "🟨 Yellow card — harsh tackle",
            }
        
        if random.random() < 0.4:
            return {
                'id': event_id,
                'minute': minute,
                'type': 'foul',
                'team': def_team,
                'team_id': defending_id,
                'zone': zone,
                'danger_level': danger_level,
                'description': "Foul — free kick awarded",
            }
        
        att_team = 'home' if attacking_id == match_state['team1_id'] else 'away'
        return {
            'id': event_id,
            'minute': minute,
            'type': 'attack',
            'team': att_team,
            'team_id': attacking_id,
            'zone': zone,
            'danger_level': danger_level,
            'description': "Strong challenge — play continues",
        }

    def _update_stats(self, stats: Dict, event: Dict):
        """Update team statistics"""
        if event['type'] == 'shot':
            stats['shots'] += 1
        elif event['type'] == 'goal':
            stats['shots'] += 1
            stats['shots_on_target'] += 1
        elif event['type'] == 'foul':
            stats['fouls'] += 1
        elif event['type'] == 'card':
            if event.get('card_type') == 'yellow':
                stats['yellow_cards'] += 1
            else:
                stats['red_cards'] += 1
        elif event['type'] == 'corner':
            stats['corners'] += 1
        elif event['type'] == 'attack':
            stats['passes'] += 3

    def _update_fatigue(self, match_state: Dict, minutes_played: int):
        """Update player fatigue based on minutes played"""
        fatigue_rate = 0.5  # PRD: -0.5 endurance per attack
        
        for team_key in ['team1', 'team2']:
            players = match_state[f'{team_key}_data'].get('players', [])
            for player in players:
                player_id = player.get('player_id') or player.get('id')
                if player_id:
                    current_fatigue = match_state['player_fatigue'].get(player_id, 0)
                    match_state['player_fatigue'][player_id] = current_fatigue + (fatigue_rate * minutes_played)

    def _process_substitution(self, match_state: Dict, team_key: str, 
                              action_data: Dict) -> Dict:
        """Process substitution intervention"""
        subs = action_data.get('substitutions', [])
        subs_used = match_state['substitutions_used'][team_key]
        
        if subs_used + len(subs) > MAX_SUBSTITUTIONS:
            return {'success': False, 'error': 'Too many substitutions'}
        
        events = []
        for sub in subs:
            event = {
                'id': len(match_state['events']) + len(events) + 1,
                'minute': match_state['current_minute'],
                'type': 'substitution',
                'team': 'home' if team_key == 'team1' else 'away',
                'team_id': match_state[f'{team_key}_id'],
                'zone': 0,
                'danger_level': 0,
                'description': f"🔄 Substitution: {sub.get('out', '?')} ↔ {sub.get('in', '?')}",
                'player_out': sub.get('out'),
                'player_in': sub.get('in'),
            }
            events.append(event)
        
        match_state['substitutions_used'][team_key] += len(subs)
        return {'success': True, 'events': events}

    def _process_formation_change(self, match_state: Dict, team_key: str,
                                   action_data: Dict) -> Dict:
        """Process formation change intervention"""
        new_formation = action_data.get('new_formation')
        if not new_formation:
            return {'success': False, 'error': 'No formation specified'}
        
        old_formation = match_state[f'{team_key}_formation']
        match_state[f'{team_key}_formation'] = new_formation
        
        # Recalculate zone ratings
        players = match_state[f'{team_key}_data'].get('players', [])
        match_state['zone_ratings'][team_key] = self._calculate_zone_ratings(
            players, new_formation)
        
        event = {
            'id': len(match_state['events']) + 1,
            'minute': match_state['current_minute'],
            'type': 'substitution',
            'team': 'home' if team_key == 'team1' else 'away',
            'team_id': match_state[f'{team_key}_id'],
            'zone': 0,
            'danger_level': 0,
            'description': f"📋 Formation changed: {old_formation} → {new_formation}",
        }
        
        return {'success': True, 'events': [event]}

    def _process_attitude_change(self, match_state: Dict, team_key: str,
                                  action_data: Dict) -> Dict:
        """Process attitude change intervention"""
        new_attitude = action_data.get('new_attitude')
        if not new_attitude or new_attitude not in ATTITUDE_MODIFIERS:
            return {'success': False, 'error': 'Invalid attitude'}
        
        old_attitude = match_state[f'{team_key}_attitude']
        match_state[f'{team_key}_attitude'] = new_attitude
        
        event = {
            'id': len(match_state['events']) + 1,
            'minute': match_state['current_minute'],
            'type': 'substitution',
            'team': 'home' if team_key == 'team1' else 'away',
            'team_id': match_state[f'{team_key}_id'],
            'zone': 0,
            'danger_level': 0,
            'description': f"🔥 Attitude changed: {old_attitude} → {new_attitude}",
        }
        
        return {'success': True, 'events': [event]}

    def _generate_player_stories(self, match_state: Dict) -> List:
        """Generate player stories from match events"""
        stories = []
        performances = match_state.get('player_performances', {})
        
        for player_id, perf in performances.items():
            team_won = False
            if perf.get('team_id') == match_state['team1_id']:
                team_won = match_state['team1_score'] > match_state['team2_score']
            else:
                team_won = match_state['team2_score'] > match_state['team1_score']
            
            score = perf.get('scored_goal', 0) * 3 + perf.get('assist', 0) * 2 + \
                    perf.get('defense_action', 0) + (2 if team_won else 0)
            
            stories.append({
                'player_id': player_id,
                'team_won': team_won,
                'overall_score': score,
                'scored_goal': perf.get('scored_goal', 0),
                'assist': perf.get('assist', 0),
                'defense_action': perf.get('defense_action', 0),
            })
        
        return stories

    def _determine_man_of_the_match(self, player_stories: List) -> Optional[str]:
        """Determine man of the match"""
        if not player_stories:
            return None
        
        best = max(player_stories, key=lambda x: x.get('overall_score', 0))
        return best.get('player_id')


# Singleton instance for use by Backend API
live_match_simulator = LiveMatchSimulator()
