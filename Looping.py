# Looping.py

import Main
import Audio
import Helpers
import pygame
import time
import os

def key_press(event):
    """Handle key press events."""
    keysym = event.keysym
    key = event.char.upper()  # Ensure key is uppercase
    current_time = time.time()

    if keysym == 'Shift_L':
        handle_shift('left', current_time)
    elif keysym == 'Shift_R':
        handle_shift('right', current_time)
    elif key in Main.input_to_note:
        octave = Main.current_octave
        if key == '=':
            octave += 1
        # Pass the current instrument to get a unique note_id
        unique_note_id = Helpers.get_note_identifier(key, octave, Main.current_folder)
        if Main.loop_mode:
            handle_loop_mode(unique_note_id, key)
        else:
            handle_normal_key_press(unique_note_id, key, octave)

def handle_shift(direction, current_time):
    """Handle octave changes with shift keys."""
    if direction == 'left':
        if current_time - Main.last_shift_l_time > Main.shift_cooldown:
            new_octave = Main.current_octave - 1
            if new_octave in Main.octave_range:
                Audio.change_octave(new_octave)
                Main.last_shift_l_time = current_time
                print(f"Octave decreased to {new_octave}")
            else:
                print("Cannot decrease octave further.")
    elif direction == 'right':
        if current_time - Main.last_shift_r_time > Main.shift_cooldown:
            new_octave = Main.current_octave + 1
            if new_octave in Main.octave_range:
                Audio.change_octave(new_octave)
                Main.last_shift_r_time = current_time
                print(f"Octave increased to {new_octave}")
            else:
                print("Cannot increase octave further.")

def handle_loop_mode(note_id, key):
    """Handle looping mode key presses."""
    if note_id in Main.looping_notes:
        # Note is already looping, stop looping it
        stop_looping_note_by_key(note_id, key, Main.current_octave)
    else:
        # Check if max loops reached
        if len(Main.looping_notes) >= Main.max_loops:
            print("Maximum number of looping notes reached.")
        else:
            # Start looping the note
            start_looping_note(note_id, key)
    # Reset loop mode
    Main.loop_mode = False
    print("Loop mode deactivated.")

def handle_normal_key_press(note_id, key, octave):
    """Handle normal key presses."""
    instrument = Main.current_folder  # Set instrument as per current folder
    sustain_option = Main.sustain_option  # Set sustain option as per current setting

    matching_note_id = find_matching_looping_note_id(key, octave, instrument, sustain_option)
    if matching_note_id:
        stop_looping_note_by_key(matching_note_id, key, octave)
    else:
        if not Main.key_status.get(key, False):
            Main.key_status[key] = True
            if Main.sustain_option:
                # Play attack sound, then schedule sustain playback
                sounds = Main.sound_objects[key]
                sounds['attack'].play()
                attack_length = int(sounds['attack'].get_length() * 1000)
                Main.root.after(attack_length, lambda: schedule_sustain_play(key))
            else:
                # Play the original sound once
                sounds = Main.sound_objects[key]
                sounds['original'].play()

def key_release(event):
    """Handle key release events."""
    key = event.char
    keysym = event.keysym

    if key in Main.input_to_note:
        if key in Main.key_status:
            Main.key_status[key] = False
            octave = Main.current_octave
            if key == '=':
                octave += 1
            instrument = Main.current_folder  # Current instrument folder
            sustain_option = Main.sustain_option  # Current sustain setting

            # Check if the exact note is looping
            matching_note_id = find_matching_looping_note_id(key, octave, instrument, sustain_option)
            if matching_note_id:
                pass
            else:
                # Cancel scheduled sustain plays
                if key in Main.scheduled_tasks:
                    Main.root.after_cancel(Main.scheduled_tasks[key])
                    del Main.scheduled_tasks[key]
                # Schedule to stop the sustain sound after sustain_interval
                task_id = Main.root.after(Main.sustain_interval, lambda: stop_sustain_sound(key))
                Main.scheduled_tasks[key] = task_id

def schedule_sustain_play(key):
    """Schedule the sustain sound to play with overlaps."""
    if Main.key_status.get(key, False):
        play_sustain_sound(key)

        # Calculate interval between sustain plays
        sustain_length = Main.sustain_lengths[key]
        interval = int(sustain_length / Main.max_overlaps)

        # Schedule the next sustain play
        task_id = Main.root.after(interval, lambda: schedule_sustain_play(key))
        Main.scheduled_tasks[key] = task_id
    else:
        # If the key is no longer pressed, schedule to stop the sustain sound
        task_id = Main.root.after(Main.sustain_interval, lambda: stop_sustain_sound(key))
        Main.scheduled_tasks[key] = task_id

def play_sustain_sound(key):
    """Play the sustain sound once, without looping."""
    sounds = Main.sound_objects[key]
    sustain_sound = sounds['sustain']
    # Play sustain sound without looping
    channel = pygame.mixer.find_channel()
    if channel:
        channel.play(sustain_sound)
        # Store the channel
        if key not in Main.active_sustain_channels:
            Main.active_sustain_channels[key] = []
        Main.active_sustain_channels[key].append(channel)

def stop_sustain_sound(key):
    """Fade out all channels playing the sustain sound for this key."""
    if key in Main.active_sustain_channels:
        for channel in Main.active_sustain_channels[key]:
            if Main.fade_out_duration > 0:
                channel.fadeout(Main.fade_out_duration)
            else:
                channel.stop()
        Main.active_sustain_channels[key] = []

    # Remove scheduled stop
    if key in Main.scheduled_tasks:
        del Main.scheduled_tasks[key]

def start_looping_note(note_id, key):
    """Start looping a note and assign it to an available slot."""
    # Find an available slot
    try:
        slot_index = Main.looping_note_slots.index(None)
    except ValueError:
        print("No available looping note slots.")
        return

    # Set up note information, including an available channel for playback
    note_info = {
        'key': key,
        'slot': slot_index,
        'octave_locked': False,
        'locked_octave': Main.current_octave,
        'sustain_option': Main.sustain_option,
        'key_locked': False,
        'locked_key': None,
        'instrument_locked': False,
        'locked_instrument': None,
        'created_octave': Main.current_octave,
        'created_instrument': Main.current_folder,
        'active_channels': [],
        'channel': pygame.mixer.find_channel(),
    }

    # Add note_info to looping notes
    Main.looping_notes[note_id] = note_info

    # Preload the sound for this looping note
    Audio.preload_sound_for_looping_note(note_id, key, instrument=Main.current_folder)

    # Schedule sustain or normal loop playback
    if Main.sustain_option:
        task_id = Main.root.after(0, lambda: schedule_loop_sustain_play(key, note_id))
    else:
        task_id = Main.root.after(0, lambda: schedule_normal_loop_play(key, note_id))
    note_info['task_id'] = task_id
    Main.looping_note_slots[slot_index] = note_id

    # Update the GUI to reflect the new looping note
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def schedule_normal_loop_play(key, note_id):
    """Schedule the next playback of the original sound for normal looping."""
    if note_id in Main.looping_notes:
        note_info = Main.looping_notes[note_id]
        sounds = note_info['sounds']
        channel = note_info['channel']
        channel.play(sounds['original'])
        sound_length = int(sounds['original'].get_length() * 1000)
        task_id = Main.root.after(sound_length, lambda: schedule_normal_loop_play(key, note_id))
        note_info['task_id'] = task_id
    else:
        # If the note is no longer looping, do nothing
        pass

def schedule_loop_sustain_play(key, note_id):
    """Schedule continuous sustain sound playback for looping."""
    if note_id in Main.looping_notes:
        note_info = Main.looping_notes[note_id]
        play_sustain_sound_loop(note_info)

        # Calculate the sustain interval
        sustain_length = note_info['sustain_length']
        interval = int(sustain_length / Main.max_overlaps)

        # Schedule the next sustain play
        task_id = Main.root.after(interval, lambda: schedule_loop_sustain_play(key, note_id))
        note_info['task_id'] = task_id

def play_sustain_sound_loop(note_info):
    """Play the sustain sound for a looping note."""
    sustain_sound = note_info['sounds']['sustain']
    # Play sustain sound without looping
    channel = pygame.mixer.find_channel()
    if channel:
        channel.play(sustain_sound)
        # Store the channel
        note_info['active_channels'].append(channel)

def stop_looping_note_by_key(note_id, key, octave, instrument, sustain_option):
    note_info = Main.looping_notes[note_id]
    if note_matches_current_settings(note_info, key, octave, instrument, sustain_option):
        stop_looping_note(note_id)
        print(f"Stopped looping note by key press: {note_id}")
    else:
        print(f"Pressed key does not match looping note settings; note continues.")


def note_matches_current_settings(note_info, key, octave, instrument, sustain_option):
    """Check if the pressed key, octave, instrument, and mode match the looping note's settings."""
    expected_key = note_info['key']
    expected_octave = note_info['locked_octave'] if note_info['octave_locked'] else note_info['created_octave']
    expected_instrument = note_info['locked_instrument'] if note_info['instrument_locked'] else note_info['created_instrument']
    expected_sustain_option = note_info['sustain_option']

    return (key == expected_key and octave == expected_octave and 
            instrument == expected_instrument and sustain_option == expected_sustain_option)

def stop_looping_note(note_id):
    """Stop looping a note and free its slot."""
    if note_id in Main.looping_notes:
        # Retrieve note info
        note_info = Main.looping_notes[note_id]
        task_id = note_info.get('task_id')
        channel = note_info.get('channel')
        slot_index = note_info.get('slot')

        if task_id:
            Main.root.after_cancel(task_id)

        if channel:
            if Main.fade_out_duration > 0:
                channel.fadeout(Main.fade_out_duration)
            else:
                channel.stop()

        # Fade out any active sustain channels
        if 'active_channels' in note_info:
            for ch in note_info['active_channels']:
                if Main.fade_out_duration > 0:
                    ch.fadeout(Main.fade_out_duration)
                else:
                    ch.stop()
            note_info['active_channels'] = []

        # Remove looping note
        del Main.looping_notes[note_id]

        # Free the slot
        Main.looping_note_slots[slot_index] = None

        # Update the GUI display
        if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

        print(f"Stopped looping note: {note_id}")
    else:
        print(f"Note {note_id} is not currently looping.")

def stop_loop_by_slot(slot_index):
    """Stop a looping note by its slot index."""
    note_id = Main.looping_note_slots[slot_index]
    if note_id:
        stop_looping_note(note_id)
        print(f"Stopped looping note in slot {slot_index + 1}: {note_id}")
    else:
        print(f"No looping note in slot {slot_index + 1} to stop.")

def stop_all_loops():
    """Stop all looping notes."""
    for note_id in list(Main.looping_notes.keys()):
        stop_looping_note(note_id)
    print("All looping notes have been stopped.")

def find_matching_looping_note_id(key, octave, instrument, sustain_option):
    """Find a looping note that matches the current key, octave, instrument, and sustain option."""
    for note_id, note_info in Main.looping_notes.items():
        if note_matches_current_settings(note_info, key, octave, instrument, sustain_option):
            return note_id
    return None

def toggle_octave_lock(slot_index):
    """Toggle the octave lock for a looping note in a given slot."""
    note_id = Main.looping_note_slots[slot_index]
    if note_id:
        note_info = Main.looping_notes[note_id]
        note_info['octave_locked'] = not note_info['octave_locked']
        if note_info['octave_locked']:
            note_info['locked_octave'] = Main.current_octave
            print(f"Octave locked for note {note_id} at octave {note_info['locked_octave']}")
            # Reload sound with the locked octave
            Audio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else Main.current_folder)
        else:
            print(f"Octave unlocked for note {note_id}")
            # Reload sound with the current global octave
            Audio.preload_sound_for_looping_note(note_id, note_info['key'])
        # Update the GUI display
        if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_octaves():
    """Lock the octave for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        if not note_info['octave_locked']:
            note_info['octave_locked'] = True
            note_info['locked_octave'] = Main.current_octave
            Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Update GUI
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All octaves locked.")

def unlock_all_octaves():
    """Unlock the octave for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        note_info['octave_locked'] = False
        # Reload sounds with the current global octave
        Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All octaves unlocked.")

def toggle_key_lock(slot_index):
    """Toggle the key lock for a looping note in a given slot."""
    note_id = Main.looping_note_slots[slot_index]
    if note_id:
        note_info = Main.looping_notes[note_id]
        note_info['key_locked'] = not note_info['key_locked']
        if note_info['key_locked']:
            note_info['locked_key'] = Main.current_key
            print(f"Key locked for note {note_id} at key {note_info['locked_key']}")
        else:
            note_info['locked_key'] = None
            print(f"Key unlocked for note {note_id}")
        # Reload sound with the locked or current key
        Audio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else Main.current_folder)
        # Update the GUI display
        if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_keys():
    """Lock the key for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        if not note_info['key_locked']:
            note_info['key_locked'] = True
            note_info['locked_key'] = Main.current_key
            Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Update GUI
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All keys locked.")

def unlock_all_keys():
    """Unlock the key for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        note_info['key_locked'] = False
        note_info['locked_key'] = None
        Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All keys unlocked.")

def toggle_instrument_lock(slot_index):
    """Toggle the instrument lock for a looping note in a given slot."""
    note_id = Main.looping_note_slots[slot_index]
    if note_id:
        note_info = Main.looping_notes[note_id]
        note_info['instrument_locked'] = not note_info.get('instrument_locked', False)
        if note_info['instrument_locked']:
            note_info['locked_instrument'] = Main.current_folder
            print(f"Instrument locked for note {note_id} at instrument {os.path.basename(note_info['locked_instrument'])}")
        else:
            note_info['locked_instrument'] = None
            print(f"Instrument unlocked for note {note_id}")
        # Reload sound with the locked or current instrument
        Audio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else Main.current_folder)
        # Update the GUI display
        if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
            Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_instruments():
    """Lock the instrument for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        if not note_info.get('instrument_locked', False):
            note_info['instrument_locked'] = True
            note_info['locked_instrument'] = Main.current_folder
            Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['locked_instrument'])

    # Update GUI display to reflect locking status
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All instruments locked.")

def unlock_all_instruments():
    """Unlock the instrument for all looping notes and update GUI checkboxes."""
    for note_id, note_info in Main.looping_notes.items():
        note_info['instrument_locked'] = False
        note_info['locked_instrument'] = None
        Audio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if Main.advanced_menu_window and Main.advanced_menu_window.winfo_exists():
        Main.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All instruments unlocked.")
