# compare_unsupervised_models.py
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, roc_curve

TRAIN_PATH = "../data/xlsx/Train-preprocessed.xlsx"

TEST_FILES = {
    "Level 1": "../data/xlsx/Test-L1-preprocessed.xlsx",
    "Level 2": "../data/xlsx/Test-L2-preprocessed.xlsx",
    "Level 3": "../data/xlsx/Test-L3-preprocessed.xlsx",
}

FEATURE_COLS = [
    "wnd_avg_goose_pkt_interval",
    "wnd_avg_goose_data_length",
    "wnd_goose_pkt_num",
    "wnd_goose_pkt_num_of_same_event",
    "wnd_goose_pkt_num_of_previous_event",
    "wnd_goose_pkt_num_of_not_previous_nor_same_event",
    "wnd_goose_num_of_all_events",
    "wnd_goose_pkt_num_of_same_sqNum",
    "wnd_goose_pkt_num_of_greater_than_current_sqNum",
    "wnd_goose_pkt_num_of_same_datSet",
    "wnd_goose_num_of_all_datSet",
]

def load_features(path: str):
    df = pd.read_excel(path)
    missing = [c for c in FEATURE_COLS + ["label"] if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns: {missing}")

    X = df[FEATURE_COLS].to_numpy(dtype=float)
    y = df["label"].astype(int).to_numpy()
    return df, X, y


def tpr_at_target_fpr(y_true, anomaly_score, target_fpr):
    """
    anomaly_score: higher means more anomalous
    """
    fpr, tpr, thresholds = roc_curve(y_true, anomaly_score)

    # Choose highest TPR among operating points with FPR <= target_fpr
    valid = np.where(fpr <= target_fpr)[0]
    if len(valid) == 0:
        return np.nan, np.nan

    idx = valid[np.argmax(tpr[valid])]
    return tpr[idx], thresholds[idx]


def summarize_scores(name, model_name, y_test, anomaly_score):
    auc = roc_auc_score(y_test, anomaly_score)
    ap = average_precision_score(y_test, anomaly_score)

    benign_scores = anomaly_score[y_test == 0]
    attack_scores = anomaly_score[y_test == 1]

    print(f"\n==== {name.upper()} | {model_name} ====")
    print("Benign:", int((y_test == 0).sum()), "| Attack:", int((y_test == 1).sum()))
    print(f"ROC AUC: {auc:.3f}")
    print(f"PR AUC : {ap:.3f}")
    print(f"Mean anomaly score (benign): {benign_scores.mean():.6f}")
    print(f"Mean anomaly score (attack): {attack_scores.mean():.6f}")

    for target in [0.01, 0.05, 0.10]:
        tpr, thr = tpr_at_target_fpr(y_test, anomaly_score, target)
        print(f"TPR at FPR={int(target*100)}%: {tpr:.3f}")

    return {
        "dataset": name,
        "model": model_name,
        "roc_auc": auc,
        "pr_auc": ap,
        "mean_score_benign": benign_scores.mean(),
        "mean_score_attack": attack_scores.mean(),
        "tpr_at_1pct_fpr": tpr_at_target_fpr(y_test, anomaly_score, 0.01)[0],
        "tpr_at_5pct_fpr": tpr_at_target_fpr(y_test, anomaly_score, 0.05)[0],
        "tpr_at_10pct_fpr": tpr_at_target_fpr(y_test, anomaly_score, 0.10)[0],
    }


def plot_score_distribution(name, model_name, y_test, anomaly_score):
    plt.figure(figsize=(8, 5))

    benign_scores = anomaly_score[y_test == 0]
    attack_scores = anomaly_score[y_test == 1]

    plt.hist(benign_scores, bins=60, alpha=0.6, density=True, label="Benign")
    plt.hist(attack_scores, bins=60, alpha=0.6, density=True, label="Attack")

    plt.xlabel("Anomaly score (higher = more anomalous)")
    plt.ylabel("Density")
    plt.title(f"{model_name} score distribution: {name}")
    plt.legend()
    plt.tight_layout()

def plot_tpr_bar_chart(results_df):
    datasets = ["Level 1", "Level 2", "Level 3"]
    models = results_df["model"].unique()

    bar_width = 0.35
    x = np.arange(len(datasets))

    plt.figure(figsize=(3.5, 2.0))
    # fig, ax = plt.subplots(figsize=(3.5, 2.0))
    for i, model in enumerate(models):
        subset = results_df[results_df["model"] == model]
        subset = subset.set_index("dataset").loc[datasets]

        values = subset["tpr_at_5pct_fpr"].values

        bars = plt.bar(
            x + i * bar_width,
            values,
            width=bar_width,
            label=model,
            zorder=3
        )

        # Add dashed reference lines at each bar height
        for v in values:
            plt.axhline(
                y=v,
                linestyle="--",
                linewidth=0.6,
                color="gray",
                alpha=0.4,
                zorder=1
            )

    plt.xticks(x + bar_width / 2, datasets)
    plt.ylabel("TPR at 5% FPR")
    plt.xlabel("Attacker Type")
    plt.ylim(0, 1)

    plt.grid(axis="y", linestyle=":", linewidth=0.5, alpha=0.7)
    plt.legend()

    plt.tight_layout()

    plt.show()

def main():
    # --------------------
    # Load training data
    # --------------------
    train_df, X_train_raw, y_train = load_features(TRAIN_PATH)

    if np.any(y_train != 0):
        raise ValueError(
            f"Training file contains non-benign rows: {(y_train != 0).sum()} attack rows found."
        )

    print("Training rows:", len(X_train_raw))
    print("Training benign rows:", int((y_train == 0).sum()))

    # --------------------
    # Scale for OCSVM
    # --------------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_raw)

    # --------------------
    # Train models
    # --------------------
    if_model = IsolationForest(
        n_estimators=200,
        contamination="auto",
        random_state=42,
        n_jobs=-1,
    )
    if_model.fit(X_train_raw)

    ocsvm_model = OneClassSVM(
        kernel="rbf",
        gamma="scale",
        nu=0.05,
    )
    ocsvm_model.fit(X_train_scaled)

    # --------------------
    # Evaluate
    # --------------------
    rows = []

    for name, path in TEST_FILES.items():
        df_test, X_test_raw, y_test = load_features(path)
        X_test_scaled = scaler.transform(X_test_raw)

        # Isolation Forest
        if_scores = -if_model.decision_function(X_test_raw)
        rows.append(summarize_scores(name, "Isolation Forest", y_test, if_scores))

        # One-Class SVM
        ocsvm_scores = -ocsvm_model.decision_function(X_test_scaled)
        rows.append(summarize_scores(name, "One-Class SVM", y_test, ocsvm_scores))

    # --------------------
    # Save summary
    # --------------------
    results_df = pd.DataFrame(rows)
    results_df = results_df.sort_values(["model", "roc_auc"], ascending=[True, False]).reset_index(drop=True)

    print("\nFinal summary table:")
    print(results_df.to_string(index=False))

    # Create grouped comparison plot
    plot_tpr_bar_chart(results_df)

if __name__ == "__main__":
    main()