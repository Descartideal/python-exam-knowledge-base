from pathlib import Path
from collections import Counter
import csv, json
import jieba
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "文本词云"

def frequencies():
    data = ROOT / "10-测试数据"
    text = (data / "article.txt").read_text(encoding="utf-8")
    stop = set((data / "stopwords.txt").read_text(encoding="utf-8").splitlines())
    jieba.load_userdict(str(data / "userdict.txt"))
    words = [w.strip() for w in jieba.lcut(text) if w.strip() and w.strip() not in stop and any(c.isalnum() for c in w)]
    freq = Counter(words)
    if not freq:
        raise ValueError("过滤后没有有效词语，请检查文本与停用词。")
    return freq

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    freq = frequencies()
    with (OUT / "top10.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f); writer.writerow(["词语", "词频"]); writer.writerows(freq.most_common(10))
    (OUT / "frequencies.json").write_text(json.dumps(dict(freq), ensure_ascii=False, indent=2), encoding="utf-8")
    print(freq.most_common(10)); print("结果保存到", OUT)
    return freq

if __name__ == "__main__":
    main()
