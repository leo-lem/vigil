# Segmentation Robustness

Transcription behaviour is invariant under different audio segmentation granularities given overlap.

## Setup

Two audio inputs:

- `ls_reading.wav`: clean, read speech
- `ami_meeting.wav`: conversational meeting speech

Two segmentation variants were compared (both with `overlap_s = 1.0`, `keep_remainder = true`):

- **Variant A (coarse):** `chunk_s = 15.0`
- **Variant B (fine):** `chunk_s = 5.0`

For each input, one transcript is produced per variant and compared using WER.

## Observed behaviour

The hypothesis is **not supported**.

Both inputs show substantial transcript differences when changing segmentation granularity:

- Read speech (`ls_reading.wav`) is affected, primarily via boundary artifacts (duplication and dropped or repeated phrases) under finer segmentation.
- Meeting speech (`ami_meeting.wav`) is even more sensitive, with noticeably higher instability under finer segmentation, including spurious insertions and duplicated fragments.

## Checks

- `WerIsUnder`: **fail**
  - Threshold: `WER ≤ 0.1`
  - `ls_reading.wav`: max WER = `0.2273` (fail)
  - `ami_meeting.wav`: max WER = `0.2890` (fail)
- `Summary`: confirms boundary-induced artefacts in the finer segmentation output
  - duplicated phrases and partial repetitions in `ls_reading.wav`
  - increased fragmentation and occasional spurious content in `ami_meeting.wav`

## Conclusion

Audio segmentation granularity is behaviourally relevant for SshWhisper under this setup. Changing `chunk_s` from 15s to 5s (with 1s overlap) produces transcript differences exceeding the specified tolerance on both clean and conversational audio.