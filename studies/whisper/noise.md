# Noise Robustness

Transcription behaviour is invariant under controlled additive noise perturbations.

## Setup

- Inputs: three audio clips (read speech, meeting speech, EU speech)
- Variants:
  - additive white noise at SNR 20 dB
  - additive white noise at SNR 10 dB
  - additive white noise at SNR 5 dB
- Noise perturbations use fixed random seeds for determinism
- Evaluation compares transcripts pairwise across the noisy variants (not against a clean baseline).

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

- `WerIsUnder`: **fail**
  - At least one pairwise WER per input exceeds the 0.05 threshold
- `Summary`: illustrates sharp behavioural shifts at lower SNRs

## Conclusion

Whisper transcription behaviour is not invariant under signal-level noise perturbations. Behaviour changes abruptly once a noise threshold is crossed, indicating non-linear robustness characteristics.