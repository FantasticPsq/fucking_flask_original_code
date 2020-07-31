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
        # loval实例化时不能带参数（因为默认采用object的初始化方法），如果带了参数必须使用自己的初始化函数进行初始化
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
通过上面的分析，大致可以知道，本地线程是通过加锁进行隔离的，这是flask实现的多线程的基础。