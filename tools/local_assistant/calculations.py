"""只读表达式计算：白名单解释 AST，不执行任意 Python 源码。"""
import ast
import json
import math
import operator
import numpy as np
import pandas as pd

LIMIT=4096
BINARY={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,
        ast.Div:operator.truediv,ast.FloorDiv:operator.floordiv,ast.Mod:operator.mod,ast.Pow:operator.pow}

def bounded(value):
    if isinstance(value,(np.ndarray,pd.Series)):
        empty_numeric_series=isinstance(value,pd.Series) and all(x is None for x in value.tolist())
        if value.size>LIMIT or (value.dtype.kind not in 'biuf' and not empty_numeric_series):
            raise ValueError('仅支持最多 4096 个元素的数值数组或 Series')
    elif isinstance(value,(int,float,np.number)):
        if math.isfinite(float(value)) and abs(value)>10**100:
            raise ValueError('数值过大')
    elif isinstance(value,(list,tuple)):
        if len(value)>LIMIT:
            raise ValueError('序列过长')
        for item in value:
            bounded(item)
    elif value is not None:
        raise ValueError('表达式只能产生数值、数值序列或 None')
    return value

def calculate(expression):
    if not isinstance(expression,str) or not expression or len(expression)>8000:
        raise ValueError('表达式为空或超过 8000 字符')
    tree=ast.parse(expression,mode='eval')
    if sum(1 for _ in ast.walk(tree))>512:
        raise ValueError('表达式过于复杂，请拆分计算')
    def visit(node,depth=0):
        if depth>24:
            raise ValueError('表达式嵌套过深')
        child=lambda item:visit(item,depth+1)
        if isinstance(node,ast.Constant) and (node.value is None or isinstance(node.value,(int,float))):
            return bounded(node.value)
        if isinstance(node,(ast.List,ast.Tuple)):
            return bounded([child(x) for x in node.elts])
        if isinstance(node,ast.UnaryOp) and isinstance(node.op,(ast.USub,ast.UAdd)):
            return bounded((-1 if isinstance(node.op,ast.USub) else 1)*child(node.operand))
        if isinstance(node,ast.BinOp) and type(node.op) in BINARY:
            left,right=child(node.left),child(node.right)
            if isinstance(node.op,ast.Pow) and (not isinstance(right,(int,float)) or abs(right)>128):
                raise ValueError('幂指数只能是绝对值不超过 128 的标量')
            if isinstance(node.op,ast.Mult) and isinstance(left,(list,tuple)):
                if not isinstance(right,int) or len(left)*max(0,right)>LIMIT:
                    raise ValueError('序列重复过多')
            if isinstance(node.op,ast.Mult) and isinstance(right,(list,tuple)):
                if not isinstance(left,int) or len(right)*max(0,left)>LIMIT:
                    raise ValueError('序列重复过多')
            if isinstance(left,(np.ndarray,pd.Series)) or isinstance(right,(np.ndarray,pd.Series)):
                if math.prod(np.broadcast_shapes(np.shape(left),np.shape(right)))>LIMIT:
                    raise ValueError('广播后的数组过大')
            return bounded(BINARY[type(node.op)](left,right))
        if isinstance(node,ast.Attribute) and node.attr in {'shape','size','ndim'}:
            value=child(node.value)
            if isinstance(value,(np.ndarray,pd.Series)):
                return bounded(getattr(value,node.attr))
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and not node.keywords:
            name=node.func.attr
            args=[child(x) for x in node.args]
            if isinstance(node.func.value,ast.Name):
                library=node.func.value.id
                if library=='np' and name=='arange':
                    if not 1<=len(args)<=3 or not all(isinstance(x,(int,float)) and math.isfinite(x) for x in args):
                        raise ValueError('arange 仅接受 1～3 个有限数值参数')
                    start,stop,step=(0,args[0],1) if len(args)==1 else (args[0],args[1],args[2] if len(args)==3 else 1)
                    if not step or max(0,math.ceil((stop-start)/step))>LIMIT:
                        raise ValueError('arange 步长为零或数组过大')
                    return bounded(np.arange(*args))
                functions={'np':{'array':np.array,'sum':np.sum,'mean':np.mean,
                                  'reshape':np.reshape,'broadcast_shapes':np.broadcast_shapes},
                           'pd':{'Series':pd.Series}}
                function=functions.get(library,{}).get(name)
                if function is not None:
                    return bounded(function(*args))
            else:
                value=child(node.func.value)
                if isinstance(value,(np.ndarray,pd.Series)) and name in {'sum','mean','count','tolist','reshape'}:
                    if name=='count' and not isinstance(value,pd.Series):
                        raise ValueError('count() 仅支持 pandas Series')
                    return bounded(getattr(value,name)(*args))
        raise ValueError('不支持此语法；仅允许数值表达式和白名单 NumPy / pandas 操作，无文件、网络、赋值或任意函数调用')
    value=visit(tree.body)
    if isinstance(value,(np.ndarray,pd.Series)):
        value=value.tolist()
    elif isinstance(value,np.generic):
        value=value.item()
    non_finite=[]
    def safe_json(item,path='$'):
        if isinstance(item,(list,tuple)):
            return [safe_json(x,f'{path}[{i}]') for i,x in enumerate(item)]
        if isinstance(item,float) and not math.isfinite(item):
            non_finite.append({'path':path,'value':'NaN' if math.isnan(item) else 'Infinity' if item>0 else '-Infinity'})
            return None
        return item
    encoded=json.dumps(safe_json(value),ensure_ascii=False,allow_nan=False)
    if len(encoded)>16000:
        raise ValueError('结果过长，请分块计算')
    return {'value':json.loads(encoded),'non_finite':non_finite,'numpy_version':np.__version__,'pandas_version':pd.__version__,
            'scope':'仅实际计算此表达式，不代表完整程序已验证'}
