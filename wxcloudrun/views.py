import json
import logging

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from wxcloudrun.models import Counters, WeChatUser
from django.views.decorators.csrf import csrf_exempt
import traceback

logger = logging.getLogger('log')

def wechat_user_view(request):
    if request.method == 'GET':
        try:
            target_openid = '18813421705'
            
            # 检查是否存在指定的 openid
            user_exists = WeChatUser.objects.filter(openid=target_openid).exists()
            
            if not user_exists:
                # 如果不存在，则创建该用户
                new_user = WeChatUser.objects.create(
                    openid=target_openid,
                    is_subscribed=True  # 根据需求设置默认值
                )
                logger.info(f"Created new WeChatUser with openid={target_openid}")
            
            # 获取所有 WeChatUser 实例，并选择需要的字段
            users = WeChatUser.objects.values('openid', 'last_access_time', 'is_subscribed')
            users_list = list(users)
            
            if not users_list:
                # 如果没有用户，返回提示信息
                return JsonResponse(
                    {'message': 'No WeChatUser entries found.'},
                    status=200
                )
            
            # 返回所有用户的数据
            return JsonResponse({'users': users_list}, status=200)
        
        except Exception as e:
            # 捕获异常，记录错误日志（可选）
            print(f"Error during GET request: {str(e)}")
            traceback.print_exc()
            # 返回错误信息作为网页响应
            return HttpResponse(
                f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>",
                status=500
            )
    
    elif request.method == 'POST':
        try:
            # 清空 WeChatUser 表中的所有数据
            WeChatUser.objects.all().delete()
            # 返回成功信息
            return HttpResponse(
                "<h1>Success</h1><p>All WeChatUser entries have been deleted.</p>",
                status=200
            )
        
        except Exception as e:
            # 捕获异常，记录错误日志（可选）
            print(f"Error during POST request: {str(e)}")
            traceback.print_exc()
            # 返回错误信息作为网页响应
            return HttpResponse(
                f"<h1>500 Internal Server Error</h1><p>{str(e)}</p>",
                status=500
            )
    
    else:
        # 不支持的 HTTP 方法
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
