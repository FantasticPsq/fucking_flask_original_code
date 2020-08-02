### 三.flask请求上下文 request_context ###
1.首先我们大致描述一下flask请求的执行流程：  
```text
第一阶段，请求开始,初始化：
app.run() -> run_simple(host, port, self, **options) -> app.__call__(environ, start_response)  
-> app.wsgi_app(environ, start_response) -> ctx=self.request_context(environ) -> ctx=RequestContext()  
-> RequestContext.__init__()-> request=app.request_class() -> request_class = Request 
-> ctx.push() -> _request_ctx_stack=LocalStack() -> LocalStack.__init__() -> self._local=Local()
-> _request_ctx_stack.push(self) -> LocalStack.push(obj) -> Local.__setattr__() 

第二阶段，请求处理：
response = self.full_dispatch_request() -> self.try_trigger_before_first_request_functions() -> rv = self.preprocess_request() 
-> rv = self.dispatch_request() -> rv = self.preprocess_request() -> self.finalize_request(rv) ->
-> response = self.process_response(response) -> self.view_functions[rule.endpoint](**req.view_args)

第三阶段，请求结束：
ctx.auto_pop(error) -> _request_ctx_stack.pop()-> stack.pop()，一个请求完成后从stack中删除，注意stack是list。
```
流程是非常重要的，先把流程基本弄明白才可能把flask上下文搞清楚；  
接下来，源码分析请看：flask源码分析之请求上下文第一阶段

