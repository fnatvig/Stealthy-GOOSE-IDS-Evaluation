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

Packets are labeled using ground-truth information from the simulation.

- `label = 0` → benign traffic  
- `label = 1` → attack traffic  

Injected packets were assigned a different VLAN priority during dataset generation to enable labeling. This field is not included in the feature set and is not available to the IDS.

## Reproducibility

Make sure you have python 3.10.11 installed on your system. To create virtual environment and install dependencies, run:
```
.\setup_venv.bat
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

## Dataset

All traces:
- ~1200 seconds duration  
- Identical switching scenario for all test traces (Test-L1, Test-L2 and Test-L3), while different for Test.   
- Test-L1, Test-L2 and Test-L3 differ only in attacker behavior, ensuring controlled comparison across scenarios.

## Reference

Paper under review (IEEE ISGT 2026).

Preprint will be added upon publication.
