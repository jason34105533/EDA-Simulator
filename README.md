# EDA-Simulator
Simulator for EDA Scheduling on Hybrid Cloud Problem
eda-simulator/
│
├── simulator/                 # Core scheduling logic
│   ├── __init__.py
│   ├── scheduler.py           # Implements scheduling algorithms
│   ├── resource_manager.py    # Tracks on-prem/cloud resources
│   └── job.py                 # Job class with license, CPU, etc.
│
├── job_submitter/            # Handles loading and submitting jobs
│   ├── __init__.py
│   └── submitter.py           # Reads YAML and submits to simulator
│
├── workflow/                 # Test cases (workflows)
│   ├── example_case.yaml
│   └── ...
│
├── config/                   # (Optional) config files for infra setup
│   └── infra_config.yaml     # CPU count, cloud capacity, license pool
│
├── results/                  # (Optional) logs or output stats
│
└── main.py                   # Entry point
