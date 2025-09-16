# Changelog

## v1 (YYYY-MM-DD)
- **Pins**: LDR = GP26 / ADC0; Buzzer = GP15 (PWM)
- **Mapping**: linear light→[A1(55 Hz), C7(2093 Hz)], then `freq_to_note()` snap
- **API**: `/` `/sensor` `/health` `/play_note` (seconds) `/tone` (ms + duty) `/melody` `/stop`

## v2 (branch; YYYY-MM-DD)
- **Pitch**: semitone quantization (12‑TET) for both sensor and API input
- **Suppression window**: optional API‑lock to avoid sensor loop interfering
- **Duty control**: constant `DUTY`; adjust for venue loudness
- **Pins**: variations may use GP18/GP16 PWM (document per branch)