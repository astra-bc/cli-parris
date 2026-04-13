"""Sound effects module - custom WAV generation + macOS system sounds."""

import wave
import struct
import math
import os
import subprocess
import tempfile
import random as _random

SAMPLE_RATE = 44100
_sound_cache = {}
_sound_dir = None


def _get_sound_dir():
    global _sound_dir
    if _sound_dir is None:
        _sound_dir = tempfile.mkdtemp(prefix="nononono_sfx_")
    return _sound_dir


def _write_wav(filepath, samples):
    """Write raw sample list (-1.0 to 1.0) to WAV."""
    int_samples = [int(max(-1.0, min(1.0, s)) * 32767) for s in samples]
    with wave.open(filepath, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(struct.pack(f'<{len(int_samples)}h', *int_samples))


def _gen_metallic_clash(base_freq=2200, duration=0.15, volume=0.8):
    """キンキン - sharp metallic sword clash at given pitch."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    freqs = [base_freq, base_freq * 1.5, base_freq * 2, base_freq * 2.5, base_freq * 3]
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0
        for f in freqs:
            val += math.sin(2 * math.pi * (f + _random.uniform(-15, 15)) * t)
        val /= len(freqs)
        env = math.exp(-t * 25)
        if i < 80:
            env *= i / 80.0
        samples.append(val * env * volume)
    return samples


def _gen_bass_drum(duration=0.18, volume=0.9):
    """ドスドス - deep bass drum thump."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # pitch drops from 150Hz to 40Hz rapidly
        freq = 150 * math.exp(-t * 20) + 40
        val = math.sin(2 * math.pi * freq * t)
        # add some punch with noise at the start
        if i < 400:
            val += 0.5 * (2 * _random.random() - 1) * (1 - i / 400)
        # fast envelope
        env = math.exp(-t * 15)
        if i < 50:
            env *= i / 50.0
        samples.append(val * env * volume)
    return samples


def _gen_slash(duration=0.12, volume=0.8):
    """ズバッ - sharp slash sound."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # noise burst filtered with descending pitch
        noise = 2 * _random.random() - 1
        freq = 800 * math.exp(-t * 30) + 200
        tone = math.sin(2 * math.pi * freq * t)
        val = noise * 0.6 + tone * 0.4
        # very fast attack and decay
        env = math.exp(-t * 20)
        if i < 30:
            env *= i / 30.0
        samples.append(val * env * volume)
    return samples


def _gen_critical_slash(duration=0.2, volume=0.9):
    """CRITICAL slash - slash + metallic ring."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # slash component
        noise = 2 * _random.random() - 1
        freq = 1000 * math.exp(-t * 25) + 300
        slash = noise * 0.4 + math.sin(2 * math.pi * freq * t) * 0.3
        # ring component
        ring = (math.sin(2 * math.pi * 3000 * t) * 0.2 +
                math.sin(2 * math.pi * 4500 * t) * 0.1)
        val = slash + ring
        env = math.exp(-t * 12)
        if i < 40:
            env *= i / 40.0
        samples.append(val * env * volume)
    return samples


def _gen_perfect_clash(base_freq=1760, duration=0.25, volume=0.9):
    """PERFECT - bright resonant metallic ring at given pitch."""
    n = int(SAMPLE_RATE * duration)
    samples = []
    freqs = [base_freq, base_freq * 1.5, base_freq * 2, base_freq * 2.5, base_freq * 3, base_freq * 3.5]
    for i in range(n):
        t = i / SAMPLE_RATE
        val = 0.0
        for j, f in enumerate(freqs):
            val += math.sin(2 * math.pi * f * t) * (1.0 / (j + 1))
        val /= 3
        env = math.exp(-t * 10)
        if i < 100:
            env *= i / 100.0
        samples.append(val * env * volume)
    return samples


def _ensure_sounds():
    """Pre-generate all custom sound effects."""
    if _sound_cache:
        return

    d = _get_sound_dir()

    # J lane melody notes (Nutcracker March scale: E F# G A B C D E)
    # Using higher octave for metallic feel
    melody_freqs = [1319, 1480, 1568, 1760, 1976, 2093, 2349, 2637]  # E6-E7
    for i, freq in enumerate(melody_freqs):
        path = os.path.join(d, f"parry_j_{i}.wav")
        _write_wav(path, _gen_metallic_clash(base_freq=freq))
        _sound_cache[f"parry_j_{i}"] = path

        path = os.path.join(d, f"perfect_j_{i}.wav")
        _write_wav(path, _gen_perfect_clash(base_freq=freq))
        _sound_cache[f"perfect_j_{i}"] = path

    _j_note_count = len(melody_freqs)
    _sound_cache["_j_note_count"] = str(_j_note_count)

    # F lane parry - bass drum
    path = os.path.join(d, "parry_f.wav")
    _write_wav(path, _gen_bass_drum())
    _sound_cache["parry_f"] = path

    # F lane PERFECT - bass + ring
    path = os.path.join(d, "perfect_f.wav")
    bass = _gen_bass_drum(duration=0.25, volume=1.0)
    clash = _gen_metallic_clash(duration=0.25, volume=0.3)
    combined = [b + c for b, c in zip(bass, clash)]
    # pad if lengths differ
    if len(clash) > len(bass):
        combined.extend(clash[len(bass):])
    _write_wav(path, combined)
    _sound_cache["perfect_f"] = path

    # Attack - slash
    path = os.path.join(d, "attack.wav")
    _write_wav(path, _gen_slash())
    _sound_cache["attack"] = path

    # Critical attack
    path = os.path.join(d, "critical.wav")
    _write_wav(path, _gen_critical_slash())
    _sound_cache["critical"] = path

    # Miss - quiet dull thud
    path = os.path.join(d, "miss.wav")
    n = int(SAMPLE_RATE * 0.08)
    miss_samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        val = math.sin(2 * math.pi * 80 * t) * math.exp(-t * 40) * 0.2
        miss_samples.append(val)
    _write_wav(path, miss_samples)
    _sound_cache["miss"] = path

    # Use system sounds for these
    _sound_cache["kill"] = "/System/Library/Sounds/Glass.aiff"
    _sound_cache["death"] = "/System/Library/Sounds/Sosumi.aiff"
    _sound_cache["start"] = "/System/Library/Sounds/Blow.aiff"
    _sound_cache["zanki"] = "/System/Library/Sounds/Purr.aiff"


def play(name):
    """Play a named sound effect asynchronously."""
    _ensure_sounds()
    path = _sound_cache.get(name)
    if path and os.path.exists(path):
        try:
            subprocess.Popen(
                ["afplay", path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except Exception:
            pass


def cleanup():
    """Remove temporary sound files."""
    import shutil
    if _sound_dir and os.path.exists(_sound_dir):
        shutil.rmtree(_sound_dir, ignore_errors=True)
