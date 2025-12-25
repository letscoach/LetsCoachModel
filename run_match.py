#!/usr/bin/env python
"""
Helper script to run a single match from LetsCoachModel
This is called by Backend via subprocess to avoid credential initialization issues
Uses Backend's established database connection
"""
import sys
import json
import os

def main():
    """
    Expected argument: JSON string with match data
    Example: python run_match.py '{"match_id": 1, "home_team_id": 10, "away_team_id": 20, "kind": "league"}'
    """
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No match data provided"}))
        sys.exit(1)
    
    try:
        match_data = json.loads(sys.argv[1])
        
        # Don't import game_launcher - just manually run the game here
        # This avoids credential issues
        from Game.game_hub import GameProcessor
        
        # Create processor and run game
        match_id = match_data.get('match_id')
        home_team_id = match_data.get('home_team_id')
        away_team_id = match_data.get('away_team_id')
        match_kind = match_data.get('kind', 'league')
        
        processor = GameProcessor(match_id, match_kind)
        result = processor.init_game(home_team_id, away_team_id)
        
        print(json.dumps({"success": True, "result": result}))
        sys.exit(0)
    except Exception as e:
        error_msg = str(e)
        import traceback
        error_details = traceback.format_exc()
        print(json.dumps({
            "success": False,
            "error": error_msg,
            "details": error_details
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
