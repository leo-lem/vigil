# Prompt Phrasing Sensitivity

Annotation behaviour changes under instruction-level prompt perturbations, even when coverage remains stable.

## Setup

- One document with mixed sentiment signals (English and German segments)
- Two prompt variants (function variation):
  - variant 1: stricter wording (“classify only sentences that clearly express sentiment”)
  - variant 2: permissive wording (“assign a category whenever it could plausibly apply”)

## Observed Behaviour

The hypothesis is **not supported** as stated (“behaviour remains stable”).  
Instead, the run shows **label-set drift under prompt variation** while coverage remains stable.

- Coverage remained stable across variants:
  - both variants annotated the same sentence ids (2 total)
- Label assignments changed under permissive wording:
  - one sentence received an expanded label set (`{Negative, Positive}`) under the permissive prompt
  - the stricter prompt assigned only `{Positive}` for that sentence
- The permissive variant also produced additional / duplicated annotation entries for the same sentence id, which collapses to a larger label set at the check level.

## Checks

- `CoverageIsStable`: **pass**
- `LabelsAgree`: **fail**
  - 1 / 2 sentences disagree (agreement ratio 0.5)
  - disagreement driven by multi-label expansion under permissive wording
- `Summary`: includes the exact prompt variants and raw suggested annotations

## Conclusion

Instruction-level prompt phrasing can change annotation behaviour even when sentence coverage is unchanged. In this run, permissive wording increased label ambiguity (multi-label assignments) rather than expanding coverage.