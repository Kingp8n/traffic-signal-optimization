# Operations and Cleanup

This repo produces a lot of artifacts. The goal is to keep the source tree
clean without deleting useful model outputs.

## What should stay out of Git

The following are generated during local development and should remain
ignored:

- Python bytecode and caches;
- frontend build output;
- dependency directories;
- temporary web workspace state;
- ad hoc simulation workspaces;
- short-lived validation scratch directories.

The root `.gitignore` already covers the main ones:

- `__pycache__/`
- `.venv/`
- `.pytest_cache/`
- `.ruff_cache/`
- `workspace/`
- `web/frontend/node_modules/`
- `web/frontend/dist/`

## What is intentionally kept

These directories contain model artifacts and evaluation material that are part
of the project history:

- `models/`
- `models_s/`
- `modelsop/`
- `modelsops/`
- `models_robust/`
- `results/evaluation/`

Do not add blanket ignore rules for those directories unless you are sure the
files are disposable.

## Recommended cleanup rule

When you generate new outputs, keep them in one of these places:

- `workspace/` for Traffic Studio runtime files;
- a dated scratch directory under `/tmp` for one-off experiments;
- the existing model/result directories if the files are meant to be kept.

That lets you distinguish:

- source changes that should be committed;
- tracked research artifacts that should be reviewed before commit;
- temporary work that should be ignored.

## Practical Git hygiene

Before committing, check:

```bash
git status --short
```

If a file is a generated artifact and should never be versioned, either:

- move it into an ignored workspace directory; or
- add a narrow ignore rule that matches the generated pattern.

Avoid broad ignore rules that hide source files or useful data.
