# Noise Robustness

Transcription behaviour is invariant under controlled additive noise perturbations.

## Setup

- Baseline: original audio
- Variants:
  - moderate additive white noise
  - strong additive white noise
- Noise perturbations use fixed random seeds for determinism

## Observed behaviour

The hypothesis is **not supported**.

- Moderate noise produces limited behavioural change
- Strong noise causes abrupt regime shifts rather than gradual degradation
- Transcripts exhibit:
  - large word dropouts
  - spurious insertions
  - rephrasing
- Conversational and accented speech are more sensitive than read speech

## Checks

- `RefWerIsUnder`: **fail**
  - strong noise exceeds acceptable WER
- `Summary`: confirms sharp transition in behaviour

## Conclusion

Whisper transcription behaviour is not invariant under signal-level noise perturbations. Behaviour changes abruptly once a noise threshold is crossed, indicating non-linear robustness characteristics.