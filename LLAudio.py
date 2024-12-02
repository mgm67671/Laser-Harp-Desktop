# LLAudio.py

import pygame
from pydub import AudioSegment
from io import BytesIO
import os
import LLMain
import LLHelpers

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
    LLMain.sound_objects = {}
    LLMain.sustain_lengths = {}

    for input_key, note in LLMain.input_to_note.items():
        octave = LLMain.current_octave
        
        if input_key == '=':
            octave += 1

        transposed_note, adjusted_octave = LLHelpers.transpose_note(note, LLMain.current_key, octave)
        sound_file = f"{transposed_note}{adjusted_octave}.wav"
        sound_path = os.path.join(LLMain.current_folder, sound_file)

        # Check if the sound file exists
        if not os.path.exists(sound_path):
            print(f"Sound file not found: {sound_path}")
            continue

        sound = AudioSegment.from_wav(sound_path)

        # Process sound for sustain and looping modes
        attack_duration = LLMain.attack_duration
        attack = sound[:attack_duration]
        sustain = sound[attack_duration:]

        # Apply fade-in and fade-out to the sustain portion
        fade_in = LLMain.fade_in_duration
        fade_out = LLMain.fade_out_duration
        sustain = sustain.fade_in(fade_in).fade_out(fade_out)

        # Convert attack and sustain portions to pygame sounds
        attack_sound = convert_pydub_to_pygame(attack)
        sustain_sound = convert_pydub_to_pygame(sustain)

        # Set volumes
        attack_sound.set_volume(LLMain.volume)
        sustain_sound.set_volume(LLMain.volume)

        # Store sounds in the dictionary
        LLMain.sound_objects[input_key] = {
            'attack': attack_sound,
            'sustain': sustain_sound
        }

        # Store sustain sound length
        LLMain.sustain_lengths[input_key] = sustain_sound.get_length() * 1000  # in milliseconds

        # Also store the original sound for non-sustain playback
        original_sound = convert_pydub_to_pygame(sound)
        original_sound.set_volume(LLMain.volume)
        LLMain.sound_objects[input_key]['original'] = original_sound

    # Preload sounds for looping notes
    for note_id, note_info in LLMain.looping_notes.items():
        key = note_info['key']
        preload_sound_for_looping_note(note_id, key, instrument=note_info['created_instrument'])

def preload_sound_for_looping_note(note_id, key, instrument):
    """Preload sounds for a specific looping note based on its current settings."""
    note_info = LLMain.looping_notes[note_id]
    octave = LLMain.current_octave
    if note_info['octave_locked']:
        octave = note_info['locked_octave']
    if key == '=':
        octave += 1

    # Use locked key if key is locked
    used_key = LLMain.current_key
    if note_info.get('key_locked'):
        used_key = note_info['locked_key']

    # Use locked instrument if instrument is locked
    instrument_folder = LLMain.current_folder
    if note_info.get('instrument_locked'):
        instrument_folder = note_info['locked_instrument']

    # Generate the transposed note
    original_note = LLMain.input_to_note[key]
    transposed_note, adjusted_octave = LLHelpers.transpose_note(original_note, used_key, octave)
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
    attack_duration = LLMain.attack_duration
    attack = sound[:attack_duration]
    sustain = sound[attack_duration:]

    # Apply fade-in and fade-out to the sustain portion
    fade_in = LLMain.fade_in_duration
    fade_out = LLMain.fade_out_duration
    sustain = sustain.fade_in(fade_in).fade_out(fade_out)

    # Convert attack and sustain portions to pygame sounds
    attack_sound = convert_pydub_to_pygame(attack)
    sustain_sound = convert_pydub_to_pygame(sustain)

    # Set volumes
    attack_sound.set_volume(LLMain.volume)
    sustain_sound.set_volume(LLMain.volume)

    # Store sounds in the looping note's info
    note_info['sounds'] = {
        'attack': attack_sound,
        'sustain': sustain_sound
    }

    # Store sustain sound length
    note_info['sustain_length'] = sustain_sound.get_length() * 1000  # in milliseconds

    # Also store the original sound for non-sustain playback
    original_sound = convert_pydub_to_pygame(sound)
    original_sound.set_volume(LLMain.volume)
    note_info['sounds']['original'] = original_sound

def choose_folder(folder_name):
    """Change the current instrument folder and preload sounds."""
    if folder_name in LLMain.instrument_folders:
        LLMain.current_folder = os.path.join(LLMain.base_folder, folder_name)
        if LLMain.running:
            preload_sounds()
            # Reload sounds for looping notes that are not instrument-locked
            for note_id, note_info in LLMain.looping_notes.items():
                if not note_info.get('instrument_locked'):
                    preload_sound_for_looping_note(note_id, note_info['key'], instrument=LLMain.current_folder)
        print(f"Instrument changed to {folder_name}")
    else:
        print(f"Instrument folder {folder_name} not found.")

def adjust_volume(value):
    """Adjust the volume of all sounds."""
    LLMain.volume = float(value)
    for sounds in LLMain.sound_objects.values():
        for sound in sounds.values():
            sound.set_volume(LLMain.volume)
    # Adjust volume for looping notes
    for note_info in LLMain.looping_notes.values():
        sounds = note_info.get('sounds', {})
        for sound in sounds.values():
            sound.set_volume(LLMain.volume)

def change_octave(octave):
    """Change the current octave."""
    LLMain.current_octave = int(octave)
    if LLMain.running:
        preload_sounds()
        # Reload sounds for looping notes
        for note_id, note_info in LLMain.looping_notes.items():
            if not note_info['octave_locked']:
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=LLMain.current_folder)

    # Update the display of looping notes
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        try:
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def change_key(key):
    """Change the current key."""
    LLMain.current_key = key
    if LLMain.running:
        preload_sounds()
        # Reload sounds for looping notes that are not key locked
        for note_id, note_info in LLMain.looping_notes.items():
            if not note_info.get('key_locked'):
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=LLMain.current_folder)
    # Update the display of looping notes
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        try:
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def choose_folder(folder_name):
    """Change the current instrument folder."""
    LLMain.current_folder = os.path.join(LLMain.base_folder, folder_name)
    if LLMain.running:
        preload_sounds()
        # Reload sounds for looping notes that are not instrument-locked
        for note_id, note_info in LLMain.looping_notes.items():
            if not note_info.get('instrument_locked'):
                preload_sound_for_looping_note(note_id, note_info['key'], instrument=LLMain.current_folder)
    print(f"Instrument changed to {folder_name}")

    # Update the display of looping notes
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        try:
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
        except Exception as e:
            print(f"Error updating advanced menu: {e}")

def start_harp():
    """Initialize and start the harp application."""
    LLMain.running = True
    preload_sounds()

def stop_harp():
    """Stop the harp application and clean up."""
    LLMain.running = False
    pygame.mixer.stop()
    # Stop all looping notes and cancel scheduled tasks
    for note_id in list(LLMain.looping_notes.keys()):
        import LLLooping  # Import here to avoid circular import
        LLLooping.stop_looping_note(note_id)
    # Cancel any scheduled sustain plays
    for key in list(LLMain.scheduled_tasks.keys()):
        LLMain.root.after_cancel(LLMain.scheduled_tasks[key])
    LLMain.scheduled_tasks.clear()