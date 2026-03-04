"""
Script to add penalty check to samrt_game.py in all relevant locations.
"""

def update_file():
    with open("Game/samrt_game.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # The pattern we need to replace (the shot attempt log)
    old_pattern = '''                if attacker:
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
                                                                              attacker["player_id"]].get("shots", 0) + 1'''

    new_pattern = '''                if attacker:
                    # Check for penalty first
                    penalty_occurred, pen_goal, pen_score = self._check_and_simulate_penalty(
                        danger_level, attack_rating, defense_rating,
                        defending_players, attacking_players, defending_team_id,
                        attacking_team_id, defense_zone, defending_formation,
                        minute, second, player_performances, attacker
                    )
                    
                    if penalty_occurred:
                        if attacking_team_id == team1_id:
                            team1_score += pen_score
                        else:
                            team2_score += pen_score
                        continue  # Skip normal shot logic

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
                                                                              attacker["player_id"]].get("shots", 0) + 1'''
    
    # Count occurrences
    count = content.count(old_pattern)
    print(f"Found {count} occurrences of the pattern")
    
    # Replace all occurrences
    new_content = content.replace(old_pattern, new_pattern)
    
    # Write back
    with open("Game/samrt_game.py", "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Replaced {count} occurrences")

if __name__ == "__main__":
    update_file()
