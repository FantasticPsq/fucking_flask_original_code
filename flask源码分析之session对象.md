### 五.flask内置session对象的分析 ###
导入session
```python
from flask import session
print(session)
```
session初始化：
```python
session = LocalProxy(partial(_lookup_req_object, 'session'))
```
对比request对象，我们可以发现，其实session和request及其相似，只是  
再给`_lookup_req_object`传递的参数为'seesion',执行`LocalProxy.__init__`:
```python
__slots__ = ('__local', '__dict__', '__name__', '__wrapped__')
# local=partial(_lookup_req_object, 'session')
def __init__(self, local, name=None):
    # 你可能会有疑问，__slots__中不包含_LocalProxy__local,为啥也可以
    # 为LocalProxy添加这个属性？这涉及到另一个知识点：类对私有属性的强制访问
    # 访问规则为：_ClassName__property,也就是说这里的_LocalProxy__local即为__local
    # 即self.__local = partial(_lookup_req_object,'session')
    object.__setattr__(self, '_LocalProxy__local', local)
    object.__setattr__(self, '__name__', name)
    if callable(local) and not hasattr(local, '__release_local__'):
        # "local" is a callable that is not an instance of Local or
        # LocalManager: mark it as a wrapped function.
        object.__setattr__(self, '__wrapped__', local)
```
print(session)将执行`LocalProxy.__str__`:
```python
#x=self=LocalProxy
__str__ = lambda x: str(x._get_current_object())
```
self.get_current_object():
```python
def _get_current_object(self):
    # 如果self.__local有__release_local__属性，
    # 则执行偏函数partial(_lookup_req_object, 'session')，
    # 实则是执行了_lookup_req_object('session)
    if not hasattr(self.__local, '__release_local__'):
        return self.__local()
    try:
        return getattr(self.__local, self.__name__)
    except AttributeError:
        raise RuntimeError('no object bound to %s' % self.__name__)
```
`_lookup_req_object('session')`:
```python
# name='session'
def _lookup_req_object(name):
    top = _request_ctx_stack.top
    if top is None:
        raise RuntimeError(_request_ctx_err_msg)
    # 返回ctx(RequestContext).session
    return getattr(top, name)
```
分析可知，print(session)也就是print(ctx.session),也就是说session和request一样，  
虽然是一LocalProxy对象，使用时实际上使用的是ctx.session,那么，我们来看一看ctx.session  
到底是啥,先得看RequestContext的`__init__`函数：
```python
def __init__(self, app, environ, request=None):
    self.app = app
    if request is None:
        request = app.request_class(environ)
    self.request = request
    self.url_adapter = app.create_url_adapter(self.request)
    self.flashes = None
    self.session = None
```
self.session=None?session最终到底是一个什么对象？细心的小伙伴可能会发现在前面请求上下文  
的流程中貌似见过session的初始化，是的，是在RequestContext.push()中，只是当时专注于  
将请求上下文而将其省略了：
```python
def push(self):
    top = _request_ctx_stack.top
    if top is not None and top.preserved:
        top.pop(top._preserved_exc)
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
    # 一开始self.session = None
    if self.session is None:
        # session_interface为SecureCookieSessionInterface的实例化对象
        session_interface = self.app.session_interface
        self.session = session_interface.open_session(
            self.app, self.request
        )
        if self.session is None:
            self.session = session_interface.make_null_session(self.app)
```
self.app.session_interface:
```python
session_interface = SecureCookieSessionInterface()
```
session_interface.open_session(self.app,self.request):
```python
def open_session(self, app, request):
    s = self.get_signing_serializer(app)
    if s is None:
        return None
    # 从请求的cookies中获取对应session的值，app.session_cookie_name可在配置中设置
    # 一开始还没有session，val自然为None,后面将执行self.session_class()
    val = request.cookies.get(app.session_cookie_name)
    if not val:
        return self.session_class()
    max_age = total_seconds(app.permanent_session_lifetime)
    try:
        data = s.loads(val, max_age=max_age)
        return self.session_class(data)
    except BadSignature:
        return self.session_class()
```
self.get_signing_serializer(app):
```python
def get_signing_serializer(self, app):
    # 如果app.secret_key=None,那么ctx.session = None
    # 将会执行SecureCookieSessionInterface.make_null_session(self.app)
    # 如果，app.secret_key!=None，将会返回可序列化的URLSafeTimedSerializer对象
    if not app.secret_key:
        return None
    signer_kwargs = dict(
        key_derivation=self.key_derivation,
        digest_method=self.digest_method
    )
    return URLSafeTimedSerializer(app.secret_key, salt=self.salt,
                                  serializer=self.serializer,
                                  signer_kwargs=signer_kwargs)
```
在app.secret_key!=None时，open_session函数中的s是一个URLSafeTimedSerializer对象，  
接下来执行self.session_class():
```python
session_class = SecureCookieSession
```
session_class就是类SecureCookieSession,那么可想而知 ctx.session是一个SecureCookieSession  
实例化对象：
也就是说使用session时，session其实是一个SecureCookieSession。  
当然如果前面的app.secret_key=None时，最终会在NullSession类中执行_fail函数抛出RuntimeError  
（建议自己点进去看一下，非常明了的）  

那么，当我用使用session保存数据时，如session['psq'] = psq，session是如何存取相关数据的呢？  
首先来看一看SecureCookieSession类的继承关系：
```python
class SecureCookieSession(CallbackDict, SessionMixin)
```
SecureCookieSession继承了两个类CallbackDict和SessionMixin,而：
```python
class CallbackDict(UpdateDictMixin, dict)
```
CallbackDict是继承了dict的，所以SecureCookieSession是一个特殊的字典，那么当有  
如下语句时，将执行`SecureCookeSession.__setitem__`:
```python
session['psq'] = 'psq'
```
但是由于SecureCookeSession自身并没有`__setitem__`方法，所以将执行dict的`__setitem__`方法，  
大家对dict都很熟悉，就不粘贴源码了。  

当有类似如下代码时，将执行`SecureCookieSession.__getitem__`方法：
```python
# 从session中取值
print(session['psq'])
```
`SecureCookieSession.__getitem__`:
```python
def __getitem__(self, key):
    self.accessed = True
    return super(SecureCookieSession, self).__getitem__(key)
```
其实最终还是执行的dict的`__getitem__方法。

我们知道，session需要保存数据到cookie中，那么flask是怎么保存的呢？  
我们之前在process_response函数中说过：
```python
def process_response(self, response):
    """执行after_request函数"""
    ctx = _request_ctx_stack.top
    bp = ctx.request.blueprint
    funcs = ctx._after_request_functions
    if bp is not None and bp in self.after_request_funcs:
        funcs = chain(funcs, reversed(self.after_request_funcs[bp]))
    if None in self.after_request_funcs:
        funcs = chain(funcs, reversed(self.after_request_funcs[None]))
    for handler in funcs:
        response = handler(response)
    # 如果请求上下文的session不为空，则保存session
    # 说得更准确一点是如果ctx.session不是NullSession的对象，则执行save_session
    # 注：session_interface= SecureCookieSessionInterface()
    if not self.session_interface.is_null_session(ctx.session):
        self.session_interface.save_session(self, ctx.session, response)
    return response
```
SecureCookieSessionInterface.save_session:
```python
def save_session(self, app, session, response):
    # 获取域名和路径
    domain = self.get_cookie_domain(app)
    path = self.get_cookie_path(app)

    # If the session is modified to be empty, remove the cookie.
    # If the session is empty, return without setting the cookie.
    if not session:
        if session.modified:
            response.delete_cookie(
                app.session_cookie_name,
                domain=domain,
                path=path
            )

        return

    # Add a "Vary: Cookie" header if the session was accessed at all.
    if session.accessed:
        response.vary.add('Cookie')

    if not self.should_set_cookie(app, session):
        return
    # http相关信息
    httponly = self.get_cookie_httponly(app)
    secure = self.get_cookie_secure(app)
    samesite = self.get_cookie_samesite(app)
    expires = self.get_expiration_time(app, session)
    # self.get_signing_serializer(app)是一个URLSafeTimedSerializer实例化对象
    # 将session中的信息序列化后赋值给val
    val = self.get_signing_serializer(app).dumps(dict(session))
    # 将val存储在response的cookie中
    response.set_cookie(
        app.session_cookie_name,
        val,
        expires=expires,
        httponly=httponly,
        domain=domain,
        path=path,
        secure=secure,
        samesite=samesite
    )
```
至此，有关session的原理我们都已经了然于心了。





