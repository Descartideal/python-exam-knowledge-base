from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = Path(__file__).resolve().parents[1] / "13-运行结果" / "绘图"
OUT.mkdir(parents=True, exist_ok=True)
scores = [55, 70, 90, 80, 60, 100]
fig, axes = plt.subplots(2, 3, figsize=(12, 7))
axes[0, 0].plot(range(1, 7), scores, marker="o", label="score")
axes[0, 0].set_title("Line"); axes[0, 0].legend(); axes[0, 0].grid(alpha=.3)
axes[0, 1].bar(list("ABCDEF"), scores); axes[0, 1].set_title("Bar")
axes[0, 2].scatter([1, 2, 3, 4, 5, 6], scores); axes[0, 2].set_title("Scatter")
axes[1, 0].hist(scores, bins=[40, 60, 80, 100, 120], edgecolor="black"); axes[1, 0].set_title("Histogram")
axes[1, 1].pie([2, 3, 1], labels=["low", "middle", "high"], autopct="%1.1f%%"); axes[1, 1].set_title("Pie")
axes[1, 2].axis("off")
for ax in axes[0, :]:
    ax.set(xlabel="Student / hours", ylabel="Score")
fig.tight_layout(); fig.savefig(OUT / "five_charts.png", dpi=150); plt.close(fig)
print("结果保存到", OUT)
