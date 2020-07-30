### 一.flask路有本质 ###
`flask`装饰器路由的简单使用        --(1)
```python
from flask import Flask
app = Flask(__name__)
@app.route("/", methods=["POST"], endpoint="in")
def index():
    return "hello"
```
`route`装饰器源代码
```python
def route(self, rule, **options):
    def decorator(f):
        # 如果传了endpoint则从options中取出endpoint,否则endpoint=None
        endpoint = options.pop('endpoint', None)
        # 等价于app.add_url_rule(rule,endpoint,f,**options)
        self.add_url_rule(rule, endpoint, f, **options)
        return f
    return decorator
```
`route`装饰器分析
```text
self=app,rule="/",options={methods:["POST"]},endpoint="in"
route装饰器返回decorator函数，decorator的参数f(function)即为index函数
也就是@app.route("/", methods=["POST"], endpoint="in") =>
@decorator => decorator(index)=> app.add_url_rule(rule,endpoint,index,methods=["POST"])
```
也就是代码段(1)等价于：
```python
app = Flask(__name__)
def index():
    return "hello"
# 需要知道的是endpoint如果不传，那么将默认为视图函数的名称，详见add_url_rule源码
app.add_url_rule("/",endpoint="in",view_func=index,methods=["POST"])  
```
而类视图中也是通过这个`add_url_rule`函数来进行视图注册的，那么我们来看一看类试图的实现原理
先看一段代码：                 --(2)
```python
from flask import Flask,views
app = Flask(__name__)
class HelloView(views.MethodView):
    def get(self):
        return "hello world"
# as_view函数中的name相当于route装饰器中的endpoint
app.add_url_rule("/hello", view_func=HelloView.as_view(name="hello"))
```
对比代码段(1)来说，类视图中最不同之处在于as_view这个关键函数，其源代码为
```python
class View(object):
    # classmethod修饰符需要as_view的第一个参数必须为cls，cls为调用as_view方法的类。可以通过cls调用类的属性和方法
    @classmethod
    def as_view(cls, name, *class_args, **class_kwargs):
        def view(*args, **kwargs):
            # view.view_class即为cls，这里是实例化cls对象
            self = view.view_class(*class_args, **class_kwargs)
            # dispatch_request(分配新的请求工作线程)后面做详细讲解
            return self.dispatch_request(*args, **kwargs)
        # decorators是装饰器列表,比如decorators = [login_required,admin_required]
        if cls.decorators: 
            # 视图函数的名字和模块设置
            view.__name__ = name
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                #用decorator装饰视图函数，和@login_required作用于视图函数等价
                view = decorator(view)
        # 一切皆对象，view.view_class相当于view函数有字段view_class,其值为cls
        view.view_class = cls
        view.__name__ = name
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.methods = cls.methods
        view.provide_automatic_options = cls.provide_automatic_options
        return view
```
下面我们来看看`dispatch_request`这个函数的源代码：
```python
from .globals import request
def dispatch_request(self, *args, **kwargs):
    #获取对应函数的属性，比如get函数，post函数等，如果request.method.lower()没有则默认为None
    meth = getattr(self, request.method.lower(), None)

    # If the request method is HEAD and we don't have a handler for it
    # retry with GET.
    if meth is None and request.method == 'HEAD':
        meth = getattr(self, 'get', None)

    assert meth is not None, 'Unimplemented method %r' % request.method
    #执行请求对应的方法
    return meth(*args, **kwargs)
```
可以看出flask的路由很多地方和django是相似的。