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

Install dependencies:
```
pip install -r requirements.txt
```

Run:
```
python scripts/extract_features.py
python scripts/run_evaluation.py
python scripts/plot_results.py
```

## Dataset

All traces:
- ~1200 seconds duration  
- Identical switching scenario  
- Differ only in attacker behavior, ensuring controlled comparison across scenarios.

## Reference

Paper under review (IEEE ISGT 2026).

Preprint will be added upon publication.
