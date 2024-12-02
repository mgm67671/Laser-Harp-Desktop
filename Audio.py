# Audio.py

import pygame
from pydub import AudioSegment
from io import BytesIO
import os
import Main
import Helpers

# Initialize the mixer with more channels if needed
pygame.mixer.set_num_channels(64)

def convert_pydub_to_pygame(sound):
    """Convert a pydub AudioSegment to a pygame Sound object."""
    raw_data = BytesIO()
    sound.export(raw_data, format="wav")
    raw_data.seek(0)
    return pygame.mixer.Sound(file=raw_data)

def preload_sounds():
    """Preload all the sounds and process them for sustain and looping modes."""
    Main.sound_objects = {}
    Main.sustain_lengths = {}

    for input_key, note in Main.input_to_note.items():
        octave = Main.current_octave
        
        if input_key == '=':
            octave += 1

        transposed_note, adjusted_octave = Helpers.transpose_note(note, Main.current_key, octave)
        sound_file = f"{transposed_note}{adjusted_octave}.wav"
        sound_path = os.path.join(Main.current_folder, sound_file)

        # Check if the sound file exists
        if not os.path.exists(sound_path):
            print(f"Sound file not found: {sound_path}")
            continue

        sound = AudioSegment.from_wav(sound_path)

        # Process sound for sustain and looping modes
        attack_duration = Main.attack_duration
        attack = sound[:attack_duration]
        sustain = sound[attack_duration:]

        # Apply fade-in and fade-out to the sustain portion
        fade_in = Main.fade_in_duration
        fade_out = Main.fade_out_duration
        sustain = sustain.fade_in(fade_in).fade_out(fade_out)

        # Convert attack and sustain portions to pygame sounds
        attack_sound = convert_pydub_to_pygame(attack)
        sustain_sound = convert_pydub_to_pygame(sustain)

        # Set volumes
        attack_sound.set_volume(Main.volume)
        sustain_sound.set_volume(Main.volume)

        # Store sounds in the dictionary
        Main.sound_objects[input_key] = {
            'attack': attack_sound,
            'sustain': sustain_sound
        }

        # Store sustain sound length
        Main.sustain_lengths[input_key] = sustain_sound.get_length() * 1000  # in milliseconds

        # Also store the original sound for non-sustain playback
        original_sound = convert_pydub_to_pygame(sound)
        original_sound.set_volume(Main.volume)
        Main.sound_objects[input_key]['original'] = original_sound

    # Preload sounds for looping notes
    for note_id, note_info in Main.looping_notes.items():
        key = note_info['key']
        preload_sound_for_looping_note(note_id, key, instrument=note_info['created_instrument'])

def preload_sound_for_looping_note(note_id, key, instrument):
    """Preload sounds for a specific looping note based on its current settings."""
    note_info = Main.looping_notes[note_id]
    octave = Main.current_octave
    if note_info['octave_locked']:
        octave = note_info['locked_octave']
    if key == '=':
        octave += 1

    # Use locked key if key is locked
    used_key = Main.current_key
    if note_info.get('key_locked'):
        used_key = note_info['locked_key']

    # Use locked instrument if instrument is locked
    instrument_folder = Main.current_folder
    if note_info.get('instrument_locked'):
        instrument_folder = note_info['locked_instrument']

    # Generate the transposed note
    original_note = Main.input_to_note[key]
    transposed_note, adjusted_octave = Helpers.transpose_note(original_note, used_key, octave)
    if key == '=':
        adjusted_octave += 1
    sound_file = f"{transposed_note}{adjusted_octave}.wav"
    sound_path = os.path.join(instrument_folder, sound_file)

    # Check if the sound file exists
    if not os.path.exists(sound_path):
        print(f"Sound file not found for looping note: {sound_path}")
        return

    sound = AudioSegment.from_wav(sound_path)

    # Process sound for sustain and looping modes
    attack_duration = Main.attack_duration
    attack = sound[:attack_duration]
    sustain = sound[attack_duration:]

    # Apply fade-in and fade-out to the sustain portion
    fade_in = Main.fade_in_duration
    fade_out = Main.fade_out_duration
    sustain = sustain.fade_in(fade_in).fade_out(fade_out)

    # Convert attack and sustain portions to pygame sounds
    attack_sound = convert_pydub_to_pygame(attack)
    sustain_sound = convert_pydub_to_pygame(sustain)

    # Set volumes
    attack_sound.set_volume(Main.volume)
    sustain_sound.set_volume(Main.volume)

    # Store sounds in the looping note's info
    note_info['sounds'] = {
        'attack': attack_sound,
        'sustain': sustain_sound
    }

    # Store sustain sound length
    note_info['sustain_length'] = sustain_sound.get_length() * 1000  # in milliseconds

    # Also store the original sound for non-sustain playback
    original_sound = convert_pydub_to_pygame(sound)
    original_sound.set_volume(Main.volume)
    note_info['sounds']['original'] = original_sound

def choose_folder(folder_name):
    """Change the current instrument folder and preload sounds."""
    if folder_name in Main.instrument_folders:
        Main.current_folder = os.path.join(Main.base_folder, folder_name)
        if Main.running:
            preload_sounds()
            # Reload sounds for looping notes that are not instrument-locked
            for note_id, note_info in Main.looping_notes.items():
                if not note_info.get('instrument_locked'):
                    preload_sound_for_looping_note(note_id, note_info['key'], instrument=Main.current_folder)
        print(f"Instrument changed to {folder_name}")
    else:
        print(f"Instrument folder {folder_name} not found.")

def adjust_volume(value):
    """Adjust the volume of all sounds."""
    Main.volume = float(value)
    for sounds in Main.sound_objects.values():
        for sound in sounds.values():
            sound.set_volume(Main.volume)
    # Adjust volume for looping notes
    for note_info in Main.looping_notes.values():
        sounds = note_info.get('sounds', {})
        for sound in sounds.values():
            sound.set_volume(Main.volume)

def change_octave(octave):
    """Change the current octave."""
    Main.current_octave = int(octave)
    if Main.running:
        preload_sounds()
        # Reload sounds for looping notes
        for note_id, note_info in Main.looping_notes.items():
            if not note_info['octave_locked']:
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=Main.current_folder)

    # Update the display of looping notes
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        try:
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def change_key(key):
    """Change the current key."""
    Main.current_key = key
    if Main.running:
        preload_sounds()
        # Reload sounds for looping notes that are not key locked
        for note_id, note_info in Main.looping_notes.items():
            if not note_info.get('key_locked'):
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=Main.current_folder)
    # Update the display of looping notes
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        try:
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def choose_folder(folder_name):
    """Change the current instrument folder."""
    Main.current_folder = os.path.join(Main.base_folder, folder_name)
    if Main.running:
        preload_sounds()
        # Reload sounds for looping notes that are not instrument-locked
        for note_id, note_info in Main.looping_notes.items():
            if not note_info.get('instrument_locked'):
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=Main.current_folder)
    print(f"Instrument changed to {folder_name}")

    # Update the display of looping notes
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        try:
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def start_harp():
    """Initialize and start the harp application."""
    Main.running = True
    preload_sounds()

def stop_harp():
    """Stop the harp application and clean up."""
    Main.running = False
    pygame.mixer.stop()
    # Stop all looping notes and cancel scheduled tasks
    for note_id in list(Main.looping_notes.keys()):
        import Looping  # Import here to avoid circular import
        Looping.stop_looping_note(note_id)
    # Cancel any scheduled sustain plays
    for key in list(Main.scheduled_tasks.keys()):
        Main.root.after_cancel(Main.scheduled_tasks[key])
    Main.scheduled_tasks.clear()