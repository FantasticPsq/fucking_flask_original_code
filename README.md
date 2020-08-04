# fucking_flask_original_code
手撕flask源码   

想要看懂这些小文章，您需要掌握：
1. 基本的魔法方法：`__init__`,`__call__`,`__slots__`,`__setattr__`,`__getattr__`等
2. Python类和对象的基础知识，比如实例化对象时该调用类的哪个函数，对象再加括号该调用哪个函数等
3. 把握动态语言的特性，注意Python语言与其他语言的区别 
4. 封装思维，需要有很强的封装思维，该怎么封装以及封装的好处
5. 装饰器以及闭包，深浅拷贝等基础知识

建议您的观看次序为：  
1. [flask源码分析之路由本质](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E8%B7%AF%E7%94%B1%E6%9C%AC%E8%B4%A8.md)  
2. [flask源码分析之本地线程](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E6%9C%AC%E5%9C%B0%E7%BA%BF%E7%A8%8B.md) 
3. [flask源码分析之请求上下文基本流程](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E8%AF%B7%E6%B1%82%E4%B8%8A%E4%B8%8B%E6%96%87%E5%9F%BA%E6%9C%AC%E6%B5%81%E7%A8%8B.md)  
4. [flask源码分析之请求上下文第一阶段](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E8%AF%B7%E6%B1%82%E4%B8%8A%E4%B8%8B%E6%96%87%E7%AC%AC%E4%B8%80%E9%98%B6%E6%AE%B5.md)
5. [flask源码分析之请求上下文第二阶段](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E8%AF%B7%E6%B1%82%E4%B8%8A%E4%B8%8B%E6%96%87%E7%AC%AC%E4%BA%8C%E9%98%B6%E6%AE%B5.md) 
6. [flask源码分析之请求上下文第三阶段](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8B%E8%AF%B7%E6%B1%82%E4%B8%8A%E4%B8%8B%E6%96%87%E7%AC%AC%E4%B8%89%E9%98%B6%E6%AE%B5.md)
7. [flask源码分析之request对象](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8Brequest%E5%AF%B9%E8%B1%A1.md)
8. [flask源码分析之session对象](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8Bsession%E5%AF%B9%E8%B1%A1.md)
9. [flask源码分析之SQLAlchemy数据库连接池](https://github.com/FantasticPsq/fucking_flask_original_code/blob/master/flask%E6%BA%90%E7%A0%81%E5%88%86%E6%9E%90%E4%B9%8BSQLAlchemy%E6%95%B0%E6%8D%AE%E5%BA%93%E8%BF%9E%E6%8E%A5%E6%B1%A0.md)

如有错误，请发送邮件(1636538091@qq.com)或私下联系告知，感激不尽。