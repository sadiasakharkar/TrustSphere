"""Feature engineering for deepfake voice detection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.fftpack import dct
from scipy.io import wavfile
from scipy.signal import spectrogram


@dataclass(slots=True)
class VoiceFeatureArtifacts:
    dataframe: pd.DataFrame
    feature_columns: list[str]


class DeepfakeVoiceFeatureEngineer:
    """Extract MFCC-like, spectrogram, and pitch variance features."""

    def build_dataset(self, rows: list[dict[str, Any]] | None = None) -> pd.DataFrame:
        if rows:
            frame = pd.DataFrame(rows)
        else:
            frame = self._mock_dataset()
        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if "label" not in frame.columns:
            raise ValueError("Voice dataset requires a label column.")
        if "waveform" not in frame.columns and "audio_path" not in frame.columns:
            raise ValueError("Voice dataset requires waveform samples or audio_path.")
        frame["label"] = pd.to_numeric(frame["label"], errors="coerce").fillna(0).astype(int)
        frame["sample_rate"] = pd.to_numeric(frame.get("sample_rate", 16000), errors="coerce").fillna(16000).astype(int)
        return frame

    def build_features(self, frame: pd.DataFrame) -> VoiceFeatureArtifacts:
        dataset = frame.copy()
        features = []
        for row in dataset.itertuples(index=False):
            waveform, sample_rate = self._load_waveform(row)
            feature_row = self._extract_features(waveform, sample_rate)
            features.append(feature_row)
        feature_frame = pd.DataFrame(features)
        dataset = pd.concat([dataset.reset_index(drop=True), feature_frame.reset_index(drop=True)], axis=1)
        feature_columns = feature_frame.columns.tolist()
        return VoiceFeatureArtifacts(dataframe=dataset, feature_columns=feature_columns)

    def _load_waveform(self, row) -> tuple[np.ndarray, int]:
        sample_rate = int(getattr(row, "sample_rate", 16000))
        waveform = getattr(row, "waveform", None)
        if waveform is None and hasattr(row, "audio_path") and getattr(row, "audio_path"):
            sample_rate, loaded = wavfile.read(getattr(row, "audio_path"))
            waveform = loaded
        waveform = np.asarray(waveform, dtype=float).flatten()
        if waveform.size == 0:
            waveform = np.zeros(sample_rate, dtype=float)
        if waveform.dtype.kind in {"i", "u"}:
            waveform = waveform / max(np.abs(waveform).max(), 1)
        return waveform.astype(float), sample_rate

    def _extract_features(self, waveform: np.ndarray, sample_rate: int) -> dict[str, float]:
        waveform = self._normalize_waveform(waveform)
        mfcc = self._mfcc(waveform, sample_rate, num_ceps=13)
        freqs, times, spec = spectrogram(waveform, fs=sample_rate, nperseg=min(256, len(waveform)), noverlap=min(128, max(0, len(waveform) // 4)))
        pitch = self._pitch_track(waveform, sample_rate)
        features = {
            **{f"mfcc_mean_{index}": float(mfcc[:, index].mean()) for index in range(mfcc.shape[1])},
            **{f"mfcc_std_{index}": float(mfcc[:, index].std()) for index in range(mfcc.shape[1])},
            "spectrogram_mean": float(spec.mean()) if spec.size else 0.0,
            "spectrogram_std": float(spec.std()) if spec.size else 0.0,
            "spectrogram_max": float(spec.max()) if spec.size else 0.0,
            "pitch_mean": float(pitch.mean()) if pitch.size else 0.0,
            "pitch_variance": float(pitch.var()) if pitch.size else 0.0,
            "energy_mean": float(np.mean(waveform**2)),
            "zero_crossing_rate": float(np.mean(np.abs(np.diff(np.sign(waveform))) > 0)),
        }
        return features

    def _normalize_waveform(self, waveform: np.ndarray) -> np.ndarray:
        max_val = np.max(np.abs(waveform)) if waveform.size else 0.0
        if max_val == 0:
            return waveform.astype(float)
        return waveform.astype(float) / max_val

    def _mfcc(self, waveform: np.ndarray, sample_rate: int, num_ceps: int = 13) -> np.ndarray:
        frame_size = int(0.025 * sample_rate)
        frame_step = int(0.010 * sample_rate)
        if frame_size <= 0 or frame_step <= 0:
            return np.zeros((1, num_ceps))
        emphasized = np.append(waveform[0], waveform[1:] - 0.97 * waveform[:-1])
        signal_length = len(emphasized)
        num_frames = max(1, int(np.ceil(abs(signal_length - frame_size) / frame_step)) + 1)
        pad_signal_length = num_frames * frame_step + frame_size
        z = np.zeros((pad_signal_length - signal_length))
        pad_signal = np.append(emphasized, z)
        indices = np.tile(np.arange(0, frame_size), (num_frames, 1)) + np.tile(np.arange(0, num_frames * frame_step, frame_step), (frame_size, 1)).T
        frames = pad_signal[indices.astype(np.int32, copy=False)]
        frames *= np.hamming(frame_size)
        magnitude = np.absolute(np.fft.rfft(frames, 512))
        power = ((1.0 / 512) * (magnitude**2))
        mel_filters = self._mel_filterbank(sample_rate, 512, 26)
        filter_banks = np.dot(power, mel_filters.T)
        filter_banks = np.where(filter_banks == 0, np.finfo(float).eps, filter_banks)
        log_fb = np.log(filter_banks)
        mfcc = dct(log_fb, type=2, axis=1, norm="ortho")[:, :num_ceps]
        return mfcc

    def _mel_filterbank(self, sample_rate: int, nfft: int, nfilt: int) -> np.ndarray:
        low_mel = 0
        high_mel = 2595 * np.log10(1 + (sample_rate / 2) / 700)
        mel_points = np.linspace(low_mel, high_mel, nfilt + 2)
        hz_points = 700 * (10 ** (mel_points / 2595) - 1)
        bins = np.floor((nfft + 1) * hz_points / sample_rate).astype(int)
        filters = np.zeros((nfilt, int(np.floor(nfft / 2 + 1))))
        for filt in range(1, nfilt + 1):
            left, center, right = bins[filt - 1], bins[filt], bins[filt + 1]
            if center == left:
                center += 1
            if right == center:
                right += 1
            for k in range(left, center):
                filters[filt - 1, k] = (k - bins[filt - 1]) / (bins[filt] - bins[filt - 1])
            for k in range(center, right):
                filters[filt - 1, k] = (bins[filt + 1] - k) / (bins[filt + 1] - bins[filt])
        return filters

    def _pitch_track(self, waveform: np.ndarray, sample_rate: int) -> np.ndarray:
        frame_length = int(0.03 * sample_rate)
        hop = int(0.01 * sample_rate)
        if frame_length <= 0 or hop <= 0 or len(waveform) < frame_length:
            return np.zeros(1)
        pitches = []
        for start in range(0, len(waveform) - frame_length + 1, hop):
            frame = waveform[start:start + frame_length]
            corr = np.correlate(frame, frame, mode="full")[len(frame) - 1:]
            corr[0] = 0
            peak = np.argmax(corr[: max(2, min(len(corr), sample_rate // 50))])
            if peak > 0:
                pitches.append(sample_rate / peak)
        return np.array(pitches if pitches else [0.0], dtype=float)

    def _mock_dataset(self) -> pd.DataFrame:
        sample_rate = 16000
        t = np.linspace(0, 1.0, sample_rate, endpoint=False)
        bonafide = 0.5 * np.sin(2 * np.pi * 220 * t) + 0.1 * np.sin(2 * np.pi * 440 * t)
        spoof = 0.5 * np.sign(np.sin(2 * np.pi * 220 * t)) + 0.05 * np.random.RandomState(42).normal(size=sample_rate)
        rows = [
            {"waveform": bonafide, "sample_rate": sample_rate, "label": 0},
            {"waveform": spoof, "sample_rate": sample_rate, "label": 1},
            {"waveform": 0.45 * np.sin(2 * np.pi * 180 * t), "sample_rate": sample_rate, "label": 0},
            {"waveform": 0.6 * np.sign(np.sin(2 * np.pi * 260 * t)) + 0.03 * np.random.RandomState(7).normal(size=sample_rate), "sample_rate": sample_rate, "label": 1},
            {"waveform": 0.55 * np.sin(2 * np.pi * 250 * t) + 0.08 * np.sin(2 * np.pi * 500 * t), "sample_rate": sample_rate, "label": 0},
            {"waveform": 0.52 * np.sign(np.sin(2 * np.pi * 190 * t)) + 0.04 * np.random.RandomState(9).normal(size=sample_rate), "sample_rate": sample_rate, "label": 1},
        ]
        return pd.DataFrame(rows)
