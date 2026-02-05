# Vigil

[![PyPi](https://img.shields.io/pypi/v/vigil-bv)](https://pypi.org/project/vigil-bv/)
[![CI](https://github.com/leo-lem/vigil/actions/workflows/ci.yml/badge.svg)](https://github.com/leo-lem/vigil/actions/workflows/ci.yml)


Vigil is a small framework for **behavioural verification under controlled variation**.

It executes a system across declared variations, evaluates the resulting behaviour with checks, and records everything in a single structured report.  
Vigil is system-agnostic and focuses on behavioural properties rather than performance benchmarks.

## Running Vigil

Run Vigil on a project directory:

```bash
vigil [project_dir] [--trace]
```

Vigil opens an interactive menu to:
- select a specification
- run all variations and checks
- inspect previous reports

Reports are written next to the specification file.

## Project layout

A project directory contains:
- exactly one backend
- one or more specifications
- optional local checks and variations

```
project/
  llm_backend.py
  language.yml
  prompts.yml
  checks/
    entity_types_agree.py
  variations/
    differ_language.py
```

Files ending in `*.report.yml` are treated as results, not specs.

## Specification

A specification defines **what behaviour is tested**.

At minimum it contains:
- hypothesis
- inputs
- variations
- checks

Optional metadata:
- title

```
title: Behavioural verification of DatsLlm with respect to language
hypothesis: Annotation behaviour remains stable across language routing

inputs:
  - text: "Hello world"

variations:
  - type: update_input_keys
    input:
      language: de

checks:
  - matches_baseline
```

## Backend

A backend wraps the system under evaluation.

It combines:
- **function configuration** (what is executed)
- **environment configuration** (how and where it runs)

Backends implement:

```
update_environment(environment)
compute(input, function) -> output
```

The framework manages execution, isolation, and cleanup automatically.

## Variations

Variations introduce controlled changes.

Each variation targets exactly one domain:
- input
- function
- environment

Variations:
- transform inputs or patch configuration
- are applied explicitly and sequentially
- never inspect outputs

Baseline execution is represented explicitly with `none`.

Vigil also supports a small convenience expansion:

```variations: [{ type: repeat, times: N, do: [...] }]```

This expands into a flat list by repeating the entries in `do` `N` times.

### Syntactic sugar

The specification format provides light syntactic sugar for common patterns. This sugar expands into ordinary variations and does not add new semantics.

Supported forms include:
- repetition of a variation block

These constructs exist purely to reduce duplication in specs. After parsing, the engine operates only on plain variations.

## Checks

Checks evaluate observed behaviour.

Three intents exist:
- unary
- reference
- group

Checks may be:
- assertive (produce PASS / WARN / ERROR)
- diagnostic (INFO only)

Checks operate only on recorded slices and never trigger execution.

## Reports

Each run produces a single structured report containing:
- metadata (title, hypothesis, timestamps)
- backend configuration
- all inputs and variations
- all check results

Reports are YAML by default and meant for inspection, comparison, and archiving.

Vigil is intentionally small, explicit, and extensible.  
New backends, variations, and checks can be added without modifying the core.