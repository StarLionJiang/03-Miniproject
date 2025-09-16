# Designs

## System Goal
Turn ambient light variations into musical pitches on Raspberry Pi Pico W, and coordinate multiple devices from a desktop client.

## Components
- **Sensing**: LDR + voltage divider → ADC (GP26 / ADC0)
- **Synthesis**: PWM on GP15 → piezo buzzer
- **Networking**: simple HTTP server on the Pico
- **Orchestration**: `dashboard.py` and `conductor.py` (PC/Mac)

## Dataflow

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


## Concurrency & Priority
- Two concurrent tasks (via `asyncio`):
  - HTTP server
  - light→music loop
- Priority: API‑driven sound overrides the default loop (an optional suppression window may be applied in v2).

## Tunables
- Light mapping range (record `raw_min/max` on site)
- Frequency bounds (default A1=55 Hz to C7=2093 Hz)
- Duty cycle (keep moderate for safety)
- Hysteresis / smoothing (optional)
- Quantization vs continuous mapping (see `Comparisons.md`)