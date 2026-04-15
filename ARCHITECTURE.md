# Architecture Notes

This repository is organized around a small shared core plus task-specific entry points.

## Shared Core

- `astra_config.py`
  Loads `.env`, resolves dataset and cache paths, and centralizes provider-specific API settings.
- `model_clients.py`
  Wraps OpenAI-compatible APIs and local generation servers in a shared interface.

## Main Pipeline

- `table2tree.py`
  Table-to-tree conversion logic.
- `treeqa.py`
  Tree-path retrieval, answer generation, and symbolic reasoning.
- `tableqa.py`
  End-to-end batch pipeline and dataset loading.

## Supporting Modules

- `evaluate.py`
  Evaluates prediction files.
- `quality_evaluate/`
  Measures tree quality.
- `Batch_evaluate/`
  Runs repeated generation for stability analysis.
- `baseline/`
  Direct and tree-direct baselines.
- `demo/`
  Interactive FastAPI + React application.

## Release-Focused Simplifications

- Local paths now resolve through environment variables instead of hardcoded author machine paths.
- Shared model logic moved to `model_clients.py` to reduce duplicated provider logic.
- Shared dataset and embedding configuration moved to `astra_config.py`.
- README and module docs now point to the current repository structure instead of removed files.
