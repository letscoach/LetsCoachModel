import requests

TOKEN = "7305962895:AAEnGATWNOkgaeutfKs3_X37efg9P0jpK8E"
GROUP_ID = "-1002330022427"

def send_log_message(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": GROUP_ID, "text": f'DEV: {message}')
    response = requests.get(url, params=params)
    print(response.json())

# res = requests.post('https://us-central1-zinc-strategy-446518-s7.cloudfunctions.net/LetscoachModel', json=dict(away_team_id=68,home_team_id=67,match_id=6), timeout=1000000)
# print(res)
