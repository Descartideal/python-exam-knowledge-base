from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "图像处理"

def save(name, img):
    ok, encoded = cv2.imencode(".png", img)
    if not ok:
        raise ValueError(f"图像编码失败: {name}")
    encoded.tofile(str(OUT / name))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = ROOT / "10-测试数据" / "test.png"
    if not p.is_file():
        raise FileNotFoundError(p)
    img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"图片解码失败: {p}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(img, (240, 160), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    ret, binary = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(blurred, 50, 150)
    cropped = img[30:160, 40:220].copy()
    for name, output in [("gray.png", gray), ("resized.png", resized), ("blurred.png", blurred), ("binary.png", binary), ("edges.png", edges), ("cropped.png", cropped)]:
        save(name, output)
        print(name, output.shape)
    print("实际阈值:", ret); print("结果保存到", OUT)

if __name__ == "__main__":
    main()
