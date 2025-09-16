# Raspberry Pi Pico 2W Light Orchestra (API Edition)

The Raspberry Pi Pico cannot run the FastAPI library, as it requires a full Python environment and operating system.
Instead, our MicroPython code will create a web server that implements an API contract.

1. Objective

Program your Raspberry Pi Pico W to function as a network-controlled "device service."
Write a separate "conductor" application on your computer to interact with the Pico 2W over the WiFi network.
This project uses the fundamentals of API design, networked devices (IoT), and client-server architecture.

2. Architecture

Your team will be responsible for the code on your Pico 2W and code on your computer to act as a Conductor.

* Device Service (main.py runs on each Pico 2W): This is the core firmware. It connects to Wi-Fi, reads the photoresistor (light sensor) and stores this data vs. time, and exposes a web API that allows it to be controlled remotely.
* Conductor (conductor.py runs on one computer): This application is the "brain" of the orchestra. It contains the logic for a song and sends a coordinated sequence of API calls to all the Device Services to play the music.

Quantities to read:

* Luminance (light intensity) from the photoresistor.

Quantities to output:

* Sound from the piezo buzzer (pitch and duration).

Future expansion to accommodate in the software:

* Chrominance (color) from a future color-sensing device.

3. API Contract (Version 1.0) feel free to edit!
All Device Services must implement the following API. This contract is the "language" that allows all our different components to talk to each other.

`GET /health`
: Returns the device's status and identity.

* Response (200 OK):

```json
{
  "status": "ok",
  "device_id": "pico-w-A1B2C3D4E5F6",
  "api": "1.0.0"
}
```

`GET /sensor`
: Returns the current reading from the photoresistor.

Response (200 OK):

```json
{
  "raw": 733,
  "norm": 0.72,
  "lux_est": 120.4
}
```

raw
: The raw 16-bit value from the ADC.

norm
: The normalized value (0.0 to 1.0).

lux_est
: A data number reading of ambient light.

`POST /tone`
: Plays a single tone immediately. This will cancel any currently playing tone or melody.

Request Body:

```json
{
  "freq": 440,
  "ms": 300,
  "duty": 0.5
}
```

duty
: The PWM duty cycle, from 0.0 (silent) to 1.0 (max volume). 0.5 is standard.

Response (202 Accepted):

```json
{
  "playing": true,
  "until_ms_from_now": 300
}
```

`POST /melody`
: Plays a sequence of notes. This will cancel any currently playing tone or melody.

Request Body:

```json
{
  "notes": [
    {"freq": 523, "ms": 200},
    {"freq": 659, "ms": 200},
    {"freq": 784, "ms": 400}
  ],
  "gap_ms": 20
}
```

gap_ms
: A short silent pause between each note in the sequence.

Response (202 Accepted):

```json
{
  "queued": 3
}
```

`GET /events` (Optional Challenge)
A Server-Sent Events (SSE) stream for real-time sensor updates.

Response: A stream of text/event-stream data.

```json
data: {"norm": 0.81, "ts": 1678886400123}

data: {"norm": 0.82, "ts": 1678886400624}
```
