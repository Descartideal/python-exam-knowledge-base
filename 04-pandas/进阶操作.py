from pathlib import Path
import pandas as pd
OUT=Path(__file__).resolve().parents[1]/'13-运行结果'/'进阶练习'
OUT.mkdir(parents=True,exist_ok=True)
scores=pd.DataFrame({'学号':['001','002','003'],'科目':['Python']*3,'成绩':['80','90','缺考']})
students=pd.DataFrame({'学号':['001','002','003'],'班级':['A','A','B']})
df=scores.merge(students,on='学号',how='left',validate='one_to_one',indicator=True)
df['成绩']=pd.to_numeric(df['成绩'],errors='coerce')
valid=df.dropna(subset=['成绩']).copy()
valid['班均分']=valid.groupby('班级')['成绩'].transform('mean')
valid['高出均分']=valid['成绩']-valid['班均分']
wide=valid.pivot_table(index='班级',columns='科目',values='成绩',aggfunc='mean')
valid.to_csv(OUT/'merged.csv',index=False,encoding='utf-8-sig')
wide.to_csv(OUT/'pivot.csv',encoding='utf-8-sig')
print(valid);print(wide)
assert wide.loc['A','Python']==85
assert valid['高出均分'].tolist()==[-5,5]
print('合并、班均分、透视验收通过；结果：',OUT)
