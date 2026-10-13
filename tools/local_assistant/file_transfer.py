"""单段下载范围；不把大型生成结果整体读入内存。"""
import re

def download_span(header,size):
    if not header:
        return 0,size-1,200
    match=re.fullmatch(r'bytes=(\d*)-(\d*)',header.strip())
    if not match or not any(match.groups()) or size==0:
        raise ValueError('下载范围无效')
    start,end=match.groups()
    if not start:
        suffix=int(end)
        if suffix<=0:
            raise ValueError('下载范围无效')
        return max(0,size-suffix),size-1,206
    start=int(start)
    end=min(size-1,int(end)) if end else size-1
    if start>=size or start>end:
        raise ValueError('下载范围超出文件')
    return start,end,206
