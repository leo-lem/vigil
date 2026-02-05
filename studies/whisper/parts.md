# Segmentation Robustness

Transcription behaviour is invariant under different audio segmentation granularities and overlaps.

## Setup

- Two audio inputs:
  - clean, read speech
  - conversational meeting speech
- Three slice types per input:
  - baseline: full audio, no segmentation
  - variant 1: moderate chunk size with overlap
  - variant 2: short chunk size with overlap

## Observed behaviour

The hypothesis is **not supported**.

- Moderate segmentation preserves transcript fidelity for clean speech
- Aggressive segmentation introduces boundary-related errors
- Conversational speech exhibits substantially higher instability
- Errors concentrate at chunk boundaries where words are split
- Increased overlap reduces but does not eliminate errors

## Checks

- `WerIsUnder`: **fail**
  - WER exceeds threshold for short chunk segmentation
- `Summary`: highlights boundary-induced duplication and deletion

## Conclusion

Audio segmentation parameters are behaviourally relevant. Transcription stability degrades non-linearly as temporal fragmentation increases.
