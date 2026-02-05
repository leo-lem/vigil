from __future__ import annotations

from atexit import register
from os import path
from shutil import rmtree
from tempfile import mkdtemp
import wave

import numpy as np

from core import InputVariation
from core.__types__ import Input


class TransformAudio(InputVariation):
    def __init__(
        self,
        gain_db: float | None = None,
        snr_db: float | None = None,
        speed_factor: float | None = None,
        seed: int | None = None,
    ):
        self.gain_db = None if gain_db is None else float(gain_db)
        self.snr_db = None if snr_db is None else float(snr_db)
        self.speed_factor = None if speed_factor is None else float(
            speed_factor)
        self.seed = None if seed is None else int(seed)

        if self.speed_factor is not None and self.speed_factor <= 0:
            raise ValueError("speed_factor must be > 0")

        self._tmp = mkdtemp(prefix="vigil_transform_audio_")
        register(lambda: rmtree(self._tmp, ignore_errors=True))
        self._rng = np.random.default_rng(self.seed)

    def vary(self, inputs: list[Input]) -> list[Input]:
        out: list[Input] = []

        for source_index, inp in enumerate(inputs):
            audio_path = inp.get("data")
            if not isinstance(audio_path, str) or not audio_path:
                raise TypeError(
                    "input.data must be a non-empty str (audio path)")

            transformed_path = self._transform_wav(audio_path, source_index)

            meta = dict(inp.get("meta") or {})
            meta.update(
                {
                    "source_data": audio_path,
                    "transform_data": transformed_path,
                    "transform_gain_db": self.gain_db,
                    "transform_snr_db": self.snr_db,
                    "transform_speed_factor": self.speed_factor,
                }
            )

            out.append({**inp, "data": transformed_path, "meta": meta})

        return out

    def _transform_wav(self, input_path: str, source_index: int) -> str:
        stem = path.splitext(path.basename(input_path))[0]
        tag_parts: list[str] = []
        if self.gain_db is not None:
            tag_parts.append(f"g{self.gain_db:g}db")
        if self.snr_db is not None:
            tag_parts.append(f"snr{self.snr_db:g}db")
        if self.speed_factor is not None:
            tag_parts.append(f"spd{self.speed_factor:g}")
        tag = "__".join(tag_parts) if tag_parts else "noop"

        out_path = path.join(
            self._tmp, f"{stem}__xfm__{tag}__{source_index:03d}.wav")

        with wave.open(input_path, "rb") as input_file:
            nchannels = input_file.getnchannels()
            sampwidth = input_file.getsampwidth()
            framerate = input_file.getframerate()
            comptype = input_file.getcomptype()
            compname = input_file.getcompname()

            if comptype != "NONE":
                raise ValueError(f"Unsupported WAV compression: {comptype}")
            if sampwidth != 2:
                raise ValueError(
                    f"Unsupported sampwidth={sampwidth}. Only 16-bit PCM is supported.")

            raw = input_file.readframes(input_file.getnframes())

        audio = np.frombuffer(raw, dtype=np.int16)

        if nchannels > 1:
            if audio.size % nchannels != 0:
                raise ValueError("Invalid PCM length for channel count")
            audio = audio.reshape(-1, nchannels)

        x = audio.astype(np.float32)

        if self.gain_db is not None:
            x *= float(10.0 ** (self.gain_db / 20.0))

        if self.snr_db is not None:
            eps = 1e-12
            sig_power = float(np.mean(x * x))
            if sig_power < eps:
                sig_power = eps
            snr_linear = 10.0 ** (float(self.snr_db) / 10.0)
            noise_power = sig_power / snr_linear
            noise = self._rng.normal(loc=0.0, scale=np.sqrt(
                noise_power), size=x.shape).astype(np.float32)
            x = x + noise

        x = np.clip(x, -32768.0, 32767.0)
        y = x.astype(np.int16)

        y_bytes = y.reshape(-1).tobytes() if nchannels > 1 else y.tobytes()

        out_rate = framerate
        if self.speed_factor is not None:
            out_rate = max(1, int(round(framerate * float(self.speed_factor))))

        with wave.open(out_path, "wb") as out_file:
            out_file.setnchannels(nchannels)
            out_file.setsampwidth(sampwidth)
            out_file.setframerate(out_rate)
            out_file.setcomptype(comptype, compname)
            out_file.writeframes(y_bytes)

        return out_path
