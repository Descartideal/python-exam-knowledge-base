# opencv API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- imread / imwrite / imdecode：读图 保存图像 中文路径

- cvtColor：灰度化 颜色空间 BGR RGB

- resize / 图像切片：缩放 裁剪 宽高 行列

- threshold：二值化 阈值 黑白

- GaussianBlur / Canny：模糊 去噪 边缘检测

- rectangle / circle / putText：画框 画圆 写字 标注

- imshow / waitKey / destroyAllWindows：窗口 显示 等待按键 关闭

## imread / imwrite / imdecode

关键词：读图 保存图像 中文路径

用途：读图；常用调用见下方例子。

关键参数：imread(path,flags)；imdecode(buffer,flags)

返回值：ndarray 或 None；imwrite 返回 bool

```python
import cv2
import numpy as np
from pathlib import Path
import numpy as np
p = Path(__file__).resolve().parents[1] / "10-测试数据" / "test.png"
img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
if img is None:
    raise ValueError("图片解码失败")
print(img.shape)
ok, buf = cv2.imencode(".png", img)
if not ok:
    raise ValueError("编码失败")
buf.tofile("copy.png")
```

常见错误：imread 失败返回 None；部分 Windows 环境中文路径用 fromfile/imdecode 更稳妥。

## cvtColor

关键词：灰度化 颜色空间 BGR RGB

用途：灰度化；常用调用见下方例子。

关键参数：code：COLOR_BGR2GRAY / COLOR_BGR2RGB

返回值：ndarray；灰度为二维

```python
import cv2
import numpy as np
img = np.zeros((40, 60, 3), dtype=np.uint8)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
print(gray.shape, rgb.shape)
```

常见错误：OpenCV 常用 BGR；Matplotlib 彩图常用 RGB。

## resize / 图像切片

关键词：缩放 裁剪 宽高 行列

用途：缩放；常用调用见下方例子。

关键参数：resize(img,(宽,高))；img[y1:y2,x1:x2]

返回值：ndarray

```python
import cv2
import numpy as np
img = np.zeros((80, 120, 3), dtype=np.uint8)
small = cv2.resize(img, (60, 40), interpolation=cv2.INTER_AREA)
crop = img[10:50, 20:70].copy()
print(small.shape, crop.shape)
```

常见错误：shape 是 (高,宽,通道)，resize 参数是 (宽,高)；切片终点不包含。

## threshold

关键词：二值化 阈值 黑白

用途：二值化；常用调用见下方例子。

关键参数：threshold(gray,阈值,最大值,THRESH_BINARY)

返回值：(实际阈值, 二值图)

```python
import cv2
import numpy as np
gray = np.array([[50, 150], [200, 20]], dtype=np.uint8)
ret, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
print(ret, binary)
```

常见错误：返回两个值；OTSU 常与 THRESH_BINARY 组合且先转灰度。

## GaussianBlur / Canny

关键词：模糊 去噪 边缘检测

用途：模糊；常用调用见下方例子。

关键参数：高斯核如 (5,5)，尺寸为正奇数；Canny 两个阈值

返回值：ndarray；Canny 输出单通道边缘图

```python
import cv2
import numpy as np
gray = np.zeros((80, 80), dtype=np.uint8)
gray[20:60, 20:60] = 255
blur = cv2.GaussianBlur(gray, (5, 5), 0)
edges = cv2.Canny(blur, 50, 150)
print(edges.shape, np.count_nonzero(edges))
```

常见错误：核尺寸写偶数可能出错；边缘阈值需要按图像调整。

## rectangle / circle / putText

关键词：画框 画圆 写字 标注

用途：画框；常用调用见下方例子。

关键参数：坐标 (x,y)，颜色 BGR，thickness=-1 填充

返回值：图像；通常原地修改

```python
import cv2
import numpy as np
img = np.zeros((100, 160, 3), dtype=np.uint8)
cv2.rectangle(img, (10, 10), (90, 70), (0, 255, 0), 2)
cv2.circle(img, (120, 50), 20, (0, 0, 255), -1)
cv2.putText(img, "OK", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
```

常见错误：putText 默认 Hershey 字体不支持直接写中文。

## imshow / waitKey / destroyAllWindows

关键词：窗口 显示 等待按键 关闭

用途：窗口；常用调用见下方例子。

关键参数：waitKey(0) 等待按键；正数为毫秒

返回值：imshow/关闭返回 None；waitKey 返回键码

```python
import cv2
import numpy as np
img = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.imshow("demo", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
```

常见错误：需要桌面图形环境；无窗口环境改为保存文件后查看。

## 来源与版本

[本地相关资料：官方参考](../14-来源资料/官方资料/opencv-basic.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
