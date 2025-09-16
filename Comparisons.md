# Comparisons — Continuous vs Quantized Mapping

| Aspect | Continuous (linear light→Hz) | Quantized (12‑TET semitones) |
|---|---|---|
| Stability under ambient jitter | Lower (needs smoothing) | Higher; snapping avoids slide |
| Ensemble sound | Can drift per device | Clean and harmonious |
| Expressiveness | High micro‑variation | Discrete; less micro detail |
| Complexity | Very low | Moderate (scale, steps) |

## Notes
- Continuous mapping may “meow” around boundaries. Add smoothing or hysteresis.
- Quantized mapping benefits from a well‑chosen octave span and calibrated light range.

## Team Decision

- **Chosen strategy**: **quantized**
- **Why**: For classroom demonstrations and multi-Pico ensemble performance, we prioritize **stability**, **cross-device consistency**, and **clean harmony** over micro-expressiveness. Quantization removes flicker-induced pitch drift from room lighting and avoids “sliding” between notes, making timing and tuning more reproducible than continuous mapping.
- **Parameters**:
  - **Scale**: 12-TET with base **C4 = 261.626 Hz**, **octaves = 2**, total **24 steps** (≈ C4..C6).
  - **Light calibration**: **MIN_LIGHT = 24,000**, **MAX_LIGHT = 60,000** (lab baseline). Re-calibrate per room by measuring the 10th/90th percentile of `ADC.read_u16()` and updating these constants.
  - **Quantization**: nearest-step rounding; **smoothing window**: **0 ms** (disabled by default).
  - **Duty**: **DUTY = 300** (range 0..65535). Increase to **2,000–8,000** for louder venues; avoid prolonged ≥50% (= 32768) without amplification/heat considerations.
  - **API priority**: During `/play_note`, suppress sensor-driven playback for the note duration **+ 2 s** tail (`api_lock_until_ms`) to prevent clashes.