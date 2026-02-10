# Determinism Under Repeated Execution

This experiment evaluates whether spaCy produces identical outputs under repeated execution when configuration and inputs are held constant.

## Setup

- Inputs: short, controlled English texts
- System: spaCy NER pipeline
- Model: `en_core_web_trf`
- Variations:
  - baseline execution
  - 49 repeated executions of the same inputs (no variation)
- Checks:
  - `MatchesBaseline`
  - `EntityTypesAgree` (sanity check on entity label sets)

## Observed Behaviour

The hypothesis is **supported**.

- All repeated executions matched the baseline output exactly.
- No differences were observed across reruns for any input.

## Checks

- `MatchesBaseline`: **pass**
- `EntityTypesAgree`: **pass**

## Conclusion

spaCy’s transformer-based English model behaved deterministically in this setup. Baseline comparison is therefore meaningful for subsequent relational checks.