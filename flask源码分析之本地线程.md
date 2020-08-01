### 二.flask threading.local ###
使用过flask的人都应该知道，flask是线程隔离的，也就是说每个任务都只在自己的线程内执行，而不影响其他线程。
线程隔离最重要的便是threading.local的local类了。  
请看其源码实现:   --(1)
```python
class local:
    # __slots__限定给local绑定的属性只能是_local__impl和__dict__
    # _local__impl是local的实现类
    # __dict__保存了local的相关属性，比如self.name="psq",那么__dict__中就会有{"name":"psq"}
    __slots__ = '_local__impl', '__dict__'
    # 实例化对象的方法，优先于初始化函数__init__被执行
    def __new__(cls, *args, **kw):
        # local实例化时不能带参数（因为默认采用object的初始化方法），如果带了参数必须使用自己的初始化函数进行初始化
        if (args or kw) and (cls.__init__ is object.__init__):
            raise TypeError("Initialization arguments are not supported")
        # 实例化 object对象
        self = object.__new__(cls)
        # 实例化local的实现类
        impl = _localimpl()
        impl.localargs = (args, kw)
        # 实例化RLock，用于后面的加锁。
        impl.locallock = RLock()
        object.__setattr__(self, '_local__impl', impl)
        # We need to create the thread dict in anticipation of
        # __init__ being called, to make sure we don't call it
        # again ourselves.
        impl.create_dict()
        return self
    
    # __getattribute__拦截对象对类属性的访问（不会拦截类对属性的访问），为了防止出现深度递归，  
    # 最安全的方式是使用object的__getattribute__方法
    def __getattribute__(self, name):
        # _patch是对操作进行加锁，下同
        with _patch(self):
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        # __dict__不可写
        if name == '__dict__':
            raise AttributeError(
                "%r object attribute '__dict__' is read-only"
                % self.__class__.__name__)
        with _patch(self):
            return object.__setattr__(self, name, value)

    def __delattr__(self, name):
        # __dict__不可删
        if name == '__dict__':
            raise AttributeError(
                "%r object attribute '__dict__' is read-only"
                % self.__class__.__name__)
        with _patch(self):
            return object.__delattr__(self, name)
```
上面的代码中有个非常重要的加锁操作_patch,其源代码如下：
```python
# contextmanager上下文管理器，封装了__enter__和__exit__，用于生成简便的with语句
# 如with open就可以用contextmanager实现
@contextmanager
def _patch(self):
    #获取对应local的实现类
    impl = object.__getattribute__(self, '_local__impl')
    try:
        # 获取impl在local中生成的dict(impl.create_dict())
        dct = impl.get_dict()
    except KeyError:
        dct = impl.create_dict()
        args, kw = impl.localargs
        self.__init__(*args, **kw)
    with impl.locallock:
        # 注意此处不能写self.__dict__ = dct,因为__dict__不可写
        # 所以只能使用object的set方法进行初始化
        object.__setattr__(self, '__dict__', dct)
        # 生成器等待执行结果
        yield
```
通过上面的分析，大致可以知道，本地线程是通过加锁进行隔离的，这是flask实现的多线程的基础。  
那么问题来了，python里面是有协程的，local能否实现协程的隔离呢？答案是否。那么，该怎么实现对协程的支持呢？  
请看Local类的源代码：
```python
# 此处导入便实现了协程的支持，如果导入getcurrent成功便支持协程，否则只支持多线程
try:
    from greenlet import getcurrent as get_ident
except ImportError:
    try:
        from thread import get_ident
    except ImportError:
        from _thread import get_ident

class Local(object):
    # 限制Local的属性
    __slots__ = ('__storage__', '__ident_func__')
    
    # 初始化Local的属性
    def __init__(self):
        # __storage__的格式为：{ID:{name:value},}
        # __storage__实际存储的值为：{ID:{'stack':[RequestContext(),],}
        object.__setattr__(self, '__storage__', {})
        # __ident_func__记录协程/线程的唯一ID
        object.__setattr__(self, '__ident_func__', get_ident)

    def __iter__(self):
        # Local可迭代
        return iter(self.__storage__.items())

    def __call__(self, proxy):
        """Create a proxy for a name."""
        return LocalProxy(self, proxy)

    def __release_local__(self):
        # 释放协程/线程
        self.__storage__.pop(self.__ident_func__(), None)
    
    # get方法，获取协程/线程的信息
    def __getattr__(self, name):
        try:
            return self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)
    # set方法，保存协程/线程信息
    def __setattr__(self, name, value):
        ident = self.__ident_func__()
        storage = self.__storage__
        try:
            storage[ident][name] = value
        except KeyError:
            storage[ident] = {name: value}
    # delete方法, 删除协程/线程信息
    def __delattr__(self, name):
        try:
            del self.__storage__[self.__ident_func__()][name]
        except KeyError:
            raise AttributeError(name)
```
其实无论线程还是协程，最重要的是唯一ID,只要获取并保存了唯一ID,就可获取相应的信息，从而执行相应的程序。  