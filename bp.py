from flask import Blueprint, jsonify, make_response,request

bp = Blueprint("bp", __name__, url_prefix="/bp")


@bp.after_request
def after_request(response):
    print("蓝图中的第一个after_request函数")
    return make_response(response)


@bp.after_request
def after_request2(response):
    print("蓝图中第二个after_request函数")
    # after_request必须要返回Response对象
    return make_response(response)


@bp.route("/first")
def test_bp():
    print("hello,bp")
    return make_response("hello,bp")
