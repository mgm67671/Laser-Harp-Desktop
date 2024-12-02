# LLLooping.py

import LLMain
import LLAudio
import LLHelpers
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
    elif key in LLMain.input_to_note:
        octave = LLMain.current_octave
        if key == '=':
            octave += 1
        # Pass the current instrument to get a unique note_id
        unique_note_id = LLHelpers.get_note_identifier(key, octave, LLMain.current_folder)
        if LLMain.loop_mode:
            handle_loop_mode(unique_note_id, key)
        else:
            handle_normal_key_press(unique_note_id, key, octave)

def handle_shift(direction, current_time):
    """Handle octave changes with shift keys."""
    if direction == 'left':
        if current_time - LLMain.last_shift_l_time > LLMain.shift_cooldown:
            new_octave = LLMain.current_octave - 1
            if new_octave in LLMain.octave_range:
                LLAudio.change_octave(new_octave)
                LLMain.last_shift_l_time = current_time
                print(f"Octave decreased to {new_octave}")
            else:
                print("Cannot decrease octave further.")
    elif direction == 'right':
        if current_time - LLMain.last_shift_r_time > LLMain.shift_cooldown:
            new_octave = LLMain.current_octave + 1
            if new_octave in LLMain.octave_range:
                LLAudio.change_octave(new_octave)
                LLMain.last_shift_r_time = current_time
                print(f"Octave increased to {new_octave}")
            else:
                print("Cannot increase octave further.")

def handle_loop_mode(note_id, key):
    """Handle looping mode key presses."""
    if note_id in LLMain.looping_notes:
        # Note is already looping, stop looping it
        stop_looping_note_by_key(note_id, key, LLMain.current_octave)
    else:
        # Check if max loops reached
        if len(LLMain.looping_notes) >= LLMain.max_loops:
            print("Maximum number of looping notes reached.")
        else:
            # Start looping the note
            start_looping_note(note_id, key)
    # Reset loop mode
    LLMain.loop_mode = False
    print("Loop mode deactivated.")

def handle_normal_key_press(note_id, key, octave):
    """Handle normal key presses."""
    instrument = LLMain.current_folder  # Set instrument as per current folder
    sustain_option = LLMain.sustain_option  # Set sustain option as per current setting

    matching_note_id = find_matching_looping_note_id(key, octave, instrument, sustain_option)
    if matching_note_id:
        stop_looping_note_by_key(matching_note_id, key, octave)
    else:
        if not LLMain.key_status.get(key, False):
            LLMain.key_status[key] = True
            if LLMain.sustain_option:
                # Play attack sound, then schedule sustain playback
                sounds = LLMain.sound_objects[key]
                sounds['attack'].play()
                attack_length = int(sounds['attack'].get_length() * 1000)
                LLMain.root.after(attack_length, lambda: schedule_sustain_play(key))
            else:
                # Play the original sound once
                sounds = LLMain.sound_objects[key]
                sounds['original'].play()

def key_release(event):
    """Handle key release events."""
    key = event.char
    keysym = event.keysym

    if key in LLMain.input_to_note:
        if key in LLMain.key_status:
            LLMain.key_status[key] = False
            octave = LLMain.current_octave
            if key == '=':
                octave += 1
            instrument = LLMain.current_folder  # Current instrument folder
            sustain_option = LLMain.sustain_option  # Current sustain setting

            # Check if the exact note is looping
            matching_note_id = find_matching_looping_note_id(key, octave, instrument, sustain_option)
            if matching_note_id:
                pass
            else:
                # Cancel scheduled sustain plays
                if key in LLMain.scheduled_tasks:
                    LLMain.root.after_cancel(LLMain.scheduled_tasks[key])
                    del LLMain.scheduled_tasks[key]
                # Schedule to stop the sustain sound after sustain_interval
                task_id = LLMain.root.after(LLMain.sustain_interval, lambda: stop_sustain_sound(key))
                LLMain.scheduled_tasks[key] = task_id

def schedule_sustain_play(key):
    """Schedule the sustain sound to play with overlaps."""
    if LLMain.key_status.get(key, False):
        play_sustain_sound(key)

        # Calculate interval between sustain plays
        sustain_length = LLMain.sustain_lengths[key]
        interval = int(sustain_length / LLMain.max_overlaps)

        # Schedule the next sustain play
        task_id = LLMain.root.after(interval, lambda: schedule_sustain_play(key))
        LLMain.scheduled_tasks[key] = task_id
    else:
        # If the key is no longer pressed, schedule to stop the sustain sound
        task_id = LLMain.root.after(LLMain.sustain_interval, lambda: stop_sustain_sound(key))
        LLMain.scheduled_tasks[key] = task_id

def play_sustain_sound(key):
    """Play the sustain sound once, without looping."""
    sounds = LLMain.sound_objects[key]
    sustain_sound = sounds['sustain']
    # Play sustain sound without looping
    channel = pygame.mixer.find_channel()
    if channel:
        channel.play(sustain_sound)
        # Store the channel
        if key not in LLMain.active_sustain_channels:
            LLMain.active_sustain_channels[key] = []
        LLMain.active_sustain_channels[key].append(channel)

def stop_sustain_sound(key):
    """Fade out all channels playing the sustain sound for this key."""
    if key in LLMain.active_sustain_channels:
        for channel in LLMain.active_sustain_channels[key]:
            if LLMain.fade_out_duration > 0:
                channel.fadeout(LLMain.fade_out_duration)
            else:
                channel.stop()
        LLMain.active_sustain_channels[key] = []

    # Remove scheduled stop
    if key in LLMain.scheduled_tasks:
        del LLMain.scheduled_tasks[key]

def start_looping_note(note_id, key):
    """Start looping a note and assign it to an available slot."""
    # Find an available slot
    try:
        slot_index = LLMain.looping_note_slots.index(None)
    except ValueError:
        print("No available looping note slots.")
        return

    # Set up note information, including an available channel for playback
    note_info = {
        'key': key,
        'slot': slot_index,
        'octave_locked': False,
        'locked_octave': LLMain.current_octave,
        'sustain_option': LLMain.sustain_option,
        'key_locked': False,
        'locked_key': None,
        'instrument_locked': False,
        'locked_instrument': None,
        'created_octave': LLMain.current_octave,
        'created_instrument': LLMain.current_folder,
        'active_channels': [],
        'channel': pygame.mixer.find_channel(),
    }

    # Add note_info to looping notes
    LLMain.looping_notes[note_id] = note_info

    # Preload the sound for this looping note
    LLAudio.preload_sound_for_looping_note(note_id, key, instrument=LLMain.current_folder)

    # Schedule sustain or normal loop playback
    if LLMain.sustain_option:
        task_id = LLMain.root.after(0, lambda: schedule_loop_sustain_play(key, note_id))
    else:
        task_id = LLMain.root.after(0, lambda: schedule_normal_loop_play(key, note_id))
    note_info['task_id'] = task_id
    LLMain.looping_note_slots[slot_index] = note_id

    # Update the GUI to reflect the new looping note
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def schedule_normal_loop_play(key, note_id):
    """Schedule the next playback of the original sound for normal looping."""
    if note_id in LLMain.looping_notes:
        note_info = LLMain.looping_notes[note_id]
        sounds = note_info['sounds']
        channel = note_info['channel']
        channel.play(sounds['original'])
        sound_length = int(sounds['original'].get_length() * 1000)
        task_id = LLMain.root.after(sound_length, lambda: schedule_normal_loop_play(key, note_id))
        note_info['task_id'] = task_id
    else:
        # If the note is no longer looping, do nothing
        pass

def schedule_loop_sustain_play(key, note_id):
    """Schedule continuous sustain sound playback for looping."""
    if note_id in LLMain.looping_notes:
        note_info = LLMain.looping_notes[note_id]
        play_sustain_sound_loop(note_info)

        # Calculate the sustain interval
        sustain_length = note_info['sustain_length']
        interval = int(sustain_length / LLMain.max_overlaps)

        # Schedule the next sustain play
        task_id = LLMain.root.after(interval, lambda: schedule_loop_sustain_play(key, note_id))
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
    note_info = LLMain.looping_notes[note_id]
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
    if note_id in LLMain.looping_notes:
        # Retrieve note info
        note_info = LLMain.looping_notes[note_id]
        task_id = note_info.get('task_id')
        channel = note_info.get('channel')
        slot_index = note_info.get('slot')

        if task_id:
            LLMain.root.after_cancel(task_id)

        if channel:
            if LLMain.fade_out_duration > 0:
                channel.fadeout(LLMain.fade_out_duration)
            else:
                channel.stop()

        # Fade out any active sustain channels
        if 'active_channels' in note_info:
            for ch in note_info['active_channels']:
                if LLMain.fade_out_duration > 0:
                    ch.fadeout(LLMain.fade_out_duration)
                else:
                    ch.stop()
            note_info['active_channels'] = []

        # Remove looping note
        del LLMain.looping_notes[note_id]

        # Free the slot
        LLMain.looping_note_slots[slot_index] = None

        # Update the GUI display
        if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

        print(f"Stopped looping note: {note_id}")
    else:
        print(f"Note {note_id} is not currently looping.")

def stop_loop_by_slot(slot_index):
    """Stop a looping note by its slot index."""
    note_id = LLMain.looping_note_slots[slot_index]
    if note_id:
        stop_looping_note(note_id)
        print(f"Stopped looping note in slot {slot_index + 1}: {note_id}")
    else:
        print(f"No looping note in slot {slot_index + 1} to stop.")

def stop_all_loops():
    """Stop all looping notes."""
    for note_id in list(LLMain.looping_notes.keys()):
        stop_looping_note(note_id)
    print("All looping notes have been stopped.")

def find_matching_looping_note_id(key, octave, instrument, sustain_option):
    """Find a looping note that matches the current key, octave, instrument, and sustain option."""
    for note_id, note_info in LLMain.looping_notes.items():
        if note_matches_current_settings(note_info, key, octave, instrument, sustain_option):
            return note_id
    return None

def toggle_octave_lock(slot_index):
    """Toggle the octave lock for a looping note in a given slot."""
    note_id = LLMain.looping_note_slots[slot_index]
    if note_id:
        note_info = LLMain.looping_notes[note_id]
        note_info['octave_locked'] = not note_info['octave_locked']
        if note_info['octave_locked']:
            note_info['locked_octave'] = LLMain.current_octave
            print(f"Octave locked for note {note_id} at octave {note_info['locked_octave']}")
            # Reload sound with the locked octave
            LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else LLMain.current_folder)
        else:
            print(f"Octave unlocked for note {note_id}")
            # Reload sound with the current global octave
            LLAudio.preload_sound_for_looping_note(note_id, note_info['key'])
        # Update the GUI display
        if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_octaves():
    """Lock the octave for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        if not note_info['octave_locked']:
            note_info['octave_locked'] = True
            note_info['locked_octave'] = LLMain.current_octave
            LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Update GUI
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All octaves locked.")

def unlock_all_octaves():
    """Unlock the octave for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        note_info['octave_locked'] = False
        # Reload sounds with the current global octave
        LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All octaves unlocked.")

def toggle_key_lock(slot_index):
    """Toggle the key lock for a looping note in a given slot."""
    note_id = LLMain.looping_note_slots[slot_index]
    if note_id:
        note_info = LLMain.looping_notes[note_id]
        note_info['key_locked'] = not note_info['key_locked']
        if note_info['key_locked']:
            note_info['locked_key'] = LLMain.current_key
            print(f"Key locked for note {note_id} at key {note_info['locked_key']}")
        else:
            note_info['locked_key'] = None
            print(f"Key unlocked for note {note_id}")
        # Reload sound with the locked or current key
        LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else LLMain.current_folder)
        # Update the GUI display
        if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_keys():
    """Lock the key for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        if not note_info['key_locked']:
            note_info['key_locked'] = True
            note_info['locked_key'] = LLMain.current_key
            LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Update GUI
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All keys locked.")

def unlock_all_keys():
    """Unlock the key for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        note_info['key_locked'] = False
        note_info['locked_key'] = None
        LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All keys unlocked.")

def toggle_instrument_lock(slot_index):
    """Toggle the instrument lock for a looping note in a given slot."""
    note_id = LLMain.looping_note_slots[slot_index]
    if note_id:
        note_info = LLMain.looping_notes[note_id]
        note_info['instrument_locked'] = not note_info.get('instrument_locked', False)
        if note_info['instrument_locked']:
            note_info['locked_instrument'] = LLMain.current_folder
            print(f"Instrument locked for note {note_id} at instrument {os.path.basename(note_info['locked_instrument'])}")
        else:
            note_info['locked_instrument'] = None
            print(f"Instrument unlocked for note {note_id}")
        # Reload sound with the locked or current instrument
        LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], note_info['locked_instrument'] if note_info['instrument_locked'] else LLMain.current_folder)
        # Update the GUI display
        if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
            LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')

def lock_all_instruments():
    """Lock the instrument for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        if not note_info.get('instrument_locked', False):
            note_info['instrument_locked'] = True
            note_info['locked_instrument'] = LLMain.current_folder
            LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['locked_instrument'])

    # Update GUI display to reflect locking status
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All instruments locked.")

def unlock_all_instruments():
    """Unlock the instrument for all looping notes and update GUI checkboxes."""
    for note_id, note_info in LLMain.looping_notes.items():
        note_info['instrument_locked'] = False
        note_info['locked_instrument'] = None
        LLAudio.preload_sound_for_looping_note(note_id, note_info['key'], instrument=note_info['created_instrument'])

    # Immediate GUI update
    if LLMain.advanced_menu_window and LLMain.advanced_menu_window.winfo_exists():
        LLMain.advanced_menu_window.event_generate('<<UpdateLoopingNotesDisplay>>', when='tail')
    print("All instruments unlocked.")
