"""排除明显恒真的占位断言；不判定一般验证器是否充分。"""
import ast

def meaningful_assertion(node):
    value=node.test
    if isinstance(value,ast.Constant) and bool(value.value):
        return False
    if isinstance(value,ast.BoolOp) and isinstance(value.op,ast.Or) and any(
            isinstance(part,ast.Constant) and bool(part.value) for part in value.values):
        return False
    if isinstance(value,ast.Compare) and len(value.ops)==1 and isinstance(value.ops[0],ast.Eq):
        left,right=value.left,value.comparators[0]
        if ast.dump(left)==ast.dump(right) and not any(isinstance(n,ast.Call) for n in ast.walk(left)):
            return False
    return True
