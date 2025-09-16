# main.py for Raspberry Pi Pico W
# Title: Pico Light Orchestra Instrument Code

import machine
import time
import network
import json
import asyncio


async def main():
    # Configure the onboard LED pin (GPIO 25) as an output
    led = machine.Pin(25, machine.Pin.OUT)

    # Loop indefinitely to blink the LED
    while True:
        led.value(1)  # Turn the LED on (set pin value to high)
        await asyncio.sleep_ms(50)  # type: ignore[attr-defined]
        led.value(0)  # Turn the LED off (set pin value to low)
        await asyncio.sleep_ms(50)  # type: ignore[attr-defined]


# Run the main event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program stopped.")
        stop_tone()
