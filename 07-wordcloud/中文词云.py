from pathlib import Path
import importlib.util, os
from wordcloud import WordCloud
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kb_segment", ROOT / "06-jieba" / "分词统计.py")
segment = importlib.util.module_from_spec(spec); spec.loader.exec_module(segment)

def main():
    freq = segment.main()
    candidates = [os.environ.get("KB_FONT", ""), "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]
    font = next((Path(p) for p in candidates if p and Path(p).is_file()), None)
    if font is None:
        raise FileNotFoundError("找不到中文字体，请设置环境变量 KB_FONT 为实际中文字体文件路径。")
    wc = WordCloud(font_path=str(font), width=900, height=500, background_color="white", max_words=100, random_state=42, collocations=False)
    wc.generate_from_frequencies(freq).to_file(str(segment.OUT / "wordcloud.png"))
    print("字体:", font); print("词云保存到", segment.OUT / "wordcloud.png")

if __name__ == "__main__":
    main()
