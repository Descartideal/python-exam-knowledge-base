// 验证生成文档与检索逻辑；使用简单 DOM 替身，不启动浏览器。
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=path.resolve(__dirname,'..');
const page=fs.readFileSync(path.join(root,'知识库.html'),'utf8');
const payload=page.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const docs=JSON.parse(payload);
assert(docs.length>=65);
for(const d of docs){assert(fs.existsSync(path.join(root,d.path)));}
class Element{
  constructor(){this.children=[];this.value='';this.dataset={};this.classList={toggle(){},remove(){}};this.textContent='';this._html='';}
  appendChild(child){this.children.push(child);return child;}
  set innerHTML(s){this._html=s;if(s.includes('id="hits"'))elements.hits=new Element();}
  get innerHTML(){return this._html;}
  querySelectorAll(){return [];}
  addEventListener(){}
  focus(){}
}
const elements={data:new Element()};elements.data.textContent=payload;
const document={getElementById(id){return elements[id]||(elements[id]=new Element());},createElement(){return new Element();},querySelectorAll(){return [];},addEventListener(){}};
const context=vm.createContext({document,window:{scrollTo(){},print(){}},navigator:{},URL,console});
const source=page.match(/<script>([\s\S]*?)<\/script>/)[1];
vm.runInContext(source,context);
assert(elements.main.innerHTML.includes('Python 考试知识库总索引'));
function search(q,filter=''){
  elements.search.value=q;elements.filter.value=filter;
  vm.runInContext('runSearch()',context);
  return elements.hits.children;
}
assert(search('分组求平均').some(x=>x.innerHTML.includes('pandas')));
assert(search('班级平均分').length>0);
assert(search('灰度化').some(x=>x.innerHTML.includes('opencv')));
assert(search('pandas 缺失值').length>0);
assert(search('pip').some(x=>x.innerHTML.includes('00-环境与入门')));
assert(search('广播').some(x=>x.innerHTML.includes('03-numpy')));
assert(search('轮廓').some(x=>x.innerHTML.includes('08-opencv')));
assert(search('官方资料').some(x=>x.innerHTML.includes('官方资料目录')));
assert(search('NumPy：初学者教程').some(x=>x.innerHTML.includes('numpy-beginner.html')));
assert(search('--no-index').length>0);
assert(search('reshape','03-numpy').length>0);
assert(search('reshpe').some(x=>x.textContent==='试试 reshape'));
assert(search('不存在的关键词xyz').length===0);
const all=search('');assert(all.length===docs.length);
all[0].onclick();assert(elements.main.innerHTML.includes('下载源文件'));
console.log(`通过：${docs.length} 文件完整性、中文检索、多词检索、章节筛选、英文拼写建议、无结果、导航逻辑。`);
