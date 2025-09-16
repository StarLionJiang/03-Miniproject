# main.py for Raspberry Pi Pico W
# Title: Pico Light Orchestra Instrument Code

import machine
import time
import network
import json
import math
import asyncio

# --- Pin Configuration ---
# The photosensor is connected to an Analog-to-Digital Converter (ADC) pin.
# We will read the voltage, which changes based on light.
photo_sensor_pin = machine.ADC(26)

# --- App Constants (tunable) ---
MIN_LIGHT = 24000       # expected dark threshold
MAX_LIGHT = 60000       # expected bright threshold

BASE_NOTE_HZ = 261.626     # C4 base frequency
OCTAVES = 2                # two octaves
SEMITONES_PER_OCTAVE = 12
TOTAL_STEPS = OCTAVES * SEMITONES_PER_OCTAVE  # 24 semitones
DUTY = 300                 # sound noise：0~65535

# The buzzer is connected to a GPIO pin that supports Pulse Width Modulation (PWM).
# PWM allows us to create a square wave at a specific frequency to make a sound.
buzzer_pin = machine.PWM(machine.Pin(18))

# --- Global State ---
# This variable will hold the task that plays a note from an API call.
# This allows us to cancel it if a /stop request comes in.
api_note_task = None
api_lock_until_ms = 0  # Used to prohibit light control

# --- Core Functions ---


def connect_to_wifi(wifi_config: str = "wifi_config.json"):
    """Connects the Pico W to the specified Wi-Fi network.

    This expects a JSON text file 'wifi_config.json' with 'ssid' and 'password' keys,
    which would look like
    {
        "ssid": "your_wifi_ssid",
        "password": "your_wifi_password"
    }
    """
    data = {
        "ssid": "Group_2/3",
        "password": "smartsys"
    }

    # with open(wifi_config, "r") as f:
      #  data = json.load(f)
    global wlan
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(data["ssid"], data["password"])

    # Wait for connection or fail
    max_wait = 10
    print("Connecting to Wi-Fi...")
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError("Network connection failed")
    else:
        status = wlan.ifconfig()
        ip_address = status[0]
        print(f"Connected! Pico IP Address: {ip_address}")
    return ip_address


def play_tone(frequency: int, duration_ms: int) -> None:
    """Plays a tone on the buzzer for a given duration."""
    if frequency > 0:
        q_step = freq_to_nearest_step(float(frequency))
        q_freq = int(step_to_freq(q_step))
        buzzer_pin.freq(q_freq)
        buzzer_pin.duty_u16(DUTY)
        time.sleep_ms(duration_ms)  # type: ignore[attr-defined]
        stop_tone()
    else:
        time.sleep_ms(duration_ms)  # type: ignore[attr-defined]

def stop_tone():
    """Stops any sound from playing."""
    buzzer_pin.duty_u16(0)  # 0% duty cycle means silence


async def play_api_note(frequency, duration_s):
    """Coroutine to play a note from an API call, can be cancelled."""
    try:
        print(f"API playing note: {frequency}Hz for {duration_s}s")
        extend_api_lock(duration_s * 1000 + 2000)
        q_step = freq_to_nearest_step(float(frequency))
        q_freq = int(step_to_freq(q_step))
        buzzer_pin.freq(q_freq)
        buzzer_pin.duty_u16(DUTY)
        await asyncio.sleep(duration_s)
        stop_tone()
        print("API note finished.")
    except asyncio.CancelledError:
        stop_tone()
        print("API note cancelled.")


def map_value(x, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another."""
    return (x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min

def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x

def get_device_id():
    uid = machine.unique_id()  # bytes
    return ''.join('{:02x}'.format(b) for b in uid)

def extend_api_lock(ms):
    """Extend the suppression window by ms milliseconds (from the current time)"""
    global api_lock_until_ms
    api_lock_until_ms = time.ticks_add(time.ticks_ms(), int(ms))

def step_to_freq(step: int) -> float:
    """Semitones -> Frequency"""
    if step < 0:
        step = 0
    elif step > TOTAL_STEPS:
        step = TOTAL_STEPS
    return BASE_NOTE_HZ * (2 ** (step / 12.0))

def freq_to_nearest_step(freq: float) -> int:
    """Any frequency -> steps to the nearest semitone (relative to C4), clamped to 0..TOTAL_STEPS"""
    if freq <= 0:
        return 0
    semi = round(12.0 * (math.log(freq / BASE_NOTE_HZ) / math.log(2.0)))
    if semi < 0:
        semi = 0
    elif semi > TOTAL_STEPS:
        semi = TOTAL_STEPS
    return int(semi)

def light_to_nearest_step(raw_adc: int) -> int:
    """ADC raw value -> nearest semitone step (linearly mapped to 0..TOTAL_STEPS and rounded)"""
    clamped = clamp(raw_adc, MIN_LIGHT, MAX_LIGHT)
    if MAX_LIGHT == MIN_LIGHT:
        return 0
    t = (clamped - MIN_LIGHT) / (MAX_LIGHT - MIN_LIGHT)  # 0..1
    step = round(t * TOTAL_STEPS)  # 0..24
    if step < 0:
        step = 0
    elif step > TOTAL_STEPS:
        step = TOTAL_STEPS
    return int(step)


async def handle_request(reader, writer):
    """Handles incoming HTTP requests."""
    global api_note_task

    print("Client connected")
    request_line = await reader.readline()
    # Skip headers
    while await reader.readline() != b"\r\n":
        pass

    try:
        request = str(request_line, "utf-8")
        method, url, _ = request.split()
        print(f"Request: {method} {url}")
    except (ValueError, IndexError):
        writer.write(b"HTTP/1.0 400 Bad Request\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Read current sensor value
    light_value = photo_sensor_pin.read_u16()

    response = ""
    content_type = "text/html"
    status_line = "HTTP/1.0 503 Service Unavailable\r\n"

    # --- API Endpoint Routing ---
    if method == "GET" and url == "/":
        html = f"""
        <html>
            <body>
                <h1>Pico Light Orchestra</h1>
                <p>Current light sensor reading: {light_value}</p>
            </body>
        </html>
        """
        response = html
        status_line = "HTTP/1.0 200 OK\r\n"
        
    elif method == "GET" and url == "/sensor":
        raw = photo_sensor_pin.read_u16()
        clamped = clamp(raw, MIN_LIGHT, MAX_LIGHT)
        norm = 0.0 if MAX_LIGHT == MIN_LIGHT else (clamped - MIN_LIGHT) / (MAX_LIGHT - MIN_LIGHT)
        # Rough lux estimate
        lux_est = norm * 200 
        
        response = json.dumps({
            "raw": raw,
            "norm": round(norm, 2),
            "lux_est": round(lux_est, 1)
        })
        status_line = "HTTP/1.0 200 OK\r\n"
        content_type = "application/json"

    elif method == "GET" and url == "/health":
        device_ok = True
        errors = []

        # Wi-Fi check (inline, no function)
        if not wlan.isconnected():
            device_ok = False
            errors.append("Wi-Fi disconnected")

    # Build the response
        response = {
        "status": "ok" if device_ok else "error",
        "device_id": get_device_id(),
        "api": "1.0.0"
        }
        if errors:
            response["errors"] = errors

    # HTTP status
        status_line = (
            "HTTP/1.0 200 OK\r\n"
            if device_ok
            else "HTTP/1.0 503 Service Unavailable\r\n"
        )
        content_type = "application/json"
        
    elif method == "POST" and url == "/play_note":
        # This requires reading the request body, which is not trivial.
        # A simple approach for a known content length:
        # Note: A robust server would parse Content-Length header.
        # For this student project, we'll assume a small, simple JSON body.
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            freq = data.get("frequency", 0)
            duration = data.get("duration", 0)

            extend_api_lock(duration * 1000 + 2000)

            # If a note is already playing via API, cancel it first
            if api_note_task:
                api_note_task.cancel()

            # Start the new note as a background task
            api_note_task = asyncio.create_task(play_api_note(freq, duration))

            response = '{"status": "ok", "message": "Note playing started."}'
            content_type = "application/json"
        except (ValueError, json.JSONDecodeError):
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error": "Invalid JSON"}\r\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

    elif method == "POST" and url == "/tone":
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            # Extract parameters
            freq = data.get("freq", 0)
            ms = data.get("ms", 0)
            duty = data.get("duty", 0.5)

            # If a note is already playing via API, cancel it first
            if api_note_task:
                api_note_task.cancel()

            # Start new tone in background
            api_note_task = asyncio.create_task(play_api_note(freq, ms, duty))

            # Prepare response (202 Accepted)
            response = json.dumps({
                "playing": True,
                "until_ms_from_now": ms
            })
            status_line = "HTTP/1.0 202 Accepted\r\n"
            content_type = "application/json"

        except (ValueError, json.JSONDecodeError):
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error": "Invalid JSON"}\r\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
    elif method == "POST" and url == "/melody":
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            notes = data["notes"]
            # Extract parameters
            duty = 0.5
            gap_ms = data["gap_ms"] / 1000
            num_notes = len(data["notes"])

            # If a note is already playing via API, cancel it first
            if api_note_task:
                api_note_task.cancel()

            # play sequence of notes
            for i, note in enumerate(notes):
                freq = note["freq"]
                ms = note["ms"]

                # Play the note
                api_note_task = asyncio.create_task(play_api_note(freq, ms, duty))
                await api_note_task  # wait for the note to finish

                # Gap between notes (skip after the last one)
                if i < num_notes - 1 and gap_ms > 0:
                    await asyncio.sleep(gap_ms)

        # Prepare response (202 Accepted)
            response = json.dumps({
                "queued": num_notes,
            })
            status_line = "HTTP/1.0 202 Accepted\r\n"
            content_type = "application/json"

        except (ValueError, json.JSONDecodeError):
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error": "Invalid JSON"}\r\n')
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return
            
    elif method == "POST" and url == "/stop":
        if api_note_task:
            api_note_task.cancel()
            api_note_task = None
        stop_tone()  # Force immediate stop
        response = '{"status": "ok", "message": "All sounds stopped."}'
        content_type = "application/json"
        
    else:
        writer.write(b"HTTP/1.0 404 Not Found\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        return

    # Send response
    writer.write(
        f"{status_line}Content-type: {content_type}\r\n\r\n".encode("utf-8")
    )
    writer.write(response.encode("utf-8"))
    writer.write(response.encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()
    print("Client disconnected")


async def main():
    """Main execution loop."""
    try:
        ip = connect_to_wifi()
        print(f"Starting web server on {ip}...")
        server = await asyncio.start_server(handle_request, "0.0.0.0", 80)
        print("HTTP server started on port 80")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # This loop runs the "default" behavior: playing sound based on light
    while True:
        # Only run this loop if no API note is currently scheduled to play
        now = time.ticks_ms()
        locked = time.ticks_diff(api_lock_until_ms, now) > 0

        if api_note_task is not None and not api_note_task.done():
            pass
        elif locked:
            stop_tone()
        else:
            light_value = photo_sensor_pin.read_u16()
            step = light_to_nearest_step(light_value)
            if step > 0:
                q_freq = int(step_to_freq(step))
                buzzer_pin.freq(q_freq)
                buzzer_pin.duty_u16(DUTY)
            else:
                stop_tone()

        await asyncio.sleep_ms(50)  # type: ignore[attr-defined]


# Run the main event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
        stop_tone()
