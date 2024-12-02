# Input.py

import Main
import Audio
import Looping

def key_press(event):
    """Handle key press events."""
    keysym = event.keysym
    key = event.char

    if keysym == 'Shift_L':
        handle_shift('left')
    elif keysym == 'Shift_R':
        handle_shift('right')
    elif key in Main.input_to_note:
        octave = Main.current_octave
        if key == '=':
            octave += 1
        note_id = Audio.get_note_identifier(key, octave)
        if Main.loop_mode:
            Looping.handle_loop_mode(note_id, key)
        else:
            handle_normal_key_press(note_id, key)

def handle_shift(direction):
    """Handle octave changes with shift keys."""
    if direction == 'left':
        new_octave = Main.current_octave - 1
        if new_octave in Main.octave_range:
            Audio.change_octave(new_octave)
            print(f"Octave decreased to {new_octave}")
        else:
            print("Cannot decrease octave further.")
    elif direction == 'right':
        new_octave = Main.current_octave + 1
        if new_octave in Main.octave_range:
            Audio.change_octave(new_octave)
            print(f"Octave increased to {new_octave}")
        else:
            print("Cannot increase octave further.")

def handle_normal_key_press(note_id, key):
    """Handle normal key presses."""
    if note_id in Main.looping_notes:
        # Stop the looping note
        Audio.stop_looping_note_by_key(note_id)
    else:
        if not Main.key_status.get(key, False):
            Main.key_status[key] = True
            if Main.sustain_option:
                # Play attack sound, then schedule sustain playback
                sounds = Main.sound_objects[key]
                sounds['attack'].play()
                attack_length = int(sounds['attack'].get_length() * 1000)
                Main.root.after(attack_length, lambda: Audio.schedule_sustain_play(key))
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
            note_id = Audio.get_note_identifier(key, octave)
            if Main.sustain_option:
                # If the note is looping, do not stop it
                if note_id in Main.looping_notes:
                    pass
                else:
                    # Cancel scheduled sustain plays
                    if key in Main.scheduled_tasks:
                        Main.root.after_cancel(Main.scheduled_tasks[key])
                        del Main.scheduled_tasks[key]
                    # Schedule to stop the sustain sound after sustain_interval
                    task_id = Main.root.after(Main.sustain_interval, lambda: Audio.stop_sustain_sound(key))
                    Main.scheduled_tasks[key] = task_id
