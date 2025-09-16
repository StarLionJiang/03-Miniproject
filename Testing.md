# Testing Plan

## Hardware Bring‑Up: Blink Test (Pico LED)

Use this minimal program to verify the board boots and runs MicroPython tasks. It blinks the onboard LED.

> Save as `blink.py` and run, or temporarily replace `main.py` for bring‑up.  
- [ ] LED visibly blinks. If not, check power, firmware, and that the LED pin is correct for your Pico/Pico W build.
## Speaker / Buzzer Bench Tests

Use interactive snippet to validate PWM audio, duty control, and note mapping. It takes a frequency, snaps to the nearest musical note, and plays it on the buzzer.

- [ ] Audible tone is produced; changing input frequency changes the played note.
- [ ] Optional: verify with a chromatic tuner app that the played note matches within ~±2%.
- [ ] Duty at `30000/65535 ≈ 46%`. Avoid prolonged testing at very high duty to prevent overheating.

**API cross‑check (optional)**
- Compare local PWM test to `POST /play_note` with the same target note to confirm consistent pitch.

## Connectivity
- [ ] Boot and obtain IP within 10 s.
- [ ] `GET /health` returns `{"status":"ok","device_id":"..."}`.

## Sensor
- [ ] `GET /sensor` shows `raw` changing with cover/shine.
- [ ] `norm` within [0,1] and monotonic with light.

## Default Behavior
- [ ] With no API note active, covering/lighting changes pitch.
- [ ] In darkness: silence or low note per spec.

## API Contracts
- [ ] `POST /play_note` overrides immediately; second call cancels the first.
- [ ] `POST /tone` obeys `ms` (duration) and `duty` (loudness).
- [ ] `POST /melody` plays in order, without gaps.
- [ ] `POST /stop` silences instantly.

## Multi‑Device Sync
- [ ] Use `conductor.py` to broadcast a short melody to multiple devices.
- [ ] Measure first‑note skew (serial timestamps or audio capture).

## Calibration
- [ ] Record `raw_min/raw_max` on site and adjust mapping or MIN/MAX constants.
- [ ] Verify mapping yields intended pitch span (A1..C7).

## Robustness
- [ ] No “stuck tone” after rapid API calls.
- [ ] Long‑run stability (≥30 min) without crash.

## Scripts
**cURL snippets**
```bash
curl -s http://<pico-ip>/health | jq .
curl -s http://<pico-ip>/sensor | jq .

curl -X POST http://<pico-ip>/play_note   -H "Content-Type: application/json"   -d '{"frequency":392,"duration":0.4}'

curl -X POST http://<pico-ip>/tone   -H "Content-Type: application/json"   -d '{"freq":523,"ms":300,"duty":0.5}'

curl -X POST http://<pico-ip>/stop
```