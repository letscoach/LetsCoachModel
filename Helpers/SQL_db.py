import os
import json
import time
import logging

import pymysql
from google.cloud.sql.connector import Connector
from Helpers.table_def import tables as DB_TABLES
import Helpers.sql_queries as sql_queries
from datetime import datetime
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

pool = None
connector = None
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

def connect_with_connector():
    """Connect to Google Cloud SQL using Cloud SQL Python Connector"""
    global connector
    
    for attempt in range(MAX_RETRIES):
        try:
            # Initialize Connector if not already
            if connector is None:
                connector = Connector()
            
            # Get connection using Cloud SQL instance connection name
            conn = connector.connect(
                "zinc-strategy-446518-s7:us-central1:letscoach",
                "pymysql",
                user="me",
                password="Ab123456",
                db="main_game",
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ Connected to Google Cloud SQL via Cloud SQL Connector!")
            return conn
        except Exception as e:
            print(f"❌ Error connecting (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print("❌ All connection attempts failed!")
                return None

# Connect using Cloud SQL Connector
print("🔍 Connecting to Google Cloud SQL...")
pool = connect_with_connector()

if pool is None:
    print("❌ Initial connection failed! Will retry on first query.")

def build_insert_query(table_name: str) -> str:
    columns = DB_TABLES[table_name]
    # Create placeholders for values, e.g., "%(col)s" for parameterized queries with dict
    placeholders = ', '.join([f'%({x})s' for x in columns])

    # Format the column names, e.g., "col1, col2, col3"
    columns_str = ', '.join(columns)

    # Build the query
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
    return query


def exec_insert_query(query, params):
    global pool
    try:
        # Reconnect if pool is None
        if pool is None:
            print("⚠️ Pool is None, attempting to reconnect...")
            pool = connect_with_connector()
            if pool is None:
                raise Exception("Failed to connect to database after retries")
        
        # LOGGING REQUESTED BY USER
        print(f"DEBUG exec_insert_query - QUERY: {query}")
        print(f"DEBUG exec_insert_query - PARAMS: {params}")

        with pool.cursor() as db_conn:
            if type(query) is list:
                for ind, quer in enumerate(query):
                    result = db_conn.execute(quer, params[ind])
                    pool.commit()
            else:
                result = db_conn.execute(query, params)
                pool.commit()  # Commit after the insert

            print("Insert successful!")
            return db_conn.lastrowid
    except IntegrityError as e:
        if 'Duplicate entry' in str(e):
            raise Exception(f"Duplicate value")
        else:
            raise Exception(f"An unexpected error occurred: {str(e)}")
    except Exception as e:
        print(f"❌ Error in exec_insert_query: {e}")
        raise e


def exec_select_query(query):
    global pool
    try:
        # Reconnect if pool is None
        if pool is None:
            print("⚠️ Pool is None, attempting to reconnect...")
            pool = connect_with_connector()
            if pool is None:
                raise Exception("Failed to connect to database after retries")
        
        with pool.cursor() as db_conn:
            db_conn.execute(query)
            result = db_conn.fetchall()
            return result
    except Exception as e:
        print(f"❌ Error in exec_select_query: {e}")
        raise e


def exec_update_query(query):
    global pool
    try:
        # Reconnect if pool is None
        if pool is None:
            print("⚠️ Pool is None, attempting to reconnect...")
            pool = connect_with_connector()
            if pool is None:
                raise Exception("Failed to connect to database after retries")
        
        with pool.cursor() as db_conn:
            result = db_conn.execute(query)
            pool.commit()
            return result
    except Exception as e:
        print(f"❌ Error in exec_update_query: {e}")
        raise e

def set_attributes_dict():
    query = 'SELECT * FROM attributes'
    try:
        data = exec_select_query(query)
        return {x['attribute_name'] : x['attribute_id'] for x in data}
    except Exception as e:
        print(f"Warning: Could not load attributes dictionary: {e}")
        return {}


try:
    ATTR = set_attributes_dict()
except Exception as e:
    print(f"Warning: Failed to initialize ATTR: {e}")
    ATTR = {}

try:
    ATTR_REVERS =  {str(v): k for k, v in ATTR.items()}
except Exception as e:
    print(f"Warning: Failed to initialize ATTR_REVERS: {e}")
    ATTR_REVERS = {}
def update_player_freshness(token, freshness):
    query = sql_queries.UPDATE_FRESHNESS_VALUE.format(token=token, freshness_value=freshness)
    exec_update_query(query)
def set_player_freshness(freshness_delta, operator ,token):
    try:
        query = sql_queries.SET_FRESHNESS_VALUE.format(token=token, freshness_value=freshness_delta, operator = operator)
        # DEBUG: Log before database update
        logger.info(f"🔄 DB UPDATE - Player {token}: freshness_delta={freshness_delta}, operator={operator}")
        print(f"🔄 DB UPDATE - Player {token}: freshness_delta={freshness_delta}, operator={operator}")
        print(f"   Query: {query[:100]}...")
        exec_update_query(query)
        logger.info(f"✅ Freshness updated for {token}")
        print(f"✅ Freshness updated for {token}")
    except Exception as e:
        print(f"❌ Error setting player freshness for {token}: {e}")
        raise

def set_player_freshness_with_timestamp(freshness_delta, operator, token, timestamp):
    """
    Updates player freshness with a specific timestamp for last_update.
    Used when freshness is updated during a match - timestamp should be match end time.
    
    :param freshness_delta: The amount to change freshness
    :param operator: '+' or '-' for addition or subtraction
    :param token: Player ID
    :param timestamp: datetime object for when to set last_update
    """
    try:
        if timestamp is None:
            timestamp = datetime.now()
        
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        query = f"""
        UPDATE player_dynamic_attributes
        SET attribute_value = 
            CASE
                WHEN attribute_value {operator} {freshness_delta} < 0 THEN 0
                ELSE attribute_value {operator} {freshness_delta}
            END,
            last_update = '{timestamp_str}'
        WHERE attribute_id = 15 AND token = '{token}'
        """
        
        logger.info(f"🔄 DB UPDATE (with timestamp) - Player {token}: freshness_delta={freshness_delta}, operator={operator}, last_update={timestamp_str}")
        print(f"🔄 DB UPDATE (with timestamp) - Player {token}: freshness_delta={freshness_delta}, last_update={timestamp_str}")
        exec_update_query(query)
        logger.info(f"✅ Freshness updated for {token} with timestamp {timestamp_str}")
        print(f"✅ Freshness updated for {token} with timestamp {timestamp_str}")
    except Exception as e:
        logger.error(f"❌ Error setting player freshness with timestamp for {token}: {e}")
        print(f"❌ Error setting player freshness with timestamp for {token}: {e}")
        raise

def set_player_satisfaction(sat_delta, operator ,token):
    try:
        query = sql_queries.SET_SATISFACTION_VALUE.format(token=token, satisfaction_value= sat_delta, operator = operator)
        exec_update_query(query)
    except Exception as e:
        print(f"❌ Error setting player satisfaction for {token}: {e}")
        raise

def select_player_freshness(token):
    query = sql_queries.SELECT_FRESHNESS_VALUE.format(token=token)
    rows = exec_select_query(query)
    return rows[0] if len(rows)> 0 else None

def insert_player_freshness(freshness,token):
    query = sql_queries.INSERT_FRESHNESS_VALUE.format(token=token, freshness=freshness)
    exec_update_query(query)
def insert_player(player_data):
    def update_attributes(player_id):
        prop = player_data['properties']
        queries = []
        params = []
        for key in prop.keys():
            if key == 'Freshness':
                insert_player_freshness(prop[key],player_data['token'])
            else:
                queries.append(build_insert_query('player_attributes'))
                params.append(dict(player_id=player_id, attribute_id=ATTR[key], attribute_value=prop[key],
                                   last_update=datetime.now()))
        exec_insert_query(queries, params)

    table_name = 'players'
    query = build_insert_query(table_name)
    player_id = exec_insert_query(query, player_data)
    update_attributes(player_id)
    return


def string_to_dict(input_string):
    # Split the string by ", " to get key-value pairs
    pairs = input_string.split(", ")
    # Create a dictionary by splitting each pair by ": " and stripping whitespace
    result_dict = {key.strip(): float(value.strip()) for key, value in (pair.split(": ") for pair in pairs)}
    return result_dict


def get_draft_players(status_id, batch, limit):
    query = sql_queries.GET_PLAYERS.format(status_id=status_id, batch=batch, limit=limit)
    result = exec_select_query(query)
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    return result


def get_team_players(team_id):
    query = sql_queries.GET_TEAM_PLAYERS.format(team_id=team_id)
    result = exec_select_query(query)
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    return {x['token']: {"properties": x['properties'], "player_id": x['token']} for x in result}


def get_team_default_formation(team_id):
    query = sql_queries.GET_TEAM_DEFAULT_FORMATION.format(team_id=team_id)
    result = exec_select_query(query)
    return None if len(result) == 0 else json.loads(result[0]['formation_positions'])


def insert_player_attributes_game_effected(players_data, match_id, match_end_time=None):
    """
    Insert player attributes after a match ends.
    
    :param players_data: List of player performance data
    :param match_id: The match ID
    :param match_end_time: Optional datetime for when match ended (used for freshness last_update)
    """
    from datetime import datetime
    
    if match_end_time is None:
        match_end_time = datetime.now()
    
    for key in players_data:
        query = sql_queries.INSERT_IMPROVEMENT_MATCH_GAME_EFFECTED
        frsheness_attr = key['performance'].get('freshness_delta')
        # DEBUG: Log freshness delta before DB insert
        logger.info(f"📌 BEFORE DB INSERT - Player {key['player_id']}: freshness_delta={frsheness_attr}, match_end_time={match_end_time}")
        print(f"\n📌 BEFORE DB INSERT - Player {key['player_id']}:")
        print(f"   - freshness_delta value: {frsheness_attr}")
        print(f"   - setting last_update to: {match_end_time}")
        if frsheness_attr:
            # Use new function with timestamp to prevent instant recovery on next refresh
            set_player_freshness_with_timestamp(frsheness_attr, '+', key['player_id'], match_end_time)
        sat_attr = key['performance'].get('satisfaction_delta')
        if sat_attr:
            set_player_satisfaction(sat_attr, '+', key['player_id'])

        attributes = {f"{ATTR.get(k, k)}": v for k, v in key['performance']['attribute_deltas'].items()}
        query = query.format(match_id=match_id, score=key['performance']['overall_score'], token=key['player_id'],
                             improved_attributes=str(attributes).replace("'", '"'))
        res = exec_update_query(query)
        for attr_id, attr_value in attributes.items():
            sub_query = sql_queries._TEMPLATE_INSERT_IMPROVMENT_MATCH
            sub_query = sub_query.format(player_id=key['player_id'], attr_delta=attr_value, attr_id=attr_id)
            res1 = exec_update_query(sub_query)


# TODO: TIKO - PLEASE MAKE SURE YOU KNOW THE player_data structure
def insert_player_attributes_training_effected(players_data, training_id):
    for key, player in players_data.items():
        query = sql_queries.INSERT_IMPROVEMENT_MATCH_TRAINING_EFFECTED
        frsheness_attr = player['properties'].get('Freshness')
        if frsheness_attr:
            del player['properties']['Freshness']
            set_player_freshness(frsheness_attr,'+',player['player_id'])

        satisfaction_attr = player['properties'].get('Satisfaction')
        if satisfaction_attr:
            del player['properties']['Satisfaction']
            set_player_satisfaction(satisfaction_attr,'+',player['player_id'])

        attributes = {f"{ATTR.get(k, k)}": v for k, v in player['properties'].items()}
        query = query.format(training_id=training_id, player_id=player['player_id'],
                             improved_attributes=str(attributes).replace("'", '"'))
        res = exec_update_query(query)
        for attr_id, attr_value in attributes.items():
            # TODO: Nissim! i need procedure that got the attributes json and update the player attributes table
            sub_query = sql_queries._TEMPLATE_INSERT_IMPROVMENT_MATCH
            sub_query = sub_query.format(player_id=player['player_id'], attr_delta=attr_value, attr_id=attr_id)
            res1 = exec_update_query(sub_query)


# TODO: Tiko! here you go..
# the function insert_player_attributes got the players object that you got from `get_team_players`, just edit the object and add
# `score` field for each player.example here:
# TEAM = get_team_players(1)
# for key in TEAM.keys():
#     TEAM[key]['score'] = 12
#     for prop in TEAM[key]['properties'].keys():
#         TEAM[key]['properties'][prop] = 0.01
# insert_player_attributes_game_effected(TEAM, 104)


# pass

def insert_opening_formations(match_id):
    query = sql_queries.SET_TEAMS_FORMATIONS_FOR_MATCH.format(match_id=match_id)
    res = exec_update_query(query)
    return res

def get_player_by_token(token):
    query = sql_queries.GET_PLAYER_BY_TOKEN.format(token=token)
    result = exec_select_query(query)
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    if len(result) >0:
        result[0]['player_id'] = result[0]['token']
    return result and result[0] or None

def get_player_by_userid(user_id):
    query = sql_queries.GET_ACCOUNT_PLAYERS.format(user_id=user_id)
    result = exec_select_query(query)
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    return result


def update_user_login(user_id):
    query = sql_queries.INSERT_USER_LOGIN.format(user_id=user_id)
    result = exec_update_query(query)
    return result


def update_player_status(token, status_id, user_id):
    query = sql_queries.UPDATE_PLAYER_STATUS.format(token=token, status_id=status_id, user_id=user_id)
    result = exec_update_query(query)
    return result

def loan_player(token, status_id, user_id):
    query = sql_queries.UPDATE_PLAYER_STATUS.format(token=token, status_id=status_id, user_id=user_id)
    result = exec_update_query(query)
    return result

def insert_team(team_data):
    table_name = 'teams'
    query = build_insert_query(table_name)
    team_id = exec_insert_query(query, team_data)
    update_teams_query = sql_queries.UPDATE_PLAYERS_TEAM.format(team_id=team_id, user_id=team_data['user_id'])
    res = exec_update_query(update_teams_query)
    return True


def get_team_by_id(user_id):
    query = sql_queries.GET_TEAM.format(user_id=user_id)
    result = exec_select_query(query)
    return None if len(result) == 0 else result[0]


def get_formations(team_id):
    result = exec_select_query(sql_queries.GET_FORMATIONS.format(team_id=team_id))
    fields = [
        "team_id",
        "formation_id",
        "default_formation",
        "formation_positions",
        "attack_score",
        "defense_score",
        "midfield_score"
    ]

    result = {
        x['formation_name']: {field: field == 'formation_positions' and json.loads(x[field]) or x[field] for field in
                              fields} for x in result}

    return result

#TODO: CHANGE THE DYNAMIC
def insert_formation(formation_data):
    formation_data['formation_positions'] = json.dumps(formation_data['formation_positions'])
    query = sql_queries.INSERT_OR_UPDATE_TEAM_FORMATION.format(**formation_data)
    formation_id = exec_update_query(query)
    return formation_id


def reset_default_formation(team_id):
    update_teams_query = sql_queries.UPDATE_RESET_DEFAULT_FORMATION.format(team_id=team_id)
    res = exec_update_query(update_teams_query)
    return True


def select_all_leagues(user_id=''):
    query = sql_queries.SELECT_ALL_LEAGUES.format(user_id=user_id)
    result = exec_select_query(query)
    return result

def join_league(team_id, league_id):
    query = sql_queries.INSERT_JOIN_LEAGUE.format(team_id=team_id,league_id=league_id)
    try:
        result = exec_update_query(query)
    except Exception as e:
        if 'VALIDATION_ERROR' in str(e):
            return False, 'VALIDATION_ERROR'
    query = sql_queries.INSERT_JOIN_LEAGUE_1.format(team_id=team_id,league_id=league_id)
    result = exec_update_query(query)
    return True, result

def select_team_leagues(team_id=''):
    query = sql_queries.SELECT_TEAM_LEAGUES.format(team_id=team_id)
    result = exec_select_query(query)
    return result


def select_league_teams(league_id):
    query = sql_queries.SELECT_LEAGUE_TEAMS.format(league_id=league_id)
    result = exec_select_query(query)
    return [row['team_id'] for row in result]


def select_league_table(league_id=''):
    query = sql_queries.SELECT_LEAGUE_TABLE.format(league_id=league_id)
    result = exec_select_query(query)
    return result


def get_league_by_id(league_id):
    """Get league info by ID to determine league type"""
    query = f"SELECT * FROM leagues WHERE league_id = {league_id}"
    result = exec_select_query(query)
    if result:
        return result[0]
    return None


def insert_init_matches(matches):
    print(f"🎯 MODEL insert_init_matches - Received {len(matches)} matches")
    for idx, match in enumerate(matches):
        # Ensure 'kind' exists before inserting
        if 'kind' not in match or match['kind'] is None:
            print(f"⚠️ Warning: Match missing 'kind' field! Setting to 1 (League) by default")
            match['kind'] = 1  # Default to League match
        
        print(f"🔍 MODEL Match #{idx+1} - kind={match.get('kind')}, league_id={match.get('league_id')}, home={match.get('home_team_id')}, away={match.get('away_team_id')}")
            
        query = build_insert_query("matches")
        
        # LOGGING: Check what we are sending
        print(f"DEBUG insert_init_matches - Match Kind: {match.get('kind')} (Type: {type(match.get('kind'))})")
        
        res = exec_insert_query(query, match)
        match['match_id'] = res

    return matches

def update_matche_result(match_id, match_result,min_played):
    query = sql_queries.UPDATE_MATCH_RESULT.format(match_id=match_id,match_result=match_result, time_played_mins=min_played)
    res = exec_update_query(query)
    return res

def update_match_time(match_id, min_played):
    query = sql_queries.UPDATE_MATCH_TIME.format(match_id=match_id, time_played_mins=min_played)
    res = exec_update_query(query)
    return res


def get_matches_by_league_id(league_id,match_day = None):
    try:
        if not match_day:
            match_day = exec_select_query(sql_queries.GET_CURRENT_OR_NEXT_MATCH_DAY)
            match_day = match_day[0]['match_day']
            pass

        query = sql_queries.SELECT_MATCHES_BY_LEAGUE_ID.format(league_id=league_id,match_day=match_day)
        result = exec_select_query(query)
        return result
    except:
        return []

def get_next_time_match(team_id):
    data = exec_select_query(sql_queries.SELECT_NEXT_TIME_MATCH.format(team_id=team_id))
    data =  data[0]['time_until_match' ]if len(data) > 0 else None
    if data:
        parts = data.split(", ")
        keys = ["days", "hours", "minutes", "seconds"]
        res = {key: int(part.split()[0]) for key, part in zip(keys, parts)}
        return res
    else:
        return {}

def get_current_matches():
    query = sql_queries.SELECT_MATCHES_FOR_CURRENT_DAY
    result = exec_select_query(query)
    return result

def get_matches_by_match_day(match_day):
    """
    קבל משחקים לפי match_day ספציפי
    """
    query = sql_queries.SELECT_MATCHES_BY_MATCH_DAY.format(match_day=match_day)
    result = exec_select_query(query)
    return result


def get_match_details(match_id):
   
    query_result_details = sql_queries.SELECT_MATCH_RESULT_DETAILS.format(match_id=match_id)
    result = exec_select_query(query_result_details)

 
    query_additional_details = sql_queries.SELECT_MATCH_DETAILS.format(match_id=match_id)
    additional_result = exec_select_query(query_additional_details)

    if result:
        match_details = result[0]
        if match_details.get('home_team_details'):
            match_details['home_team_details'] = json.loads(match_details['home_team_details'])
            for p in match_details['home_team_details']['players']:
                p["improved_attributes"] = {ATTR_REVERS[k]: v for k, v in p["improved_attributes"].items()}
        if match_details.get('away_team_details'):
            ATTR
            match_details['away_team_details'] = json.loads(match_details['away_team_details'])
            for p in match_details['away_team_details']['players']:
                p["improved_attributes"] = {ATTR_REVERS[k]: v for k, v in p["improved_attributes"].items()}
    else:
        match_details = {}
        match_result_details = {}

   
    if additional_result:

        additional_match_details = [x for x in additional_result]
        for amd in additional_match_details:
            amd['action_timestamp'] = str(amd['action_timestamp'])
    else:
        additional_match_details = []

    return match_details, additional_match_details


def get_matches_by_team_id(team_id=''):
    query = sql_queries.SELECT_MATCHES_BY_LEAGUE_ID.format(team_id=team_id)
    result = exec_select_query(query)
    return result


def get_training_types():
    query = sql_queries.SELECT_TRAINING_TYPES
    result = exec_select_query(query)
    for res in result:
        res['affected_attributes'] = json.loads(res['affected_attributes'])
    return result


def get_training_levels():
    query = sql_queries.SELECT_TRAINING_LEVELS
    result = exec_select_query(query)
    return result

def set_team_training(trainig_parmaters):
    trainig_parmaters['participating_players'] = json.dumps(trainig_parmaters.get('participating_players',[]))
    query = sql_queries.INSERT_TEAM_TRAINING.format(**trainig_parmaters)
    result = exec_update_query(query)
    return result

def is_trainable(team_id):
    query = sql_queries.IS_TRAINABLE.format(team_id=team_id)
    result = exec_select_query(query)
    return result[0]
def get_team_training(team_id):
    query = sql_queries.SELECT_TEAM_TRAININGS.format(team_id=team_id)
    result = exec_select_query(query)
    return result


def get_team_training_by_id(training_id):
    query = sql_queries.SELECT_TEAM_TRAINING_BY_ID.format(training_id=training_id)
    result = exec_select_query(query)
    return result

def insert_match_details(match_id, details):
    if type(details) is list:
        for det in details:
            det['match_id']=match_id
            query = sql_queries.INSERT_MATCH_DETAILS.format(**det)
            exec_update_query(query)
    else:
        details['match_id'] = match_id
        query = sql_queries.INSERT_MATCH_DETAILS.format(**details)
        exec_update_query(query)
# insert_match_details(dict( match_id=1,
#     action_id=1,
#     action_timestamp='10:00:00',
#     token='token1'))
def set_formations_for_next_mathces():
    exec_update_query(sql_queries.SET_FORMATION_FOR_MATCH)

def get_tarainable_players(team_id):
    query = sql_queries.GET_TRAINABLE_PLAYERS.format(team_id=team_id)
    data = exec_select_query(query)
    return data

def get_training_team_history(team_id, offset):
    query = sql_queries.SELECT_TRAINING_TEAM_HISTORY.format(team_id=team_id, offset=offset)
    data = exec_select_query(query)
    return data

def get_training_details(training_id):
    query = sql_queries.SELECT_TRAINING_DETAILS.format(training_id=training_id)
    data = exec_select_query(query)
    return data

def cancel_match(match_id):
    query = sql_queries.UPDATE_MATCH_RESULT_CANCELLED.format(match_id=match_id)
    exec_update_query(query)

#TODO: Tiko - here your freshness calculator
def get_freshness_last_effort(token):
    query = sql_queries.GET_FRESHNESS_LAST_EFFORT.format(token=token)
    data = exec_select_query(query)
    return len(data) > 0 and data[0] or {}
# get_freshness_last_effort("a0x24291884383d3fbe2bc74ae452d42cced24a85fc24")

def get_training_history_by_team_id(team_id):
    query = sql_queries.SELECT_PLAYERS_TARINING_HISTORY_BY_TEAM_ID.format(team_id = team_id)
    data = exec_select_query(query)
    return data

def insert_man_of_the_match(token, match_id ):
    query = sql_queries.INSERT_MAN_OF_THE_MATCH.format(token=token, match_id=match_id)
    exec_update_query(query)


############################COMPETITIONS##############################
def select_players_for_competition(competition_id):
    query = sql_queries.GET_COMPETITION_PLAYERS.format(competition_id=competition_id)
    data = exec_select_query(query)
    tmp = [
        {**x, 'attributes': json.loads(x['attributes'])}
        for x in data
    ]
    return tmp


def insert_player_attributes_competition_effected(players_data, competition_id):
    import logging
    logger = logging.getLogger(__name__)
    
    success_count = 0
    error_count = 0
    
    try:
        for key, player in players_data.items():
            try:
                logger.info(f"Processing player {player['token']} for competition {competition_id}")
                
                # Handle Freshness
                frsheness_attr = player['attributes'].get('Freshness')
                if frsheness_attr:
                    del player['attributes']['Freshness']
                    logger.info(f"  - Updating Freshness: {frsheness_attr}")
                    set_player_freshness(frsheness_attr,'+',player['token'])

                # Handle Satisfaction
                satisfaction_attr = player['attributes'].get('Satisfaction')
                if satisfaction_attr:
                    del player['attributes']['Satisfaction']
                    logger.info(f"  - Updating Satisfaction: {satisfaction_attr}")
                    set_player_satisfaction(satisfaction_attr,'+',player['token'])

                # Insert competition results
                attributes = {f"{ATTR.get(k, k)}": v for k, v in player['attributes'].items()}
                query = sql_queries.INSERT_COMPETITION_RESULTS.format(
                    competition_id=competition_id, 
                    token=player['token'],
                    score=player.get('score',0), 
                    rank_position=player.get('rank_position',0),
                    is_winner=player.get('is_winner',0)
                )
                logger.info(f"🔍 SQL INSERT Query: {query}")
                print(f"🔍 SQL INSERT: {query}")  # Print to stdout
                res = exec_update_query(query)
                logger.info(f"✅ INSERT Result: {res}")
                print(f"✅ INSERT Result: {res}")
                
                # Insert attribute improvements
                for attr_id, attr_value in attributes.items():
                    sub_query = sql_queries._TEMPLATE_INSERT_IMPROVMENT_MATCH
                    sub_query = sub_query.format(player_id=player['token'], attr_delta=attr_value, attr_id=attr_id)
                    res1 = exec_update_query(sub_query)
                    logger.info(f"  - Attribute {attr_id} update status: {res1}")
                
                success_count += 1
                logger.info(f"✅ Player {player['token']} processed successfully")
            
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error processing player {player.get('token', 'unknown')}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"📊 Competition {competition_id} results summary: {success_count} succeeded, {error_count} failed")
        return success_count, error_count
    
    except Exception as e:
        logger.error(f"❌ Critical error in insert_player_attributes_competition_effected: {str(e)}", exc_info=True)
        raise e


def get_current_competitions():
    """
    Get all competitions scheduled to run now (within their time window)
    Status 14 = Scheduled/Active
    Returns list of competition dicts
    """
    query = sql_queries.SELECT_COMPETITIONS_FOR_CURRENT_TIME
    result = exec_select_query(query)
    return result


def update_competition_status(competition_id, status_id):
    """
    Update competition status
    Status IDs: 14=Scheduled, 15=Completed, etc.
    """
    import logging
    logger = logging.getLogger(__name__)
    query = sql_queries.UPDATE_COMPETITION_STATUS.format(competition_id=competition_id, status_id=status_id)
    logger.info(f"🔍 SQL UPDATE Query: {query}")
    print(f"🔍 SQL UPDATE: {query}")  # Print to stdout
    res = exec_update_query(query)
    logger.info(f"✅ UPDATE Result: {res}")
    print(f"✅ UPDATE Result: {res}")
    return res

#########################END - COMPETITIONS###########################

def get_match_kind_id(kind_name):
    """
    Get the match kind ID from the match_kinds table by kind name
    Returns the ID (1 for League, 2 for Friendly, etc.)
    """
    try:
        query = f"SELECT id FROM match_kinds WHERE name = '{kind_name}'"
        result = exec_select_query(query)
        if result:
            return result[0][0]
        else:
            print(f"Warning: Match kind '{kind_name}' not found in match_kinds table")
            return None
    except Exception as e:
        print(f"Error getting match kind ID: {e}")
        return None

def get_match_kind_factors(match_kind_id):
    """
    Get the factors for a specific match kind from the database
    Returns dict with improvement_factor, fatigue_factor, satisfaction_factor
    """
    try:
        query = f"""
        SELECT 
            id,
            name,
            improvement_factor,
            fatigue_factor,
            satisfaction_factor
        FROM match_kinds 
        WHERE id = {match_kind_id}
        """
        result = exec_select_query(query)
        if result:
            row = result[0]
            return {
                'kind_id': row.get('id', match_kind_id),
                'name': row.get('name', 'Unknown'),
                'improvement_factor': float(row.get('improvement_factor', 1.0)),
                'fatigue_factor': float(row.get('fatigue_factor', 1.0)),
                'satisfaction_factor': float(row.get('satisfaction_factor', 1.0))
            }
        else:
            print(f"⚠️ Warning: Match kind ID {match_kind_id} not found in match_kinds table. Using default factors.")
            return {
                'kind_id': match_kind_id,
                'name': 'Unknown',
                'improvement_factor': 1.0,
                'fatigue_factor': 1.0,
                'satisfaction_factor': 1.0
            }
    except Exception as e:
        print(f"❌ Error getting match kind factors: {e}. Using default factors.")
        return {
            'kind_id': match_kind_id,
            'name': 'Unknown',
            'improvement_factor': 1.0,
            'fatigue_factor': 1.0,
            'satisfaction_factor': 1.0
        }

def get_all_match_kinds():
    """
    Get all match kinds from the database
    Returns list of dicts with all match kind information
    """
    try:
        query = """
        SELECT 
            id,
            name,
            improvement_factor,
            fatigue_factor,
            satisfaction_factor,
            must_win,
            description
        FROM match_kinds
        ORDER BY id
        """
        result = exec_select_query(query)
        return result
    except Exception as e:
        print(f"Error getting all match kinds: {e}")
        return []

def init_mock_db():
    return None


def distribute_competition_prizes(competition_id, competition_type_id):
    """
    Distribute prizes to competition winners based on their rank.
    
    Args:
        competition_id: The ID of the competition
        competition_type_id: The type of competition (1=100M, 2=5000M, 3=Penalty, 4=Goalkeeper)
    
    Returns:
        dict: Summary of prize distribution
    """
    print(f"\n{'='*80}")
    print(f"💰💰💰 FUNCTION CALLED: distribute_competition_prizes")
    print(f"    Competition ID: {competition_id}")
    print(f"    Competition Type: {competition_type_id}")
    print(f"{'='*80}\n")
    
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"💰 Starting prize distribution for competition {competition_id} (type {competition_type_id})")
    
    try:
        # Step 1: Check if prizes already distributed (prevent duplicates)
        check_query = f"""
        SELECT COUNT(*) as count 
        FROM transactions 
        WHERE description LIKE '%Competition%{competition_id}%'
        AND transaction_type = 'Prize'
        """
        existing = exec_select_query(check_query)
        if existing and len(existing) > 0:
            count_value = existing[0]['count'] if isinstance(existing[0], dict) else existing[0][0]
            if count_value > 0:
                logger.warning(f"⚠️ Prizes already distributed for competition {competition_id}, skipping")
                return {'status': 'already_distributed', 'competition_id': competition_id}
        
        # Step 2: Get prize information for this competition type
        prize_query = f"""
        SELECT 
            place,
            amount,
            token_coin_id
        FROM competition_type_prizes
        WHERE competition_type_id = {competition_type_id}
        ORDER BY place
        """
        prizes = exec_select_query(prize_query)
        
        if not prizes:
            logger.error(f"❌ No prizes defined for competition type {competition_type_id}")
            return {'status': 'no_prizes_defined', 'competition_id': competition_id}
        
        # Convert to dict for easy lookup
        prizes_dict = {}
        for row in prizes:
            if isinstance(row, dict):
                prizes_dict[row['place']] = {'amount': row['amount'], 'token_coin_id': row['token_coin_id']}
            else:
                prizes_dict[row[0]] = {'amount': row[1], 'token_coin_id': row[2]}
        logger.info(f"📋 Found {len(prizes_dict)} prize tiers")
        
        # Step 3: Get winners from competition_results
        winners_query = f"""
        SELECT 
            cr.rank_position,
            cr.token,
            p.user_id,
            p.name as player_name
        FROM competition_results cr
        LEFT JOIN players p ON cr.token = p.token
        WHERE cr.competition_id = {competition_id}
        AND cr.rank_position <= 3
        ORDER BY cr.rank_position
        """
        winners = exec_select_query(winners_query)
        
        if not winners:
            logger.warning(f"⚠️ No winners found for competition {competition_id}")
            return {'status': 'no_winners', 'competition_id': competition_id}
        
        logger.info(f"🏆 Found {len(winners)} winners")
        
        # Step 4: Get competition type name for description
        competition_names = {
            1: "100M Sprint",
            2: "5000M Run",
            3: "Penalty Shooter",
            4: "Goalkeeper"
        }
        comp_name = competition_names.get(competition_type_id, f"Competition Type {competition_type_id}")
        
        # Step 5: Create transactions for each winner
        transactions_created = 0
        for winner in winners:
            if isinstance(winner, dict):
                rank_position = winner['rank_position']
                token = winner['token']
                user_id = winner['user_id']
                player_name = winner.get('player_name')
            else:
                rank_position, token, user_id, player_name = winner
            
            if not user_id:
                logger.warning(f"⚠️ No user_id found for token {token}, skipping")
                continue
            
            # Get prize for this rank
            if rank_position not in prizes_dict:
                logger.warning(f"⚠️ No prize defined for rank {rank_position}, skipping")
                continue
            
            prize_info = prizes_dict[rank_position]
            amount = prize_info['amount']
            token_coin_id = prize_info['token_coin_id']
            
            # Create description
            description = f"Place {rank_position} - Competition {comp_name} (ID: {competition_id})"
            
            # Insert transaction
            transaction_query = f"""
            INSERT INTO transactions (
                user_id,
                token_coin_id,
                amount,
                timestamp,
                description,
                transaction_type
            ) VALUES (
                '{user_id}',
                {token_coin_id},
                {amount},
                NOW(),
                '{description}',
                'Prize'
            )
            """
            
            # הדפס את ה-INSERT לפני ביצוע
            print(f"\n{'🔵'*40}")
            print(f"💾 EXECUTING INSERT QUERY:")
            print(f"   User: {user_id}")
            print(f"   Amount: {amount}")
            print(f"   Token Coin ID: {token_coin_id}")
            print(f"   Description: {description}")
            print(f"\nFull Query:\n{transaction_query}")
            print(f"{'🔵'*40}\n")
            
            try:
                exec_update_query(transaction_query)
                transactions_created += 1
                print(f"✅ INSERT SUCCESS - Transaction created for rank {rank_position}")
                logger.info(f"✅ Prize distributed: {amount} tokens to {player_name or user_id[:10]+'...'} (Rank {rank_position})")
            except Exception as e:
                logger.error(f"❌ Failed to create transaction for rank {rank_position}: {e}")
        
        logger.info(f"🎉 Prize distribution complete: {transactions_created}/{len(winners)} transactions created")
        
        result = {
            'status': 'success',
            'competition_id': competition_id,
            'transactions_created': transactions_created,
            'winners_count': len(winners)
        }
        
        print(f"\n{'='*80}")
        print(f"✅✅✅ PRIZE DISTRIBUTION COMPLETED SUCCESSFULLY")
        print(f"    Competition: {competition_id}")
        print(f"    Transactions: {transactions_created}/{len(winners)}")
        print(f"    Result: {result}")
        print(f"{'='*80}\n")
        
        return result
        
    except Exception as e:
        error_msg = f"❌ Error distributing prizes for competition {competition_id}: {e}"
        print(f"\n{'='*80}")
        print(f"❌❌❌ PRIZE DISTRIBUTION FAILED")
        print(f"    Competition: {competition_id}")
        print(f"    Error: {e}")
        print(f"{'='*80}\n")
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return {
            'status': 'error',
            'competition_id': competition_id,
            'error': str(e)
        }
        return {
            'status': 'error',
            'competition_id': competition_id,
            'error': str(e)
        }
