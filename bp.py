from flask import Blueprint

bp = Blueprint("bp", __name__)


@bp.after_request
def after_request(*args, **kwargs):
    print("蓝图中的第一个after_request函数")


@bp.after_request
def after_request2(*args, **kwargs):
    print("蓝图中第二个after_request函数")


@bp.route("/bp")
def test_bp():
    return "hello,bp"
