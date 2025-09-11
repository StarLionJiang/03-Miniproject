# main.py for Raspberry Pi Pico W
# Title: Pico Light Orchestra Instrument Code

import machine
import time
import network
import json
import asyncio

# --- Pin Configuration ---
# The photosensor is connected to an Analog-to-Digital Converter (ADC) pin.
# We will read the voltage, which changes based on light.
photo_sensor_pin = machine.ADC(26)

# The buzzer is connected to a GPIO pin that supports Pulse Width Modulation (PWM).
# PWM allows us to create a square wave at a specific frequency to make a sound.
buzzer_pin = machine.PWM(machine.Pin(18))
buzzer_pin.duty_u16(0)  # ensure silent at boot

# --- Global State ---
# Holds the task that plays a note from an API call (so it can be cancelled).
api_note_task = None

# --- Core Functions ---


def connect_to_wifi():
    """Connects the Pico W to Wi-Fi using hardcoded SSID and password."""
    ssid = "Group_2/3"        # 改成你的 Wi-Fi 名
    password = "smartsys"  # 改成你的 Wi-Fi 密码

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connection or fail
    max_wait = 15
    print("Connecting to Wi-Fi...")
    while max_wait > 0:
        status = wlan.status()
        if status < 0 or status >= 3:
            break
        max_wait -= 1
        time.sleep(1)

    if wlan.status() != 3:
        raise RuntimeError("Network connection failed")
    else:
        ip_address = wlan.ifconfig()[0]
        print(f"Connected! Pico IP Address: {ip_address}")
    return ip_address


# === Mode switches ===
ENABLE_LIGHT_MODE = True   # 需要光敏互动就 True；只想听指挥就改 False

# === Light-mode suppression window ===
# 任何一次收到 /tone 或 /play_note 后，在 suppress_light_until 之前禁止光敏发声
suppress_light_until = 0  # ticks_ms 时间戳

def suppress_light(ms_from_now: int):
    """在未来 ms_from_now 毫秒内禁用光敏发声（用于避免与指挥模式抢占）"""
    global suppress_light_until
    suppress_light_until = time.ticks_add(time.ticks_ms(), int(ms_from_now))


def stop_tone():
    """Stops any sound from playing."""
    buzzer_pin.duty_u16(0)  # 0% duty cycle means silence


async def play_api_note(frequency, duration_s, duty_u16=None):
    """Coroutine to play a note from an API call, can be cancelled."""
    try:
        print(f"API playing note: {frequency}Hz for {duration_s}s")
        buzzer_pin.freq(int(frequency))
        if duty_u16 is None:
            buzzer_pin.duty_u16(32768)  # default 50%
        else:
            buzzer_pin.duty_u16(int(duty_u16))
        await asyncio.sleep(duration_s)
        stop_tone()
        print("API note finished.")
    except asyncio.CancelledError:
        stop_tone()
        print("API note cancelled.")


def map_value(x, in_min, in_max, out_min, out_max):
    """Maps a value from one range to another (clamped integer)."""
    if in_max == in_min:
        return out_min
    x = max(in_min, min(x, in_max))
    return int((x - in_min) * (out_max - out_min) // (in_max - in_min) + out_min)


def read_light_norm():
    """Returns (raw_u16, norm_0_to_1) for the photosensor."""
    raw = photo_sensor_pin.read_u16()
    # Adjust these to your lighting conditions
    min_light = 1000
    max_light = 65000
    clamped = max(min_light, min(raw, max_light))
    norm = (clamped - min_light) / (max_light - min_light)
    return raw, norm


async def handle_request(reader, writer):
    """Handles incoming HTTP requests."""
    global api_note_task

    request_line = await reader.readline()
    # Skip headers
    while True:
        line = await reader.readline()
        if line == b"\r\n" or not line:
            break

    try:
        request = str(request_line, "utf-8")
        method, url, _ = request.split()
        print(f"Request: {method} {url}")
    except (ValueError, IndexError):
        writer.write(b"HTTP/1.0 400 Bad Request\r\n\r\n")
        await writer.drain()
        await writer.wait_closed()
        return

    # Read current sensor value
    raw_light, norm_light = read_light_norm()

    response = ""
    content_type = "text/html"

    # --- API Endpoint Routing ---
    if method == "GET" and url == "/":
        html = f"""
        <html>
            <body>
                <h1>Pico Light Orchestra</h1>
                <p>Current light sensor reading (raw): {raw_light}</p>
                <p>Normalized (0~1): {norm_light:.3f}</p>
            </body>
        </html>
        """
        response = html

    elif method == "GET" and url == "/health":
        try:
            import ubinascii
            device_id = ubinascii.hexlify(machine.unique_id()).decode()
        except Exception:
            device_id = "unknown"
        try:
            ip = network.WLAN(network.STA_IF).ifconfig()[0]
        except Exception:
            ip = "0.0.0.0"
        response = json.dumps({"status": "ok", "device_id": device_id, "ip": ip})
        content_type = "application/json"

    elif method == "GET" and url == "/sensor":
        response = json.dumps({"raw": raw_light, "norm": norm_light})
        content_type = "application/json"

    elif method == "POST" and url == "/play_note":
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            freq = float(data.get("frequency", 0))
            duration = float(data.get("duration", 0))  # seconds
            
            suppress_light(int(duration * 1000) + 200)
            
            if api_note_task:
                api_note_task.cancel()
            api_note_task = asyncio.create_task(
                play_api_note(freq, duration, duty_u16=32768)
            )
            response = '{"status": "ok", "message": "Note playing started."}'
            content_type = "application/json"
        except Exception:
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error":"Invalid JSON"}')
            await writer.drain()
            await writer.wait_closed()
            return

    elif method == "POST" and url == "/tone":
        # conductor.py uses this: {"freq": Hz, "ms": milliseconds, "duty": 0..1}
        raw_data = await reader.read(1024)
        try:
            data = json.loads(raw_data)
            freq = float(data.get("freq", 0))
            ms = int(data.get("ms", 0))
            duty = float(data.get("duty", 0.5))
            duty = 0.0 if duty < 0 else (1.0 if duty > 1.0 else duty)
            duty_u16 = int(duty * 65535)
            
            suppress_light(ms + 800)

            if api_note_task:
                api_note_task.cancel()
            api_note_task = asyncio.create_task(
                play_api_note(freq, ms / 1000.0, duty_u16=duty_u16)
            )
            response = '{"status":"ok","message":"tone started"}'
            content_type = "application/json"
        except Exception:
            writer.write(b'HTTP/1.0 400 Bad Request\r\n\r\n{"error":"Invalid JSON"}')
            await writer.drain()
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
        await writer.wait_closed()
        return

    # Send response
    writer.write(
        f"HTTP/1.0 200 OK\r\nContent-type: {content_type}\r\n\r\n".encode("utf-8")
    )
    writer.write(response.encode("utf-8"))
    await writer.drain()
    await writer.wait_closed()


async def main():
    """Main execution loop."""
    try:
        ip = connect_to_wifi()
        # Properly start and keep a reference to the server
        server = await asyncio.start_server(handle_request, "0.0.0.0", 80)
        print(f"HTTP server started on {ip}:80")
    except Exception as e:
        print(f"Failed to initialize: {e}")
        return

    # Default behavior: play tone based on light if no API note is playing
    # Default behavior: light→tone only when not suppressed and no API note
# Default behavior: light→tone only when not suppressed and no API note
    while True:
        now = time.ticks_ms()
        in_suppress = time.ticks_diff(suppress_light_until, now) > 0
        api_busy = (api_note_task is not None) and (not api_note_task.done())

        if api_busy:
            # 指挥在播歌：不要动蜂鸣器，避免打断
            pass

        elif in_suppress:
            # 在抑制窗口内：无论光线如何，都强制静音，避免“插嘴”
            stop_tone()

        elif ENABLE_LIGHT_MODE:
            # 光敏主导（仅当未被抑制且没有API播放）
            raw_light, norm_light = read_light_norm()
            if norm_light > 0.0:
                min_freq = 130   # C4
                max_freq = 520  # C6
                frequency = int(min_freq + norm_light * (max_freq - min_freq))
                buzzer_pin.freq(frequency)
                buzzer_pin.duty_u16(32768)  # 50% duty
            else:
                stop_tone()
        else:
            # 既没有API在播，光敏也关闭时，保持静音
            stop_tone()

        await asyncio.sleep_ms(50)


# Run the main event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
        stop_tone()

