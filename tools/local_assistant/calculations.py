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

def bounded(value,ancestors=frozenset(),depth=0,budget=None):
    budget=[LIMIT*2] if budget is None else budget
    budget[0]-=1
    if budget[0]<0 or depth>24 or id(value) in ancestors:
        raise ValueError('结果过于复杂或含循环引用')
    if isinstance(value,(np.ndarray,pd.Series)):
        budget[0]-=value.size
        empty_numeric_series=isinstance(value,pd.Series) and all(x is None for x in value.tolist())
        if value.size>LIMIT or budget[0]<0 or (value.dtype.kind not in 'biuf' and not empty_numeric_series):
            raise ValueError('仅支持最多 4096 个元素的数值数组或 Series')
    elif isinstance(value,(int,float,np.number)):
        if math.isfinite(float(value)) and abs(value)>10**100:
            raise ValueError('数值过大')
    elif isinstance(value,(list,tuple,dict)):
        if len(value)>LIMIT:
            raise ValueError('序列过长')
        if isinstance(value,dict) and (len(value)>32 or not all(isinstance(k,str) and len(k)<=80 for k in value)):
            raise ValueError('对象键必须为短字符串，最多 32 项')
        for item in (value.values() if isinstance(value,dict) else value):
            bounded(item,ancestors|{id(value)},depth+1,budget)
    elif value is not None:
        raise ValueError('表达式只能产生数值、数值序列或 None')
    return value

def calculate(expression):
    if not isinstance(expression,str) or not expression or len(expression)>8000:
        raise ValueError('表达式为空或超过 8000 字符')
    try:
        tree=ast.parse(expression,mode='eval')
    except SyntaxError:
        # 模型有时给表达式附带标准导入；只识别写法，不执行任何导入语句。
        statements=ast.parse(expression,mode='exec').body
        while statements and isinstance(statements[0],ast.Import):
            statement=statements.pop(0)
            if not all((alias.name,alias.asname) in {('numpy','np'),('pandas','pd')} for alias in statement.names):
                raise ValueError('只识别 import numpy as np / import pandas as pd；其他导入不允许')
        if not statements or len(statements)>16 or not isinstance(statements[-1],ast.Expr):
            raise ValueError('最多 16 条受限计算语句，最后一条应是结果表达式或 print')
        tree=ast.Module(body=statements,type_ignores=[])
    if sum(1 for _ in ast.walk(tree))>512:
        raise ValueError('表达式过于复杂，请拆分计算')
    variables={}
    printed=[]
    def visit(node,depth=0):
        if depth>24:
            raise ValueError('表达式嵌套过深')
        child=lambda item:visit(item,depth+1)
        if isinstance(node,ast.Constant) and (node.value is None or isinstance(node.value,(int,float))):
            return bounded(node.value)
        if isinstance(node,ast.Name) and node.id in variables:
            return bounded(variables[node.id])
        if isinstance(node,(ast.List,ast.Tuple)):
            values=[child(x) for x in node.elts]
            return bounded(tuple(values) if isinstance(node,ast.Tuple) else values)
        if isinstance(node,ast.Dict):
            if not all(isinstance(k,ast.Constant) and isinstance(k.value,str) for k in node.keys):
                raise ValueError('对象键必须是字符串常量')
            return bounded({k.value:child(v) for k,v in zip(node.keys,node.values)})
        if isinstance(node,ast.Subscript):
            value=child(node.value)
            index=child(node.slice)
            if isinstance(node.slice,ast.Tuple):index=tuple(index)
            if not isinstance(value,(list,tuple,np.ndarray,pd.Series)) or not isinstance(index,(int,slice,tuple)):
                raise ValueError('仅支持数值序列的整数索引或切片')
            return bounded(value[index])
        if isinstance(node,ast.Slice):
            values=[child(x) if x is not None else None for x in [node.lower,node.upper,node.step]]
            if not all(x is None or isinstance(x,int) for x in values):
                raise ValueError('切片参数必须为整数')
            return slice(*values)
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
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='print' and not node.keywords:
            args=[child(x) for x in node.args]
            value=bounded(args[0] if len(args)==1 else args)
            printed.append(value);bounded(printed)
            return value
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute):
            name=node.func.attr
            args=[child(x) for x in node.args]
            allowed_keywords={'sum':{'axis','keepdims','skipna'},'mean':{'axis','keepdims','skipna'}}.get(name,set())
            if any(k.arg not in allowed_keywords for k in node.keywords):
                raise ValueError('该调用不支持指定关键字参数')
            keywords={k.arg:child(k.value) for k in node.keywords}
            if isinstance(node.func.value,ast.Name) and node.func.value.id in {'np','pd'}:
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
                    return bounded(function(*args,**keywords))
            else:
                value=child(node.func.value)
                if isinstance(value,list) and name=='append' and len(args)==1:
                    if len(value)>=LIMIT:raise ValueError('列表过长')
                    value.append(args[0]);bounded(value);return None
                if isinstance(value,list) and name=='copy' and not args:
                    return bounded(value.copy())
                if isinstance(value,(np.ndarray,pd.Series)) and name in {'sum','mean','count','tolist','reshape','copy'}:
                    if name=='count' and not isinstance(value,pd.Series):
                        raise ValueError('count() 仅支持 pandas Series')
                    return bounded(getattr(value,name)(*args,**keywords))
        raise ValueError('不支持此语法；仅允许受限数值计算和白名单 NumPy / pandas 操作，无文件、网络、循环、函数定义或任意函数调用')
    if isinstance(tree,ast.Expression):
        value=visit(tree.body)
    else:
        value=None
        for statement in tree.body:
            if isinstance(statement,ast.Expr):value=visit(statement.value)
            elif isinstance(statement,ast.Assign) and len(statement.targets)==1:
                target=statement.targets[0]
                result=visit(statement.value)
                if isinstance(target,ast.Name) and not target.id.startswith('_') and target.id not in {'np','pd','print'}:
                    variables[target.id]=result
                elif isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and target.value.id in variables:
                    container=variables[target.value.id]
                    index=visit(target.slice)
                    if not isinstance(container,(list,np.ndarray)) or not isinstance(index,int):
                        raise ValueError('只允许临时数值列表或数组的整数位置赋值')
                    container[index]=result;bounded(container)
                else:raise ValueError('赋值只能使用临时数值变量，不允许修改模块或属性')
            else:raise ValueError('只支持受限赋值和计算语句，不执行控制流或任意 Python 代码')
        last=tree.body[-1].value
        if isinstance(last,ast.Call) and isinstance(last.func,ast.Name) and last.func.id=='print' and len(printed)>1:
            value=printed
    if isinstance(value,(np.ndarray,pd.Series)):
        value=value.tolist()
    elif isinstance(value,np.generic):
        value=value.item()
    non_finite=[]
    def safe_json(item,path='$'):
        if isinstance(item,(np.ndarray,pd.Series)):item=item.tolist()
        elif isinstance(item,np.generic):item=item.item()
        if isinstance(item,dict):
            return {k:safe_json(v,path+'.'+k) for k,v in item.items()}
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
            'scope':'仅计算白名单语句；返回最后结果，多个 print 返回值列表。不代表完整 Python 程序已验证'}
