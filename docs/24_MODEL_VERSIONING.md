# 24_MODEL_VERSIONING.md

## Model Versioning

## Version Format

`
model_{algorithm}_v{MAJOR}.{MINOR}.{PATCH}
`

Examples:
- model_xgboost_v1.0.0 - Initial release
- model_xgboost_v1.1.0 - New features added
- model_xgboost_v1.1.1 - Bug fix
- model_xgboost_v2.0.0 - Breaking change (new architecture)

## Tracked Metadata

| Field | Description |
|-------|-------------|
| model_id | Unique identifier |
| algorithm | xgboost, lightgbm, lstm, ensemble |
| version | Semantic version |
| feature_version | feat_v1.3 |
| label_version | label_v2.1 |
| dataset_version | ds_feat_v1.3_label_v2.1_split_expanding_a1b2c3d4 |
| hyperparameters | All hyperparameters |
| metrics | Validation + test metrics |
| trained_date | Timestamp |
| training_period | Data range used |
| validation_period | Holdout range |
| test_period | Test range |
| artifact_path | S3/MinIO path |
| status | candidate/shadow/production/archived |
| promoted_date | When promoted |
| demoted_date | When demoted |
| git_commit | Code version |
| environment_hash | Conda/pip hash |

## Version Lifecycle

`
candidate -> validation -> shadow -> production -> archived
`

## Promotion Rules

1. Candidate must beat production on validation holdout
2. Shadow deployment for 2-4 weeks
3. Must beat production on live outcomes (statistical significance)
4. Human approval required
5. Rollback plan documented

## Storage

Model artifacts stored in MLflow artifact store with versioned paths:
`
s3://predixa-models/model_xgboost_v1.2.0/
  ├── model.pkl
  ├── config.yaml
  ├── metrics.json
  ├── feature_names.json
  └── calibration.pkl
`