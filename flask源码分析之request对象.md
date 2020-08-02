### 四.request对象分析 ###
1.导入
```python
from flask import request
```
2.查看flask对象
```python
request = LocalProxy(partial(_lookup_req_object, 'request'))
```
此处涉及到偏函数partial,对partial不了解的请看  [偏函数.py](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/%E5%81%8F%E5%87%BD%E6%95%B0.py) 文件  
由于实例化了LocalProxy类，调用`LocalProxy.__init__`方法
```python
__slots__ = ('__local', '__dict__', '__name__', '__wrapped__')
# local=partial(_lookup_req_object, 'request')
def __init__(self, local, name=None):
    # 你可能会有疑问，__slots__中不包含_LocalProxy__local,为啥也可以
    # 为LocalProxy添加这个属性？这涉及到另一个知识点：类对私有属性的强制访问
    # 访问规则为：_ClassName__property,也就是说这里的_LocalProxy__local即为__local
    # 即self.__local = partial(_lookup_req_object,'request')
    object.__setattr__(self, '_LocalProxy__local', local)
    object.__setattr__(self, '__name__', name)
    if callable(local) and not hasattr(local, '__release_local__'):
        # "local" is a callable that is not an instance of Local or
        # LocalManager: mark it as a wrapped function.
        object.__setattr__(self, '__wrapped__', local)
```
这些完全不足以让我们了解request,那么我们可以执行如下语句：
```python
print(request)
```
打印request时，访问`LocalProxy.__str__`函数：
```python
#x=self=LocalProxy
__str__ = lambda x: str(x._get_current_object())
```
接下来调用了self._get_current_object():
```python
def _get_current_object(self):
    # 如果self.__local有__release_local__属性，
    # 则执行偏函数partial(_lookup_req_object, 'request')，
    # 实则是执行了_lookup_req_object('request)
    if not hasattr(self.__local, '__release_local__'):
        return self.__local()
    try:
        return getattr(self.__local, self.__name__)
    except AttributeError:
        raise RuntimeError('no object bound to %s' % self.__name__)
```
`_lookup_req_object('request')`
```python
# name='request'
def _lookup_req_object(name):
    # 获取ctx(请求上下文）
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(_request_ctx_err_msg)
    # 返回getattr(ctx,'request'),即返回ctx的request属性
    # 从之前的分析可知，ctx的request其实是一个Request实例化对象
    return getattr(top, name)
```
综合上面的分析可知，flask.request虽然是一个LocalProxy对象，但是其最终是一个Request对象  
LocalProxy只是做了一个代理  
提问：代理模式有什么好处？
