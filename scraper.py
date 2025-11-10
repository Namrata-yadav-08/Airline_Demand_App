from opensky_api import OpenSkyApi
from dotenv import load_dotenv
import pandas as pd
import random
import os

load_dotenv()

username = os.getenv("OPENSKY_USERNAME")
password = os.getenv("OPENSKY_PASSWORD")

bbox = (-44.0, -10.0, 113.0, 154.0)  

def fetch_live_flights_over_aus():
    api = OpenSkyApi(username,password)
    print("Fetching live flight data over Australia...")

    states = api.get_states(bbox=bbox)

    if not states or not states.states:
        print("⚠️ No data found.")
        return []

    flights = []
    for s in states.states:
        flights.append({
            "origin": s.origin_country or "Unknown",
            "destination": f"AUS-{random.randint(1, 5)}",
            "price": round(random.uniform(150, 500), 2),
            "demand_score": random.randint(40, 100)
        })

    return flights

def save_to_csv(filename="data/live_flights.csv"):
    flights = fetch_live_flights_over_aus()
    if flights:
        os.makedirs("data", exist_ok=True) 
        df = pd.DataFrame(flights)
        df.to_csv(filename, index=False)
        print(f"✅ Saved {len(flights)} flights to {filename}")
    else:
        print("❌ No flight data to save.")

if __name__ == "__main__":
    try:
        save_to_csv()
    except Exception as e:
        print("🔥 ERROR in scraper.py:", str(e))
        raise 
