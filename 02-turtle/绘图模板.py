"""正六边形、五角星；关闭窗口后脚本退出。"""
import turtle
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.penup(); t.goto(-180, 0); t.pendown()
t.color("navy", "gold")
t.begin_fill()
for _ in range(6):
    t.forward(80)
    t.left(60)
t.end_fill()
t.penup(); t.goto(50, 0); t.pendown()
t.color("red")
for _ in range(5):
    t.forward(100)
    t.right(144)
t.hideturtle()
turtle.done()
