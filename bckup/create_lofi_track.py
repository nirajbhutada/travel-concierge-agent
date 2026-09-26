import wave
import numpy as np

sample_rate = 44100
duration = 36.0  # seconds to match video duration
num_samples = int(sample_rate * duration)

t = np.linspace(0, duration, num_samples, endpoint=False)

# 1. Upbeat Lo-Fi Drums (BPM = 88)
bpm = 88.0
beat_dur = 60.0 / bpm
eight_dur = beat_dur / 2.0

drums = np.zeros(num_samples)

np.random.seed(42)

# Kick, Snare, Hi-hat synthesis
for i in range(int(duration / eight_dur)):
    beat_time = i * eight_dur
    sample_idx = int(beat_time * sample_rate)
    
    # Hi-hat on every 8th note
    hat_len = int(0.04 * sample_rate)
    if sample_idx + hat_len < num_samples:
        hat_noise = (np.random.rand(hat_len) * 2 - 1) * np.exp(-np.linspace(0, 10, hat_len))
        drums[sample_idx:sample_idx+hat_len] += hat_noise * 0.10
        
    # Kick on beat 0 and 5 (16th note syncopation)
    bar_pos = i % 8
    if bar_pos in [0, 5]:
        kick_len = int(0.18 * sample_rate)
        if sample_idx + kick_len < num_samples:
            kick_t = np.linspace(0, 0.18, kick_len)
            freq = 110 * np.exp(-kick_t * 25) + 35
            kick = np.sin(2 * np.pi * freq * kick_t) * np.exp(-kick_t * 10)
            drums[sample_idx:sample_idx+kick_len] += kick * 0.55

    # Snare on beat 2 and 6
    if bar_pos in [2, 6]:
        snare_len = int(0.15 * sample_rate)
        if sample_idx + snare_len < num_samples:
            snare_t = np.linspace(0, 0.15, snare_len)
            snare_tone = np.sin(2 * np.pi * 170 * snare_t) * np.exp(-snare_t * 22)
            snare_noise = (np.random.rand(snare_len) * 2 - 1) * np.exp(-snare_t * 14)
            drums[sample_idx:sample_idx+snare_len] += (snare_tone * 0.25 + snare_noise * 0.3) * 0.45

# 2. Warm Upbeat Chords (Fmaj7 -> Dm7 -> Gm7 -> C7)
chords_freqs = [
    [174.6, 220.0, 261.6, 329.6],  # Fmaj7
    [146.8, 174.6, 220.0, 261.6],  # Dm7
    [196.0, 233.1, 293.7, 349.2],  # Gm7
    [130.8, 164.8, 196.0, 233.1],  # C7
]

chords = np.zeros(num_samples)
bar_dur = beat_dur * 4

for bar in range(int(duration / bar_dur) + 1):
    chord = chords_freqs[bar % len(chords_freqs)]
    start_time = bar * bar_dur
    start_idx = int(start_time * sample_rate)
    chord_len = int(bar_dur * sample_rate)
    
    if start_idx >= num_samples:
        break
    actual_len = min(chord_len, num_samples - start_idx)
    ct = np.linspace(0, actual_len / sample_rate, actual_len)
    
    chord_wave = np.zeros(actual_len)
    for freq in chord:
        # Soft Rhodes / EP sine + 2nd harmonic
        wave_f = np.sin(2 * np.pi * freq * ct) + 0.25 * np.sin(2 * np.pi * freq * 2 * ct)
        chord_wave += wave_f
        
    # Envelope with soft attack and smooth decay
    env = np.minimum(ct / 0.04, 1.0) * np.exp(-ct * 0.75)
    chords[start_idx:start_idx+actual_len] += chord_wave * env * 0.12

# 3. Vinyl Texture
vinyl = (np.random.rand(num_samples) * 2 - 1) * 0.012

# Combine & Normalize
master = chords + drums + vinyl
master = master / np.max(np.abs(master)) * 0.75

audio_data = (master * 32767).astype(np.int16)

with wave.open("recordings/lofi_track.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    wf.writeframes(audio_data.tobytes())

print("Generated lofi_track.wav successfully!")
