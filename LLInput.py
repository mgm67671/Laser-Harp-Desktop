# LLInput.py

import LLMain
import LLAudio
import LLLooping

def key_press(event):
    """Handle key press events."""
    keysym = event.keysym
    key = event.char

    if keysym == 'Shift_L':
        handle_shift('left')
    elif keysym == 'Shift_R':
        handle_shift('right')
    elif key in LLMain.input_to_note:
        octave = LLMain.current_octave
        if key == '=':
            octave += 1
        note_id = LLAudio.get_note_identifier(key, octave)
        if LLMain.loop_mode:
            LLLooping.handle_loop_mode(note_id, key)
        else:
            handle_normal_key_press(note_id, key)

def handle_shift(direction):
    """Handle octave changes with shift keys."""
    if direction == 'left':
        new_octave = LLMain.current_octave - 1
        if new_octave in LLMain.octave_range:
            LLAudio.change_octave(new_octave)
            print(f"Octave decreased to {new_octave}")
        else:
            print("Cannot decrease octave further.")
    elif direction == 'right':
        new_octave = LLMain.current_octave + 1
        if new_octave in LLMain.octave_range:
            LLAudio.change_octave(new_octave)
            print(f"Octave increased to {new_octave}")
        else:
            print("Cannot increase octave further.")

def handle_normal_key_press(note_id, key):
    """Handle normal key presses."""
    if note_id in LLMain.looping_notes:
        # Stop the looping note
        LLAudio.stop_looping_note_by_key(note_id)
    else:
        if not LLMain.key_status.get(key, False):
            LLMain.key_status[key] = True
            if LLMain.sustain_option:
                # Play attack sound, then schedule sustain playback
                sounds = LLMain.sound_objects[key]
                sounds['attack'].play()
                attack_length = int(sounds['attack'].get_length() * 1000)
                LLMain.root.after(attack_length, lambda: LLAudio.schedule_sustain_play(key))
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
            note_id = LLAudio.get_note_identifier(key, octave)
            if LLMain.sustain_option:
                # If the note is looping, do not stop it
                if note_id in LLMain.looping_notes:
                    pass
                else:
                    # Cancel scheduled sustain plays
                    if key in LLMain.scheduled_tasks:
                        LLMain.root.after_cancel(LLMain.scheduled_tasks[key])
                        del LLMain.scheduled_tasks[key]
                    # Schedule to stop the sustain sound after sustain_interval
                    task_id = LLMain.root.after(LLMain.sustain_interval, lambda: LLAudio.stop_sustain_sound(key))
                    LLMain.scheduled_tasks[key] = task_id
