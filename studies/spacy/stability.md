# Determinism Under Repeated Execution

This experiment evaluates whether spaCy produces identical outputs under repeated execution when configuration and inputs are held constant.

## Setup

- Inputs: short, controlled English texts
- Model: `en_core_web_trf`
- Variations:
  - baseline execution
  - repeated executions of the same input
- Check:
  - `MatchesBaseline`

## Observed behaviour

All repeated executions matched the baseline output exactly.

No differences were observed across reruns.

## Checks

- `MatchesBaseline`: pass

## Conclusion

spaCy’s transformer-based English model behaves deterministically in this setup. Baseline comparison is therefore meaningful for subsequent relational checks.