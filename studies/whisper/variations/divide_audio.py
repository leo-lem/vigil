from __future__ import annotations

from atexit import register
from os import path
from shutil import rmtree
from tempfile import mkdtemp
import wave

from core import InputVariation
from core.__types__ import Input


class DivideAudio(InputVariation):
    def __init__(self, chunk_s: float, overlap_s: float = 0.0, keep_remainder: bool = True):
        if chunk_s <= 0:
            raise ValueError("chunk_s must be > 0")
        if overlap_s < 0:
            raise ValueError("overlap_s must be >= 0")
        if overlap_s >= chunk_s:
            raise ValueError("overlap_s must be < chunk_s")

        self.chunk_s = float(chunk_s)
        self.overlap_s = float(overlap_s)
        self.keep_remainder = bool(keep_remainder)

        self._tmp = mkdtemp(prefix="vigil_segment_audio_")
        register(lambda: rmtree(self._tmp, ignore_errors=True))

    def vary(self, inputs: list[Input]) -> list[Input]:
        out: list[Input] = []

        for inp in inputs:
            audio_path = inp.get("data")
            if not isinstance(audio_path, str) or not audio_path:
                raise TypeError(
                    "input.data must be a non-empty str (audio path)")

            parts = self._divide_wav(audio_path)

            data = {
                "data": audio_path,
                "parts": parts,
                "chunk_s": self.chunk_s,
                "overlap_s": self.overlap_s,
            }

            meta = dict(inp.get("meta") or {})
            meta.update(
                {
                    "source_data": audio_path,
                    "chunk_s": self.chunk_s,
                    "overlap_s": self.overlap_s,
                    "num_parts": len(parts),
                }
            )

            out.append({**inp, "data": data, "meta": meta})

        return out

    def _divide_wav(self, input_path: str) -> list[dict]:
        stem = path.splitext(path.basename(input_path))[0]

        with wave.open(input_path, "rb") as base_file:
            nframes = base_file.getnframes()
            fr = base_file.getframerate()

            chunk_frames = int(round(self.chunk_s * fr))
            overlap_frames = int(round(self.overlap_s * fr))
            step_frames = chunk_frames - overlap_frames

            if chunk_frames <= 0:
                raise ValueError("chunk_s too small for this framerate")

            parts: list[dict] = []
            start = 0
            part_index = 0

            while start < nframes:
                end = start + chunk_frames
                if end > nframes:
                    if not self.keep_remainder:
                        break
                    end = nframes

                base_file.setpos(start)
                frames = base_file.readframes(end - start)

                out_path = path.join(
                    self._tmp, f"{stem}__seg{part_index:03d}.wav")
                with wave.open(out_path, "wb") as out_file:
                    out_file.setnchannels(base_file.getnchannels())
                    out_file.setsampwidth(base_file.getsampwidth())
                    out_file.setframerate(fr)
                    out_file.setcomptype(
                        base_file.getcomptype(), base_file.getcompname())
                    out_file.writeframes(frames)

                parts.append(
                    {
                        "data": out_path,
                        "part_index": part_index,
                        "start_ms": int(round(1000.0 * start / fr)),
                        "end_ms": int(round(1000.0 * end / fr)),
                    }
                )

                part_index += 1
                start += step_frames

                if end >= nframes:
                    break

        return parts
