import threading
from datetime import datetime, timedelta, timezone

from firebase_admin import firestore
import Helpers.SQL_db as sql_db

import Game.game_hub as game_controller
import Helpers.telegram_manager as telegram
from Helpers.google_cloud_helpers import create_task_for_match


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

    # Insert matches into the database with kind=1 (League)
    for match in schedule:
        match['kind'] = 1
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
    
    # Add kind=1 (League) to all matches
    for match in schedule:
        match['kind'] = 1
    
    sql_db.insert_init_matches(schedule)
    # for sc in schedule:
    #     create_task_for_match(sc)
    telegram.send_log_message(f'Scheduling insert successfully! : {start_date}')

    return schedule


# generate_schedule_single_round(1, '26.02.2025')


def game_launcher(match):
    telegram.send_log_message("1.launch game now")
    game_processor = game_controller.GameProcessor(match['match_id'], match['kind'])
    output = game_processor.init_game(match['home_team_id'], match['away_team_id'])
    telegram.send_log_message(f'Match id : {match.get("match_id", "Not Available")} Completed!, Score: {output.get("result",{}).get("team1_score")}'
                              f'-{output.get("result",{}).get("team2_score")}')
    return output
# game_launcher(dict(match_id = 169,home_team_id=67,away_team_id=68  ))

def get_current_matches():
    telegram.send_log_message('Start to scan daily games..')
    matches_lst = sql_db.get_current_matches()
    for match in matches_lst:
        # Check if friendly match has no opponent
        if match.get("away_team_id") is None:
            telegram.send_log_message(f'Cancelling friendly match {match.get("match_id")} - No opponent found.')
            sql_db.cancel_match(match.get("match_id"))
            continue

        telegram.send_log_message(f'Here we go, new game : {match.get("match_id","Not Avilable")} starting now!!')
        game_launcher(match)
        try:
            pass
        except Exception as e:
            telegram.send_log_message(f'Error with game {match.get("match_id","Not Avilable")}: {e}' )

        # thread = threading.Thread(target=game_launcher, args=(match,))
        # thread.start()

#get_current_matches()
def generate_schedule_double_round(league_id, start_date, start_time_gmt, days_between_matchdays=7,
                                   match_times_in_round=None):
    """
    Generates a double-round (home & away) schedule with flexible match timing.

    :param league_id: ID of the league for which schedule is generated
    :param start_date: "dd.mm.yyyy" string for the first matchday
    :param start_time_gmt: Starting time in GMT as "HH:MM" or float hour
    :param days_between_matchdays: number of days between consecutive matchdays
    :param match_times_in_round: Optional list of times (in "HH:MM" or float) for matches in a round
                                  If None, all matches in a round are scheduled at the same time
    :return: Combined schedule of both rounds
    """

    # Helper function to convert time to hours and minutes
    def parse_time(time_input):
        if isinstance(time_input, (int, float)):
            # If it's a number, treat it as hours
            hours = int(time_input)
            minutes = int((time_input - hours) * 60)
            return hours, minutes
        elif isinstance(time_input, str):
            # If it's a string in "HH:MM" format
            hours, minutes = map(int, time_input.split(':'))
            return hours, minutes
        else:
            raise ValueError("Invalid time format. Use 'HH:MM' or float.")

    # Validate input parameters
    if days_between_matchdays < 0:
        raise ValueError("days_between_matchdays must be non-negative")

    # Parse and validate start time
    start_hours, start_minutes = parse_time(start_time_gmt)
    if not (0 <= start_hours <= 23 and 0 <= start_minutes <= 59):
        raise ValueError("Start time must be between 00:00 and 23:59")

    # Validate match times if provided
    if match_times_in_round is not None:
        parsed_match_times = []
        for time in match_times_in_round:
            hours, minutes = parse_time(time)
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Match times must be between 00:00 and 23:59")
            parsed_match_times.append((hours, minutes))
        match_times_in_round = parsed_match_times

    # 1) Fetch teams from your DB
    telegram.send_log_message(
        f'Starting to build your league! date: {start_date}, GMT time: {start_hours:02d}:{start_minutes:02d}')
    team_leagues = sql_db.select_league_teams(league_id)
    num_teams = len(team_leagues)

    # 2) Convert start_date string to datetime object with specified GMT time
    start_dt = datetime.strptime(start_date, "%d.%m.%Y").replace(
        hour=start_hours,
        minute=start_minutes,
        second=0,
        microsecond=0
    )

    # The single round schedule
    schedule_first_round = []

    # We'll have (num_teams - 1) total matchdays in a single round-robin
    total_matchdays = num_teams - 1

    # ---------------------------
    # Generate the FIRST ROUND
    # ---------------------------
    for round_idx in range(total_matchdays):
        # Calculate the base date for this round
        round_date = start_dt + timedelta(days=round_idx * days_between_matchdays)

        matches_for_round = []

        # Generate pairings for the day:
        for match_idx in range(num_teams // 2):
            # Alternate home/away based on parity
            if (round_idx + match_idx) % 2 == 0:
                home_team = team_leagues[match_idx]
                away_team = team_leagues[num_teams - 1 - match_idx]
            else:
                home_team = team_leagues[num_teams - 1 - match_idx]
                away_team = team_leagues[match_idx]

            # Determine match time
            if match_times_in_round is None:
                # Default: all matches at the same time (start_time_gmt)
                match_datetime = round_date
            else:
                # Use the provided times (cycling if fewer times than matches)
                match_hours, match_minutes = match_times_in_round[match_idx % len(match_times_in_round)]
                match_datetime = round_date.replace(hour=match_hours, minute=match_minutes, second=0, microsecond=0)

            match = {
                "league_id": league_id,
                "match_datetime": match_datetime,
                "home_team_id": home_team,
                "away_team_id": away_team,
                "match_day": round_idx + 1  # 1-based matchday numbering
            }
            matches_for_round.append(match)

        # Collect this round's matches
        schedule_first_round.extend(matches_for_round)

        # Rotate teams for next round (keeping the first team in place)
        # Circle method: T[0], T[n-1], T[1], T[2], …, T[n-2]
        team_leagues = [team_leagues[0]] + [team_leagues[-1]] + team_leagues[1:-1]

    # ---------------------------
    # Generate the SECOND ROUND by reversing the FIRST ROUND
    # ---------------------------
    schedule_second_round = []

    # Offset: how many days to jump after the FIRST ROUND is done
    offset_days = total_matchdays * days_between_matchdays

    for match in schedule_first_round:
        # Create a reversed match
        if match_times_in_round is None:
            # Default: all matches at the same time
            second_round_match_datetime = match['match_datetime'] + timedelta(days=offset_days)
        else:
            # Find the original match's time index
            original_match_idx = schedule_first_round.index(match)
            match_hours, match_minutes = match_times_in_round[original_match_idx % len(match_times_in_round)]
            second_round_match_datetime = (match['match_datetime'] + timedelta(days=offset_days)).replace(
                hour=match_hours, minute=match_minutes, second=0, microsecond=0
            )

        second_round_match = {
            "league_id": match["league_id"],
            "match_datetime": second_round_match_datetime,
            "home_team_id": match["away_team_id"],  # swapped
            "away_team_id": match["home_team_id"],  # swapped
            "match_day": match["match_day"] + total_matchdays
        }
        schedule_second_round.append(second_round_match)

    # Combine both rounds
    full_schedule = schedule_first_round + schedule_second_round

    # Optional: Log schedule for debugging
    league_msg = 'Double Round League Schedule:\n'
    for m in full_schedule:
        dt_str = m['match_datetime'].strftime("%d.%m.%Y %H:%M")
        league_msg += f"Round {m['match_day']} | {dt_str} | {m['home_team_id']} vs {m['away_team_id']}\n"
    telegram.send_log_message(league_msg)

    # Add kind=1 (League) to all matches
    for match in full_schedule:
        match['kind'] = 1
    
    full_schedule = sql_db.insert_init_matches(full_schedule)
    for sc in full_schedule:
        create_task_for_match(sc)

    telegram.send_log_message(f"Scheduling insert successfully! Start date: {start_date}")

    return full_schedule

# generate_schedule_double_round(1,'1.04.2025', '15:30',  3.5)
#get_current_matches()
