# Case Study: DATS Whisper Transcription Service

This case study applies Vigil to the DATS Whisper transcription service to examine whether transcription behaviour remains stable under controlled changes to audio segmentation and signal noise. The system is treated as a black box and evaluated at the pipeline level, observing only structured transcription outputs rather than semantic correctness.

## System under evaluation

The DATS Whisper service is accessed via a remote API exposed through an SSH tunnel:
- raw audio is submitted as a binary payload
- the service performs transcription asynchronously
- the returned payload includes segments, word timing metadata, transcript text, and language information

This is pipeline-level verification. The study evaluates stability and sensitivity of observable transcription behaviour under controlled input variation.

## Backend

`SshWhisper` (`ssh_whisper_backend.py`) wraps the Whisper service as a Vigil backend.

- **Inputs**
  - `data.audio_path` (required): local path to an audio file
  - Each input may be expanded into multiple execution slices when segmentation or noise variations are applied.

- **Function configuration**
  - fixed transcription endpoint (`/whisper/transcribe`)
  - no decoding or model parameters are varied in this study

- **Environment configuration**
  - `host`: Whisper service host
  - `port`: SSH forwarded service port

The backend:
- submits audio to the service
- normalises timestamps to millisecond precision
- aggregates word-level output into a single transcript string
- removes volatile identifiers and execution-specific fields

No linguistic interpretation or correction is performed.

## Custom checks

This study defines Whisper-specific checks in `studies/whisper/checks/`:

- `WerIsUnder`
  - computes pairwise word error rate between slice transcripts
  - asserts WER remains below a fixed threshold

- `RefWerIsUnder`
  - compares each slice transcript against a fixed reference transcript
  - asserts absolute accuracy remains within tolerance

Both checks report observable transcription stability only.
