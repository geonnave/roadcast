import threading
import queue
import time
import os
from playsound import playsound  # Install this package with 'pip install playsound'

class AudioPlayer:
    def __init__(self):
        self.audio_queue = queue.Queue()  # Queue to hold the audio file paths
        self.is_playing = False  # Flag to check if audio is currently playing
        self.lock = threading.Lock()  # Lock to synchronize access to 'is_playing'

        # Start a background thread to monitor the queue and play audio
        self.thread = threading.Thread(target=self._play_audio_from_queue, daemon=True)
        self.thread.start()

    def add_audio_to_queue(self, audio_file):
        """Adds a new audio file to the queue."""
        if os.path.exists(audio_file):
            self.audio_queue.put(audio_file)  # Add audio file to queue
            print(f"Audio file {audio_file} added to queue.")
        else:
            print(f"Audio file {audio_file} does not exist.")

    def _play_audio_from_queue(self):
        """Monitors the queue and plays audio if available."""
        while True:
            # Check if there is anything in the queue and nothing is currently playing
            if not self.is_playing and not self.audio_queue.empty():
                # Mark that we're now playing an audio file
                with self.lock:
                    self.is_playing = True

                # Get the next audio file from the queue
                audio_file = self.audio_queue.get()

                # Play the audio file
                print(f"Playing audio: {audio_file}")
                playsound(audio_file)  # This will block until the audio is finished

                # Mark as not playing when done
                with self.lock:
                    self.is_playing = False

            time.sleep(0.1)  # Small delay to prevent busy waiting

# Example usage
if __name__ == "__main__":
    player = AudioPlayer()

    # Simulating adding new audio files over time
    player.add_audio_to_queue("audio1.mp3")
    time.sleep(1)
    player.add_audio_to_queue("audio2.mp3")
    time.sleep(2)
    player.add_audio_to_queue("audio3.mp3")

    # Keep the main thread alive to let the background thread play audio
    while True:
        time.sleep(1)
