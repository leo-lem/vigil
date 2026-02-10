# Language Routing Sensitivity

Annotation behaviour changes when the same multilingual document is routed under different language contexts.

## Setup

- One multilingual document containing aligned English and German sentences
- Two slices:
  - baseline: default routing (no explicit language)
  - variant: `language = de`

## Observed Behaviour

The hypothesis is **not supported**.

- The variant (`language = de`) produced an additional annotation compared to baseline.
- The diff indicates an extra sentence-level annotation entry (sentence id 1) labelled `Neutral`.

This suggests language routing can influence which sentences are annotated, even when document content is multilingual and semantically aligned.

## Checks

- `MatchesBaseline`: **fail**
- `Summary`: provides the raw outputs for inspection

## Conclusion

Language routing can affect annotation behaviour for multilingual inputs. In this run, the change manifested as a difference in produced annotations (coverage/decisiveness), rather than a simple label substitution.