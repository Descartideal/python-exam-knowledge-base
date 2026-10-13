(function(root){
  'use strict';
  const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const mathCache=new Map();
  function math(value,display){
    if(root.katex&&value.length<=8000){
      const key=display+':'+value;
      if(mathCache.has(key))return mathCache.get(key);
      try{const html=root.katex.renderToString(value,{displayMode:display,throwOnError:false,trust:false,maxExpand:1000,maxSize:10,strict:'warn'});if(mathCache.size>=128)mathCache.delete(mathCache.keys().next().value);mathCache.set(key,html);return html;}catch{}
    }
    return '<code>'+escape(value)+'</code>';
  }
  function plain(text){
    let out='',last=0;
    const format=s=>escape(s).replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>');
    const pattern=/\[([^\]\n]+)\]\(([^\s)]+)\)/g;
    for(const match of text.matchAll(pattern)){
      out+=format(text.slice(last,match.index));
      const href=match[2];
      out+=/^(?:https?:\/\/|\/(?!\/)|#)/i.test(href)?'<a href="'+escape(href)+'" target="_blank" rel="noopener noreferrer">'+format(match[1])+'</a>':format(match[1]);
      last=match.index+match[0].length;
    }
    return out+format(text.slice(last));
  }
  function inline(text){
    let out='',last=0;
    const pattern=/(`+)([\s\S]*?)\1|\\\(([\s\S]*?)\\\)|\$(?!\$)([^\n$]+)\$/g;
    for(const match of text.matchAll(pattern)){
      out+=plain(text.slice(last,match.index));
      if(match[1])out+='<code>'+escape(match[2])+'</code>';
      else if(match[3]!==undefined)out+=math(match[3],false);
      else out+=/^\d[\d.,]*\s*\w*\s*$/.test(match[4])?plain(match[0]):math(match[4],false);
      last=match.index+match[0].length;
    }
    return out+plain(text.slice(last));
  }
  function cells(row){
    row=row.trim().replace(/^\||\|$/g,'');
    const result=[];let part='',code=false;
    for(let i=0;i<row.length;i++){
      const c=row[i];
      if(c==='\\'&&row[i+1]==='|'){part+='|';i++;}
      else if(c==='`'){code=!code;part+=c;}
      else if(c==='|'&&!code){result.push(part.trim());part='';}
      else part+=c;
    }
    result.push(part.trim());return result;
  }
  function render(value,depth=0){
    if(depth>8)return '<p>'+escape(value)+'</p>';
    const lines=String(value).replace(/\r\n?/g,'\n').split('\n');
    let out='',paragraph=[];
    const flush=()=>{if(paragraph.length){out+='<p>'+inline(paragraph.join('\n'))+'</p>';paragraph=[];}};
    for(let i=0;i<lines.length;){
      const line=lines[i],trim=line.trim();
      if(!trim){flush();i++;continue;}
      const fence=trim.match(/^(`{3,}|~{3,})(.*)$/);
      if(fence){
        flush();const code=[];const marker=fence[1];i++;
        while(i<lines.length&&!lines[i].trim().startsWith(marker)){code.push(lines[i++]);}
        if(i<lines.length)i++;
        out+='<div class="code"><button class="copy">复制</button><pre>'+escape(code.join('\n'))+'</pre></div>';continue;
      }
      if(trim.startsWith('$$')||trim.startsWith('\\[')){
        flush();const open=trim.startsWith('$$')?'$$':'\\[',close=open==='$$'?'$$':'\\]';
        let formula=trim.slice(open.length);i++;
        while(!formula.includes(close)&&i<lines.length)formula+='\n'+lines[i++];
        const end=formula.indexOf(close);
        out+='<div class="math-block">'+math(end<0?formula:formula.slice(0,end),true)+'</div>';
        if(end>=0&&formula.slice(end+close.length).trim())out+='<p>'+inline(formula.slice(end+close.length))+'</p>';
        continue;
      }
      const heading=trim.match(/^(#{1,6})\s+(.+)$/);
      if(heading){flush();const level=Math.min(heading[1].length+1,6);out+='<h'+level+'>'+inline(heading[2])+'</h'+level+'>';i++;continue;}
      if(/^([-*_])(?:\s*\1){2,}$/.test(trim)){flush();out+='<hr>';i++;continue;}
      if(/^\s*>/.test(line)){
        flush();const quote=[];
        while(i<lines.length&&/^\s*>/.test(lines[i]))quote.push(lines[i++].replace(/^\s*> ?/,''));
        out+='<blockquote>'+render(quote.join('\n'),depth+1)+'</blockquote>';continue;
      }
      if(line.includes('|')&&i+1<lines.length&&cells(lines[i+1]).every(c=>/^:?-{3,}:?$/.test(c))){
        flush();const headers=cells(line);out+='<table><thead><tr>'+headers.map(c=>'<th>'+inline(c)+'</th>').join('')+'</tr></thead><tbody>';i+=2;
        while(i<lines.length&&lines[i].trim()&&lines[i].includes('|')){
          const row=cells(lines[i++]);out+='<tr>'+headers.map((_,n)=>'<td>'+inline(row[n]||'')+'</td>').join('')+'</tr>';
        }
        out+='</tbody></table>';continue;
      }
      const item=line.match(/^(\s*)([-+*]|\d+[.)])\s+(.+)$/);
      if(item){
        flush();const ordered=/^\d/.test(item[2]),tag=ordered?'ol':'ul',indent=item[1].length;
        out+='<'+tag+(ordered?' start="'+parseInt(item[2],10)+'"':'')+'>';
        while(i<lines.length){
          const next=lines[i].match(/^(\s*)([-+*]|\d+[.)])\s+(.+)$/);
          if(!next||next[1].length!==indent||/^\d/.test(next[2])!==ordered)break;
          const body=[next[3]];i++;
          while(i<lines.length&&lines[i].trim()&&/^\s+/.test(lines[i])&&lines[i].match(/^\s*/)[0].length>indent)body.push(lines[i++].slice(indent+2));
          out+='<li>'+render(body.join('\n'),depth+1)+'</li>';
        }
        out+='</'+tag+'>';continue;
      }
      paragraph.push(line);i++;
    }
    flush();return out;
  }
  const api={render,inline,escape};
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.KBMarkdown=api;
})(typeof globalThis==='object'?globalThis:this);
