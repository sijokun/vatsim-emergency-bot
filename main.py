import requests
import telebot
import json
import time
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

VATSIM_URL = "https://data.vatsim.net/v3/vatsim-data.json"
MAP_URL = "https://api2.simaware.ca/api/livedata/live.json"
EMERGENCY_CODES = ["7600", "7700"]

emergency_callsigns = {}

with open("./types.json", "r") as f:
    aircraft_types = json.load(f)

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="MARKDOWN")
print(f"Starting... [@{bot.user.username}]")


def get_map_url_by_callsign(callsign: str) -> str:
    response = requests.get(MAP_URL)
    data = response.json()

    # Loop over the dictionary to find the key with the target value
    for key, value in data.items():
        if value["callsign"] == callsign:
            return f"https://map.vatsim.net/?uid={key}"
    return ""


def check_for_emergency():
    global emergency_callsigns
    global types

    response = requests.get(VATSIM_URL)
    data = response.json()

    for pilot in data["pilots"]:
        # Look for pilots with transponder code 7700/7600
        if (
            pilot["transponder"] in EMERGENCY_CODES
            and pilot["callsign"] not in emergency_callsigns
        ):
            emergency_callsigns[pilot["callsign"]] = pilot["transponder"]

            departure = pilot["flight_plan"]["departure"]
            arrival = pilot["flight_plan"]["arrival"]
            aircraft_type = pilot["flight_plan"]["aircraft_short"]

            if aircraft_type in aircraft_types.keys():
                aircraft_type = aircraft_types[aircraft_type]

            map_url = get_map_url_by_callsign(pilot["callsign"])
            message = (
                f"{aircraft_type} with callsign {pilot['callsign']} is squawking {pilot['transponder'] } departure from {departure} and arriving at {arrival}.\n\n"
                f"{map_url}"
            )
            print(message)
            bot.send_message(TELEGRAM_CHAT_ID, message)

        # Delete callsign from dict if transponder changed from emergency
        if (
            pilot["callsign"] in emergency_callsigns.keys()
            and pilot["transponder"] not in EMERGENCY_CODES
        ):
            emergency_callsigns.pop(pilot["callsign"])
            message = f"{pilot['callsign']} is squawking {pilot['transponder']}."
            print(message)

    # Check if emergency callsign went offline
    for callsign in emergency_callsigns.keys():
        if callsign not in [*(c["callsign"] for c in data["pilots"])]:
            emergency_callsigns.pop(callsign)
            message = f"{callsign} is offline."
            print(message)


if __name__ == "__main__":
    while True:
        check_for_emergency()
        time.sleep(10)
