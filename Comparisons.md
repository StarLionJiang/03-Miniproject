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

## Team Decision (fill-in)
- **Chosen strategy**: <quantized / continuous / hybrid>
- **Why**: <reasons; classroom vs installation; robustness vs expressiveness>
- **Parameters**: <octaves, MIN/MAX light, smoothing window, duty>