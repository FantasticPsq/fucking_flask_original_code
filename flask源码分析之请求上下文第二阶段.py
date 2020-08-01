from flask import signals


def func(*args, **kwargs):
    print("hello")


# 向request_started信号中注册func函数
signals.request_started.connect(func)

# 调用send方法触发request_started信号
signals.request_started.send()
