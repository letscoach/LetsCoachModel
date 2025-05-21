import os

import google.auth
from google.cloud.sql.connector import Connector, IPTypes
import pymysql
import sqlalchemy
from google.auth import exceptions
from sqlalchemy import text
from Helpers.table_def import tables as DB_TABLES
import Helpers.sql_queries as sql_queries
from datetime import datetime
from sqlalchemy.exc import IntegrityError


def connect_with_connector() -> sqlalchemy.engine.base.Engine:
    instance_connection_name = 'zinc-strategy-446518-s7:us-central1:letscoach-dev'
    db_user = 'me'  # e.g. 'my-db-user'
    db_pass = 'Ab123456'  # e.g. 'my-db-password'
    db_name = 'main_game'  # e.g. 'my-database'
    ip_type = IPTypes.PUBLIC  # Choose PUBLIC or PRIVATE depending on your configuration

    # Path to your service account key JSON file
    credentials_path = os.path.join(os.path.dirname(__file__), "sql_cred.json")

    # Load credentials manually
    try:
        credentials, project = google.auth.load_credentials_from_file(credentials_path)
    except exceptions.DefaultCredentialsError:
        print("Error loading credentials from file.")
        return None

    # Initialize Cloud SQL connector
    connector = Connector(ip_type, credentials=credentials)

    # Define a function to get the connection
    def getconn() -> pymysql.connections.Connection:
        conn = connector.connect(
            instance_connection_name,
            "pymysql",
            user=db_user,
            password=db_pass,
            db=db_name,
        )
        return conn

    # Create SQLAlchemy engine with the correct connection string
    pool = sqlalchemy.create_engine(
        f"mysql+pymysql://{db_user}:{db_pass}@127.0.0.1/{db_name}",
        creator=getconn,
    )
    return pool


# Connect to the database and execute a query
pool = connect_with_connector()


def build_insert_query(table_name: str) -> str:
    columns = DB_TABLES[table_name]
    # Create placeholders for values, e.g., "%s, %s, %s" for parameterized queries
    placeholders = ', '.join([':' + x for x in columns])

    # Format the column names, e.g., "col1, col2, col3"
    columns_str = ', '.join(columns)

    # Build the query
    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders});"
    return query


def exec_insert_query(query, params):
    try:
        with pool.connect() as db_conn:
            if type(query) is list:
                for ind, quer in enumerate(query):
                    result = db_conn.execute(text(quer), params[ind])
                    db_conn.connection.commit()
            else:
                result = db_conn.execute(text(query), params)
                db_conn.connection.commit()  # Commit after the insert

            print("Insert successful!")
            return result.lastrowid
    except IntegrityError as e:
        if 'Duplicate entry' in str(e.orig):
            raise Exception(f"Duplicate value")
        else:
            raise Exception(f"An unexpected error occurred: {str(e)}")


def exec_select_query(query):
    try:
        with pool.connect() as db_conn:
            result = db_conn.execute(text(query)).fetchall()

            return result
    except Exception as e:
        raise e


def exec_update_query(query):
    try:
        with pool.connect() as db_conn:
            result = db_conn.execute(text(query))
            db_conn.connection.commit()
            return result
    except Exception as e:
        raise e

def set_attributes_dict():
    query = 'SELECT * FROM attributes'
    data = exec_select_query(query)
    data = [x._asdict() for x in data]
    return {x['attribute_name'] : x['attribute_id'] for x in data}


ATTR = set_attributes_dict()
ATTR_REVERS =  {str(v): k for k, v in ATTR.items()}
def update_player_freshness(token, freshness):
    query = sql_queries.UPDATE_FRESHNESS_VALUE.format(token=token, freshness_value=freshness)
    exec_update_query(query)
def set_player_freshness(freshness_delta, operator ,token):
    query = sql_queries.SET_FRESHNESS_VALUE.format(token=token, freshness_value=freshness_delta, operator = operator)
    exec_update_query(query)

def set_player_satisfaction(sat_delta, operator ,token):
    query = sql_queries.SET_SATISFACTION_VALUE.format(token=token, satisfaction_value= sat_delta, operator = operator)
    exec_update_query(query)

def select_player_freshness(token):
    query = sql_queries.SELECT_FRESHNESS_VALUE.format(token=token)
    rows = exec_select_query(query)
    rows = [row._asdict() for row in rows]
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
    result = [row._asdict() for row in result]
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    return result


def get_team_players(team_id):
    query = sql_queries.GET_TEAM_PLAYERS.format(team_id=team_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    return {x['token']: {"properties": x['properties'], "player_id": x['token']} for x in result}


def get_team_default_formation(team_id):
    query = sql_queries.GET_TEAM_DEFAULT_FORMATION.format(team_id=team_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
    return None if len(result) == 0 else json.loads(result[0]['formation_positions'])


def insert_player_attributes_game_effected(players_data, match_id):
    for key in players_data:
        query = sql_queries.INSERT_IMPROVEMENT_MATCH_GAME_EFFECTED
        frsheness_attr = key['performance'].get('freshness_delta')
        if frsheness_attr:
            set_player_freshness(frsheness_attr, '+', key['player_id'])
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
    result = [row._asdict() for row in result]
    for row in result:
        row['properties'] = string_to_dict(row['attributes'])
    if len(result) >0:
        result[0]['player_id'] = result[0]['token']
    return result and result[0] or None

def get_player_by_userid(user_id):
    query = sql_queries.GET_ACCOUNT_PLAYERS.format(user_id=user_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
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
    result = [row._asdict() for row in result]
    return None if len(result) == 0 else result[0]


def get_formations(team_id):
    result = exec_select_query(sql_queries.GET_FORMATIONS.format(team_id=team_id))
    result = [row._asdict() for row in result]
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
    result = [row._asdict() for row in result]
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
    result = [row._asdict() for row in result]
    return result


def select_league_teams(league_id):
    query = sql_queries.SELECT_LEAGUE_TEAMS.format(league_id=league_id)
    result = exec_select_query(query)
    result = [row._asdict()['team_id'] for row in result]
    return result


def select_league_table(league_id=''):
    query = sql_queries.SELECT_LEAGUE_TABLE.format(league_id=league_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
    return result


def insert_init_matches(matches):
    for match in matches:
        query = build_insert_query("matches")
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
            match_day = match_day[0]._asdict()['match_day']
            pass

        query = sql_queries.SELECT_MATCHES_BY_LEAGUE_ID.format(league_id=league_id,match_day=match_day)
        result = exec_select_query(query)
        result = [row._asdict() for row in result]
        return result
    except:
        return []

def get_next_time_match(team_id):
    data = exec_select_query(sql_queries.SELECT_NEXT_TIME_MATCH.format(team_id=team_id))
    data =  data[0]._asdict()['time_until_match' ]if len(data) > 0 else None
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
    result = [row._asdict() for row in result]
    return result
import json

def get_match_details(match_id):
   
    query_result_details = sql_queries.SELECT_MATCH_RESULT_DETAILS.format(match_id=match_id)
    result = exec_select_query(query_result_details)

 
    query_additional_details = sql_queries.SELECT_MATCH_DETAILS.format(match_id=match_id)
    additional_result = exec_select_query(query_additional_details)

    if result:
        match_details = result[0]._asdict()
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

        additional_match_details = [x._asdict() for x in additional_result]
        for amd in additional_match_details:
            amd['action_timestamp'] = str(amd['action_timestamp'])
    else:
        additional_match_details = []

    return match_details, additional_match_details


def get_matches_by_team_id(team_id=''):
    query = sql_queries.SELECT_MATCHES_BY_LEAGUE_ID.format(team_id=team_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
    return result


def get_training_types():
    query = sql_queries.SELECT_TRAINING_TYPES
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
    for res in result:
        res['affected_attributes'] = json.loads(res['affected_attributes'])
    return result


def get_training_levels():
    query = sql_queries.SELECT_TRAINING_LEVELS
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
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
    result = [row._asdict() for row in result]
    return result


def get_team_training_by_id(training_id):
    query = sql_queries.SELECT_TEAM_TRAINING_BY_ID.format(training_id=training_id)
    result = exec_select_query(query)
    result = [row._asdict() for row in result]
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
    return [x._asdict() for x in data]

def get_training_team_history(team_id, offset):
    query = sql_queries.SELECT_TRAINING_TEAM_HISTORY.format(team_id=team_id, offset=offset)
    data = exec_select_query(query)
    return [x._asdict() for x in data]

def get_training_details(training_id):
    query = sql_queries.SELECT_TRAINING_DETAILS.format(training_id=training_id)
    data = exec_select_query(query)
    return [x._asdict() for x in data]


#TODO: Tiko - here your freshness calculator
def get_freshness_last_effort(token):
    query = sql_queries.GET_FRESHNESS_LAST_EFFORT.format(token=token)
    data = exec_select_query(query)
    return len(data) > 0 and [x._asdict() for x in data][0] or {}
# get_freshness_last_effort("a0x24291884383d3fbe2bc74ae452d42cced24a85fc24")

def get_training_history_by_team_id(team_id):
    query = sql_queries.SELECT_PLAYERS_TARINING_HISTORY_BY_TEAM_ID.format(team_id = team_id)
    data = exec_select_query(query)
    data =  [x._asdict() for x in data]
    # for d in data:
    #     d['players'] = json.loads(d['players'])
    return data

def insert_man_of_the_match(token, match_id ):
    query = sql_queries.INSERT_MAN_OF_THE_MATCH.format(token=token, match_id=match_id)
    exec_update_query(query)


############################COMPETITIONS##############################
def select_players_for_competition(competition_id):
    query = sql_queries.GET_COMPETITION_PLAYERS.format(competition_id=competition_id)
    data = exec_select_query(query)
    tmp = [
        {**x._asdict(), 'attributes': json.loads(x.attributes)}
        for x in data
    ]
    return tmp


#TODO: MAKE SURE THAT THE PLAYERS_DATA STRUCTURE IS:
#[
#   {'token' : '0xdeldewd',
#    'attributes' : {attribute_name: delta},
#    'is_winner' : OPTINAL 0,1,2 OR WITHOUT THIS FIELD!!
#    'rank_position': NUMBER
#    'score' : NUMBER
#    },...
# ]
def insert_player_attributes_competition_effected(players_data, competition_id):
    for key, player in players_data.items():
        query = sql_queries.INSERT_COMPETITION_RESULTS
        frsheness_attr = player['attributes'].get('Freshness')
        if frsheness_attr:
            del player['attributes']['Freshness']
            set_player_freshness(frsheness_attr,'+',player['token'])

        satisfaction_attr = player['attributes'].get('Satisfaction')
        if satisfaction_attr:
            del player['attributes']['Satisfaction']
            set_player_satisfaction(satisfaction_attr,'+',player['token'])

        attributes = {f"{ATTR.get(k, k)}": v for k, v in player['attributes'].items()}
        query = query.format(competition_id=competition_id, token=player['token'],
                             score=player.get('score',0), rank_position=player.get('rank_position',0),is_winner=player.get('is_winner','NULL'))
        res = exec_update_query(query)
        for attr_id, attr_value in attributes.items():
            # TODO: Nissim! i need procedure that got the attributes json and update the player attributes table
            sub_query = sql_queries._TEMPLATE_INSERT_IMPROVMENT_MATCH
            sub_query = sub_query.format(player_id=player['token'], attr_delta=attr_value, attr_id=attr_id)
            res1 = exec_update_query(sub_query)
#########################END - COMPETITIONS###########################
def init_mock_db():
    return None
