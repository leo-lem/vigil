# Case Study: DATS LLM Assistant API

This case study applies Vigil to the DATS LLM Assistant API to examine whether annotation behaviour remains stable under controlled changes to language routing and prompt wording. The system is treated as a black box and evaluated at the pipeline level, observing only the structured job outputs returned by DATS rather than semantic correctness of individual annotations.

## System under evaluation

The DATS LLM Assistant is accessed as an asynchronous job:
- a job is submitted via the public API
- the job is polled until it reaches a terminal status
- the returned job payload (status metadata plus task-specific results) is the observable behaviour surface

This is pipeline-level verification: we do not claim anything about semantic correctness, only about stability and change in the observed contract.

## Backend

`DatsLlm` (`dats_llm_backend.py`) wraps the DATS API as a Vigil backend.

- **Inputs**
  - `data.text` (required): the document text
  - `data.language` (optional): `en` or `de` (defaults to `en`)
  - For each input, the backend ensures a corresponding DATS source document exists and uses its `sdoc_id`.

- **Function configuration (base defaults)**
  - `llm_job_type`: `SENTENCE_ANNOTATION` | `TAGGING` | `METADATA_EXTRACTION`
  - `llm_approach_type`: `LLM_ZERO_SHOT` | `LLM_FEW_SHOT`
  - Task parameters:
    - `codes` for sentence annotation
    - `tags` for tagging
    - `metadata_keys` for metadata extraction
  - Prompt templates:
    - if no prompts are provided and the approach is zero-shot, prompts are fetched via `create_prompt_templates`
    - few-shot prompt generation is not implemented

- **Environment configuration**
  - `project_name`: target DATS project
  - `recreate_project`: whether to recreate the project
  - `project_id` is derived and stored after project resolution

The backend also normalises outputs for comparison by removing volatile fields and enriching annotations with `code_name`.

## Custom checks

This study defines LLM-specific checks in `studies/llm/checks/`:

- `AnnotationCountsEqual`
  - compares the number of suggested annotations across slices

- `CoverageIsStable`
  - compares which sentence ids are covered by annotations across slices

- `LabelsAgree`
  - compares assigned labels per sentence id across slices
  - reports per-sentence differences when labels diverge