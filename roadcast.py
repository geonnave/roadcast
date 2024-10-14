from dataclasses import dataclass, field
from threading import Thread
from enum import Enum

from openai import OpenAI

from os import environ as env
from dotenv import load_dotenv
load_dotenv()

import logging, time, json, requests, os, threading, queue

import prompts
import log_setup  # Import the log setup file
from audio_player import AudioPlayer

log_setup.setup_logging()

class MissionModes(Enum):
    CITY = 1
    COUNTRYSIDE = 2

class LocationUpdaterMock(Thread):
    def __init__(self):
        super().__init__()
        # self.lat, self.lon = 48.844676, 2.342112
        # self.lat, self.lon = 48.846645, 2.344636 # in front of the Pantheon -> ok
        # self.lat, self.lon = 48.846645, 2.3460557 # the Pantheon itself -> ok
        # self.lat, self.lon = 48.847107, 2.340572 # next to Jardin du Luxembourg -> medium
        # self.lat, self.lon = 48.853754, 2.347436 # Notre Dame -> ok
        # self.lat, self.lon = 48.862190, 2.337132 # Louvre -> ok
        self.lat, self.lon = 48.8670837,2.3382194 # Palais Royal -> medium
        self.update_interval = 15

    def run(self):
        while True:
            # mock new latlon
            self.lon = round(self.lon + 0.0005, 6) # about 40 meters
            logging.debug(f"User latlon: {self.lat}, {self.lon}")
            time.sleep(self.update_interval)

    def get_latlon(self):
        return self.lat, self.lon

    def set_latlon(self, lat, lon):
        self.lat, self.lon = lat, lon

class GPT:
    def __init__(self) -> None:
        self.client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key=env["OPENAPI_KEY"],
        )

    def call(self, prompt, model="gpt-4o"):
        logging.debug("GPT: start call...")
        logging.debug(f"Prompt for {model}: {prompt}")
        res = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o",
        )
        try:
            content = res.choices[0].message.content
            logging.debug(f"GPT answer has content, with {len(content)} characters.")
            return content
        except:
            return None

    def ask_target_places(self, user_interests):
        if env["MOCK_GPT"] == "1":
            return json.loads(env["MOCK_INTEREST_POINTS"])
        places_filter_prompt = prompts.places_filter(user_interests)
        result = self.call(places_filter_prompt, model="o1-preview")
        if result is not None:
            result = json.loads(result)
            logging.debug(f"========\n\nGenerated target places: {result}\n\n========")
            input("Press Enter to continue...")
            return result
        else:
            raise("Had a problem generating result.")

    def ask_guide_speech(self, user_interests, latlon, radius, nearby_places):
        prompt = prompts.guide_instructions(user_interests, latlon, radius, nearby_places)
        result = self.call(prompt)
        logging.debug(f"========\n\nGenerated guide speech: {result}\n\n========")
        return result

    def ask_guide_speech_one_place(self, user_interests, latlon, place, continuation=False):
        prompt = prompts.guide_instructions_one_place(user_interests, latlon, place, continuation)
        result = self.call(prompt)
        logging.debug(f"========\n\nGenerated guide speech: {result}\n\n========")
        return result

    def adjust_places(self, user_interests, places_from_maps, latlon, radius):
        prompt = prompts.adjust_places(user_interests, places_from_maps, latlon, radius)
        result = self.call(prompt)
        if result is not None:
            result = json.loads(result)
            logging.debug(f"========\n\nGenerated adjusted places: {result}\n\n========")
            input("Press Enter to continue...")
            return result
        else:
            raise("Had a problem generating adjusted places.")

class Whisper:
    def __init__(self) -> None:
        self.count = 0
        self.client = OpenAI(
            api_key=env["OPENAPI_KEY"],
        )

    def synth_audio(self, script, place):
        logging.debug(f"Synthesizing audio for script about {place} of length {len(script)}")
        response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=script,
        )
        return self.save_audio_and_script(script, place, response)

    def save_audio_and_script(self, script, place, response):
        filename = f"{log_setup.OUTPUT_DIR}/{self.count}-{place}"
        self.count += 1
        response.stream_to_file(f"{filename}.mp3")
        with open(f"{filename}.txt", "w") as f:
            f.write(script)
        logging.debug(f"Saved text and audio for {place} to {filename}")
        logging.debug(f"Play audio with:    vlc '{filename}.mp3'")
        return f"{filename}.mp3"

@dataclass
class Places:
    target_points: list = field(default_factory=list)
    radius: int = None

    def set_radius(self, mode):
        self.radius = 200 if mode == MissionModes.CITY else 300

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
        logging.debug(f"========\n\n{response.json()}\n\n========")
        try:
            return True, [p["displayName"]["text"] for p in response.json()["places"]]
        except:
            # get the unsupported place types
            # example json: {'error': {'code': 400, 'message': 'Unsupported types: science_museum.', 'status': 'INVALID_ARGUMENT'}}
            message = response.json()["error"]["message"]
            unsupported_types = message.split(": ")[1].split(", ")
            unsupported_types = [t.replace(".", "") for t in unsupported_types]
            logging.error(f"Unsupported types: {unsupported_types}")
            return None, unsupported_types

@dataclass
class Mission:
    user_interests: list
    mode: MissionModes
    start_latlon: tuple
    location_updater = LocationUpdaterMock()
    gpt = GPT()
    whisper = Whisper()
    places = Places()
    player = AudioPlayer()

    def __post_init__(self):
        self.places.set_radius(self.mode)
        if self.start_latlon is not None:
            self.location_updater.set_latlon(*self.start_latlon)

    def run(self):
        self.load_target_types()
        print(self.places)
        self.location_updater.start()
        while True:
            ok, returned_places = self.places.call_nearby(self.location_updater.get_latlon())
            if not ok:
                # remove places from target types
                logging.error(f"Removing unsupported place types from target types: {returned_places}")
                self.places.target_points = [t for t in self.places.target_points if t not in returned_places]
                time.sleep(2)
                continue
            adjusted_places = self.gpt.adjust_places(self.user_interests, returned_places, self.location_updater.get_latlon(), self.places.radius)
            # script = self.gpt.ask_guide_speech(self.user_interests, self.location_updater.get_latlon(), self.places.radius, places)
            for i, place in enumerate(adjusted_places):
                logging.debug(f"========\n\nNow speaking about place: {place}========")
                if i == 0:
                    script = self.gpt.ask_guide_speech_one_place(self.user_interests, self.location_updater.get_latlon(), place)
                else:
                    script = self.gpt.ask_guide_speech_one_place(self.user_interests, self.location_updater.get_latlon(), place, continuation=True)
                input("Press enter to hear audio")
                audio_filename = self.whisper.synth_audio(script, place)
                self.player.add_audio_to_queue(audio_filename)
                input("Press Enter to continue...")
            time.sleep(10)
            print()
        self.location_updater.join()

    def load_target_types(self):
        targets = self.gpt.ask_target_places(self.user_interests)
        if targets is not None:
            self.places.set_targets(targets)

# TODO: allow user input such as e.g. "what are the most interesting places nearby?"
mission = Mission(
    # ["history", "architecture", "geography", "local culture"]
    # ["museum", "historical_landmark", "library", "art_gallery", "cultural_center", "park", "tourist_attraction", "visitor_center", "city_hall", "national_park", "tea"]
    # "cars agriculture barbecue".split(" "),
    "science university research-institute croissant thai-food".split(" "),
    mode=MissionModes.CITY,
    start_latlon=(48.825784, 2.346573) # Inria Paris
)

mission.run()
