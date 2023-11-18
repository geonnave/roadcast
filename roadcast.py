from dataclasses import dataclass, field
from threading import Thread
from enum import Enum

from openai import OpenAI

from os import environ as env
from dotenv import load_dotenv
load_dotenv()

import logging, time, json, requests

import prompts

logging.basicConfig(level=logging.DEBUG)

class MissionModes(Enum):
    CITY = 1
    COUNTRYSIDE = 2

class LocationUpdaterMock(Thread):
    def __init__(self):
        super().__init__()
        self.lat = 48.844676
        self.lon = 2.342112

    def run(self):
        while True:
            # mock new latlon
            self.lon = round(self.lon + 0.0005, 6)
            logging.debug(f"User latlon: {self.lat}, {self.lon}")
            time.sleep(2)

    def get_latlon(self):
        return self.lat, self.lon

class GPT:
    def __init__(self) -> None:
        self.client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=env["OPENAPI_KEY"],
        )

    def call(self, prompt):
        logging.debug("GPT: start call...")
        res = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4",
        )
        logging.debug(f"GPT answer:\n\n{res}")
        try:
            return res.choices[0].message.content
        except:
            return None

    def ask_target_places(self, user_interests):
        if env["MOCK_GPT"] == "1":
            return json.loads(env["MOCK_INTEREST_POINTS"])
        places_filter_prompt = prompts.places_filter(user_interests)
        result = self.call(places_filter_prompt)
        if result is not None:
            print(f"Got result: {result}")
            result = json.loads(result)
            print(f"Got result dict: {result}")
            return result
        else:
            raise("Had a problem generating result.")

    def ask_guide_speech(self, user_interests, latlon, radius, nearby_places):
        prompt = prompts.guide_instructions(user_interests, latlon, radius, nearby_places)
        print(prompt)
        result = self.call(prompt)
        print(f"========\n\n{result}\n\n========")

@dataclass
class Places:
    target_points: list = field(default_factory=list)
    radius: int = None

    def set_radius(self, mode):
        self.radius = 50 if mode == MissionModes.CITY else 300

    def set_targets(self, targets):
        self.target_points = targets

    def call_nearby(self, latlon):
        url = "https://places.googleapis.com/v1/places:searchNearby"
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': env["GOOGLE_MAPS_KEY"],  # Replace 'API_KEY' with your actual API key
            'X-Goog-FieldMask': 'places.displayName',
        }
        data = {
            "includedTypes": self.target_points,
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latlon[0],
                        "longitude": latlon[1]
                    },
                    "radius": self.radius
                }
            }
        }
        logging.debug(f"Prepared data: {data}")
        response = requests.post(url, headers=headers, data=json.dumps(data))
        print(response.status_code)
        print(f"========\n\n{response.json()}\n\n========")
        return [p["displayName"]["text"] for p in response.json()["places"]]

@dataclass
class Mission:
    user_interests: list
    mode: MissionModes
    location_updater = LocationUpdaterMock()
    gpt = GPT()
    places = Places()

    def __post_init__(self):
        self.places.set_radius(self.mode)

    def run(self):
        self.load_target_types()
        print(self.places)
        self.location_updater.start()
        while True:
            nearby_places = self.places.call_nearby(self.location_updater.get_latlon())
            self.gpt.ask_guide_speech(self.user_interests, self.location_updater.get_latlon(), self.places.radius, nearby_places)
            # self.generate_script()
            # self.synth_audio()
            # self.dispatch_play()
            time.sleep(2)
            print()
        self.location_updater.join()
    
    def load_target_types(self):
        targets = self.gpt.ask_target_places(self.user_interests)
        if targets is not None:
            self.places.set_targets(targets)

# TODO: allow user input such as e.g. "what are the most interesting places nearby?"
user_interests=["history", "architecture", "geography", "local culture"]
mission = Mission(user_interests, mode=MissionModes.CITY)

mission.run()
