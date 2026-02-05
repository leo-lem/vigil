# Entity Type Stability Across Model Variants

This experiment evaluates whether named entity *types* remain consistent when swapping spaCy’s English models while keeping the pipeline configuration fixed.

## Setup

- Inputs: short, deliberately ambiguous English texts
- Baseline model: `en_core_web_sm`
- Variant models:
  - `en_core_web_md`
  - `en_core_web_lg`
  - `en_core_web_trf`
- Check:
  - `EntityTypesAgree`

The check compares, per input:
- the set of entity labels produced by each model
- pairwise differences between model outputs

Only entity types are considered. Span boundaries and counts are ignored.

## Observed behaviour

- Two inputs showed full agreement across all models
- One input exhibited model-dependent variation

For the varying input:
- `sm`, `lg`, and `trf` predicted both `DATE` and `PERCENT`
- `md` predicted `PERCENT` only

## Checks

- `EntityTypesAgree`: fail

## Conclusion

Named entity type predictions are mostly stable across spaCy English models but can diverge in ambiguous contexts. Behavioural variance is localized rather than systematic.