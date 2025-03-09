tables = {
    "player_attributes": [
        'player_id',
        'attribute_id',
        'attribute_value'
    ],
    "players": [
        "name",
        "birthday",
        "team_id",
        "status_id",
        "image_url",
        "opensea_url",
        "description",
        "last_update",
        "token",
        "user_id"
    ],
    "player_attributes": [
        'player_id',
        'attribute_id',
        'attribute_value',
        'last_update'
    ],
    "teams": [
        "team_name",
        "logo_url",
        "home_color",
        "away_color",
        "creation_date",
        "user_id"
    ],
    "team_formation_positions": [
        "team_id",
        "formation_id",
        "default_formation",
        "formation_positions",
        'midfield_score',
        "defense_score",
        "attack_score"
    ],
    "matches": [
        "league_id",
        "match_day",
        "home_team_id",
        "away_team_id",
        "match_datetime"
    ]

}

ATTRIBUTES = {
    "Dribble": 1,
    "Trainability": 2,
    "Tackle_Precision": 3,
    "Heading": 4,
    "Aggression": 5,
    "Pass_Precision": 6,
    "Injury_Risk": 7,
    "Leadership": 8,
    "Shoot_Precision": 9,
    "GK_Kicking": 10,
    "Physicality": 11,
    "Endurance": 12,
    "Speed": 13,
    "Reflexes": 14,
    "Game_vision": 16,
    "Diving": 17,
    "Shoot_Power": 18
}
ATTR_REVERS = {str(v): k for k, v in ATTRIBUTES.items()}