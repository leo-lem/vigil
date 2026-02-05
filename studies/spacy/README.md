# Case Study: spaCy English Pipeline

This case study applies Vigil to spaCy’s English NLP pipeline to examine behavioural stability under controlled variation. The system is treated as a black box and evaluated at the pipeline level, observing only the structured annotations returned by spaCy rather than semantic correctness.

## System under evaluation

spaCy is accessed through a local runtime and executed synchronously.

- Inputs are processed as plain text
- Outputs are structured linguistic annotations (tokens, sentences, entities)
- Behaviour is observed exclusively through serialized pipeline outputs

This is pipeline-level behavioural verification. No claims are made about linguistic correctness.

## Backend

`Spacy` (`spacy_backend.py`) wraps a spaCy pipeline as a Vigil backend.

- **Inputs**
  - `data.text` (required): input document text

- **Function configuration**
  - `model`: spaCy English model identifier
    - `en_core_web_sm`
    - `en_core_web_md`
    - `en_core_web_lg`
    - `en_core_web_trf`
  - `disable`: optional list of pipeline components to disable

- **Environment configuration**
  - none (kept for symmetry)

The backend:
- loads the requested model
- applies a fixed pipeline to the input
- serializes tokens, sentences, and entities into a stable JSON format
- does not post-process or reinterpret annotations

## Custom checks

This case study defines spaCy-specific checks in `studies/spacy/checks/`:

- `EntityTypesAgree`
  - compares sets of named entity *types* across slices
  - ignores span boundaries and counts