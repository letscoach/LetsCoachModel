#!/usr/bin/env python
"""
Helper script to run a single match from LetsCoachModel
This is called by Backend via subprocess to avoid credential initialization issues
Uses Backend's established database connection
"""
import sys
sys.path.append('c:/Users/gideo/Documents/GitHub/LetsCoachBackend')
import json
import os
import pymysql
import backend.SQL_db as db

def connect_to_database():
    """Establish a connection to the database."""
    connection = pymysql.connect(
        host='127.0.0.1',
        user='me',
        password='Ab123456',
        database='main_game',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

def fetch_match_data(match_id):
    """Fetch match data from the database."""
    connection = connect_to_database()
    try:
        with connection.cursor() as cursor:
            query = "SELECT * FROM matches WHERE match_id = %s"
            cursor.execute(query, (match_id,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"No match found with match_id: {match_id}")
            return result
    finally:
        connection.close()

def fetch_next_match():
    """Fetch the next match from the database."""
    query = "SELECT * FROM matches WHERE status = 'pending' ORDER BY match_date ASC LIMIT 1"
    result = db.exec_select_query(query)
    if not result:
        raise ValueError("No pending matches found in the database.")
    return result[0]

def main():
    """
    Run the next match from the database.
    """
    try:
        match_data = fetch_next_match()

        from Game.game_hub import GameProcessor

        match_id = match_data['match_id']
        home_team_id = match_data['home_team_id']
        away_team_id = match_data['away_team_id']
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
