# Input Sensitivity

This study evaluates whether named entity predictions produced by spaCy remain stable under minor, realistic perturbations of the same input text.

## Hypothesis

Named entity predictions produced by spaCy remain stable under minor text input perturbations.

## Setup

- System under test: spaCy (`en_core_web_sm`)
- Task: named entity recognition (entity *types* as the compared signal)
- Inputs: 4 short documents (reviews, support style messages, notes)
- For each input, Vigil generates perturbed variants and compares the detected entity types across the resulting slices.

## Variations

Each input is perturbed independently to create slices:

- `PerturbWhitespace` (collapse, expand)
- `PerturbLinebreaks` (insert, wrap width 60)
- `InjectHeadline` (headline templates with separator)
- `InsertJunkCharacters` (invisible and punctuation-like characters)
- `AddTypos` (swap, delete, replace; 4 edits)
- `AddBoilerplate` (3 appended lines drawn from common boilerplate templates)

These perturbations model common ingestion artefacts (copy paste noise, email forwarding, “read on the web” footers, and invisible Unicode characters).

## Observed Behaviour

The hypothesis is **not supported**.

- Input 0: stable, no entities detected in any slice.
- Input 2: stable, entity types remained `{DATE, ORG}` across all slices.
- Input 1: unstable under `InsertJunkCharacters`.
  - Most slices produced `{CARDINAL, DATE, PERSON}`.
  - The `InsertJunkCharacters` slice produced `{DATE, PERSON}` (missing `CARDINAL`).
- Input 3: unstable under `InsertJunkCharacters`.
  - Most slices produced no entities (`{}`).
  - The `InsertJunkCharacters` slice produced `{GPE, ORG}`.

Overall, the stability failures were concentrated in the `InsertJunkCharacters` perturbation, suggesting that invisible and non-standard Unicode characters can trigger changes in spaCy’s NER behaviour, even when the surface text appears only minimally altered.

## Checks

- `EntityTypesAgree`: **fail**
  - Fail groups: inputs 1 and 3
  - Pass groups: inputs 0 and 2
- `Summary`: omitted (raw outputs are long and mainly useful for debugging)

## Conclusion

For two of four inputs, spaCy’s predicted entity *types* were consistent under the tested perturbations. However, inserting junk or invisible characters caused entity type sets to change for two inputs, including both entity loss (`CARDINAL`) and spurious entity emergence (`GPE`, `ORG`). This indicates spaCy NER robustness is sensitive to certain Unicode-level artefacts and should be validated explicitly when text may contain such noise.
