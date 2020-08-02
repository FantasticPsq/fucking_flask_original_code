接下来，我们来看一看第二阶段请求处理部分的相关源码：
先把总函数粘贴出来：
```python
def wsgi_app(self,environ,start_response):
    # 第一阶段
    # 实例化RequestContext对象
    ctx = self.request_context(environ)
    error = None
    try:
        try:
            # 第一阶段
            # 将ctx加入到Local.stack中
            ctx.push()
            # 第二阶段
            # 寻找视图函数并执行，结果返回给response
            response = self.full_dispatch_request()
        except Exception as e:
            error = e
            response = self.handle_exception(e)
        except:
            error = sys.exc_info()[1]
            raise
        # 注意由于返回的response进行实例化了，所以返回的response必须是Response对象
        return response(environ, start_response)
    finally:
        if self.should_ignore_error(error):
            error = None
        # 第三阶段
        ctx.auto_pop(error)
```
Flask.full_dispatch_request，其作用为请求预处理和捕获和处理相关错误
```python
def full_dispatch_request(self):
    """Dispatches the request and on top of that performs request
    pre and postprocessing as well as HTTP exception catching and
    error handling.

    .. versionadded:: 0.7
    """
    # 执行第一次请求之前要执行的函数，即执行所有的@app.before_first_request装饰的函数
    self.try_trigger_before_first_request_functions()
    try:
        # 触发请求开始的信号
        request_started.send(self)
        # 执行所有before_request装饰的函数
        rv = self.preprocess_request()
        if rv is None:
            # 如果before_request装饰的函数没有返回值，则执行视图函数
            # 如果before_request装饰的函数有返回值，不在执行视图函数
            rv = self.dispatch_request()
    except Exception as e:
        rv = self.handle_user_exception(e)
        # 将视图函数或者before_request的返回值进行修饰
    return self.finalize_request(rv)
```
由于后面的代码与flask信号机制息息相关，咋们先来看看flask的信号机制：  
首先flask内置了这些信号：
```python
from flask import signals
```
signals.py:
```python
_signals = Namespace()
# Core signals.  For usage examples grep the source code or consult
# the API documentation in docs/api.rst as well as docs/signals.rst
# 模板渲染完毕
template_rendered = _signals.signal('template-rendered')
# 模板渲染之前
before_render_template = _signals.signal('before-render-template')
# 请求开始
request_started = _signals.signal('request-started')
# 请求结束
request_finished = _signals.signal('request-finished')
# 请求失败
request_tearing_down = _signals.signal('request-tearing-down')
# 请求出现异常
got_request_exception = _signals.signal('got-request-exception')
appcontext_tearing_down = _signals.signal('appcontext-tearing-down')
appcontext_pushed = _signals.signal('appcontext-pushed')
appcontext_popped = _signals.signal('appcontext-popped')
# 闪现信号
message_flashed = _signals.signal('message-flashed')
```
信号的简单使用：
```python
from flask import signals
def func(*args,**kwargs):
    print("hello")

# 向request_started信号中注册func函数
signals.request_started.connect(func)
# 调用send方法触发request_started信号,我们这是手动触发，在flask内不需要手动触发
# full_dispatch_request中会自动调用request_started.send(),示例请见app.py
signals.request_started.send()
```
也就是说信号最重要的两个方法：connect和send  
那么我们回过头来继续看full_dispatch_request的源码：执行到：
self.try_trigger_before_first_request_functions()
```python
def try_trigger_before_first_request_functions(self):
    """Called before each request and will ensure that it triggers
    the :attr:`before_first_request_funcs` and only exactly once per
    application instance (which means process usually).

    :internal:
    """
    # 一开始_got_first_request=false,_got_first_request标志
    # before_first_request是否执行完毕
    if self._got_first_request:
        return
    # 处理before_first_request时先加锁，我也不知道为啥要加锁`_`
    with self._before_request_lock:
        if self._got_first_request:
            return
    # 遍历所有的before_first_request函数，依次执行每个函数
    # 初始化时 self.before_first_request_funcs = []
        for func in self.before_first_request_funcs:
            func()
    # 执行玩所有before_first_request函数后，设置_got_first_request为true退出while循环
        self._got_first_request = True
```
那么，所有的before_first_request函数是怎么被加入到before_first_request_funcs中的呢？
请看before_first_request的源码：
```python
@setupmethod
def before_first_request(self, f):
    # 在这里添加before_first_request
    self.before_first_request_funcs.append(f)
    return f
```
接下来执行request_started.send(self)触发request_started信号  
触发信号机制后，执行rv = self.preprocess_request()：
```python
def preprocess_request(self):
    # 获取request请求的蓝图
    bp = _request_ctx_stack.top.request.blueprint
    
    # 获取url_value_preprocessor函数，进行url预处理
    funcs = self.url_value_preprocessors.get(None, ())
    if bp is not None and bp in self.url_value_preprocessors:
        # self.url_value_preprocessors获取蓝图的所有url_value_preprocessor函数
        # chain将列表或者元组进行连接
        funcs = chain(funcs, self.url_value_preprocessors[bp])
    # 依次执行所有url_value_preprocessor函数
    for func in funcs:
        func(request.endpoint, request.view_args)
    # 获取app对应的所有的before_request函数
    # 需要注意的是，before_request_funcs是字典，而before_first_request_funcs是列表
    funcs = self.before_request_funcs.get(None, ())
    if bp is not None and bp in self.before_request_funcs:
        # self.before_request_funcs[bp]获取蓝图对应的所有的before_request函数
        # chain用于连接列表或元组
        funcs = chain(funcs, self.before_request_funcs[bp])
    # 遍历所有的before_request函数，依次执行，先执行的是app中的before_request
    # 如果before_request函数有返回值，则不再执行视图函数
    for func in funcs:
        rv = func()
        if rv is not None:
            return rv
```
接下来执行rv = self.dispatch_request()：
```python
def dispatch_request(self):
    """Does the request dispatching.  Matches the URL and returns the
    return value of the view or error handler.  This does not have to
    be a response object.  In order to convert the return value to a
    proper response object, call :func:`make_response`.

    .. versionchanged:: 0.7
       This no longer does the exception handling, this code was
       moved to the new :meth:`full_dispatch_request`.
    """
    # 获取request(Request对象），_request_ctx_stack.top是RequestContext对象
    # RequestContext初始化时会实例化Request对象
    req = _request_ctx_stack.top.request
    if req.routing_exception is not None:
        self.raise_routing_exception(req)
    # 获取请求的url_rule，路由规则
    rule = req.url_rule
    # if we provide automatic options for this URL and the
    # request came with the OPTIONS method, reply automatically
    if getattr(rule, 'provide_automatic_options', False) \
       and req.method == 'OPTIONS':
        return self.make_default_options_response()
    # otherwise dispatch to the handler for that endpoint
    # 从路由本质一文中可知所有的视图函数都会被注册到view_functions这个字典中
    # 现在根据endpoint获取对应的视图函数进而执行视图函数
    return self.view_functions[rule.endpoint](**req.view_args)
```
self.finalize_request(rv)：
```python
def finalize_request(self, rv, from_error_handler=False):
    # 封装视图函数返回的数据为一个Response对象
    response = self.make_response(rv)
    try:
        # 执行after_request函数
        response = self.process_response(response)
        request_finished.send(self, response=response)
    except Exception:
        if not from_error_handler:
            raise
        self.logger.exception('Request finalizing failed with an '
                              'error while handling an error')
    return response
```
process_response
```python
def process_response(self, response):
    """执行after_request函数"""
    # 获取请求上下文对象
    ctx = _request_ctx_stack.top
    # 获取蓝图对象
    bp = ctx.request.blueprint
    # 获取RequestContext的after_request函数,这种after_request在蓝图和app的after_request之前执行
    funcs = ctx._after_request_functions
    if bp is not None and bp in self.after_request_funcs:
        # self.after_request_funcs[bp]获取蓝图的after_request_funcs
        # reversed(self.after_request_funcs[bp])将蓝图所有after_request_funcs次序进行反转
        funcs = chain(funcs, reversed(self.after_request_funcs[bp]))
    if None in self.after_request_funcs:
        # reversed(self.after_request_funcs[None])获取app的after_request函数并反转
        # Flask中after_request源代码：self.after_request_funcs.setdefault(None, []).append(f)
        # setdefault(None,[])的意思是：如果after_request_funcs有None这个key,则返回对应的value
        # 如果after_request_funcs没有None这个key，则设置None这个key的value为[]，并返回[]
        # 所以after_request函数的执行顺序为先逆序执行蓝图种after_request函数，然后逆序执行app中after_request函数
        funcs = chain(funcs, reversed(self.after_request_funcs[None]))
    for handler in funcs:
        # 执行after_request函数，并将response进行封装，返回的必须是Response对象
        # 所以after_request函数必须返回Response对象，通常可以使用make_response！！！（重点）
        # 如果after_request返回的不是make_response(response)，那么视图函数返回的值将被覆盖
        response = handler(response)
    # 如果请求上下文的session不为空，则保存session
    if not self.session_interface.is_null_session(ctx.session):
        self.session_interface.save_session(self, ctx.session, response)
    return response
```
回到finalize_request继续执行request_finished.send(self, response=response)，  
触发request_finished信号，请求结束  
第二阶段遗留问题：
1. 为什么处理before_first_request函数时需要加锁？而处理before_request函数却不需要？  
2. RequestContext中为什么也会有after_request函数，它是在哪里定义的？以及它是用来干啥的？
