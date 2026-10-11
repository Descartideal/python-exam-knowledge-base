from pathlib import Path
import numpy as np
from wordcloud import WordCloud
OUT=Path(__file__).resolve().parents[1]/'13-运行结果'/'进阶练习'
OUT.mkdir(parents=True,exist_ok=True)
y,x=np.ogrid[:300,:300]
inside=(x-150)**2+(y-150)**2<=130**2
mask=np.where(inside,0,255).astype(np.uint8)
wc=WordCloud(mask=mask,background_color=None,mode='RGBA',random_state=42,colormap='viridis',max_words=30)
wc.generate_from_frequencies({'Python':8,'data':5,'learning':3,'plot':2,'array':2})
wc.to_file(str(OUT/'circle-cloud.png'))
print('透明圆形词云：',OUT/'circle-cloud.png')
