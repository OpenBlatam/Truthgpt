"""
AI B-Roll Generator & Sound FX Synthesizer Module v5.5
======================================================
Leverages NumPy, SciPy, Wave, and yt-dlp to synthesize real audio SFX files (.wav),
generate AI stock B-roll prompts, and mix audio timelines.
"""

from __future__ import annotations

import logging
import os
import random
import sys
import wave
from pathlib import Path
from typing import Dict, Any, List, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore
    except Exception:
        pass

import numpy as np

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

class SynthesisError(Exception):
    """Custom exception raised when audio synthesis or file writing fails."""
    pass


class C:
    """Terminal ANSI Color Codes."""
    H = '\033[95m'; B = '\033[94m'; CY = '\033[96m'; G = '\033[92m'
    Y = '\033[93m'; R = '\033[91m'; E = '\033[0m'; BD = '\033[1m'
    DIM = '\033[2m'; W = '\033[97m'


# ═══════════════════════════════════════════════════════════════════════════
# REAL SOUND SYNTHESIZER
# ═══════════════════════════════════════════════════════════════════════════

class RealSoundSynthesizer:
    """
    Real-time audio synthesizer using standard library wave + numpy.
    Generates real 16-bit PCM WAV audio files for SFX sound effects.
    """

    @staticmethod
    def generate_bass_drop(output_path: str, duration: float = 1.0, sample_rate: int = 44100) -> str:
        """
        Synthesizes a cinematic bass drop sweep (150 Hz -> 35 Hz with exponential decay).

        Args:
            output_path: Destination WAV filepath.
            duration: Duration in seconds.
            sample_rate: Audio sampling frequency in Hz.

        Returns:
            str: Output file path.
        """
        dur = max(0.1, float(duration))
        srate = max(8000, int(sample_rate))
        num_samples = int(dur * srate)
        t = np.linspace(0, dur, num_samples, False)
        freq = 150.0 * np.exp(-3.5 * t) + 35.0
        phase = 2 * np.pi * np.cumsum(freq) / srate
        envelope = np.exp(-2.0 * t)
        signal = np.sin(phase) * envelope * 0.8

        RealSoundSynthesizer._write_wav(output_path, signal, srate)
        return output_path

    @staticmethod
    def generate_whoosh(output_path: str, duration: float = 0.5, sample_rate: int = 44100) -> str:
        """
        Synthesizes a transition whoosh effect (Modulated white noise).

        Args:
            output_path: Destination WAV filepath.
            duration: Duration in seconds.
            sample_rate: Audio sampling frequency in Hz.

        Returns:
            str: Output file path.
        """
        dur = max(0.1, float(duration))
        srate = max(8000, int(sample_rate))
        num_samples = int(dur * srate)
        t = np.linspace(0, dur, num_samples, False)
        noise = np.random.normal(0, 0.5, num_samples)
        envelope = np.sin(np.pi * t / dur) ** 2
        signal = noise * envelope * 0.6

        RealSoundSynthesizer._write_wav(output_path, signal, srate)
        return output_path

    @staticmethod
    def generate_pop(output_path: str, duration: float = 0.15, sample_rate: int = 44100) -> str:
        """
        Synthesizes a short pop effect (800Hz sine burst with fast decay).

        Args:
            output_path: Destination WAV filepath.
            duration: Duration in seconds.
            sample_rate: Audio sampling frequency in Hz.

        Returns:
            str: Output file path.
        """
        dur = max(0.05, float(duration))
        srate = max(8000, int(sample_rate))
        num_samples = int(dur * srate)
        t = np.linspace(0, dur, num_samples, False)
        freq = 800.0 * (1.0 - 0.5 * t / dur)
        envelope = np.exp(-25.0 * t)
        signal = np.sin(2 * np.pi * freq * t) * envelope * 0.9

        RealSoundSynthesizer._write_wav(output_path, signal, srate)
        return output_path

    @staticmethod
    def generate_cash_register(output_path: str, duration: float = 0.6, sample_rate: int = 44100) -> str:
        """
        Synthesizes cash register / coin sound effect (High frequency harmonic chord).

        Args:
            output_path: Destination WAV filepath.
            duration: Duration in seconds.
            sample_rate: Audio sampling frequency in Hz.

        Returns:
            str: Output file path.
        """
        dur = max(0.1, float(duration))
        srate = max(8000, int(sample_rate))
        num_samples = int(dur * srate)
        t = np.linspace(0, dur, num_samples, False)
        freq1, freq2 = 2400.0, 3200.0
        envelope = np.exp(-8.0 * t)
        signal = (np.sin(2 * np.pi * freq1 * t) + 0.6 * np.sin(2 * np.pi * freq2 * t)) * envelope * 0.5

        RealSoundSynthesizer._write_wav(output_path, signal, srate)
        return output_path

    @staticmethod
    def _write_wav(filename: str, signal: np.ndarray, sample_rate: int = 44100) -> None:
        """Normalizes and exports signal array to mono 16-bit PCM WAV file.

        Args:
            filename: Target WAV file path.
            signal: Audio signal numpy array.
            sample_rate: Sampling frequency rate in Hz.

        Raises:
            SynthesisError: If file writing or WAV generation fails.
        """
        max_val = float(np.max(np.abs(signal)))
        if max_val > 0:
            signal = signal / max_val
        audio_data = (signal * 32767).astype(np.int16)

        out_path = Path(filename).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with wave.open(str(out_path), 'w') as wav_file:
                wav_file.setnchannels(1)   # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            logger.debug("Successfully generated WAV file: %s", out_path)
        except OSError as e:
            logger.error("Failed to write WAV file to '%s': %s", out_path, e)
            raise SynthesisError(f"Failed to write WAV audio file to '{out_path}': {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# AI BROLL & SOUND ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class AIBRollSoundEngine:
    """
    Visual B-Roll & AI Sound Effects Synthesizer Engine (SFX v5.5).
    Synchronizes visual pattern interrupts with synthesized real .wav audio effects.
    """

    BROLL_CATEGORIES: Dict[str, List[str]] = {
        "finance": ["Chart graph rising quickly", "Stock market numbers digital overlay", "Hands counting money", "High-tech server room"],
        "tech": ["AI neural network 3D nodes", "Developer typing code fast macro shot", "Futuristic robot interface", "Cyberpunk digital city"],
        "marketing": ["Social media notification icons floating", "CTR growth arrow 3D green", "Viral video views counter ticking up"],
        "lifestyle": ["Close up intense focus eye", "Founder looking at sunset skyline", "Mind map whiteboard brainstorming"]
    }

    def __init__(self, sfx_dir: str = "opus_clips_output/sfx_library") -> None:
        """Initializes AIBRollSoundEngine.

        Args:
            sfx_dir: Target directory path for storing synthesized WAV SFX library.
        """
        self.sfx_dir: str = os.path.abspath(sfx_dir or "opus_clips_output/sfx_library")
        os.makedirs(self.sfx_dir, exist_ok=True)
        self.sfx_files: Dict[str, str] = self._synthesize_sfx_library()

    def _synthesize_sfx_library(self) -> Dict[str, str]:
        """Synthesizes complete library of real WAV sound effect files."""
        files: Dict[str, str] = {}
        files["bass"] = RealSoundSynthesizer.generate_bass_drop(os.path.join(self.sfx_dir, "sfx_bass_drop.wav"))
        files["whoosh"] = RealSoundSynthesizer.generate_whoosh(os.path.join(self.sfx_dir, "sfx_whoosh.wav"))
        files["pop"] = RealSoundSynthesizer.generate_pop(os.path.join(self.sfx_dir, "sfx_pop.wav"))
        files["cash"] = RealSoundSynthesizer.generate_cash_register(os.path.join(self.sfx_dir, "sfx_cash.wav"))
        return files

    def enhance_clip(self, clip_meta: Dict[str, Any], topic: str = "marketing") -> Dict[str, Any]:
        """
        Enhances video clip metadata with B-roll insertion points and SFX audio timeline.

        Args:
            clip_meta: Clip metadata dictionary containing transcript and title.
            topic: Domain topic for B-roll theme matching.

        Returns:
            Dict containing inserted B-rolls, SFX timeline, and audio suggestions.
        """
        clip_data = clip_meta if isinstance(clip_meta, dict) else {}
        transcript = clip_data.get("transcript", []) if isinstance(clip_data.get("transcript"), list) else []
        topic_str = str(topic or "marketing").lower()

        brolls: List[Dict[str, Any]] = []
        sfx_timeline: List[Dict[str, Any]] = []

        category_key = "marketing"
        for k in self.BROLL_CATEGORIES.keys():
            if k in topic_str:
                category_key = k
                break

        broll_options = self.BROLL_CATEGORIES[category_key]

        # 1. B-Roll Insertion points
        for idx, t in enumerate(transcript):
            if not isinstance(t, dict):
                continue
            try:
                start_t = float(t.get("start", idx * 5.0))
            except (ValueError, TypeError):
                start_t = idx * 5.0

            if idx % 2 == 1:
                brolls.append({
                    "timestamp_sec": start_t,
                    "timestamp_str": f"{int(start_t // 60):02d}:{int(start_t % 60):02d}",
                    "broll_prompt": random.choice(broll_options),
                    "transition": "Zoom Cut + Blur Flash",
                    "duration_sec": 2.5
                })

        # 2. Real SFX WAV Timeline Placement
        sfx_timeline.append({
            "timestamp_sec": 0.5,
            "sfx_name": "🔊 Deep Bass Drop (Sine Sweep)",
            "wav_file": self.sfx_files.get("bass", ""),
            "reason": "Retención inicial (0-3s)"
        })

        for idx, t in enumerate(transcript):
            if not isinstance(t, dict):
                continue
            try:
                start_t = float(t.get("start", idx * 5.0))
            except (ValueError, TypeError):
                start_t = idx * 5.0

            text = str(t.get("text", ""))
            if any(w in text.lower() for w in ["dinero", "presupuesto", "100k", "ganar", "ctr", "conversión"]):
                sfx_timeline.append({
                    "timestamp_sec": start_t,
                    "sfx_name": "💰 Cash Register Ring",
                    "wav_file": self.sfx_files.get("cash", ""),
                    "reason": f"Palabra clave de ROI: '{text[:25]}...'"
                })
            else:
                sfx_timeline.append({
                    "timestamp_sec": start_t + 1.0,
                    "sfx_name": "⚡ Cinematic Whoosh",
                    "wav_file": self.sfx_files.get("whoosh", ""),
                    "reason": "Cambio de idea / subtítulo"
                })

        return {
            "clip_title": clip_data.get("title", "Clip"),
            "brolls_inserted": brolls,
            "sfx_timeline": sfx_timeline,
            "sfx_library_dir": self.sfx_dir,
            "background_music_suggestion": "Lo-Fi Beats Energéticos (85 BPM) - Nivel audio: -22dB"
        }

    def render_broll_sfx_summary(self, enhanced_data: Dict[str, Any]) -> None:
        """Prints B-roll and SFX enhancement summary to terminal.

        Args:
            enhanced_data: Enhancement metadata dictionary.
        """
        data = enhanced_data if isinstance(enhanced_data, dict) else {}
        print(f"\n{C.H}{C.BD}🎨 MEJORAS DE B-ROLLS & SÍNTESIS DE SONIDOS IA (SFX) APLICADAS:{C.E}")
        print(f"  {C.CY}Librería de Sonidos Sintetizada (.wav):{C.E} {data.get('sfx_library_dir')}")
        print(f"  {C.CY}Música de Fondo Suggestion:{C.E} {data.get('background_music_suggestion')}")
        print(f"\n  {C.BD}🎥 B-Rolls Insertados (Interrupción de Patrón Visual):{C.E}")
        for b in data.get("brolls_inserted", []):
            if isinstance(b, dict):
                print(f"     • [{b.get('timestamp_str', '00:00')}] {C.Y}{b.get('broll_prompt', 'B-Roll')}{C.E} ({b.get('transition', 'Cut')}, {b.get('duration_sec', 2.0)}s)")

        print(f"\n  {C.BD}🔊 Efectos de Sonido Sintetizados (SFX WAV Timeline):{C.E}")
        for s in data.get("sfx_timeline", []):
            if isinstance(s, dict):
                wav_file = s.get('wav_file', '')
                wav_name = os.path.basename(wav_file) if wav_file else "None"
                print(f"     • [{s.get('timestamp_sec', 0.0)}s] {C.G}{s.get('sfx_name', 'SFX')}{C.E} → {C.CY}{wav_name}{C.E} ({C.DIM}{s.get('reason', '')}{C.E})")
        print()
