import threading
from flask import signals

from flask import Flask, request
from flask import views

from bp import bp

app = Flask(__name__)

threading.local()


@app.before_first_request
def before_first_request():
    print("进行第一次请求之前的处理")


@app.url_value_preprocessor
def url_value_preprocessor(endpoint, values):
    print("url预处理", endpoint, values)


@app.before_request
def before_request():
    print("进行请求之前的处理")


def func(*args, **kwargs):
    print("信号机制触发")


signals.request_started.connect(func)


@app.route("/<id>", methods=["GET"], endpoint="in")
def index(id):
    print("hello,index" + str(id))
    return "hello"


def greeting():
    return "你好"


app.add_url_rule("/greet", endpoint="greeting", methods=["GET"], view_func=greeting)


class HelloView(views.MethodView):
    def __init__(self):
        self.hello = "hello"

    decorators = []

    def get(self):
        print(request)
        print(self.__dict__)
        return "hello world"


app.add_url_rule("/hello", view_func=HelloView.as_view(name="hello"))


@app.after_request
def after_request(*args, **kwargs):
    print("app中第一个请求之后的处理")


@app.after_request
def after_request2(*args, **kwargs):
    print("app中第二个请求之后的处理")


if __name__ == '__main__':
    app.register_blueprint(bp)
    app.run(port=8080)
