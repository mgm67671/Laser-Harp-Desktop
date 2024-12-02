# LLGui.py

import os
import tkinter as tk
from tkinter import ttk
import LLMain
import LLAudio
import LLLooping
import LLHelpers

def octave_buttons():
    """Create octave switcher buttons."""
    tk.Label(main_frame, text="Octave Switcher").grid(row=0, column=0, sticky='nsw')
    octave_buttons_frame = tk.Frame(main_frame)
    octave_buttons_frame.grid(row=1, column=0, sticky='nsw')

    main_frame.grid_rowconfigure(1, weight=10)
    octave_buttons_frame.grid_rowconfigure(0, weight=1)

    for i, octave in enumerate(LLMain.octave_range):
        octave_button = tk.Button(
            octave_buttons_frame,
            text=f"Octave {octave}",
            command=lambda o=octave: LLAudio.change_octave(o),
            width=20,
            activebackground="blue",
            activeforeground="white"
        )
        octave_button.grid(row=i * 2, column=0, pady=padding_y, sticky='nsw')
        octave_buttons_frame.grid_rowconfigure(i * 2, weight=1)

def volume_slider():
    """Create volume slider."""
    tk.Label(main_frame, text="Volume").grid(row=0, column=1, pady=padding_y)
    volume_slider = tk.Scale(
        main_frame,
        from_=1,
        to=0,
        orient='vertical',
        command=LLAudio.adjust_volume,
        resolution=.01,
        width=padding_y * 4,
        activebackground="blue",
        showvalue=0,
        repeatdelay=100
    )
    volume_slider.set(LLMain.volume)
    volume_slider.grid(row=1, column=1, sticky='ns')

def instrument_buttons():
    """Create instrument switcher buttons."""
    tk.Label(main_frame, text="Instrument Switcher").grid(row=0, column=2, sticky='nse')
    instrument_button_frame = tk.Frame(main_frame)
    instrument_button_frame.grid(row=1, column=2, sticky='nse')

    instrument_button_frame.grid_rowconfigure(0, weight=1)
    instrument_button_frame.grid_columnconfigure(0, weight=1)

    for i, instrument in enumerate(LLMain.instrument_folders):
        instrument_button = tk.Button(
            instrument_button_frame,
            text=f"{instrument}",
            width=20,
            command=lambda i=instrument: LLAudio.choose_folder(i),
            activebackground="blue",
            activeforeground="white"
        )
        instrument_button.grid(row=i, column=0, pady=padding_y, sticky='nse')
        instrument_button_frame.grid_rowconfigure(i, weight=1)

def advanced_menu():
    """Create the advanced options menu."""
    menu = tk.Toplevel(root)
    menu.title("Advanced Options")
    menu.attributes('-fullscreen', True)

    # Store the reference to the advanced menu window
    LLMain.advanced_menu_window = menu

    # Create a frame inside the advanced menu for layout
    advanced_frame = tk.Frame(menu)
    advanced_frame.pack(expand=True, fill='both', padx=padding_x, pady=padding_y)

    # Divide the advanced frame into columns
    advanced_frame.grid_columnconfigure(0, weight=1)
    advanced_frame.grid_columnconfigure(1, weight=1)

    # Left side: Key selection and other controls
    controls_frame = tk.Frame(advanced_frame)
    controls_frame.grid(row=0, column=0, sticky='nsew')

    tk.Label(controls_frame, text="Select Key").pack(pady=padding_y)
    key_dropdown = ttk.Combobox(controls_frame, values=LLMain.keys, state="readonly")
    key_dropdown.set(LLMain.current_key)
    key_dropdown.bind(
        "<<ComboboxSelected>>",
        lambda e: LLAudio.change_key(key_dropdown.get())
    )
    key_dropdown.pack(pady=padding_y)

    # Sustain option
    sustain_var = tk.BooleanVar(value=LLMain.sustain_option)

    def update_sustain():
        LLMain.sustain_option = sustain_var.get()
        if LLMain.running:
            LLAudio.preload_sounds()

    sustain_check = tk.Checkbutton(
        controls_frame,
        text="Sustain",
        variable=sustain_var,
        command=update_sustain
    )
    sustain_check.pack(pady=padding_y)

    # Loop button
    def activate_loop_mode():
        LLMain.loop_mode = True

    loop_button = tk.Button(
        controls_frame,
        text="Loop Next Note",
        command=activate_loop_mode
    )
    loop_button.pack(pady=padding_y)

    # Stop All Loops button
    stop_all_button = tk.Button(
        controls_frame,
        text="Stop All Loops",
        command=LLLooping.stop_all_loops
    )
    stop_all_button.pack(pady=padding_y)

    # Right side: Looping notes display
    looping_frame = tk.Frame(advanced_frame)
    looping_frame.grid(row=0, column=1, sticky='nsew')

    tk.Label(looping_frame, text="Looping Notes Slots").pack(pady=padding_y)

    # Reset the slot frames list
    LLMain.looping_slot_frames = []

    for i in range(LLMain.max_loops):
        slot_frame = tk.Frame(looping_frame, relief='sunken', borderwidth=1)
        slot_frame.pack(fill='x', pady=padding_y/4)

        slot_label = tk.Label(slot_frame, text=f"Slot {i+1}: Available")
        slot_label.pack(side='left', padx=padding_x/2)

        # Instrument lock checkbox
        instrument_lock_var = tk.BooleanVar()
        instrument_lock_check = tk.Checkbutton(
            slot_frame,
            text="Instrument Lock",
            variable=instrument_lock_var,
            command=lambda idx=i: LLLooping.toggle_instrument_lock(idx)
        )
        instrument_lock_check.pack(side='right', padx=padding_x/2)

        # Key lock checkbox
        key_lock_var = tk.BooleanVar()
        key_lock_check = tk.Checkbutton(
            slot_frame,
            text="Key Lock",
            variable=key_lock_var,
            command=lambda idx=i: LLLooping.toggle_key_lock(idx)
        )
        key_lock_check.pack(side='right', padx=padding_x/2)

        # Octave lock checkbox
        octave_lock_var = tk.BooleanVar()
        octave_lock_check = tk.Checkbutton(
            slot_frame,
            text="Octave Lock",
            variable=octave_lock_var,
            command=lambda idx=i: LLLooping.toggle_octave_lock(idx)
        )
        octave_lock_check.pack(side='right', padx=padding_x/2)

        # Stop Loop Button
        stop_loop_button = tk.Button(
            slot_frame,
            text="Stop",
            command=lambda idx=i: LLLooping.stop_loop_by_slot(idx)
        )
        stop_loop_button.pack(side='right', padx=padding_x/2)

        # Store frame, label, and variables
        LLMain.looping_slot_frames.append({
            'frame': slot_frame,
            'label': slot_label,
            'octave_lock_var': octave_lock_var,
            'key_lock_var': key_lock_var,
            'instrument_lock_var': instrument_lock_var  # Store the instrument lock variable
        })

    # Add Lock All and Unlock All buttons for instruments
    instrument_lock_buttons_frame = tk.Frame(looping_frame)
    instrument_lock_buttons_frame.pack(pady=padding_y)

    lock_all_instruments_button = tk.Button(
        instrument_lock_buttons_frame,
        text="Lock All Instruments",
        command=LLLooping.lock_all_instruments
    )
    lock_all_instruments_button.pack(side='left', padx=padding_x/2)

    unlock_all_instruments_button = tk.Button(
        instrument_lock_buttons_frame,
        text="Unlock All Instruments",
        command=LLLooping.unlock_all_instruments
    )
    unlock_all_instruments_button.pack(side='right', padx=padding_x/2)


    # Add Lock All and Unlock All buttons for octaves
    octave_lock_buttons_frame = tk.Frame(looping_frame)
    octave_lock_buttons_frame.pack(pady=padding_y)

    lock_all_octaves_button = tk.Button(
        octave_lock_buttons_frame,
        text="Lock All Octaves",
        command=LLLooping.lock_all_octaves
    )
    lock_all_octaves_button.pack(side='left', padx=padding_x/2)

    unlock_all_octaves_button = tk.Button(
        octave_lock_buttons_frame,
        text="Unlock All Octaves",
        command=LLLooping.unlock_all_octaves
    )
    unlock_all_octaves_button.pack(side='right', padx=padding_x/2)

    # Add Lock All and Unlock All buttons for keys
    key_lock_buttons_frame = tk.Frame(looping_frame)
    key_lock_buttons_frame.pack(pady=padding_y)

    lock_all_keys_button = tk.Button(
        key_lock_buttons_frame,
        text="Lock All Keys",
        command=LLLooping.lock_all_keys
    )
    lock_all_keys_button.pack(side='left', padx=padding_x/2)

    unlock_all_keys_button = tk.Button(
        key_lock_buttons_frame,
        text="Unlock All Keys",
        command=LLLooping.unlock_all_keys
    )
    unlock_all_keys_button.pack(side='right', padx=padding_x/2)

    # Bind a custom event to update the display
    menu.bind('<<UpdateLoopingNotesDisplay>>', update_looping_notes_display)

    # Call update_looping_notes_display to initialize the display
    update_looping_notes_display()

    button_frame = tk.Frame(menu)
    button_frame.pack(side=tk.BOTTOM, pady=padding_y)

    tk.Button(
        button_frame,
        text="Exit",
        command=menu.destroy,
        width=20
    ).pack(side=tk.RIGHT, padx=padding_x)

    if LLMain.running:
        menu.bind("<KeyPress>", LLLooping.key_press)
        menu.bind("<KeyRelease>", LLLooping.key_release)

    # Handle the advanced menu closing
    def on_advanced_menu_close():
        LLMain.advanced_menu_window = None
        menu.destroy()

    menu.protocol("WM_DELETE_WINDOW", on_advanced_menu_close)

    # Ensure the window remains on top and modal
    menu.grab_set()
    root.wait_window(menu)

def update_looping_notes_display(event=None):
    """Update the display of looping note slots."""
    if not hasattr(LLMain, 'looping_slot_frames'):
        return  # Advanced menu is not open

    for i, slot_info in enumerate(LLMain.looping_slot_frames):
        note_id = LLMain.looping_note_slots[i]
        slot_label = slot_info['label']
        octave_lock_var = slot_info['octave_lock_var']
        key_lock_var = slot_info['key_lock_var']
        instrument_lock_var = slot_info['instrument_lock_var']
        if note_id is not None:
            note_info = LLMain.looping_notes[note_id]
            key = note_info['key']
            original_note = LLMain.input_to_note[key]
            # Determine the correct octave
            if note_info['octave_locked']:
                octave = note_info['locked_octave']
            else:
                octave = LLMain.current_octave
            if key == '=':
                octave += 1
            # Use locked key if key is locked
            used_key = note_info['locked_key'] if note_info['key_locked'] else LLMain.current_key
            # Use locked instrument if instrument is locked
            used_instrument = note_info['locked_instrument'] if note_info['instrument_locked'] else LLMain.current_folder
            instrument_name = os.path.basename(used_instrument)
            # Transpose the note based on the used key
            transposed_note, adjusted_octave = LLHelpers.transpose_note(original_note, used_key, octave)
            display_note_id = f"{transposed_note}{adjusted_octave}"
            # Check if sustain mode is on for this looping note
            sustain_status = "Sustain" if note_info['sustain_option'] else "Normal"
            # Display lock statuses
            key_status = f"Key Locked ({used_key})" if note_info['key_locked'] else "Key Unlocked"
            octave_status = f"Octave Locked ({octave})" if note_info['octave_locked'] else "Octave Unlocked"
            instrument_status = f"Instrument Locked ({instrument_name})" if note_info['instrument_locked'] else "Instrument Unlocked"
            slot_label.config(text=f"Slot {i+1}: {display_note_id} ({sustain_status}, {key_status}, {octave_status}, {instrument_status})")
            # Update lock checkboxes
            octave_lock_var.set(note_info['octave_locked'])
            key_lock_var.set(note_info['key_locked'])
            instrument_lock_var.set(note_info['instrument_locked'])
        else:
            slot_label.config(text=f"Slot {i+1}: Available")
            octave_lock_var.set(False)
            key_lock_var.set(False)
            instrument_lock_var.set(False)


def start_harp():
    """Start the harp application."""
    LLAudio.start_harp()
    start_button.config(text="Stop", command=stop_harp)
    root.bind("<KeyPress>", LLLooping.key_press)
    root.bind("<KeyRelease>", LLLooping.key_release)

def stop_harp():
    """Stop the harp application."""
    LLAudio.stop_harp()
    start_button.config(text="Start", command=start_harp)
    root.unbind("<KeyPress>")
    root.unbind("<KeyRelease>")

def main_menu():
    """Set up the main GUI layout."""
    global start_button
    global root
    root = tk.Tk()
    LLMain.root = root
    root.title("Laser Harp Main Menu")
    root.attributes('-fullscreen', True)

    global screen_width
    global screen_height
    global padding_x
    global padding_y
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    padding_x = int(screen_width * 0.02)
    padding_y = int(screen_height * 0.02)

    global main_frame
    main_frame = tk.Frame(root)
    main_frame.pack(expand=True, fill='both', padx=padding_x, pady=padding_y)

    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_columnconfigure(1, weight=1)
    main_frame.grid_columnconfigure(2, weight=1)

    octave_buttons()
    volume_slider()
    instrument_buttons()

    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.BOTTOM, pady=padding_y)

    start_button = tk.Button(button_frame, text="Start", command=start_harp, width=20)
    start_button.pack(side=tk.LEFT, padx=padding_x)

    tk.Button(
        button_frame,
        text="Advanced Options",
        command=advanced_menu,
        width=20
    ).pack(side=tk.RIGHT, padx=padding_x)

    tk.Button(
        button_frame,
        text="Exit",
        command=root.quit,
        width=20
    ).pack(side=tk.RIGHT, padx=padding_x)

    root.mainloop()