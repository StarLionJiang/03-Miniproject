# 2025 Fall ECE Senior Design Miniproject

[Project definition](./Project.md)

This project uses the Raspberry Pi Pico 2WH SC1634 (wireless, with header pins).

Each team must provide a micro-USB cable that connects to their laptop to plug into the Pi Pico.
The cord must have the data pins connected.
Splitter cords with multiple types of connectors fanning out may not have data pins connected.
Such micro-USB cords can be found locally at Microcenter, convenience stores, etc.
The student laptop is used to program the Pi Pico.
The laptop software to program and debug the Pi Pico works on macOS, Windows, and Linux.

This miniproject focuses on using
[MicroPython](./doc/micropython.md)
using
[Thonny IDE](./doc/thonny.md).
Other IDE can be used, including Visual Studio Code or
[rshell](./doc/rshell.md).

## Demo


https://github.com/user-attachments/assets/6497bf12-17d6-4e06-a6e5-461943005262

![image](https://github.com/user-attachments/assets/83f0bfa6-9904-4269-af44-d7886ecc4591)

![image](https://github.com/user-attachments/assets/4c8b7e93-297e-4210-a4f1-4b59f8c630b7)

## Hardware

* Raspberry Pi Pico WH [SC1634](https://pip.raspberrypi.com/categories/1088-raspberry-pi-pico-2-w) (WiFi, Bluetooth, with header pins)
* Freenove Pico breakout board [FNK0081](https://store.freenove.com/products/fnk0081)
* Piezo Buzzer SameSky CPT-3095C-300
* 10k ohm resistor
* 2 [tactile switches](hhttps://www.mouser.com/ProductDetail/E-Switch/TL59NF160Q?qs=QtyuwXswaQgJqDRR55vEFA%3D%3D)

### Photoresistor details

The photoresistor uses the 10k ohm resistor as a voltage divider
[circuit](./doc/photoresistor.md).
The 10k ohm resistor connects to "3V3" and to ADC2.
The photoresistor connects to the ADC2 and to AGND.
Polarity is not important for this resistor and photoresistor.

The MicroPython
[machine.ADC](https://docs.micropython.org/en/latest/library/machine.ADC.html)
class is used to read the analog voltage from the photoresistor.
The `machine.ADC(id)` value corresponds to the "GP" pin number.
On the Pico W, GP28 is ADC2, accessed with `machine.ADC(28)`.

### Piezo buzzer details

PWM (Pulse Width Modulation) can be used to generate analog signals from digital outputs.
The Raspberry Pi Pico has eight PWM groups each with two PWM channels.
The [Pico WH pinout diagram](https://datasheets.raspberrypi.com/picow/PicoW-A4-Pinout.pdf)
shows that almost all Pico pins can be used for multiple distinct tasks as configured by MicroPython code or other software.
In this exercise, we will generate a PWM signal to drive a speaker.

GP16 is one of the pins that can be used to generate PWM signals.
Connect the speaker with the black wire (negative) to GND and the red wire (positive) to GP16.

In a more complete project, we would use additional resistors and capacitors with an amplifer to boost the sound output to a louder level with a bigger speaker.
The sound output is quiet but usable for this exercise.

Musical notes correspond to particular base frequencies and typically have rich harmonics in typical musical instruments.
An example soundboard showing note frequencies is [clickable](https://muted.io/note-frequencies/).
Over human history, the corresspondance of notes to frequencies has changed over time and location and musical cultures.
For the question below, feel free to use musical scale of your choice!

### Pin Map (this version)
- **Photosensor (LDR)**: `GP26 / ADC0` (`machine.ADC(26)`)
- **Buzzer (Piezo)**: `GP15` (PWM capable)

> Note: Other branches/variants may use `GP28/ADC2` or `GP16/18` for PWM. See `doc/Changelog.md` for differences.

---
## Device Code Logic (`src/main.py`)

1. Connect to Wi‑Fi (reads `wifi_config.json`: `{ "ssid": "...", "password": "..." }`).
2. Continuously read light sensor (typ. ~1000…100000).
3. Map light to frequency range **55 Hz (A1) → 2093 Hz (C7)**.
4. Snap to the nearest musical note via `freq_to_note()` (12‑TET).
5. Run an HTTP server; if no API‑driven sound is active, the default “light‑to‑music” loop plays continuously.

`asyncio` is used to run the HTTP server and the sensor/audio loop concurrently.

---
## HTTP API (Device)

Base URL: `http://<pico-ip>/`

- **GET /** → simple HTML with current light reading.
- **GET /sensor** → `{"raw": <u16>, "norm": <0..1>}`.
- **GET /health** → `{"device_id": "<hex>", "status": "ok"}`.
- **POST /play_note** (seconds) → body: `{"frequency": <float Hz>, "duration": <float sec>}`.
- **POST /tone** (milliseconds + duty) → body: `{"freq": <int Hz>, "ms": <int>, "duty": <0..1>}`.
- **POST /melody** → body: `{"notes":[{"frequency":440,"duration":0.5}, ...]}`.
- **POST /stop** → stop all sounds immediately.

**cURL examples**
```bash
curl -X POST http://<pico-ip>/play_note   -H "Content-Type: application/json"   -d '{"frequency":440,"duration":0.5}'

curl -X POST http://<pico-ip>/tone   -H "Content-Type: application/json"   -d '{"freq":523,"ms":300,"duty":0.5}'

curl -X POST http://<pico-ip>/stop
```

---

## Run & Usage

### Flash & first connect
- Use Thonny (MicroPython) to flash `src/main.py` to Pico.
- Place `wifi_config.json` at the Pico root:
```json
{"ssid":"<your-ssid>","password":"<your-password>"}
```
- Reboot; the serial log prints: `Pico IP Address: <ip>`.

### Desktop tools (student computer)
- `pip install requests`
- **Dashboard**: `python src/dashboard.py` (polls `/health` and `/sensor` for each Pico).
- **Conductor**: `python src/conductor.py` (broadcasts a short melody to all Picos).

> Update `PICO_IPS = ["<ip1>", "<ip2>", ...]` in both scripts.

---

## Architecture & Dataflow



```
      Ambient Light            Wi‑Fi / HTTP
           │                      ▲
   LDR + Divider (GP26/ADC0)      │
           │ (ADC u16)            │          ┌───────────────┐
    ┌──────▼───────┐        ┌─────┴──────┐   │ dashboard.py  │
    │  main.py     │        │ Web Client │   │ conductor.py  │
    │              │◄──────►│  (PC/Mac)  │   └───────────────┘
    │  map → freq  │  API   └────────────┘
    │  freq_to_note│
    │  PWM (GP15)  │────────► Buzzer (piezo)
    └──────────────┘
```

---

## Design Comparison (Continuous vs Quantized)

Two mapping strategies were explored:

1) **Continuous frequency** (linear light→Hz, optional snap):
- Pros: expressive continuous timbre; trivial to implement.
- Cons: jittery under ambient flicker; without snap it “meows”, with snap it may chatter between notes.

2) **Quantized to semitones (12‑TET)**:
- Pros: stable, clean harmonies for ensembles; consistent across devices.
- Cons: loses micro‑variations; requires octave range calibration.

**Recommendation**: classroom demos & ensembles → **quantized** (optionally add hysteresis). Interactive soundscapes → **continuous** (add smoothing). See `doc/Comparisons.md` for details and the team’s final choice.

---

## Frequency to Note Logic

- Input frequency is obtained and rounded to nearest note using a known musical formula 
- Notes are mapped to their corresponding MIDI value
- Note name and octave is extracted using modulo and integer division
- Frequency of note is then returned by the function, which is sent to the buzzer

**Note**: The frequency is first converted to a note and then converted back to the corresponding frequency. We only want the buzzer to play musical notes, rather than random frequencies that sound off-pitch. We round the frequency to a note and convert back to a frequency in order to avoid having to create a dictionary entry for every note and frequency.

---

## Testing (quick checklist)

- Connectivity: `/health` returns `ok` with `device_id`.
- Sensor: `/sensor.raw` changes with cover/shine; `norm ∈ [0,1]`.
- Default loop: pitch changes with light; silence or low note in darkness (per spec).
- API: `/play_note` overrides immediately; `/stop` is instant.
- `/tone`: `ms` affects duration, `duty` affects loudness.
- `/melody`: in‑order playback, no dropped notes.
- Multi‑Pico sync: use `conductor.py` to broadcast 8–16 notes; measure first‑note skew.
- Calibration: record `raw_min/max` and adjust mapping.
- Safety: keep duty moderate to avoid overheating.

Full plan and scripts: `doc/Testing.md`.

---

## Project Structure

```
.
├─ src/
│  ├─ main.py
│  ├─ dashboard.py
│  └─ conductor.py
├─ doc/
│  ├─ Designs.md
│  ├─ Comparisons.md
│  ├─ Testing.md
│  └─ Changelog.md
├─ media/
│  └─ README.txt       # put demo.mp4 / audio clips here
└─ README.md
```

---

## Changes in Designs (pointer)

- v1: GP26/ADC0 + GP15; linear light→[A1,C7] then `freq_to_note`; API: `/` `/sensor` `/health` `/play_note`(sec) `/tone`(ms+duty) `/melody` `/stop`.
- v2 (branch candidate): semitone quantization for both sensor and API; optional API‑lock window; constant `DUTY`; possible PWM pin variants.

See `doc/Changelog.md` for full history and breaking changes.

## Notes

Pico MicroPython time.sleep() doesn't error for negative values even though such are obviously incorrect--it is undefined for a system to sleep for negative time.
Duty cycle greater than 1 is undefined, so we clip the duty cycle to the range [0, 1].


## Reference

* [Pico 2WH pinout diagram](https://datasheets.raspberrypi.com/picow/pico-2-w-pinout.pdf) shows the connections to analog and digital IO.
* Getting Started with Pi Pico [book](https://datasheets.raspberrypi.com/pico/getting-started-with-pico.pdf)

