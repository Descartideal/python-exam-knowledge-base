"""广播、视图、分组筛选、统计与文件；结果保存在独立练习目录。"""
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parents[1]/'13-运行结果'/'进阶练习'
OUT.mkdir(parents=True,exist_ok=True)
a=np.array([[10,20,30],[40,50,60]],dtype=float)
print('列加权：',a+np.array([100,200,300]))
print('行偏移：',a+np.array([[10],[20]]))
print('每行去均值：',a-a.mean(axis=1,keepdims=True))
print('行均分>=40：',a[a.mean(axis=1)>=40])
view=a[:,0];view[0]=99
print('视图修改后的原数组：',a)
isolated=a.copy();isolated[0,0]=-1
print('独立副本：',isolated)
print('中位数/四分位：',np.median(a),np.percentile(a,25))
np.save(OUT/'array.npy',a)
assert np.allclose(np.load(OUT/'array.npy',allow_pickle=False),a)
print('读回数组与原数组一致；结果：',OUT)
