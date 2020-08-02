from functools import partial


def func(a, b, c, d):
    print(a, b, c, d)


# 偏函数就是通过partial构造一个函数partial_func
# 执行partial_func时，实际上是执行func函数，只是参数分开两次传递
# 第一次是在生成偏函数时，给func传递了参数
# 第二次是在调用偏函数时给func传递了剩下的参数
partial_func = partial(func, 1, 2)

partial_func(3, 4)

# 结果为：
# 控制台打印 1 2 3 4
