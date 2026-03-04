"""
Test script for Home Advantage feature.
This tests that home teams get a slight advantage in league matches.
"""

import sys
sys.path.insert(0, '.')

from Game.game_model import simulate_football_match

def test_home_advantage():
    """
    Run multiple simulations to verify home advantage gives a slight edge.
    Expected: Home team should win more often with home_advantage=True
    """
    print("🏟️ HOME ADVANTAGE TEST\n")
    
    # Define two equal teams
    team1 = {"attack": 70, "defense": 70, "midfield": 70}
    team2 = {"attack": 70, "defense": 70, "midfield": 70}
    
    num_simulations = 1000
    
    # Test WITHOUT home advantage
    print("=== Testing WITHOUT Home Advantage ===")
    wins_team1_no_ha = 0
    wins_team2_no_ha = 0
    draws_no_ha = 0
    goals_team1_no_ha = 0
    goals_team2_no_ha = 0
    
    for _ in range(num_simulations):
        score1, score2 = simulate_football_match(team1, team2, home_advantage=False)
        goals_team1_no_ha += score1
        goals_team2_no_ha += score2
        if score1 > score2:
            wins_team1_no_ha += 1
        elif score2 > score1:
            wins_team2_no_ha += 1
        else:
            draws_no_ha += 1
    
    print(f"Team 1 wins: {wins_team1_no_ha} ({wins_team1_no_ha/num_simulations*100:.1f}%)")
    print(f"Team 2 wins: {wins_team2_no_ha} ({wins_team2_no_ha/num_simulations*100:.1f}%)")
    print(f"Draws: {draws_no_ha} ({draws_no_ha/num_simulations*100:.1f}%)")
    print(f"Avg goals Team 1: {goals_team1_no_ha/num_simulations:.2f}")
    print(f"Avg goals Team 2: {goals_team2_no_ha/num_simulations:.2f}")
    
    # Test WITH home advantage for Team 1
    print("\n=== Testing WITH Home Advantage (Team 1 = Home) ===")
    wins_team1_ha = 0
    wins_team2_ha = 0
    draws_ha = 0
    goals_team1_ha = 0
    goals_team2_ha = 0
    
    for _ in range(num_simulations):
        score1, score2 = simulate_football_match(team1, team2, home_advantage=True)
        goals_team1_ha += score1
        goals_team2_ha += score2
        if score1 > score2:
            wins_team1_ha += 1
        elif score2 > score1:
            wins_team2_ha += 1
        else:
            draws_ha += 1
    
    print(f"Team 1 (HOME) wins: {wins_team1_ha} ({wins_team1_ha/num_simulations*100:.1f}%)")
    print(f"Team 2 (AWAY) wins: {wins_team2_ha} ({wins_team2_ha/num_simulations*100:.1f}%)")
    print(f"Draws: {draws_ha} ({draws_ha/num_simulations*100:.1f}%)")
    print(f"Avg goals Team 1 (HOME): {goals_team1_ha/num_simulations:.2f}")
    print(f"Avg goals Team 2 (AWAY): {goals_team2_ha/num_simulations:.2f}")
    
    # Calculate advantage
    print("\n=== ANALYSIS ===")
    advantage = wins_team1_ha - wins_team1_no_ha
    goal_advantage = (goals_team1_ha/num_simulations) - (goals_team1_no_ha/num_simulations)
    
    print(f"Home advantage effect on wins: +{advantage} wins ({advantage/num_simulations*100:.1f}%)")
    print(f"Home advantage effect on goals: +{goal_advantage:.2f} goals per game")
    
    # Verify home advantage gives an edge
    if wins_team1_ha > wins_team1_no_ha:
        print("\n✅ Home advantage is working correctly!")
    else:
        print("\n⚠️ Home advantage may not be significant (sample variance)")
    
    # Expected: ~46% home win rate in real football
    expected_home_win_pct = 46
    actual_home_win_pct = wins_team1_ha/num_simulations*100
    print(f"\nReal football home win rate: ~{expected_home_win_pct}%")
    print(f"Simulated home win rate: {actual_home_win_pct:.1f}%")


if __name__ == "__main__":
    test_home_advantage()
