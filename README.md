# NeuroSymbolic Math Solver

Math solver with a structured pipeline for parsing, symbolic computation, verification, and explanation.

## Overview

The project handles natural-language math questions by converting them to structured data, routing to the right engine, and returning a verified result.

## Workflow

1. Parse user input into a structured problem object.
2. Route the problem to symbolic or numerical engines.
3. Verify the result with operation-specific checks.
4. Generate a readable explanation for the user.

## Features

- Solve algebraic equations
- Differentiate and integrate expressions
- Evaluate limits and series
- Factor and expand expressions
- Plot functions
- Verify identities (including Z3-backed checks)
- Provide step-by-step explanations
