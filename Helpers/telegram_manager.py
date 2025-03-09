import requests

TOKEN = "7305962895:AAEnGATWNOkgaeutfKs3_X37efg9P0jpK8E"
GROUP_ID = "-1002330022427"

def send_log_message(message):

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": GROUP_ID, "text": message}
    response = requests.get(url, params=params)
    print(response.json())

