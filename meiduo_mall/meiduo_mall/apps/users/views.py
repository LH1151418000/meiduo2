from django.shortcuts import render
from django.views import View
from users.models import User
from django import http
from django_redis import get_redis_connection
from django.contrib.auth import login, logout
import json
import re
import logging

# Create your views here.
logger = logging.getLogger('django')


class UsernameCountView(View):

    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '数据读取错误'})
        return http.JsonResponse({'code': 0, 'errmsg': 'ok', 'count': count})


class MobileCountView(View):

    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '数据读取错误'})
        return http.JsonResponse({'code': 0, 'errmsg': 'ok', 'count': count})


class RegisterView(View):

    def post(self, request):
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
        password2 = data.get('password2')
        mobile = data.get('mobile')
        sms_code = data.get('sms_code')
        allow = data.get('allow')

        if not ([username, password, password2, mobile, sms_code]):
            return http.JsonResponse({
                'code': 400,
                'errmsg': '缺少必传参数'
            })
        if username.isdigit():
            return http.JsonResponse({
                'code': 400,
                'errmsg': '用户名不能为全数字'
            })
        print("用户名：", username, type(username))
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({
                'code': 400,
                'errmsg': '用户名格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9_-]{8,20}$', password):
            return http.JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            })
        if password != password2:
            return http.JsonResponse({
                'code': 400,
                'errmsg': '两次密码不一致'
            })
        if not mobile.isdigit():
            return http.JsonResponse({
                'code': 400,
                'errmsg': '手机号格式错误'
            })
        if not re.match(r'^1[3-9][0-9]{9}$', mobile):
            return http.JsonResponse({
                'code': 400,
                'errmsg': '手机号格式错误'
            })
        conn = get_redis_connection('verify_code')
        try:
            redis_code = conn.get('sms_%s' % mobile).decode()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': 400,
                'errmsg': '短信验证码已过期'
            })
        if redis_code != sms_code:
            return http.JsonResponse({
                'code': 400,
                'errmsg': '短信验证码错误'
            })
        if allow == False:
            return http.JsonResponse({
                'code': 400,
                'errmsg': '未勾选协议'
            })
        try:
            user = User.objects.create_user(username=username,
                                     password=password,
                                     mobile=mobile)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({
                'code': 400,
                'errmsg': '数据库写入错误'
            })

        login(request, user)

        return http.JsonResponse({
            'code': 200,
            'errmsg': '注册成功'
        })
