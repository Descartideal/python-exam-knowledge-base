"""综合练习参考答案；复用相应章节的核心代码。"""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    runpy.run_path(str(ROOT / "07-wordcloud/中文词云.py"), run_name="__main__")
