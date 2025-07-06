from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from dotenv import load_dotenv
import requests
import subprocess
import os
import sys

load_dotenv() 

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")


def load_data():
    if os.path.exists("data/live_flights.csv"):
        return pd.read_csv("data/live_flights.csv")
    else:
        return pd.DataFrame(columns=["origin", "destination", "price", "demand_score"])  # fallback structure


@app.route("/", methods=["GET", "POST"])
def home():
    df = load_data()
    selected_origin = None
    filtered_data = df.copy()
    popular_routes = (
        df.groupby(["origin", "destination"])
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(5)
    )
    popular_routes = popular_routes.to_dict(orient="records")


    if request.method == "POST":
        selected_origin = request.form.get("origin")
        if selected_origin:
            filtered_data = df[df["origin"] == selected_origin]

    origin_options = sorted(df["origin"].dropna().unique())
    chart_labels = filtered_data["destination"].tolist() if "destination" in filtered_data else []
    chart_values = filtered_data["demand_score"].tolist() if "demand_score" in filtered_data else []

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
    filtered_data = df.copy()
    if selected_origin:
        filtered_data = df[df["origin"] == selected_origin]

    payload = filtered_data.to_dict(orient="records")
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
        script_path = os.path.join(os.path.dirname(__file__), "scraper.py")
        subprocess.run([sys.executable, script_path], check=True)
        flash("✅ Fetched latest flight data from OpenSky.")
    except Exception as e:
        flash(f"❌ Failed to fetch data: {e}")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
