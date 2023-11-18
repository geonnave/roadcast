from dataclasses import dataclass, field
from threading import Thread
from enum import Enum

from openai import OpenAI

from os import environ as env
from dotenv import load_dotenv
load_dotenv()

import logging, time, json

import prompts

logging.basicConfig(level=logging.DEBUG)

class MissionModes(Enum):
    CITY = 1
    COUNTRYSIDE = 2

class LocationUpdaterMock(Thread):
    def __init__(self):
        super().__init__()
        self.lat = 48.865725
        self.lon = 2.349100

    def run(self):
        while True:
            # mock new latlon
            self.lon = round(self.lon + 0.0001, 6)
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

    def ask_target_places(self):
        if env["MOCK_GPT"] == "1":
            return json.loads(env["MOCK_INTEREST_POINTS"])
        places_filter_prompt = prompts.places_filter(self.user_interests)
        result = self.call(places_filter_prompt)
        if result is not None:
            print(f"Got result: {result}")
            result = json.loads(result)
            print(f"Got result dict: {result}")
            return result
        else:
            raise("Had a problem generating result.")

@dataclass
class Places:
    target_points: list = field(default_factory=list)
    radius: int = 30

    def set_radius(self, mode):
        self.radius = 30 if mode == MissionModes.CITY else 300

    def set_targets(self, targets):
        self.target_points = targets

    def call(self):
        pass

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
            self.find_nearby_places(self.location_updater.get_latlon())
            # self.generate_script()
            # self.synth_audio()
            # self.dispatch_play()
            time.sleep(0.1)
        self.location_updater.join()
    
    def find_nearby_places(self, latlon):
        res = self.places.call()

    def load_target_types(self):
        targets = self.gpt.ask_target_places()
        if targets is not None:
            self.places.set_targets(targets)

user_interests=["history", "architecture", "geography", "local culture"]
mission = Mission(user_interests, mode=MissionModes.CITY)

mission.run()
