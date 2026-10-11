# turtle API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- forward / backward：前进 后退 移动 fd bk

- left / right / setheading：转向 旋转 方向 正多边形

- penup / pendown / goto：抬笔 落笔 坐标 定位 pu pd

- color / pensize / speed：颜色 线宽 速度

- begin_fill / end_fill：填充 封闭图形

- circle / dot / done：圆 圆点 窗口 保持

## forward / backward

关键词：前进 后退 移动 fd bk

用途：前进；常用调用见下方例子。

关键参数：distance：距离；负数反向

返回值：None；改变位置

```python
import turtle
t = turtle.Turtle()
t.forward(80)
t.backward(20)
turtle.done()
```

常见错误：角度与距离是不同单位。

## left / right / setheading

关键词：转向 旋转 方向 正多边形

用途：转向；常用调用见下方例子。

关键参数：angle：角度；setheading 为绝对朝向

返回值：None；改变方向

```python
import turtle
t = turtle.Turtle()
t.left(90)
t.forward(50)
t.setheading(0)
turtle.done()
```

常见错误：left/right 为相对旋转；标准模式 0 度向右，90 度向上。

## penup / pendown / goto

关键词：抬笔 落笔 坐标 定位 pu pd

用途：抬笔；常用调用见下方例子。

关键参数：goto(x, y)：目标坐标

返回值：None

```python
import turtle
t = turtle.Turtle()
t.penup()
t.goto(-100, 0)
t.pendown()
t.goto(100, 0)
turtle.done()
```

常见错误：移动时若未抬笔，会留下连线。

## color / pensize / speed

关键词：颜色 线宽 速度

用途：颜色；常用调用见下方例子。

关键参数：color(线色, 填充色)；pensize(width)；speed(0) 最快

返回值：设置调用通常返回 None

```python
import turtle
t = turtle.Turtle()
t.color("navy", "gold")
t.pensize(3)
t.speed(0)
t.forward(100)
turtle.done()
```

常见错误：默认颜色值可用英文名称；RGB 数值需与 colormode 一致。

## begin_fill / end_fill

关键词：填充 封闭图形

用途：填充；常用调用见下方例子。

关键参数：成对使用，绘图放在中间

返回值：None

```python
import turtle
t = turtle.Turtle()
t.fillcolor("orange")
t.begin_fill()
for _ in range(4):
    t.forward(60)
    t.left(90)
t.end_fill()
turtle.done()
```

常见错误：遗漏 end_fill 就不会完成填充。

## circle / dot / done

关键词：圆 圆点 窗口 保持

用途：圆；常用调用见下方例子。

关键参数：circle(radius, extent=360)；dot(size, color)

返回值：None

```python
import turtle
t = turtle.Turtle()
t.circle(50)
t.dot(10, "red")
turtle.done()
```

常见错误：circle 的圆心不在当前画笔点；done 进入窗口事件循环。

## 来源与版本

[本地资料：官方参考](../14-来源资料/官方资料/turtle-manual.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
