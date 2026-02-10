# Environment Configuration Sensitivity

Sentence-level annotation behaviour changes when project-level code descriptions (environment configuration) are varied while inputs and function remain fixed.

## Setup

- One document with mixed sentiment signals
- Two environment variants (environment variation), executed as separate DATS projects:
  - Env A: neutral code descriptions
  - Env B: biased code descriptions
- Function held constant:
  - `SENTENCE_ANNOTATION`, `LLM_ZERO_SHOT`
  - codes: `Positive`, `Negative`, `Neutral`

The environment variants differ only in the code descriptions used by the project. These descriptions are incorporated into the server-generated prompt templates.

## Observed Behaviour

The hypothesis is **supported**.

- Coverage remained stable across environment variants:
  - both variants annotated the same sentence ids
  - annotated sentence overlap ratio: `1.0`
- Label assignment drift occurred under environment change:
  - one sentence flipped from `{Neutral}` (Env A) to `{Positive}` (Env B)
  - the other annotated sentence remained `{Negative}` in both variants

## Checks

- `AnnotatedSentenceOverlaps`: **pass**
  - overlap ratio `1.0` (union and intersection identical)
- `LabelsAgree` (scope: `intersection`): **fail**
  - 1 / 2 sentences disagree (agreement ratio 0.5)
  - disagreement driven by `{Neutral}` vs `{Positive}` on the same sentence id
- `Summary`: confirms that the generated prompt templates embed the environment-specific code descriptions

## Conclusion

Project-level configuration can induce behavioural drift even when the input and function configuration are unchanged. In this case, changing only code descriptions was sufficient to flip the assigned label for an ambiguous sentence while keeping coverage identical.