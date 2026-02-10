
# Input Sensitivity

This study evaluates whether sentence-level annotation behaviour produced by the **DATS LLM assistant** remains stable under minor, realistic perturbations of the same input text.

## Hypothesis

Sentence-level annotation behaviour remains stable under minor text input perturbations.

## Setup

- System under test: **DATS LLM assistant** (sentence annotation job)
- Task: classify sentences using the codes `Positive`, `Negative`, `Neutral`
- Inputs: 4 short documents (reviews, support-style messages, notes)
- For each input, Vigil generates perturbed variants and compares the produced annotations across the resulting slices.

## Variations

Each input is perturbed independently to create slices:

- `PerturbWhitespace` (collapse, expand)
- `PerturbLinebreaks` (insert, wrap width 60)
- `InjectHeadline` (simple headline templates with separator)
- `InsertJunkCharacters` (invisible and punctuation-like characters)
- `AddTypos` (swap, delete, replace; 4 edits)
- `AddBoilerplate` (3 lines appended from common email-style boilerplate templates)

These perturbations are intended to be realistic for ingestion pipelines, copied text, email forwarding, and “seen on the web” style artefacts.

## Observed Behaviour

The hypothesis is **not supported**.

- Inputs 1, 2, and 3 were stable across all perturbations for the shared sentence set (checks passed).
- Input 0 showed instability under stronger perturbations:
  - Under `InsertJunkCharacters` and `AddTypos`, the overlapping annotated sentence changed label compared to the other variants.
  - Most variants labelled the overlapping sentence as `Neutral`, while the stronger perturbations produced `Negative`.

This indicates that even small-looking text artefacts (invisible characters, minor typos) can shift label decisions for some inputs, despite otherwise stable behaviour.

## Checks

- `AnnotatedSentenceOverlaps`: **fail** (input 0)
  - Union size: 2, intersection size: 1
  - Overlap ratio: 0.5 (below thresholds)
- `LabelsAgree`: **fail** (input 0, intersection scope)
  - Agreement ratio: 0.0
  - Disagreement: `{Neutral}` vs `{Negative}` on the overlapping sentence set
- Inputs 1–3: **pass** for both checks

## Conclusion

For most inputs in this run, the **DATS LLM assistant** behaved consistently under realistic text perturbations. However, one input exhibited a label flip under stronger perturbations (`InsertJunkCharacters`, `AddTypos`), which Vigil surfaced via overlap and label-agreement checks. This suggests robustness can be input-dependent and is worth tracking as a stability property rather than assuming.