from dataclasses import dataclass, field
from threading import Thread
import logging, time

logging.basicConfig(level=logging.DEBUG)

class LocationUpdaterMock(Thread):
    def __init__(self):
        super().__init__()
        self.lat = None
        self.lon = None

    def run(self):
        self.lat = 48.865725
        self.lon = 2.349100
        while True:
            # mock new latlon
            self.lon = round(self.lon + 0.0001, 6)
            logging.debug(f"User latlon: {self.lat}, {self.lon}")
            time.sleep(2)

    def get_latlon(self):
        return self.lat, self.lon

@dataclass
class Mission:
    user_interests: list = field(default_factory=list)
    location_updater = LocationUpdaterMock()

    def run(self):
        self.location_updater.start()
        while True:
            self.gather_nearby_interest_points(self.location_updater.get_latlon())
            # self.generate_script()
            # self.synth_audio()
            # self.dispatch_play()
            time.sleep(0.1)
        self.location_updater.join()
    
    def gather_nearby_interest_points(self, latlon):
        pass

mission = Mission(user_interests=["history", "architecture", "geography", "local culture"])

mission.run()
