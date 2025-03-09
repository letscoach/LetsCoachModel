import threading
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
import Helpers.SQL_db as sql_db

import Game.game_hub as game_controller
import Helpers.telegram_manager as telegram


def generate_schedule(league_id, start_date):
    team_leagues = sql_db.select_league_teams(league_id)
    num_teams = len(team_leagues)
    schedule = []

    # Convert start_date string to datetime object
    start_date = datetime.strptime(start_date, "%d.%m.%Y")
    match_day_counter = 0
    # Generate the first round of matches
    for ind, week in enumerate(range(num_teams - 1)):
        date = start_date + timedelta(weeks=week)
        matches_for_day = []
        ind = ind + 1
        # Pair teams for the round-robin
        for i in range(num_teams // 2):
            home, away = team_leagues[i], team_leagues[num_teams - 1 - i]
            match = {
                "league_id": league_id,
                "match_datetime": date,
                "home_team_id": home,
                "away_team_id": away,
                "match_day": ind
            }

            matches_for_day.append(match)
            match_day_counter = ind

        # Add matches for this day to the schedule
        schedule.extend(matches_for_day)

        # Rotate teams for the next week, excluding the first team
        team_leagues = [team_leagues[0]] + team_leagues[-1:] + team_leagues[1:-1]

    #TODO: TIKO : i think this is the problem..JUST ADD THIS ROW
    # match_day_counter +=1
    # TODO: END ------TIKO : i think this is the problem..
    # Generate the second round (reverse home and guest)
    for week in range(num_teams - 1):
        date = start_date + timedelta(weeks=(week + num_teams - 1))
        matches_for_day = []

        # Pair teams again in reverse (guest becomes host and vice versa)
        for i in range(num_teams // 2):
            home, away = team_leagues[num_teams - 1 - i], team_leagues[i]
            match = {
                "league_id": league_id,
                "match_datetime": date,
                "home_team_id": home,
                "away_team_id": away,
                "match_day": match_day_counter
            }

            matches_for_day.append(match)

        match_day_counter = match_day_counter + 1
        # Add matches for this day to the schedule
        schedule.extend(matches_for_day)

        # Rotate teams for the next week in the second round
        team_leagues = [team_leagues[0]] + team_leagues[-1:] + team_leagues[1:-1]

    # Insert matches into the database
    sql_db.insert_init_matches(schedule)

from datetime import datetime, timedelta

def generate_schedule_single_round(league_id, start_date):
    # 1) Fetch teams from your DB
    telegram.send_log_message(f'Starting to build your league! date : {start_date}')

    team_leagues = sql_db.select_league_teams(league_id)
    num_teams = len(team_leagues)

    # 2) Convert start_date string to datetime object
    start_dt = datetime.strptime(start_date, "%d.%m.%Y")

    schedule = []
    # We'll have (num_teams - 1) rounds in a single round-robin
    for round_idx in range(num_teams - 1):
        # Calculate the date for this round (e.g., each round 1 week apart)
        round_date = start_dt + timedelta(weeks=round_idx)

        matches_for_round = []
        # 3) Generate pairings for the day:
        for i in range(num_teams // 2):
            # Optionally alternate home/away based on the parity of (round_idx + i)
            if (round_idx + i) % 2 == 0:
                home_team = team_leagues[i]
                away_team = team_leagues[num_teams - 1 - i]
            else:
                home_team = team_leagues[num_teams - 1 - i]
                away_team = team_leagues[i]

            match = {
                "league_id": league_id,
                "match_datetime": round_date,
                "home_team_id": home_team,
                "away_team_id": away_team,
                "match_day": round_idx + 1  # 1-based matchday numbering
            }
            matches_for_round.append(match)

        # 4) Add this round’s matches to the master schedule
        schedule.extend(matches_for_round)

        # 5) Rotate teams for the next round (keeping the first team in place)
        # Circle method: T[0], T[n-1], T[1], T[2], …, T[n-2]
        team_leagues = [team_leagues[0]] + [team_leagues[-1]] + team_leagues[1:-1]

    # 6) Insert matches into the DB
    league_msg = 'League Table:\n'
    for i in schedule:
        league_msg += 'Round {match_day} | {match_datetime} | {home_team_id} vs {away_team_id}\n'.format(**i)
    telegram.send_log_message(f'{league_msg}')
    sql_db.insert_init_matches(schedule)
    telegram.send_log_message(f'Scheduling insert successfully! : {start_date}')

    return schedule


# generate_schedule_single_round(1, '26.02.2025')


def game_launcher(match):
    game_processor = game_controller.GameProcessor(match['match_id'])
    output = game_processor.init_game(match['home_team_id'], match['away_team_id'])
    telegram.send_log_message(f'Match id : {match.get("match_id", "Not Available")} Completed!, Score: {output.get("result",{}).get("team1_score")}'
                              f'-{output.get("result",{}).get("team2_score")}')
# game_launcher(dict(match_id = 169,home_team_id=67,away_team_id=68  ))

def get_current_matches():
    telegram.send_log_message('Start to scan daily games..')
    matches_lst = sql_db.get_current_matches()
    for match in matches_lst:
        telegram.send_log_message(f'Here we go, new game : {match.get("match_id","Not Avilable")} starting now!!')
        game_launcher(match)
        try:
            pass
        except Exception as e:
            telegram.send_log_message(f'Error with game {match.get("match_id","Not Avilable")}: {e}' )

        # thread = threading.Thread(target=game_launcher, args=(match,))
        # thread.start()

#get_current_matches()
