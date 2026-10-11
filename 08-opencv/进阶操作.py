from pathlib import Path
import numpy as np
import cv2
OUT=Path(__file__).resolve().parents[1]/'13-运行结果'/'进阶练习'
OUT.mkdir(parents=True,exist_ok=True)
binary=np.zeros((120,160),dtype=np.uint8)
cv2.rectangle(binary,(20,20),(70,90),255,-1)
cv2.circle(binary,(115,60),20,255,-1)
binary[5,5]=255
kernel=cv2.getStructuringElement(cv2.MORPH_RECT,(3,3))
opened=cv2.morphologyEx(binary,cv2.MORPH_OPEN,kernel)
contours,_=cv2.findContours(opened,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
canvas=cv2.cvtColor(opened,cv2.COLOR_GRAY2BGR)
large=[c for c in contours if cv2.contourArea(c)>100]
for c in large:
    x,y,w,h=cv2.boundingRect(c)
    cv2.rectangle(canvas,(x,y),(x+w-1,y+h-1),(0,0,255),1)
    print('面积/外接框：',cv2.contourArea(c),(x,y,w,h))
for name,img in [('noisy.png',binary),('opened.png',opened),('contours.png',canvas)]:
    ok,data=cv2.imencode('.png',img)
    if not ok:raise ValueError('编码失败')
    data.tofile(str(OUT/name))
assert len(large)==2
print('有效目标数为 2；结果：',OUT)
