import requests

TOKEN = "MTMxODcwOTczNTA1MDE4MjcxNw.GW-vQS.X_D9GUt22HmOgVtcsn_YOYXyzy7tsVqbW0fsWg"
url = "https://discord.com/api/v10/users/@me"
headers = {"Authorization": f"Bot {TOKEN}"}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    print("Token is valid!")
else:
    print(f"Invalid token. Status code: {response.status_code}, Response: {response.text}")
