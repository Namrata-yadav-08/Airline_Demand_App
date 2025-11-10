# from flask import Flask, render_template, request, redirect, url_for, flash
# import pandas as pd
# from dotenv import load_dotenv
# import requests
# import subprocess
# import os
# import sys

# load_dotenv() 

# app = Flask(__name__)
# app.secret_key = os.getenv("SECRET_KEY", "fallback123")


# def load_data():
#     if os.path.exists("data/live_flights.csv"):
#         return pd.read_csv("data/live_flights.csv")
#     else:
#         return pd.DataFrame(columns=["origin", "destination", "price", "demand_score"])  # fallback structure


# @app.route("/", methods=["GET", "POST"])
# def home():
#     df = load_data()
#     selected_origin = None
#     filtered_data = df.copy()
#     popular_routes = (
#         df.groupby(["origin", "destination"])
#         .size()
#         .reset_index(name="count")
#         .sort_values("count", ascending=False)
#         .head(5)
#     )
#     popular_routes = popular_routes.to_dict(orient="records")


#     if request.method == "POST":
#         selected_origin = request.form.get("origin")
#         if selected_origin:
#             filtered_data = df[df["origin"] == selected_origin]

#     origin_options = sorted(df["origin"].dropna().unique())
#     chart_labels = filtered_data["destination"].tolist() if "destination" in filtered_data else []
#     chart_values = filtered_data["demand_score"].tolist() if "demand_score" in filtered_data else []

#     return render_template(
#         "index.html",
#         data=filtered_data.to_dict(orient="records"),
#         origin_options=origin_options,
#         selected_origin=selected_origin,
#         chart_labels=chart_labels,
#         chart_values=chart_values,
#         popular_routes=popular_routes  
#     )


# @app.route("/submit", methods=["POST"])
# def submit():
#     df = load_data()
#     selected_origin = request.form.get("origin")
#     filtered_data = df.copy()
#     if selected_origin:
#         filtered_data = df[df["origin"] == selected_origin]

#     payload = filtered_data.to_dict(orient="records")
#     response = requests.post(
#         "https://httpbin.org/post",
#         json=payload,
#         headers={"Content-Type": "application/json"}
#     )

#     if response.status_code == 200:
#         flash("✅ Data submitted successfully!")
#     else:
#         flash("❌ Failed to submit data.")

#     return redirect(url_for("home"))


# @app.route("/fetch")
# def fetch_latest_data():
#     try:
#         script_path = os.path.join(os.path.dirname(__file__), "scraper.py")
#         subprocess.run([sys.executable, script_path], check=True)
#         flash("✅ Fetched latest flight data from OpenSky.")
#     except Exception as e:
#         flash(f"❌ Failed to fetch data: {e}")
#     return redirect(url_for("home"))


# if __name__ == "__main__":
#     import os
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
from flask import Flask, render_template, request, redirect, url_for, flash
from opensky_api import OpenSkyApi
from dotenv import load_dotenv
import pandas as pd
import random
import os

# Load environment variables
load_dotenv()

# Flask setup
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# Credentials for OpenSky
username = os.getenv("OPENSKY_USERNAME")
password = os.getenv("OPENSKY_PASSWORD")

# Default bounding box for Australia
bbox = (-44.0, -10.0, 113.0, 154.0)


# ======================================================
# 🚀 1. Fetch & Save Flight Data (merged scraper logic)
# ======================================================
def fetch_live_flights_over_aus():
    print("Fetching live flight data over Australia...")
    api = OpenSkyApi(username, password)

    try:
        states = api.get_states(bbox=bbox)
    except Exception as e:
        print("⚠️ OpenSky API error:", str(e))
        states = None

    # If no data, fallback gracefully
    if not states or not states.states:
        print("⚠️ No live data from OpenSky — using fallback demo dataset.")
        return [
            {"origin": "SYD", "destination": "MEL", "price": 210.5, "demand_score": 85},
            {"origin": "PER", "destination": "BNE", "price": 305.0, "demand_score": 72},
            {"origin": "BNE", "destination": "ADL", "price": 270.0, "demand_score": 68},
        ]

    # Build flight list from OpenSky states
    flights = []
    for s in states.states[:100]:
        flights.append({
            "origin": s.origin_country or "Unknown",
            "destination": f"AUS-{random.randint(1, 5)}",
            "price": round(random.uniform(150, 500), 2),
            "demand_score": random.randint(40, 100)
        })

    return flights


def save_to_csv(filename="data/live_flights.csv"):
    flights = fetch_live_flights_over_aus()
    os.makedirs("data", exist_ok=True)
    df = pd.DataFrame(flights)
    df.to_csv(filename, index=False)
    print(f"✅ Saved {len(flights)} flights to {filename}")


# ======================================================
# 🧭 2. Helper: Load flight data
# ======================================================
def load_data():
    if os.path.exists("data/live_flights.csv"):
        return pd.read_csv("data/live_flights.csv")
    else:
        return pd.DataFrame(columns=["origin", "destination", "price", "demand_score"])


# ======================================================
# 🏠 3. Routes
# ======================================================
@app.route("/", methods=["GET", "POST"])
def home():
    df = load_data()
    selected_origin = None
    filtered_data = df.copy()

    # Popular route summary
    popular_routes = (
        df.groupby(["origin", "destination"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(5)
        .to_dict(orient="records")
    )

    # Handle form filtering
    if request.method == "POST":
        selected_origin = request.form.get("origin")
        if selected_origin:
            filtered_data = df[df["origin"] == selected_origin]

    # Prepare dropdown and chart data
    origin_options = sorted(df["origin"].dropna().unique())
    chart_labels = filtered_data.get("destination", []).tolist() if not filtered_data.empty else []
    chart_values = filtered_data.get("demand_score", []).tolist() if not filtered_data.empty else []

    return render_template(
        "index.html",
        data=filtered_data.to_dict(orient="records"),
        origin_options=origin_options,
        selected_origin=selected_origin,
        chart_labels=chart_labels,
        chart_values=chart_values,
        popular_routes=popular_routes
    )


@app.route("/submit", methods=["POST"])
def submit():
    df = load_data()
    selected_origin = request.form.get("origin")
    filtered_data = df[df["origin"] == selected_origin] if selected_origin else df.copy()

    payload = filtered_data.to_dict(orient="records")

    import requests
    response = requests.post(
        "https://httpbin.org/post",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    if response.status_code == 200:
        flash("✅ Data submitted successfully!")
    else:
        flash("❌ Failed to submit data.")
    return redirect(url_for("home"))


@app.route("/fetch")
def fetch_latest_data():
    try:
        save_to_csv()
        flash("✅ Fetched latest flight data successfully!")
    except Exception as e:
        print("🔥 ERROR fetching data:", str(e))
        flash("⚠️ Failed to fetch data. Using last saved dataset.")
    return redirect(url_for("home"))


# ======================================================
# 🚀 4. Run the App
# ======================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
