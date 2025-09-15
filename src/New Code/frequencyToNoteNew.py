import math
from machine import Pin, PWM
import time

A4_FREQ = 440.0   # Hz
A4_MIDI = 69      # MIDI note number for A4
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

BUZZER_PIN = 15   # GPIO pin where buzzer is connected
buzzer = PWM(Pin(BUZZER_PIN))

def freq_to_note(freq):
    if freq <= 0:
        return None, None

    # Convert frequency to MIDI note number
    midi = round(12 * (math.log(freq / A4_FREQ) / math.log(2)) + A4_MIDI)

    # Clamp between C1 (MIDI 24) and A7 (MIDI 93)
    if midi < 24:
        midi = 24
    elif midi > 93:
        midi = 93

    # Note name + octave
    note_name = NOTE_NAMES[midi % 12]
    octave = (midi // 12) - 1
    note_label = "{}{}".format(note_name, octave)

    # Exact frequency of that note
    note_freq = A4_FREQ * (2 ** ((midi - A4_MIDI) / 12))

    return note_label, note_freq

def play_buzzer(freq, duration=0.5):
    """Play a frequency on the buzzer for given duration in seconds."""
    if freq <= 0:
        return
    buzzer.freq(int(freq))
    buzzer.duty_u16(30000)  # Set volume (0–65535)
    time.sleep(duration)
    buzzer.duty_u16(0)      # Stop sound

# Example usage
while True:
    try:
        s = input("Enter frequency in Hz (or 0 to quit): ")
        freq = float(s)
        if freq == 0:
            buzzer.deinit()
            break
        note, note_freq = freq_to_note(freq)
        print("Nearest note:", note, "({:.2f} Hz)".format(note_freq))
        play_buzzer(note_freq, 0.5)
    except:
        print("Please enter a valid number.")
