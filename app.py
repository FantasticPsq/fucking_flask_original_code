import threading

from flask import Flask
from flask import views

app = Flask(__name__)

threading.local()


@app.route("/", methods=["POST"], endpoint="in")
def index():
    return "hello"


def greeting():
    return "你好"


app.add_url_rule("/greet", endpoint="greeting", methods=["GET"], view_func=greeting)


class HelloView(views.MethodView):
    def __init__(self):
        self.hello = "hello"
    decorators = []

    def get(self):
        print(self.__dict__)
        return "hello world"



app.add_url_rule("/hello", view_func=HelloView.as_view(name="hello"))
if __name__ == '__main__':
    app.run(port=8080)
