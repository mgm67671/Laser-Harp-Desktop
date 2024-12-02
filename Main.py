# dependencies: pip install pygame pydub

# Main.py

import pygame
import os
import Gui

# Initialize Pygame mixer
pygame.mixer.init()

# Global Variables
running = False

# Paths and Folders
base_folder = "Sound Samples/"
current_folder = os.path.join(base_folder, "Harp")
instrument_folders = [
    f for f in os.listdir(base_folder) if os.path.isdir(os.path.join(base_folder, f))
]

# Audio Settings
volume = 0.5
sound_objects = {}
sustain_lengths = {}

# Key Mappings and Notes
input_to_note = {
    '`': "C",
    '1': "C#",
    '2': "D",
    '3': "D#",
    '4': "E",
    '5': "F",
    '6': "F#",
    '7': "G",
    '8': "G#",
    '9': "A",
    '0': "A#",
    '-': "B",
    '=': "C"
}
keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
current_key = "C"

# Octave Settings
octave_range = [2, 3, 4, 5]
current_octave = 3

# Sustain and Overlap Settings
fade_in_duration = 500    # milliseconds
fade_out_duration = 500   # milliseconds
attack_duration = 100     # milliseconds
sustain_interval = 1000   # milliseconds
sustain_option = False
max_overlaps = 10

# Looping Notes Settings
loop_mode = False         # Indicates if loop mode is active
max_loops = 15             # Maximum number of looping notes
looping_notes = {}
looping_note_slots = [None] * max_loops  # Initialize slots based on max_loops

# GUI and Event Handling
root = None
advanced_menu_window = None  # Reference to the advanced menu window

# Key Status and Scheduling
key_status = {}
scheduled_tasks = {}

# Shift Key Timing for Octave Changes
last_shift_l_time = 0
last_shift_r_time = 0
shift_cooldown = 0.2  # 200 milliseconds

# Key Status and Scheduling
key_status = {}
scheduled_tasks = {}

# Store active channels for sustain sounds
active_sustain_channels = {}

# Add this debounce time
DEBOUNCE_TIME = 0.1  # 100ms

# Track the last key press time
last_press_time = {}

if __name__ == "__main__":
    Gui.main_menu()