import json
import logging

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from wxcloudrun.models import Counters, WeChatUser
from django.views.decorators.csrf import csrf_exempt
import traceback

logger = logging.getLogger('log')

def wechat_user_view(request, _):
    if request.method == 'GET':
        try:
            # 获取所有 WeChatUser 实例
            users = WeChatUser.objects.all()

            if not users.exists():
                # 如果没有用户，返回提示信息
                return JsonResponse(
                    {'message': 'No WeChatUser entries found.'},
                    status=200
                )

            # 序列化所有用户的数据
            users_list = [{
                'openid': user.openid,
                'last_access_time': user.last_access_time.isoformat(),  # 将 datetime 转换为字符串
                'is_subscribed': user.is_subscribed
            } for user in users]

            # 返回所有用户的数据
            return JsonResponse({'users': users_list}, status=200)

        except Exception as e:
            # 记录错误日志
            logger.error(f"Error during GET request: {str(e)}", exc_info=True)
            # 返回错误信息作为网页响应
            return HttpResponse(
                "<h1>500 Internal Server Error</h1><p>An error occurred while processing your request.</p>",
                status=500
            )

    elif request.method == 'POST':
        try:
            # 解码请求体为UTF-8字符串
            body_unicode = request.body.decode('utf-8')
            # 将JSON字符串解析为Python字典
            body = json.loads(body_unicode)

            # 检查是否存在'openid'字段
            if 'openid' not in body:
                return JsonResponse(
                    {'error': 'Missing "openid" field.'},
                    status=400
                )

            # 检查是否存在'is_subscribed'字段
            if 'is_subscribed' not in body:
                return JsonResponse(
                    {'error': 'Missing "is_subscribed" field.'},
                    status=400
                )

            # 获取'openid'和'is_subscribed'的值
            openid = body['openid']
            is_subscribed = body['is_subscribed']

            # 使用get_or_create方法获取或创建WeChatUser实例
            user, created = WeChatUser.objects.get_or_create(openid=openid)
            # 更新is_subscribed字段
            user.is_subscribed = is_subscribed
            user.save()

            # 根据是否创建了新用户，返回不同的提示信息
            if created:
                return JsonResponse(
                    {'message': 'User created and subscribed status updated.'},
                    status=201
                )
            else:
                return JsonResponse(
                    {'message': 'User subscribed status updated.'},
                    status=200
                )

        except Exception as e:
            # 记录错误日志
            logger.error(f"Error during POST request: {str(e)}", exc_info=True)
            # 返回错误信息作为网页响应
            return HttpResponse(
                "<h1>500 Internal Server Error</h1><p>An error occurred while processing your request.</p>",
                status=500
            )

    else:
        # 处理不支持的 HTTP 方法
        return HttpResponse(
            "<h1>405 Method Not Allowed</h1><p>Unsupported HTTP method.</p>",
            status=405
        )
def index(request, _):
    """
    获取主页

     `` request `` 请求对象
    """

    return render(request, 'index.html')


def counter(request, _):
    """
    获取当前计数

     `` request `` 请求对象
    """

    rsp = JsonResponse({'code': 0, 'errorMsg': ''}, json_dumps_params={'ensure_ascii': False})
    if request.method == 'GET' or request.method == 'get':
        rsp = get_count()
    elif request.method == 'POST' or request.method == 'post':
        rsp = update_count(request)
    else:
        rsp = JsonResponse({'code': -1, 'errorMsg': '请求方式错误'},
                            json_dumps_params={'ensure_ascii': False})
    logger.info('response result: {}'.format(rsp.content.decode('utf-8')))
    return rsp


def get_count():
    """
    获取当前计数
    """
    try:
        data = Counters.objects.get(id=1)
    except Counters.DoesNotExist:
        return JsonResponse({'code': 0, 'data': 0, 'Subscribe': "Object Not Exist!"},
                    json_dumps_params={'ensure_ascii': False})
    return JsonResponse({'code': 0, 'data': data.count, 'enabled': data.subscribe, "test": data.test},
                        json_dumps_params={'ensure_ascii': False})


def update_count(request):
    """
    更新计数，自增或者清零

    `` request `` 请求对象
    """

    logger.info('update_count req: {}'.format(request.body))

    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)

    if 'action' not in body:
        return JsonResponse({'code': -1, 'errorMsg': '缺少action参数'},
                            json_dumps_params={'ensure_ascii': False})

    if body['action'] == 'inc':
        try:
            data = Counters.objects.get(id=1)
        except Counters.DoesNotExist:
            data = Counters()
        data.id = 1
        data.count += 1
        data.save()
        return JsonResponse({'code': 0, "data": data.count},
                    json_dumps_params={'ensure_ascii': False})
    elif body['action'] == 'clear':
        try:
            data = Counters.objects.get(id=1)
            data.delete()
        except Counters.DoesNotExist:
            logger.info('record not exist')
        return JsonResponse({'code': 0, 'data': 0},
                    json_dumps_params={'ensure_ascii': False})
    else:
        return JsonResponse({'code': -1, 'errorMsg': 'action参数错误'},
                    json_dumps_params={'ensure_ascii': False})
