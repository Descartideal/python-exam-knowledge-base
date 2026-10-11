from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "成绩分析"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "10-测试数据" / "scores.csv", encoding="utf-8")
    df["成绩"] = pd.to_numeric(df["成绩"], errors="coerce")
    valid = df.dropna(subset=["成绩"]).copy()  # 本题排除缺考，不填 0
    failed = valid.loc[valid["成绩"] < 60].sort_values("成绩")
    summary = valid.groupby("班级")["成绩"].agg(["mean", "max", "count"]).sort_values("mean", ascending=False)
    failed.to_csv(OUT / "failed.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUT / "class_summary.csv", encoding="utf-8-sig")
    values = valid["成绩"].to_numpy(dtype=float)
    stats = {"valid_count": len(valid), "excluded_count": len(df)-len(valid), "mean": float(np.mean(values)), "max": float(np.max(values)), "std": float(np.std(values, ddof=0))}
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    font = Path("C:/Windows/Fonts/msyh.ttc")
    if font.exists():
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(summary.index.astype(str), summary["mean"], color="steelblue")
    ax.set(title="班级平均分", xlabel="班级", ylabel="平均分", ylim=(0, 100))
    for i, value in enumerate(summary["mean"]):
        ax.text(i, value+1, f"{value:.1f}", ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "class_mean.png", dpi=150)
    plt.close(fig)
    print(failed.to_string(index=False)); print(summary); print(stats)
    print("结果保存到", OUT)

if __name__ == "__main__":
    main()
