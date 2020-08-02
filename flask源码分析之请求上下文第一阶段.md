接下来，我们一段一段来看重要的源代码：
app.run()
```python
def run(args):
    from werkzeug.serving import run_simple
    try:
        # run_simple启动服务，由于self被当作参数传递给run_simple,说明self可调用
        # 那么调用self时便会访问self的__call__方法，注：self=app=Flask()
        run_simple(host, port, self, **options)
    finally:
        # reset the first request information if the development server
        # reset normally.  This makes it possible to restart the server
        # without reloader and that stuff from an interactive shell.
        self._got_first_request = False
```
`Flask.__call__`
```python
def __call__(self, environ, start_response):
    """The WSGI server calls the Flask application object as the
    WSGI application. This calls :meth:`wsgi_app` which can be
    wrapped to applying middleware."""
    # 注：environ包含所有的请求信息
    return self.wsgi_app(environ, start_response)
```
Flask.wsgi_app(environ,start_response)
```python
def wsgi_app(self,environ,start_response):
    #实例化RequestContext对象
    ctx = self.request_context(environ)
    error = None
    try:
        try:
            # 将ctx加入到Local.stack中
            ctx.push()
            # 寻找视图函数并执行，结果返回给response
            response = self.full_dispatch_request()
        except Exception as e:
            error = e
            response = self.handle_exception(e)
        except:
            error = sys.exc_info()[1]
            raise
        return response(environ, start_response)
    finally:
        if self.should_ignore_error(error):
            error = None
        ctx.auto_pop(error)
```
self.request_context(environ)
```python
def request_context(self, environ):
    return RequestContext(self, environ)
```
`RequestContext.__init__`
```python
def __init__(self, app, environ, request=None):
    self.app = app
    if request is None:
        request = app.request_class(environ)
    # request_class = Request
    # self.request = Request(environ)
    self.request = request
    self.url_adapter = app.create_url_adapter(self.request)
    self.flashes = None
    self.session = None
```
app.request_class(environ)，注：app=Flask(args)
```python
request_class = Request
```
从上面的一段分析，最终wsgi_app函数中的ctx=self.request_context(environ)=RequestContext(args)  
也就是说ctx就是请求上下文RequestContext的对象，而RequestContext中的request是一个Request的对象，  
可以说，ctx基本包含了请求相关的所有信息  
继续看：
ctx.push()=>RequestContext.push()
```python
def push(self):
    """Binds the request context to the current context."""
    top = _request_ctx_stack.top
    if top is not None and top.preserved:
        top.pop(top._preserved_exc)
    # Before we push the request context we have to ensure that there
    # is an application context.
    app_ctx = _app_ctx_stack.top
    if app_ctx is None or app_ctx.app != self.app:
        app_ctx = self.app.app_context()
        app_ctx.push()
        self._implicit_app_ctx_stack.append(app_ctx)
    else:
        self._implicit_app_ctx_stack.append(None)

    if hasattr(sys, 'exc_clear'):
        sys.exc_clear()

    _request_ctx_stack.push(self)
```
_request_ctx_stack.top  
先看看`_request_ctx_stack`这条路
```python
# _request_ctx_stack是项目一启动就被初始化的，等待被调用
_request_ctx_stack = LocalStack()
```
`LocalStack.__init__`
```python
def __init__(self):
    # Local便是在本地线程一文中所讲的Local类
    self._local = Local()
```
`Local.__init__`
```python
def __init__(self):
    # __storage__存储的信息为{唯一标识:{'stack':[RequestContext(),]}}
    object.__setattr__(self, '__storage__', {})
    # __ident_func__即为__storage__中的唯一标识
    object.__setattr__(self, '__ident_func__', get_ident)
```
你可能觉得说stack哪里来的？那么请看LocalStack.push():
```python
def push(self, obj):
    """Pushes a new item to the stack"""
    # 获取Local的stack属性，没有则为None
    rv = getattr(self._local, 'stack', None)
    if rv is None:
        # list是引用类型，self._local.stack和rv指向同一个地址
        self._local.stack = rv = []
    # 向self._local.stack中添加对象（实则为RequestContext对象）
    rv.append(obj)
    return rv
```
再来看_request_ctx_stack.top的top
```python
@property
def top(self):
    """The topmost item on the stack.  If the stack is empty,
    `None` is returned.
    """
    try:
        # self._local是一个Local对象，self._local.stack会调用Local的get方法__getattr__
        # 用数组模拟栈，取栈首的那一个，不过一般stack中只有一个值。
        return self._local.stack[-1]
    except (AttributeError, IndexError):
        return None
```
`Local.__getattr__`
```python
# name=stack[-1]
def __getattr__(self, name):
    try:
        return self.__storage__[self.__ident_func__()][name]
    except KeyError:
        raise AttributeError(name)
```
然后回到ctx.push()函数继续往下看：  
app_ctx = _app_ctx_stack.top，这是应用上下文，由于应用上下文和请求上下文的请求流程以及思路基本  
相同，看懂请求上下文，应用上下文自然不在话下，所以咋们先专注于请求上下文：  
_request_ctx_stack.push(self),注：self=ctx,作为参数传入LocalStack.push(args)  
有关LocalStack.push前文已经有讲过，这里复制下来：
```python
def push(self, obj):
    """Pushes a new item to the stack"""
    # 获取Local的stack属性，没有则为None
    rv = getattr(self._local, 'stack', None)
    if rv is None:
        # list是引用类型，self._local.stack和rv指向同一个地址
        self._local.stack = rv = []
    # 向self._local.stack中添加对象（实则为RequestContext对象），这里会调用Local的set方法__set__
    rv.append(obj)
    return rv
```
需要强调的是，由于self=ctx,传入之后就是obj=ctx（ctx为RequestContext对象）,注意两个self的区分。
`Local.__setattr__`  
```python
def __setattr__(self, name, value):
    # 获取唯一标识
    ident = self.__ident_func__()
    storage = self.__storage__
    try:
        storage[ident][name] = value
    except KeyError:
        storage[ident] = {name: value}
# 执行上述操作之后__storage__存储的内容为 {ident:{'stack':[ctx,]}
```
以上是第一阶段的基本流程，其中需要重点把握的__storage__以及_request_ctx_stack。
第一阶段提问：  
1. flask如何处理的多线程？
2. Local的stack为什么是一个列表？不是一般一个请求对应一个独立线程吗？一个独立
的线程内不是一般只有一个请求上下文(RequestContext)吗？
