第三阶段我们看看请求结束之后，flask做了什么工作：  
先把wsgi_app()函数粘贴出来：
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
        return response(environ, start_response)
    finally:
        if self.should_ignore_error(error):
            error = None
        # 第三阶段
        ctx.auto_pop(error)
```
我们来看第三阶段的ctx.auto_pop(error):
```python
def auto_pop(self, exc):
    # 如果设置了保存ctx,或者出现了相关错误(exc=error)并且开了debug模式和相关配置时保留ctx（这个不重要）
    if self.request.environ.get('flask._preserve_context') or \
       (exc is not None and self.app.preserve_context_on_exception):
        self.preserved = True
        self._preserved_exc = exc
    # 调用ctx.pop(exc)方法
    else:
        self.pop(exc)      
```
ctx.pop(exc),exc=error:
```python
# 如果error=None,那么pop函数中exc=_sentinel
def pop(self, exc=_sentinel):
    """
    从stack中将ctx删除，并触发Flask.teardown_request装饰器，执行被此装饰器装饰的函数
    """
    # 获取隐含创建的应用上下文,注意_implicit_app_ctx_stack是个列表
    app_ctx = self._implicit_app_ctx_stack.pop()

    try:
        clear_request = False
        # 如果存在被隐式创建（flask自动创建）的app_ctx，则触发teardown_request函数
        if not self._implicit_app_ctx_stack:
            self.preserved = False
            self._preserved_exc = None
            if exc is _sentinel:
                exc = sys.exc_info()[1]
            # 执行teardown_request函数
            self.app.do_teardown_request(exc)

            # 只支持python2.x，python3.x中此处无效
            if hasattr(sys, 'exc_clear'):
                sys.exc_clear()
            # 获取request（Request对象）的close属性
            request_close = getattr(self.request, 'close', None)
            # 关闭请求
            if request_close is not None:
                request_close()
            clear_request = True
    finally:
        # 将ctx从请求上下文stack中删除
        rv = _request_ctx_stack.pop()
        # get rid of circular dependencies at the end of the request
        # so that we don't require the GC to be active.
        if clear_request:
            rv.request.environ['werkzeug.request'] = None
        # 删除app上下文
        if app_ctx is not None:
            app_ctx.pop(exc)
        assert rv is self, 'Popped wrong request context.  ' \
            '(%r instead of %r)' % (rv, self)
```
接下来看self.app.do_teardown_request(exc):
```python
def do_teardown_request(self, exc=_sentinel):
    if exc is _sentinel:
        exc = sys.exc_info()[1]
    # 获取app的teardown_request函数并反转他们的执行顺序
    funcs = reversed(self.teardown_request_funcs.get(None, ()))
    bp = _request_ctx_stack.top.request.blueprint
    if bp is not None and bp in self.teardown_request_funcs:
        # 获取蓝图中的teardown函数并反转次序后和funcs相连
        funcs = chain(funcs, reversed(self.teardown_request_funcs[bp]))
    for func in funcs:
        # 依次执行teardown_request函数
        func(exc)
    # 触发request_tearing_down信号
    request_tearing_down.send(self, exc=exc)
```
然后执行_request_ctx_stack.pop()：
```python
def pop(self):
    # 获取Local的stack
    stack = getattr(self._local, 'stack', None)
    if stack is None:
        return None
    elif len(stack) == 1:
        release_local(self._local)
        return stack[-1]
    else:
        return stack.pop()
```
最后从stack中删除请求上下文，至此，请求完毕