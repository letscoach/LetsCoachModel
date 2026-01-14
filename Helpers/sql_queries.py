GET_PLAYERS = '''
SELECT 
    p.*, 
    s.status_name,
    CONCAT(
        IFNULL(attr_static, ''), 
        IF(attr_static IS NOT NULL AND attr_dynamic IS NOT NULL, ', ', ''), 
        IFNULL(attr_dynamic, '')
    ) AS attributes
FROM players p
LEFT JOIN statuses s ON p.status_id = s.status_id
LEFT JOIN (
    SELECT 
        pa.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pa.attribute_value) SEPARATOR ', ') AS attr_static
    FROM player_attributes pa
    LEFT JOIN attributes a ON pa.attribute_id = a.attribute_id
    GROUP BY pa.token
) pa ON p.token = pa.token
LEFT JOIN (
    SELECT 
        pda.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pda.attribute_value) SEPARATOR ', ') AS attr_dynamic
    FROM player_dynamic_attributes pda
    LEFT JOIN attributes a ON pda.attribute_id = a.attribute_id
    GROUP BY pda.token
) pda ON p.token = pda.token
WHERE p.status_id IN ({status_id})
GROUP BY p.token, s.status_name, pa.attr_static, pda.attr_dynamic
ORDER BY p.status_id, p.creation_date DESC, p.player_id
LIMIT {limit} OFFSET {batch};
'''
INSERT_OR_UPDATE_TEAM_FORMATION = '''
INSERT INTO
  team_formation_positions (
    team_id,
    formation_id,
    default_formation,
    formation_positions,
    attack_score,
    defense_score,
    midfield_score)
VALUES
 ({team_id},{formation_id},{default_formation},'{formation_positions}',{attack_score},{defense_score},{midfield_score})
ON
  DUPLICATE KEY
UPDATE
  formation_positions =
VALUES
  (formation_positions),
  default_formation = 
  VALUES
  (default_formation),
  attack_score =
VALUES
  (attack_score),
  defense_score =
VALUES
  (defense_score),
  midfield_score =
VALUES
  (midfield_score);
'''

GET_TEAM_PLAYERS = '''
SELECT
    p.name,
    p.token,
    GROUP_CONCAT(
        CONCAT(a.attribute_name, ': ', pa.attribute_value) SEPARATOR ', '
    ) AS attributes
FROM teams t
JOIN players p 
    ON p.user_id = t.user_id
LEFT JOIN (
    SELECT token, attribute_id, attribute_value FROM player_attributes
    UNION ALL
    SELECT token, attribute_id, attribute_value FROM player_dynamic_attributes
) pa 
    ON p.token = pa.token
LEFT JOIN attributes a 
    ON pa.attribute_id = a.attribute_id
WHERE
    t.team_id = '{team_id}'
GROUP BY
    p.token;


'''

UPDATE_FRESHNESS_VALUE = '''
UPDATE
  player_dynamic_attributes
SET
  attribute_value = attribute_value + {delta}
WHERE
attribute_id = 15 
AND  token = '{token}'
'''
SET_FRESHNESS_VALUE = '''
UPDATE player_dynamic_attributes
SET attribute_value = 
    CASE
        WHEN attribute_value {operator} {freshness_value} < 0 THEN 0
        ELSE attribute_value {operator} {freshness_value}
    END,
    last_update = NOW()
WHERE attribute_id = 15 AND token = '{token}'
'''

SET_SATISFACTION_VALUE = '''
UPDATE
  player_dynamic_attributes
SET attribute_value = 
    CASE
        WHEN attribute_value {operator} {satisfaction_value} < 0 THEN 0
        WHEN attribute_value {operator} {satisfaction_value} > 100 THEN 100
        ELSE attribute_value {operator} {satisfaction_value}
    END
WHERE
attribute_id = 22 
AND  token = '{token}'
'''

SELECT_FRESHNESS_VALUE = '''
SELECT * 
FROM   player_dynamic_attributes
WHERE
attribute_id = 15 
AND  token = '{token}'
'''
INSERT_FRESHNESS_VALUE = '''
INSERT INTO player_dynamic_attributes (
    token,
    attribute_id,
    attribute_value,
    last_update
) VALUES
    ('{token}', 15, {freshness}, NOW());
'''
_TEMPLATE_UPDATE_PLAYERS_ATTRIBUTES = '''
SET
  attribute_value = {attr_value}
WHERE
  player_id = {player_id}
  AND attribute_id = {attr_id};
UPDATE
  player_attributes
'''
# '{"1": 8, "2": 6}'
INSERT_IMPROVEMENT_MATCH_GAME_EFFECTED = '''
INSERT INTO player_match_results (
    match_id,
    token,
    score,
    improved_attributes
)
VALUES
    ({match_id}, '{token}', LEAST({score}, 5), '{improved_attributes}');
'''
INSERT_IMPROVEMENT_MATCH_TRAINING_EFFECTED = '''
INSERT INTO player_training_results (
    training_id,
    token,
    improved_attributes
)
VALUES
    ({training_id}, '{player_id}', '{improved_attributes}');
'''

_TEMPLATE_INSERT_IMPROVMENT_MATCH = '''
UPDATE player_attributes
SET attribute_value = attribute_value + {attr_delta},
    last_update = NOW()
WHERE token = '{player_id}' AND attribute_id = {attr_id} ;
'''

GET_PLAYER_BY_TOKEN = '''
SELECT 
    p.*, 
    s.status_name,
    CONCAT(
        IFNULL(attr_static, ''), 
        IF(attr_static IS NOT NULL AND attr_dynamic IS NOT NULL, ', ', ''), 
        IFNULL(attr_dynamic, '')
    ) AS attributes
FROM players p
LEFT JOIN statuses s ON p.status_id = s.status_id
LEFT JOIN (
    SELECT 
        pa.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pa.attribute_value) SEPARATOR ', ') AS attr_static
    FROM player_attributes pa
    LEFT JOIN attributes a ON pa.attribute_id = a.attribute_id
    GROUP BY pa.token
) pa ON p.token = pa.token
LEFT JOIN (
    SELECT 
        pda.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pda.attribute_value) SEPARATOR ', ') AS attr_dynamic
    FROM player_dynamic_attributes pda
    LEFT JOIN attributes a ON pda.attribute_id = a.attribute_id
    GROUP BY pda.token
) pda ON p.token = pda.token
WHERE p.token = '{token}'
GROUP BY p.token, s.status_name, pa.attr_static, pda.attr_dynamic
ORDER BY p.status_id, p.creation_date DESC, p.player_id
'''
GET_ACCOUNT_PLAYERS = '''
SELECT 
    p.*, 
    s.status_name,
    CONCAT(
        IFNULL(attr_static, ''), 
        IF(attr_static IS NOT NULL AND attr_dynamic IS NOT NULL, ', ', ''), 
        IFNULL(attr_dynamic, '')
    ) AS attributes
FROM players p
LEFT JOIN statuses s ON p.status_id = s.status_id
LEFT JOIN (
    SELECT 
        pa.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pa.attribute_value) SEPARATOR ', ') AS attr_static
    FROM player_attributes pa
    LEFT JOIN attributes a ON pa.attribute_id = a.attribute_id
    GROUP BY pa.token
) pa ON p.token = pa.token
LEFT JOIN (
    SELECT 
        pda.token, 
        GROUP_CONCAT(CONCAT(a.attribute_name, ': ', pda.attribute_value) SEPARATOR ', ') AS attr_dynamic
    FROM player_dynamic_attributes pda
    LEFT JOIN attributes a ON pda.attribute_id = a.attribute_id
    GROUP BY pda.token
) pda ON p.token = pda.token
WHERE p.user_id = '{user_id}'
GROUP BY p.token, s.status_name, pa.attr_static, pda.attr_dynamic
ORDER BY p.status_id, p.creation_date DESC, p.player_id
'''

UPDATE_PLAYER_STATUS = '''
UPDATE
  players
SET
  status_id = {status_id}, user_id = '{user_id}'
WHERE
  token = '{token}';
'''

GET_TEAM = '''
SELECT 
    t.team_id,
    t.team_name,
    t.logo_url AS team_logo,
    t.home_color,
    t.away_color,
    t.creation_date,
    lt.league_id
FROM 
    teams t
LEFT JOIN 
    league_teams lt
ON 
    t.team_id = lt.team_id
WHERE 
    t.user_id = '{user_id}';

'''

GET_FORMATIONS = '''
SELECT 
    tfp.team_id,
    f.formation_id,
    tfp.default_formation,
    COALESCE(tfp.formation_positions, f.formation_positions) AS formation_positions,
    tfp.attack_score,
    tfp.defense_score,
    tfp.midfield_score,
    f.formation_name
FROM 
    formations f
LEFT JOIN 
    team_formation_positions tfp
ON 
    f.formation_id = tfp.formation_id AND tfp.team_id = "{team_id}"
WHERE 
    tfp.team_id = "{team_id}" OR tfp.team_id IS NULL
'''
GET_TEAM_DEFAULT_FORMATION = '''
SELECT 
 *
FROM 
    team_formation_positions 
WHERE 
    team_id = {team_id} AND default_formation = 1
'''

UPDATE_PLAYERS_TEAM = '''
UPDATE players
SET team_id = {team_id}
WHERE user_id = '{user_id}';
'''

UPDATE_RESET_DEFAULT_FORMATION = '''
UPDATE team_formation_positions
SET default_formation = 0
WHERE team_id = {team_id};
'''

INSERT_USER_LOGIN = '''
INSERT INTO users (user_id, first_login, last_login, login_count)
VALUES ('{user_id}', NOW(), NOW(), 1)
ON DUPLICATE KEY UPDATE
    last_login = NOW(),
    login_count = login_count + 1
'''
SELECT_ALL_LEAGUES = '''
SELECT
    leagues.league_id,
    leagues.league_name,
    leagues.logo_url,
    leagues.start_date,
    leagues.match_day,
    leagues.match_hour,
    leagues.required_number_of_teams,
    leagues.status_id,
    statuses.status_name,
    COUNT(league_teams.team_id) AS team_count,
    MAX(CASE WHEN teams.user_id = '{user_id}' THEN teams.team_id ELSE NULL END) AS user_team_id
FROM
    leagues
LEFT JOIN
    league_teams ON leagues.league_id = league_teams.league_id
LEFT JOIN
    teams ON league_teams.team_id = teams.team_id
LEFT JOIN
    statuses ON leagues.status_id = statuses.status_id
GROUP BY
    leagues.league_id, statuses.status_name
ORDER BY
    MAX(teams.user_id = '{user_id}') DESC;

'''
SELECT_LEAGUE_TEAMS = '''
SELECT team_id
FROM league_teams
WHERE league_id = {league_id};
'''
INSERT_JOIN_LEAGUE = '''
INSERT INTO league_teams (league_id, team_id)
VALUES ({league_id}, {team_id});
'''
INSERT_JOIN_LEAGUE_1 = '''
INSERT into league_standings (league_id,team_id,matches_played,points,goals_scored,goals_conceded)
VALUES ({league_id}, {team_id},0,0,0,0);
'''

UPDATE_MATCH_RESULT = '''
UPDATE
  matches
SET
  result = '{match_result}'
WHERE
  match_id = {match_id};
'''

UPDATE_MATCH_TIME = '''
UPDATE
  matches
SET
  time_played_mins = '{time_played_mins}'
WHERE
  match_id = {match_id};
'''

INSERT_INIT_MATCHES = '''
INSERT INTO
  matches(
    league_id,
    match_day,
    home_team_id,
    away_team_id,
    match_datetime)
VALUES
  {matches_values}
'''
_INSERT_INIT_MATCHES_VALUES = '''
({league_id}, {match_day}, {home_team_id}, {away_team_id}, {match_datetime})
'''
SELECT_TEAM_LEAGUES = '''
SELECT
    leagues.league_id,
    leagues.league_name,
    leagues.logo_url,
    leagues.start_date,
    leagues.match_day,
    leagues.match_hour,
    (SELECT COUNT(lt.team_id)
     FROM league_teams lt
     WHERE lt.league_id = leagues.league_id) AS team_count
FROM
    leagues
LEFT JOIN
    league_teams ON leagues.league_id = league_teams.league_id
WHERE
    league_teams.team_id = '{team_id}';

'''

SELECT_LEAGUE_TABLE = '''
SELECT 
    ls.team_id,
    t.team_name,
    t.logo_url,
    ls.matches_played,
    ls.points,
    ls.goal_difference,
    ls.goals_scored,
    ls.goals_conceded,
    ls.Win,
    ls.Draw,
    ls.Lost,
    l.league_name
FROM 
    league_standings ls
JOIN 
    teams t 
ON 
    ls.team_id = t.team_id
    JOIN 
    leagues l 
ON 
    ls.league_id = l.league_id
WHERE 
    ls.league_id = {league_id} 
ORDER BY   
  ls.points DESC,
  ls.goal_difference DESC,
  ls.goals_scored DESC;
'''
SELECT_MATCHES_BY_LEAGUE_ID = '''
SELECT 
    m.match_id,
    m.league_id,
    l.league_name,
    m.match_datetime,
    home_team.team_id AS home_team_id,
    home_team.team_name AS home_team_name,
    home_team.logo_url AS home_team_logo,
    away_team.team_id AS away_team_id,
    away_team.team_name AS away_team_name,
    away_team.logo_url AS away_team_logo,
    m.result,
    m.match_day,
    m.match_datetime
FROM 
    matches m
JOIN 
    leagues l 
ON 
    m.league_id = l.league_id
JOIN 
    teams home_team 
ON 
    m.home_team_id = home_team.team_id
JOIN 
    teams away_team 
ON 
    m.away_team_id = away_team.team_id
WHERE 
    m.league_id = {league_id} AND m.match_day = {match_day}
ORDER BY 
    m.match_datetime ASC;
'''
GET_CURRENT_OR_NEXT_MATCH_DAY = '''
SELECT
  match_day
FROM
  matches
WHERE
  match_datetime >= CURRENT_DATE()
ORDER BY
  match_datetime
LIMIT
  1;
'''
SELECT_MATCHES_FOR_CURRENT_DAY = '''
SELECT *
FROM matches
WHERE DATE(match_datetime) = CURRENT_DATE()
AND HOUR(match_datetime) = HOUR(NOW())
AND result IS NULL;
'''

SELECT_MATCHES_BY_MATCH_DAY = '''
SELECT *
FROM matches
WHERE match_day = {match_day}
AND result IS NULL
ORDER BY match_datetime ASC;
'''


SELECT_MATCH_RESULT_DETAILS = '''
SELECT 
    JSON_OBJECT(
        'team_id', m.home_team_id,
        'team_name', home_team.team_name,
        'formation', m.home_team_formation,
        'formation_name', m.home_team_formation_name,
        'players', (
            SELECT JSON_ARRAYAGG(
                JSON_OBJECT(
                    'player_token', p.token,
                    'player_name', p.name,
                    'player_image', p.image_url,
                    'player_score', IFNULL(pmr.score, 0), -- הוספת player_score כמו בשאילתא המקורית
                    'improved_attributes', IFNULL(pmr.improved_attributes, JSON_OBJECT()) -- הוספת improved_attributes כמו במקור
                )
            )
            FROM players p
            LEFT JOIN player_match_results pmr 
                ON pmr.token = p.token AND pmr.match_id = m.match_id -- חיבור לתוצאות משחק עבור הוספת score
            WHERE JSON_CONTAINS(m.home_team_formation, JSON_QUOTE(p.token), '$')
        )
    ) AS home_team_details,

    JSON_OBJECT(
        'team_id', m.away_team_id,
        'team_name', away_team.team_name,
        'formation', m.away_team_formation,
        'formation_name', m.away_team_formation_name,
        'players', (
            SELECT JSON_ARRAYAGG(
                JSON_OBJECT(
                    'player_token', p2.token,
                    'player_name', p2.name,
                    'player_image', p2.image_url,
                    'player_score', IFNULL(pmr2.score, 0), -- הוספת player_score
                    'improved_attributes', IFNULL(pmr2.improved_attributes, JSON_OBJECT()) -- הוספת improved_attributes
                )
            )
            FROM players p2
            LEFT JOIN player_match_results pmr2 
                ON pmr2.token = p2.token AND pmr2.match_id = m.match_id
            WHERE JSON_CONTAINS(m.away_team_formation, JSON_QUOTE(p2.token), '$')
        )
    ) AS away_team_details

FROM 
    matches m
JOIN 
    teams home_team ON m.home_team_id = home_team.team_id
JOIN 
    teams away_team ON m.away_team_id = away_team.team_id
WHERE 
    m.match_id = {match_id};


'''
SELECT_MATCH_DETAILS = '''
SELECT 
    md.detail_id,
    md.match_id,
    md.token,
    md.action_id,
    a.action_name,
    md.action_timestamp,
    p.token,
    p.name AS player_name,
    p.image_url,
    t.team_name AS player_team_name,
    t.logo_url AS team_logo_url
FROM 
    match_details md
LEFT JOIN 
    actions a 
    ON md.action_id = a.action_id
LEFT JOIN
    players p
    ON p.token = md.token
LEFT JOIN
    teams t
    ON md.team_id = t.team_id 
WHERE 
    md.match_id = {match_id}
'''

INSERT_MATCH_DETAILS = '''
INSERT INTO
  match_details ( match_id,
    action_id,
    action_timestamp,
    token, 
    team_id)
VALUES
  ({match_id},{action_id}, '{action_timestamp}', '{token}', {team_id});
'''

SELECT_TRAINING_TYPES = '''
SELECT *
FROM training_types;
'''
SELECT_TRAINING_LEVELS = '''
SELECT * 
FROM training_intensities
'''

INSERT_TEAM_TRAINING = '''
INSERT INTO team_training (
    team_id,
    training_type_id,
    intensity_id,
    participating_players,
    start_time,
    end_time,
    creation_time
)
VALUES (
    {team_id},
    {training_type_id},
    {intensity_id},
    '{participating_players}', 
    NOW(), 
    DATE_ADD(NOW(), INTERVAL (
        SELECT duration_minutes + recovery_minutes 
        FROM training_intensities 
        WHERE intensity_id = {intensity_id}
    ) MINUTE), 
    NOW()
);
'''
SELECT_TRANING_INTENSITY = '''
SELECT * 
FROM training_intensities
'''

SELECT_TEAM_TRAINING_BY_ID = '''

SELECT
  team_training.training_id,
  team_training.team_id,
  team_training.training_type_id,
  team_training.intensity_id,
  team_training.participating_players,
  team_training.start_time,
  team_training.end_time,
  team_training.creation_time,
  training_types.training_name,
  training_intensities.intensity_name,
  training_intensities.duration_minutes,
  training_intensities.recovery_minutes,
  training_intensities.improvement_factor
FROM
  team_training
INNER JOIN
  training_types
ON
  team_training.training_type_id = main_game.training_types.training_id
INNER JOIN
  training_intensities
ON
  team_training.intensity_id = training_intensities.intensity_id
WHERE
  team_training.training_id = {training_id};
'''

SELECT_TEAM_TRAININGS = '''
SELECT
  team_training.*,
  training_types.training_name,
  training_types.link_icon,
  training_types.affected_attributes,
  training_intensities.intensity_name,
  training_intensities.duration_minutes,
  training_intensities.recovery_minutes,
  training_intensities.improvement_factor
FROM
  team_training
JOIN
  training_types
ON
  team_training.training_type_id = training_types.training_id
JOIN
  training_intensities
ON
  team_training.intensity_id = training_intensities.intensity_id
WHERE
  team_id = {team_id}
'''

IS_TRAINABLE = '''
WITH recent_match AS (
    SELECT TIMESTAMPDIFF(SECOND, match_datetime, NOW()) AS seconds_since_last
    FROM matches
    WHERE (home_team_id = {team_id} OR away_team_id = {team_id})
    AND match_datetime <= NOW()
    ORDER BY match_datetime DESC
    LIMIT 1
),
upcoming_match AS (
    SELECT TIMESTAMPDIFF(SECOND, NOW(), match_datetime) AS seconds_until_next
    FROM matches
    WHERE (home_team_id = {team_id} OR away_team_id = {team_id})
    AND match_datetime > NOW()
    ORDER BY match_datetime ASC
    LIMIT 1
),
training_check AS (
    SELECT COUNT(*) AS has_active_training,
           COALESCE(MIN(TIMESTAMPDIFF(SECOND, NOW(), end_time)), 0) AS seconds_until_training_ends
    FROM team_training
    WHERE team_id = {team_id} AND end_time > NOW()
)
SELECT 
    CASE 
        WHEN tc.has_active_training > 0 THEN 0  
        WHEN rm.seconds_since_last IS NOT NULL AND rm.seconds_since_last < 21600 THEN 0 
        WHEN um.seconds_until_next IS NOT NULL AND um.seconds_until_next < 108000 THEN 0   
        ELSE 1
    END AS IS_TRAINABLE,

    CASE 
        WHEN tc.has_active_training > 0 THEN tc.seconds_until_training_ends  
        WHEN rm.seconds_since_last IS NOT NULL AND rm.seconds_since_last < 21600 THEN 21600 - rm.seconds_since_last
        WHEN um.seconds_until_next IS NOT NULL AND um.seconds_until_next < 108000 THEN 108000 - um.seconds_until_next
        ELSE 0  
    END AS SECONDS_UNTIL_TRAINABLE

FROM training_check tc
LEFT JOIN recent_match rm ON TRUE
LEFT JOIN upcoming_match um ON TRUE
LIMIT 1;
'''
SELECT_NEXT_TIME_MATCH = '''
SELECT 
    CASE 
        WHEN TIMESTAMPDIFF(MINUTE, NOW(), match_datetime) <= 15 
        THEN CONCAT(
            FLOOR(TIMESTAMPDIFF(SECOND, NOW(), match_datetime) / 86400), ' days, ',
            FLOOR(MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 86400) / 3600), ' hours, ',
            FLOOR(MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 3600) / 60), ' minutes, ',
            MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 60), ' seconds - Note: Changes in the formation made now will not affect the upcoming match.'
        )
        ELSE CONCAT(
            FLOOR(TIMESTAMPDIFF(SECOND, NOW(), match_datetime) / 86400), ' days, ',
            FLOOR(MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 86400) / 3600), ' hours, ',
            FLOOR(MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 3600) / 60), ' minutes, ',
            MOD(TIMESTAMPDIFF(SECOND, NOW(), match_datetime), 60), ' seconds'
        )
    END AS time_until_match
FROM 
    matches
WHERE 
    (home_team_id = {team_id} OR away_team_id = {team_id})
    AND match_datetime >= NOW()
ORDER BY 
    match_datetime ASC
LIMIT 1;

'''

SET_FORMATION_FOR_MATCH = '''
UPDATE matches m
JOIN (
    SELECT 
        m.match_id,
        home_form.formation_positions AS home_default_formation,
        hf.formation_name AS home_formation_name,
        away_form.formation_positions AS away_default_formation,
        af.formation_name AS away_formation_name
    FROM matches m
    LEFT JOIN team_formation_positions AS home_form
        ON m.home_team_id = home_form.team_id AND home_form.default_formation = 1
    LEFT JOIN formations AS hf
        ON home_form.formation_id = hf.formation_id
    LEFT JOIN team_formation_positions AS away_form
        ON m.away_team_id = away_form.team_id AND away_form.default_formation = 1
    LEFT JOIN formations AS af
        ON away_form.formation_id = af.formation_id
    WHERE m.match_datetime > NOW() 
      AND m.result IS NULL
      AND TIMESTAMPDIFF(MINUTE, NOW(), m.match_datetime) > 15
) AS formations_to_update
ON m.match_id = formations_to_update.match_id
SET 
    m.home_team_formation = formations_to_update.home_default_formation,
    m.home_team_formation_name = formations_to_update.home_formation_name,
    m.away_team_formation = formations_to_update.away_default_formation,
    m.away_team_formation_name = formations_to_update.away_formation_name;
'''

SET_TEAMS_FORMATIONS_FOR_MATCH = '''
UPDATE matches AS mtc
LEFT JOIN team_formation_positions AS tfp_home 
    ON mtc.home_team_id = tfp_home.team_id AND tfp_home.default_formation = 1
LEFT JOIN team_formation_positions AS tfp_away 
    ON mtc.away_team_id = tfp_away.team_id AND tfp_away.default_formation = 1
SET 
    mtc.home_team_formation = COALESCE(tfp_home.formation_positions, mtc.home_team_formation),
    mtc.home_team_formation_name = COALESCE(tfp_home.formation_id, mtc.home_team_formation_name),
    mtc.away_team_formation = COALESCE(tfp_away.formation_positions, mtc.away_team_formation),
    mtc.away_team_formation_name = COALESCE(tfp_away.formation_id, mtc.away_team_formation_name)
WHERE 
    mtc.match_id = {match_id};

'''
GET_TRAINABLE_PLAYERS = '''
SELECT DISTINCT p.token
FROM players p
JOIN teams t ON p.user_id = t.user_id 
LEFT JOIN team_training tt 
    ON tt.team_id = t.team_id 
    AND tt.end_time > NOW()
    AND JSON_CONTAINS(tt.participating_players, JSON_QUOTE(p.token), '$') 
LEFT JOIN (
    SELECT pmr.token
    FROM player_match_results pmr
    JOIN matches m ON pmr.match_id = m.match_id
    WHERE m.match_datetime BETWEEN DATE_SUB(NOW(), INTERVAL 6 HOUR) AND NOW()
) recent_matches 
ON recent_matches.token = p.token
WHERE t.team_id = {team_id}
AND (tt.participating_players IS NULL OR JSON_CONTAINS(tt.participating_players, JSON_QUOTE(p.token), '$') = 0)
AND recent_matches.token IS NULL;

'''
SELECT_TRAINING_TEAM_HISTORY = '''
SELECT
    tt.training_id,
    tt.team_id,
    t.team_name,
    tt.training_type_id,
    tt.intensity_id,
    tt.start_time,
    tt.end_time,
    tt.creation_time,
    training_types.training_name,
    training_intensities.intensity_name
FROM team_training tt
JOIN teams t ON tt.team_id = t.team_id
JOIN training_types tt_type ON tt.training_type_id = tt_type.training_id
JOIN training_intensities tt_intensity ON tt.intensity_id = tt_intensity.intensity_id
WHERE tt.team_id = {team_id}
AND tt.end_time < NOW()
ORDER BY tt.end_time DESC
LIMIT 5 OFFSET {offset};
'''

SELECT_TRAINING_DETAILS = '''
SELECT
    p.token,
    p.name AS player_name,
    p.image_url,
    (
        SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'improved_attributes', ptr.improved_attributes,
                'last_update', ptr.last_update
            )
        )
        FROM player_training_results ptr
        WHERE ptr.token = p.token AND ptr.training_id = tt.training_id
    ) AS improvements
FROM players p
JOIN team_training tt
    ON JSON_CONTAINS(tt.participating_players, JSON_QUOTE(p.token), '$')
WHERE tt.training_id = {training_id};

'''
GET_FRESHNESS_LAST_EFFORT = '''
WITH last_match AS (
    SELECT m.match_id, m.match_datetime, m.result, m.time_played_mins
    FROM matches m
    WHERE (JSON_CONTAINS(m.home_team_formation, JSON_QUOTE('{token}'), '$')
           OR JSON_CONTAINS(m.away_team_formation, JSON_QUOTE('{token}'), '$'))
      AND m.match_datetime <= NOW()
    ORDER BY m.match_datetime DESC
    LIMIT 1
),
last_training AS (
    SELECT tt.start_time, ti.duration_minutes
    FROM team_training tt
    JOIN training_intensities ti ON tt.intensity_id = ti.intensity_id
    WHERE JSON_CONTAINS(tt.participating_players, JSON_QUOTE('{token}'), '$')
    ORDER BY tt.start_time DESC
    LIMIT 1
)

SELECT
    CASE
        WHEN (SELECT COUNT(*) FROM last_match WHERE result IS NULL) > 0
        THEN 'in_match'

    WHEN (SELECT COUNT(*) FROM last_match WHERE NOW() < DATE_ADD(match_datetime, INTERVAL time_played_mins MINUTE)) > 0
    THEN 'in_training'

    WHEN (SELECT COUNT(*) FROM last_training WHERE NOW() < DATE_ADD(start_time, INTERVAL duration_minutes MINUTE)) > 0
    THEN 'in_training'

    ELSE 'last_effort'
END AS status,

CASE 
    WHEN (SELECT COUNT(*) FROM last_match WHERE result IS NULL) > 0
    THEN 'To be updated at the end of the match'

    ELSE GREATEST(
        IFNULL((SELECT MAX(DATE_ADD(match_datetime, INTERVAL time_played_mins MINUTE)) FROM last_match), '0000-00-00 00:00:00'),
        IFNULL((SELECT MAX(DATE_ADD(start_time, INTERVAL duration_minutes MINUTE)) FROM last_training), '0000-00-00 00:00:00')
    )
END AS last_effort_time;

'''
SELECT_CURRWNT_TRAINING = '''
SELECT 
tt.training_id,
tt.start_time,
tt.end_time,
tt.training_type_id,
tt.intensity_id,
tt.participating_players,
tt.creation_time,
JSON_ARRAYAGG(
JSON_OBJECT('token', p.token,'name', p.name,'image_url', p.image_url)
) AS players
FROM team_training tt
LEFT JOIN JSON_TABLE(
tt.participating_players COLLATE utf8mb4_general_ci, 
'$[*]' COLUMNS (token VARCHAR(255) PATH '$')
) jt ON jt.token IS NOT NULL
LEFT JOIN players p 
ON p.token COLLATE utf8mb4_general_ci = jt.token COLLATE utf8mb4_general_ci
WHERE tt.team_id = {team_id}
AND tt.start_time <= NOW() 
AND tt.end_time > NOW()
GROUP BY tt.training_id;
'''
GET_BEST_PLAYER_BY_LEAGUE = '''
SELECT 
    a.action_name, 
    p.name AS player_name, 
    p.image_url AS player_image, 
    COALESCE(t.team_name, ut.team_name) AS team_name, 
    COALESCE(t.logo_url, ut.logo_url) AS team_image, 
    COUNT(md.action_id) AS action_count
FROM match_details md
JOIN matches m ON md.match_id = m.match_id
JOIN actions a ON md.action_id = a.action_id
JOIN players p ON md.token = p.token
LEFT JOIN teams t ON p.team_id = t.team_id 
LEFT JOIN users u ON p.user_id = u.user_id  
LEFT JOIN teams ut ON u.user_id = ut.user_id  
WHERE m.league_id = {league_id}
AND a.action_id IN (1, 2, 7,8)  
GROUP BY a.action_name, p.name, p.image_url, COALESCE(t.team_name, ut.team_name), COALESCE(t.logo_url, ut.logo_url)
ORDER BY a.action_name ASC, action_count DESC;

'''
GET_CURRENT_TRAINING_BY_TEAM = '''


'''


SELECT_PLAYERS_TARINING_HISTORY_BY_TEAM_ID = '''
SELECT 
    p.token,
    MAX(tt.end_time) AS last_training_date,
    COUNT(CASE WHEN tt.intensity_id = 3 AND tt.start_time >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) AS hard_trainings_last_7_days
FROM 
    team_training tt
JOIN 
    players p ON JSON_CONTAINS(tt.participating_players, JSON_QUOTE(p.token), '$')
WHERE 
    tt.team_id = {team_id}
GROUP BY 
    p.token;
'''

INSERT_MAN_OF_THE_MATCH = '''
INSERT INTO
  trophies (trophy_id,
    token,
    match_id,
    awarded_at)
VALUES
  (1, '{token}', {match_id}, NOW());
'''

##################################COMPETITION ###################################

GET_COMPETITION_PLAYERS = '''
SELECT 
    p.token, 
    cp.competition_id,
    JSON_OBJECTAGG(attr_name, attr_value) AS attributes
FROM players p
INNER JOIN competition_participants cp ON cp.token = p.token
LEFT JOIN (
    SELECT 
        token,
        attribute_name AS attr_name,
        attribute_value AS attr_value
    FROM (
        SELECT pa.token, a.attribute_name, pa.attribute_value
        FROM player_attributes pa
        LEFT JOIN attributes a ON pa.attribute_id = a.attribute_id
        UNION ALL
        SELECT pda.token, a.attribute_name, pda.attribute_value
        FROM player_dynamic_attributes pda
        LEFT JOIN attributes a ON pda.attribute_id = a.attribute_id
    ) all_attrs
) attrs ON p.token = attrs.token
WHERE cp.competition_id = {competition_id}
GROUP BY p.token, cp.competition_id;
'''

INSERT_COMPETITION_RESULTS = '''
INSERT INTO competition_results (
   competition_id,
    token,
    score,
    rank_position,
    is_winner
    )
VALUES
    ({competition_id}, '{token}', '{score}', {rank_position}, {is_winner});
'''

SELECT_COMPETITIONS_FOR_CURRENT_TIME = '''
SELECT 
    c.id as competition_id,
    c.competition_type_id,
    ct.name as competition_type_name,
    c.start_time,
    c.end_time,
    c.status_id,
    c.group_id
FROM competitions c
JOIN competition_types ct ON c.competition_type_id = ct.id
WHERE c.start_time <= NOW()
AND c.end_time >= NOW()
AND c.status_id = 14;
'''

UPDATE_COMPETITION_STATUS = '''
UPDATE competitions
SET status_id = {status_id}
WHERE id = {competition_id};
'''

UPDATE_MATCH_RESULT_CANCELLED = '''
UPDATE matches
SET result = 'CANCELED'
WHERE match_id = {match_id};
'''

################################## END COMPETITION ##############################