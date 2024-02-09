import datetime as dt
import json

import requests
from flask import Flask, jsonify, request

API_TOKEN = ""
# http://api.weatherapi.com/
API_KEY = ""

app = Flask(__name__)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


def get_weather(city: str, days: str, limit: int = 1):

    url = f"http://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={city}&days={days}&aqi=no&alerts=no"

    response = requests.get(url)

    if response.status_code == requests.codes.ok:
        return json.loads(response.text)
    else:
        raise InvalidUsage(response.text, status_code=response.status_code)


def is_valid_date_format(date_string):
    try:
        dt.datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route("/")
def home_page():
    return "<p><h2>Little Dummy Welcome Message</h2></p>"


@app.route("/weather", methods=["POST"])
def weather_endpoint():
    json_data = request.get_json()

    if json_data.get("token") is None:
        raise InvalidUsage("token is required", status_code=400)
    token = json_data.get("token")
    if token != API_TOKEN:
        raise InvalidUsage("wrong API token", status_code=403)

    if json_data.get("requester_name") is None:
        raise InvalidUsage("requester_name is required", status_code=400)
    requester_name = json_data.get("requester_name")

    if json_data.get("city") is None:
        raise InvalidUsage("city is required", status_code=400)
    city = json_data.get("city")

    if json_data.get("date") is None:
        raise InvalidUsage("date is required", status_code=400)
    date = json_data.get("date")
    if is_valid_date_format(date) is False:
        raise InvalidUsage("Date format is invalid", status_code=400)

    given_date = dt.datetime.strptime(date, "%Y-%m-%d").date()
    today_date = dt.datetime.now().date()
    difference = given_date - today_date
    if difference.days > 0:
        days = difference.days
    else:
        days = 1

    weather = get_weather(city, days)

    end_dt = dt.datetime.utcnow()
    end_dt_string = end_dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    weather_dict = {}
    for record in weather["forecast"]["forecastday"]:
        weather_dict = record
        if weather_dict["date"] == date:
            break

    result = {
        "requester_name": requester_name,
        "timespamp": end_dt_string,
        "location": city,
        "weather": {
            "Date": weather_dict["date"],
            "Max Temperature, C": weather_dict["day"]["maxtemp_c"],
            "Min Temperature, C": weather_dict["day"]["mintemp_c"],
            "Max Wind Speed, kph": weather_dict["day"]["maxwind_kph"],
            "Total Precipitation, mm": weather_dict["day"]["totalprecip_mm"],
            "Total Snow, cm": weather_dict["day"]["totalsnow_cm"],
            "Will it rain?": (
                "yes" if (weather_dict["day"]["daily_will_it_rain"] == 1) else "no"
            ),
            "Will it snow?": (
                "yes" if (weather_dict["day"]["daily_will_it_snow"] == 1) else "no"
            ),
            "Condition": weather_dict["day"]["condition"]["text"],
        },
    }

    return result
