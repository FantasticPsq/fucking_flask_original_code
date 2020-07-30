from flask import Flask
from flask import views

app = Flask(__name__)


@app.route("/", methods=["POST"], endpoint="in")
def index():
    return "hello"


def greeting():
    return "你好"


app.add_url_rule("/greet", endpoint="greeting", methods=["GET"], view_func=greeting)


class HelloView(views.MethodView):
    decorators = []

    def get(self):
        return "hello world"


app.add_url_rule("/hello", view_func=HelloView.as_view(name="hello"))
if __name__ == '__main__':
    app.run(port=8080)
