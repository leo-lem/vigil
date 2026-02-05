# Language Routing Sensitivity

Annotation behaviour is invariant when the same multilingual document is routed under different language contexts.

## Setup

- One multilingual document containing aligned English and German sentences
- Two slices:
  - baseline: no language specified
  - variant: `language = de`

## Observed Behaviour

The hypothesis is **not supported**.

- Both slices annotate the same sentence
- The assigned label differs:
  - baseline: `Positive`
  - `language = de`: `Neutral`

Coverage is identical, but label assignment changes under language routing.

## Checks

- `MatchesBaseline`: **fail**
- `DiffBaseline`: shows label substitution for sentence 0
- `Summary`: confirms no other behavioural differences

## Conclusion

Language routing affects annotation behaviour even when document content is multilingual and semantically aligned.