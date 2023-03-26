import logging

from logger import logger

import requests
import telebot

import json
import time
import os


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SLEEP_TIME_SEC = 15
VATSIM_URL = "https://data.vatsim.net/v3/vatsim-data.json"
MAP_URL = "https://api2.simaware.ca/api/livedata/live.json"
EMERGENCY_CODES = ["7600", "7700"]

active_emergencies = {}

with open("data/types.json", "r") as f:
    aircraft_types = json.load(f)

with open("data/airlines.json", "r") as f:
    airlines = json.load(f)

with open("data/airports.json", "r") as f:
    airports = json.load(f)

bot = telebot.TeleBot(TELEGRAM_TOKEN, parse_mode="MARKDOWN")
logger.info(f"Starting... [@{bot.user.username}]")


def get_map_url_by_callsign(callsign: str) -> str:
    # Get list of live flights on map
    response = requests.get(MAP_URL)
    data = response.json()

    # Loop over the dictionary to find the uid with the target flight with callsign
    for key, value in data.items():
        if value["callsign"] == callsign:
            logger.debug(f"Found uid {key} for callsign {callsign}")
            return f"https://map.vatsim.net/?uid={key}"
    return ""


def check_for_emergency():
    global active_emergencies, aircraft_types, airlines, airports

    response = requests.get(VATSIM_URL)
    data = response.json()

    for pilot in data["pilots"]:
        # Check if it is a new emergency (pilot with transponder code 7700/7600 now in list of known emergencies)
        if (
            pilot["transponder"] in EMERGENCY_CODES
            and pilot["callsign"] not in active_emergencies
        ):
            logger.info(
                f'Processing new emergency {pilot["callsign"]} with squawk {pilot["transponder"]}'
            )

            # Add emergency to list of known emergencies
            active_emergencies[pilot["callsign"]] = pilot["transponder"]

            # Extract information about emergency from pilot object
            departure = pilot["flight_plan"]["departure"]
            arrival = pilot["flight_plan"]["arrival"]
            aircraft_type = pilot["flight_plan"]["aircraft_short"]
            callsign = pilot["callsign"]

            # TODO: Write log to SQL database

            # Replace aircraft ICAO type with aircraft type (for example: A319 -> Airbus A319 Ceo)
            if aircraft_type in aircraft_types.keys():
                aircraft_type = aircraft_types[aircraft_type]

            # Replace airline code with full name (for example: A319 -> Airbus A319 Ceo)
            if callsign[:3] in airlines.keys():
                callsign = f"{airlines[callsign[:3]]} {callsign[3:]}"

            # Replace departure airport ICAO code with airport name (for example: LLBG -> Tel Aviv Ben Gurion)
            if departure in airports.keys():
                departure = f"{airports[departure]} ({departure})"

            # Replace arrival airport ICAO code with airport name (for example: LLBG -> Tel Aviv Ben Gurion)
            if arrival in airports.keys():
                arrival = f"{airports[arrival]} ({arrival})"

            # Get url to map.vatsim.net with emergency flight selected
            map_url = get_map_url_by_callsign(pilot["callsign"])

            # Generate message about emergency
            message = f"{callsign} from {departure} to {arrival}"
            if pilot["transponder"] == "7600":
                message += (
                    f" reported the loss of radio communication (squawk code 7600)"
                )
            elif pilot["transponder"] == "7700":
                message += f" reported emergency (squawk code 7700)"
            else:
                message += f" reported squawk code {pilot['transponder']}"
            message += f" on {aircraft_type}\n\n {map_url}"

            logger.info(
                f'Sending message about emergency of {pilot["callsign"]} to telegram'
            )

            #  Send message about emergency to telegram
            bot.send_message(TELEGRAM_CHAT_ID, message)

            logger.info(f'New emergency {pilot["callsign"]} processed')

        # Delete emergency from dict if transponder changed to not emergency squawk
        if (
            pilot["callsign"] in active_emergencies.keys()
            and pilot["transponder"] not in EMERGENCY_CODES
        ):
            active_emergencies.pop(pilot["callsign"])
            message = f"{pilot['callsign']} is now longer squawking emergency, new squawk is {pilot['transponder']}."
            logging.info(message)

    # Check if emergency flight went offline
    offline_callsigns = []
    for callsign in active_emergencies.keys():
        if callsign not in [*(c["callsign"] for c in data["pilots"])]:
            offline_callsigns.append(callsign)
            message = f"{callsign} is no longer online."
            logger.info(message)

    # Delete flight from dict if it went offline
    for offline_callsign in offline_callsigns:
        active_emergencies.pop(offline_callsign)


if __name__ == "__main__":
    # Check for new emergencies every SLEEP_TIME_SEC seconds.
    while True:
        check_for_emergency()
        time.sleep(SLEEP_TIME_SEC)
