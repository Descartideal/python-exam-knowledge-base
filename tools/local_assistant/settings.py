"""本机已验证可加载模型原生 256K 上下文；生成空间独立预留。"""
CONTEXT_LENGTH = 262144
RESPONSE_TOKENS = 8192
CONTEXT_OVERHEAD = 1024
MAX_QUERY_CHARS = 100000

# Qwen 原生思考开关 + 应用层预算；不是模型原生的五档 API。
PROFILES = {
    'none': {'label':'无思考','think':False,'response_tokens':4096,'rounds':10,'candidates':1,'review':0,'retrieval':5},
    'light': {'label':'轻度','think':True,'response_tokens':8192,'rounds':12,'candidates':1,'review':0,'retrieval':6},
    'medium': {'label':'中等','think':True,'response_tokens':16384,'rounds':18,'candidates':2,'review':1,'retrieval':8},
    'heavy': {'label':'重度','think':True,'response_tokens':32768,'rounds':28,'candidates':3,'review':1,'retrieval':8},
    'max': {'label':'最大限度','think':True,'response_tokens':65536,'rounds':40,'candidates':5,'review':2,'retrieval':8},
}
DEFAULT_EFFORT = 'medium'
TASK_TOKEN_LIMIT = 262144
for name, seconds, lines in [('none',60,200),('light',60,300),('medium',90,500),('heavy',180,800),('max',300,1000)]:
    PROFILES[name].update(runtime_seconds=seconds,read_lines=lines)
for name, budget in [('none',0),('light',1024),('medium',4096),('heavy',8192),('max',16384)]:
    PROFILES[name]['reasoning_slice_tokens']=budget
