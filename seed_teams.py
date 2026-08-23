from supabase import create_client
import tomllib
import random

# -----------------------------
# READ SUPABASE CREDENTIALS
# -----------------------------

with open(".streamlit/secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

url = secrets["supabase"]["url"]
key = secrets["supabase"]["key"]

supabase = create_client(url, key)

# -----------------------------
# CREATE 30 TEAMS
# -----------------------------

# Fixed seed = same PINs if you ever rerun this script
random.seed(42)

used_pins = set()
teams = []

for i in range(1, 31):

    while True:
        pin = str(random.randint(1000, 9999))
        if pin not in used_pins:
            used_pins.add(pin)
            break

    teams.append({
        "id": i,
        "teamname": f"Team {i}",
        "pin": pin,
        "cash": 500000,
        "debt": 0,
        "ev": 1000000
    })

# Upsert means Team 1 and Team 2 will be updated rather than duplicated
response = (
    supabase
    .table("teams")
    .upsert(teams)
    .execute()
)

print("30 teams created successfully.")
print()
print("TEAM PINS")
print("-" * 25)

for team in teams:
    print(f"{team['teamname']}: {team['pin']}")