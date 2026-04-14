# Stealthy GOOSE IDS Evaluation

This repository provides datasets and code for:

**"When Flooding Looks Legitimate: Evaluating Intrusion Detection under Stealthy GOOSE Attacks"**
(submitted to IEEE PES ISGT Europe 2026)

## Overview

This work investigates stealthy flooding attacks on IEC 61850 GOOSE communication and their impact on anomaly-based intrusion detection systems (IDSs).

Three attacker models are considered:
- Level 1: Periodic bursts on a single stream  
- Level 2: Distributed traffic across streams  
- Level 3: Traffic aligned with switching events  

## Contents

- PCAP datasets (benign + three attack scenarios)
- Feature extraction and evaluation scripts
- Code for reproducing results

## Labels

Labels are provided in the preprocessed `.xlsx` files.

- `label = 0` → benign traffic  
- `label = 1` → attack traffic  

The raw PCAP files do not contain explicit labels. During dataset generation, injected packets were assigned a different VLAN priority to enable labeling. This information is used internally when generating the labeled datasets, but is not included in the feature set and is not available to the IDS.

## Reproducibility

Requires Python 3.10.11.

To create the virtual environment and install dependencies, run:
```
.\scripts\setup_venv.bat
```

### Results
To reproduce table 3 and figure 4 from the paper, run:
```
python scripts/run_evaluation.py
```

### Figures
To reproduce figure 2 and figure 3 from the paper, run:
```
python scripts/plot_data.py
```
The evaluation scripts use the preprocessed `.xlsx` files directly.
## Dataset

All traces:
- ~1200 seconds duration  
- The training trace (Train) uses a different switching scenario  
- Test-L1, Test-L2, and Test-L3 share the same switching scenario  
- Test-L1, Test-L2, and Test-L3 differ only in attacker behavior, ensuring controlled comparison across scenarios

## Data Processing

The preprocessed `.xlsx` files used for evaluation are generated from the raw PCAP traces in two steps:

1. Convert PCAP to raw tabular format:
```
python scripts/pcap_parser.py data/pcap/Test-L1.pcapng data/xlsx/Test-L1-raw.xlsx
```
2. Extract features:
```
```bash
python scripts/extract_features.py --in data/xlsx/Test-L1-raw.xlsx --out data/xlsx/Test-L1-preprocessed.xlsx
```
The same procedure applies to all traces (Train, Test-L1, Test-L2, Test-L3).

## Related repository

Dataset generation (SASMaker):
https://github.com/fnatvig/SASMaker/tree/isgt-data

## Reference

Paper under review (IEEE ISGT 2026).

Preprint will be added upon publication.


