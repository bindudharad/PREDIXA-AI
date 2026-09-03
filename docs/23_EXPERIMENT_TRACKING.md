# 23_EXPERIMENT_TRACKING.md

Experiment Tracking Document

Every experiment records:
- experiment_id: UUID
- name: Human-readable
- description: What this tests
- dataset_version: Exact dataset hash
- feature_version: Feature set version
- label_version: Label generation version
- model: Algorithm
- hyperparameters: JSON
- training_period: Start/end dates
- validation_period: Start/end dates
- test_period: Start/end dates
- metrics: All evaluation metrics
- backtest_results: Backtest metrics
- model_version: Resulting model version
- status: RUNNING/COMPLETED/FAILED
- created_by: User/system
- created_at: Timestamp
- completed_at: Timestamp
- tags: Searchable tags
- git_commit: Code version
- environment: Conda/pip hash

MLflow Integration:
- Set experiment
- Log params, metrics, artifacts
- Register model

Naming: {model}_{feat}_{label}_{split}_{fold}_{date}

Reproducibility: Fixed seeds, env capture, code version, data version, config version