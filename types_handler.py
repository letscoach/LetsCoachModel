try:
    from Game.Matches import game_launcher
except Exception as e:
    import traceback
    print(f"ERROR during imports: {e}")
    print(traceback.format_exc())


def match_handler(data):
    return game_launcher({
        'away_team_id': data.get('away_team_id'),
        'home_team_id': data.get('home_team_id'),
        'match_id': data.get('match_id'),
        'kind': data.get('kind', 'league'),
    })


ACTION_MAP = {
    'match': match_handler,
}