### SqlAlchemy数据库连接池 ###
其实flask连接数据库有两种方式，一种是通过`sessionmaker`产生session,一种是通过scoped_session  
产生session(session也叫数据库连接池)  
那么我们先来看一下通过`sessionmaker`是如何产生session的：
```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306", max_overflow=0)
Session = sessionmaker(bind=engine)
session = Session()
session.add(None)
session.commit()
```
首先是初始化sessionmaker：`sessionmaker.__init__`
```python
def __init__(
    self,
    bind=None,
    class_=Session,
    autoflush=True,
    autocommit=False,
    expire_on_commit=True,
    info=None,
    **kw
):
    kw["bind"] = bind
    kw["autoflush"] = autoflush
    kw["autocommit"] = autocommit
    kw["expire_on_commit"] = expire_on_commit
    if info is not None:
        kw["info"] = info
    self.kw = kw
    # make our own subclass of the given class, so that
    # events can be associated with it specifically.
    self.class_ = type(class_.__name__, (class_,), {})
```
从初始化函数可知，`class_`默认为`Session`类,其实`sessoinmaker`类的作用就是产生Session类  
更确切地说`sessionmaker`的作用是创建数据库连接池，而`Session`是获取对数据库的连接，如下  
源码给出的示例所示：
```python
"""
Session = sessionmaker(binds={
                SomeMappedClass: create_engine('postgresql://engine1'),
                SomeDeclarativeBase: create_engine('postgresql://engine2'),
                some_mapper: create_engine('postgresql://engine3'),
                some_table: create_engine('postgresql://engine4'),
                })"""
```
也就是一开始给出的代码示例中：
```python
# Session是数据库连接池
Session = sessionmaker(bind=engine)
# session是对某个数据库的连接
session = Session()
```
这是第一种方式，直接实例化`sessionmaker`创建出的`Session`来获取数据库的连接。  
那第二种方式是啥？可能你已经听过或者用过，那就是使用`scoped_session`:
```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session

engine = create_engine("mysql+pymysql://root:1234@127.0.0.1:3306", max_overflow=0)
Session = sessionmaker(bind=engine)
session = scoped_session(Session)
```
示例最后一行会执行`scoped_session.__init__`:
```python
# session_factory=Session
def __init__(self, session_factory, scopefunc=None):
    self.session_factory = session_factory
    # scopefunc = None,执行ThreadLocalRegistry.__init__
    if scopefunc:
        self.registry = ScopedRegistry(session_factory, scopefunc)
    else:
        self.registry = ThreadLocalRegistry(session_factory)
```
`ThreadingLocalRegistry.__init__`:
```python
# createfunc = session_factory = Session
def __init__(self, createfunc):
    # self.createfunc = Session
    self.createfunc = createfunc
    # self.registry是一个local对象，有关local相关分析，请见本地线程一节
    # 这体现了一个线程内一个连接
    self.registry = threading.local()
```
也就是说`scoped_session`中的registry(self.registry)是一个ThreadLocalRegistry对象，  
这个对象中封装了两个类：Session和threading.local。

使用过`scoped_session`的人都应该知道它创建出来的session(对某个数据库的连接),是可以  
使用`session.add()`和`session.commit()`方法的，但是你去`scoped_session`类找找会发现  
`scoped_session`类并没有`add`和`commit`等方法，而且`scoped_session`并没有继承除  
`object`之外的任何类，那么它的这些方法怎么来的呢？其实在`scoping.py`文件中，请看：
```python
# Session为Session类
for meth in Session.public_methods:
    setattr(scoped_session, meth, instrument(meth))
```
`Session.public_methods`:
```python
public_methods = (
        "__contains__",
        "__iter__",
        "add",
        "add_all",
        "begin",
        "begin_nested",
        "close",
        "commit",
        "connection",
        "delete",
        "execute",
        "expire",
        "expire_all",
        "expunge",
        "expunge_all",
        "flush",
        "get_bind",
        "is_modified",
        "bulk_save_objects",
        "bulk_insert_mappings",
        "bulk_update_mappings",
        "merge",
        "query",
        "refresh",
        "rollback",
        "scalar",
    )
```
可见`Session.public_methods`包含了几乎所有操作数据库的方法，那么，这些函数是  
怎么被`scoped_session`调用的？关键在于`setattr(scoped_session, meth, instrument(meth))`这句：  
其中`meth`是`Session.public_methods`中的一个方法。这行代码是给`scoped_session`设置一个属性，  
这个属性的名字(key)便是`Session.public_methods`中的相关函数名，值(value)便是`instrument(meth)`:
```python
# name=meth
# 这是个闭包，很明显闭包的作用是传递name参数执行对应函数
def instrument(name):
    def do(self, *args, **kwargs):
        # self.registry = ThreadLocalRegistry(session_factory)
        # self.registry已经是一个对象，并不是类，所以self.registry()
        # 将执行 ThreadLocalRegistry.__call__方法
        return getattr(self.registry(), name)(*args, **kwargs)
    return do
```
`ThreadLocalRegistry.__call__`:
```python
def __call__(self):
    try:
        # self.registry一开始并没有value,所以报错AttributeError
        return self.registry.value
    except AttributeError:
        # self.createfunc = Session
        # val = self.registry.value = Session()
        # 也就是说将Session对象返回,并将这个Session对象绑定到
        # threading.local对象中，实现了线程隔离
        # 也就是说不同请求操作不同的数据库互不影响
        val = self.registry.value = self.createfunc()
        return val
```
最终`instrument`函数中`do`函数中的`self.registry`是一个`Session`类，以add为例  
`Session`是有`add`方法的，所以最终相当于是执行了`Session`中的`add`方法。即：  
`scoped_session.add`等价于`Session.add`,但是由于`scoped_session`已经帮我们实现了  
线程隔离，更推荐使用`scoped_session`。

我们也可以看看`flask_sqlalchemy`的`SQLAlchemy`中使用的是哪种`session`:
```python
from flask_sqlalchemy import SQLAlchemy
```
`SQLAlchemy.__init__`:
```python
def __init__(self, app=None, use_native_unicode=True, session_options=None,
             metadata=None, query_class=BaseQuery, model_class=Model,
             engine_options=None):

    self.use_native_unicode = use_native_unicode
    self.Query = query_class
    # 执行self.create_scoped_session
    self.session = self.create_scoped_session(session_options)
    self.Model = self.make_declarative_base(model_class, metadata)
    self._engine_lock = Lock()
    self.app = app
    self._engine_options = engine_options or {}
    _include_sqlalchemy(self, query_class)
```
`SQLAlchemy.create_scoped_session`:
```python
def create_scoped_session(self, options=None):

    if options is None:
        options = {}

    scopefunc = options.pop('scopefunc', _app_ctx_stack.__ident_func__)
    options.setdefault('query_cls', self.Query)
    return orm.scoped_session(
        self.create_session(options), scopefunc=scopefunc
    )
```
最终返回的是一个`scoped_session`实例化对象，所以`SQLAlchemy`使用的也是`scoped_session`，  
因此使用SQLAlchemy时不必担心线程隔离的问题。
