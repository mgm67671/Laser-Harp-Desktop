# LLHelpers.py

import os
import LLMain

def transpose_note(note, key, octave, locked_key=None):
    """Transpose a note based on the current key or locked key, adjusting the octave if necessary."""
    used_key = locked_key if locked_key else key
    key_index = LLMain.keys.index(used_key)
    note_index = LLMain.keys.index(note)
    transposed_index = (note_index + key_index) % len(LLMain.keys)
    transposed_note = LLMain.keys[transposed_index]
    # If transposed_index < note_index, we've wrapped around, so increment the octave
    octave_adjustment = 0
    if transposed_index < note_index:
        octave_adjustment = 1
    return transposed_note, octave + octave_adjustment

def get_note_identifier(key, octave, instrument=None):
    """Generate a unique identifier for a note based on its transposed note, octave, and instrument."""
    original_note = LLMain.input_to_note[key]
    transposed_note, adjusted_octave = transpose_note(original_note, LLMain.current_key, octave)
    if key == '=':
        adjusted_octave += 1
    instrument_part = f"_{os.path.basename(instrument)}" if instrument else ""
    return f"{transposed_note}{adjusted_octave}{instrument_part}"