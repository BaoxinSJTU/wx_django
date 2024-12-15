import json
import logging

from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from wxcloudrun.models import Counters, WeChatUser
from django.views.decorators.csrf import csrf_exempt
import traceback
from django.core.cache import cache
from django.conf import settings
import requests

logger = logging.getLogger('log')
def get_wechat_access_token():
    """
    获取微信的Access Token，并缓存以减少请求次数。
    """
    access_token = cache.get('wechat_access_token')
    if access_token:
        return access_token

    appid = settings.WECHAT_APPID
    secret = settings.WECHAT_SECRET
    url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}"

    try:
        response = requests.get(url)
        data = response.json()
        if 'access_token' in data:
            access_token = data['access_token']
            expires_in = data.get('expires_in', 7200)  # 默认7200秒
            cache.set('wechat_access_token', access_token, expires_in - 200)  # 提前200秒过期
            logger.info(f"get access_token: {access_token}")
            return access_token
        else:
            logger.error(f"Failed to obtain access token: {data}")
            return None
    except Exception as e:
        logger.error(f"Exception while obtaining access token: {str(e)}", exc_info=True)
        return None
def send_wechat_template_message(openid, template_id, data, url=None, mini_program=None):
    """
    发送微信模板消息。

    参数:
        openid (str): 接收者的openid。
        template_id (str): 模板ID。
        data (dict): 模板数据。
        url (str, optional): 模板跳转链接。
        mini_program (dict, optional): 小程序页面信息。

    返回:
        dict: 微信API的响应。
    """
    access_token = get_wechat_access_token()
    if not access_token:
        logger.error("Cannot send template message without access token.")
        return None

    send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    payload = {
        "touser": openid,
        "template_id": template_id,
        "data": data
    }

    try:
        response = requests.post(send_url, json=payload)

        return response.json()
    except Exception as e:
        logger.error(f"Exception while sending template message: {str(e)}", exc_info=True)
        return None
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
            logger.info(body)
            # 检查是否存在'openid'字段
            if 'openid' not in body:
                logger.error('Missing "openid" field.')
                return JsonResponse(
                    {'error': 'Missing "openid" field.'},
                    status=400
                )

            # 检查是否存在'is_subscribed'字段
            if 'is_subscribed' not in body:
                logger.error('Missing "is_subscribed" field.')
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

            template_id = "qrMCaZ15_RvZ2QqSbaGhn1JtO8LsL1fWxApJDUvGHmI"
            
            template_data = {
                "date1": {
                    "value": "2019年10月15日"
                },
                "phrase2": {
                    "value": "东莞市"
                },
                "phrase3": {
                    "value": "晴"
                },
                "character_string4": {
                    "value": "25~28°"
                },
                "thing5": {
                    "value": "温度较低，请注意保暖哦"
                }
            }
            send_result = send_wechat_template_message(
                openid=openid,
                template_id=template_id,
                data=template_data,
                url='https://django-b65k-131657-9-1333067814.sh.run.tcloudbase.com/',  # 可选，点击模板消息后跳转的链接
                mini_program={
                    "appid": settings.WECHAT_APPID,  # 替换为您的小程序AppID
                    "pagepath": "path/to/page"  # 替换为小程序内的具体页面路径
                }
            )

            if send_result and send_result.get('errcode') == 0:
                logger.info(f"Template message sent successfully to {openid}.")
            else:
                logger.error(f"Failed to send template message: {send_result}")
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
