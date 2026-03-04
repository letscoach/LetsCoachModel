"""
Test script for penalty kick functionality.
"""

import sys
sys.path.insert(0, '.')

from Game.penalty_kick import PenaltyKick, InGamePenalty, PenaltyShootoutSimulator
import random

def test_single_penalty():
    """Test a single penalty kick simulation."""
    print("=== Testing Single Penalty Kick ===")
    
    # Create mock players
    kicker = {
        "player_id": "player_1",
        "name": "Test Striker",
        "position": "Striker",
        "properties": {
            "Shoot_Precision": 75,
            "Shoot_Power": 70,
            "Finishing": 80,
            "Satisfaction": 85,
            "Freshness": 90
        }
    }
    
    goalkeeper = {
        "player_id": "player_gk",
        "name": "Test Goalkeeper",
        "position": "GK",
        "properties": {
            "Reflexes": 70,
            "Diving": 65,
            "Game_Vision": 60,
            "Satisfaction": 80,
            "Freshness": 85
        }
    }
    
    # Simulate 100 penalties
    goals = 0
    saved = 0
    missed = 0
    
    for _ in range(100):
        outcome, details = PenaltyKick.simulate_kick(kicker, goalkeeper)
        if outcome == PenaltyKick.OUTCOME_GOAL:
            goals += 1
        elif outcome == PenaltyKick.OUTCOME_SAVED:
            saved += 1
        else:
            missed += 1
    
    print(f"Results over 100 penalties:")
    print(f"  Goals: {goals}%")
    print(f"  Saved: {saved}%")
    print(f"  Missed: {missed}%")
    print(f"  Conversion rate: {goals}%")
    print(f"  Expected: ~76% (realistic penalty conversion rate)")
    print()


def test_penalty_check():
    """Test in-game penalty check."""
    print("=== Testing In-Game Penalty Check ===")
    
    # Simulate 1000 dangerous attacks
    penalties_awarded = 0
    
    for _ in range(1000):
        # Level 4 attack
        awarded, _ = InGamePenalty.check_penalty_awarded(
            danger_level=4,
            attack_rating=60,
            defense_rating=50,
            defender_aggression=60
        )
        if awarded:
            penalties_awarded += 1
    
    print(f"Penalties awarded in 1000 dangerous attacks: {penalties_awarded}")
    print(f"Rate: {penalties_awarded/10:.1f}%")
    print(f"Expected: ~2-5% (realistic in-game penalty rate)")
    print()


def test_penalty_shootout():
    """Test full penalty shootout."""
    print("=== Testing Full Penalty Shootout ===")
    
    # Create mock teams
    team1_players = []
    team2_players = []
    
    for i in range(11):
        team1_players.append({
            "player_id": f"t1_p{i}",
            "name": f"Team1 Player {i}",
            "position": "GK" if i == 0 else "Midfielder",
            "properties": {
                "Shoot_Precision": 60 + random.randint(0, 30),
                "Shoot_Power": 55 + random.randint(0, 30),
                "Finishing": 50 + random.randint(0, 30),
                "Satisfaction": 70 + random.randint(0, 20),
                "Freshness": 60 + random.randint(0, 30),
                "Reflexes": 65 + random.randint(0, 30) if i == 0 else 40,
                "Diving": 60 + random.randint(0, 30) if i == 0 else 40,
                "Game_Vision": 55 + random.randint(0, 30)
            }
        })
        
        team2_players.append({
            "player_id": f"t2_p{i}",
            "name": f"Team2 Player {i}",
            "position": "GK" if i == 0 else "Midfielder",
            "properties": {
                "Shoot_Precision": 60 + random.randint(0, 30),
                "Shoot_Power": 55 + random.randint(0, 30),
                "Finishing": 50 + random.randint(0, 30),
                "Satisfaction": 70 + random.randint(0, 20),
                "Freshness": 60 + random.randint(0, 30),
                "Reflexes": 65 + random.randint(0, 30) if i == 0 else 40,
                "Diving": 60 + random.randint(0, 30) if i == 0 else 40,
                "Game_Vision": 55 + random.randint(0, 30)
            }
        })
    
    simulator = PenaltyShootoutSimulator(
        team1_players, team2_players,
        "team1", "team2"
    )
    
    result = simulator.simulate()
    
    print(f"Shootout result: Team1 {result['team1_score']} - {result['team2_score']} Team2")
    print(f"Winner: {result['winner_id']}")
    print(f"Total rounds: {result['total_rounds']}")
    print(f"Total kicks: {len(result['kicks'])}")
    print()
    
    # Print kick details
    print("Kick-by-kick:")
    for kick in result['kicks'][:10]:  # First 10 kicks
        outcome_str = "⚽" if kick['outcome'] == 'goal' else "❌"
        print(f"  Round {kick['round']}: {kick['kicker_name']} - {outcome_str} ({kick['outcome']})")
    
    if len(result['kicks']) > 10:
        print(f"  ... and {len(result['kicks']) - 10} more kicks")


if __name__ == "__main__":
    print("🎯 PENALTY KICK MODULE TEST\n")
    
    test_single_penalty()
    test_penalty_check()
    test_penalty_shootout()
    
    print("\n✅ All tests completed!")
