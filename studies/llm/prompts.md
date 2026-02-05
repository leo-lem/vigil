# Prompt Phrasing Sensitivity

Annotation behaviour changes under semantically similar but instruction-level prompt perturbations.

## Setup

- One document with mixed sentiment signals
- Three slices:
  - baseline: server-generated prompts
  - variant 1: stricter wording
  - variant 2: permissive wording

## Observed Behaviour

The hypothesis is **supported** in a structured way.

- Stricter prompts:
  - same coverage and labels as baseline
- Permissive prompts:
  - increased annotation count
  - expanded sentence coverage
  - labels match baseline on overlapping coverage

## Checks

- `AnnotationCountsEqual`: **fail**
- `CoverageIsStable`: **fail**
- `LabelsMatch`: **pass**
- `DiffBaseline`: shows added annotation entries

## Conclusion

Prompt wording primarily affects annotation scope, not label assignment on shared coverage.