from django.shortcuts import render
from meiduo_mall.libs.captcha.captcha import captcha
from django.http import HttpResponse, JsonResponse
from django_redis import get_redis_connection
from django.views import View
# from ronglian_sms_sdk import SmsSDK
from random import randint
from celery_tasks.sms.tasks import sms_send
import logging

# Create your views here.
logger = logging.getLogger('django')

class ImageCodeView(View):
    # 1.导入captcha生成验证码和图片
    # 2.将前端返回的uuid及生成的验证码存储到redis， 目的为了在注册时对验证码进行判断
    # 3.返回前端需要对验证码图片

    def get(self, request, uuid):

        # 获取生成的图形验证码及图片
        text, img = captcha.generate_captcha()
        # 连接redis缓存数据库
        conn = get_redis_connection('verify_code')
        a = uuid
        # 刷新图形验证码后删除原有图形验证码
        conn.delete("img_%s" % a)
        # 写入缓存
        conn.setex("img_%s" % uuid, 300, text)
        # 响应数据
        return HttpResponse(img, content_type="image/jpg")


class SmsCodeView(View):
    def get(self, request, mobile):
        print(mobile)
        # 获取前端输入的--图形验证
        img_code = request.GET.get('image_code')
        # 获取uuid
        uuid = request.GET.get('image_code_id')
        print(img_code, uuid)

        # 判断是否输入图形验证及uuid是否正确
        if not ([img_code, uuid]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数!'})

        # 连接redis
        conn = get_redis_connection('verify_code')
        # 获取缓存中图形验证码
        try:
            redis_img = conn.get("img_%s" % uuid).decode()
        except Exception as e:
            logger.error(e)
            # 如果缓存中没有验证码
            return JsonResponse({'code': 400, 'errmsg': '图形验证码已过期!'})

        # 未防止用户恶意刷图，删除缓存中验证码
        try:
            conn.delete("img_%s" % uuid)
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400, 'errmsg': '数据已被删除!'})

        # 判断用户输入的图形验证码是否与缓存中验证码一致
        if img_code.upper() != redis_img.upper():
            return JsonResponse({'code': 400, 'errmsg': '图形验证码不一致!'})

        # 判断缓存中是否有 占位 短信验证码
        if not conn.get("sms_S_%s" % mobile):
            # sms = SmsSDK('8aaf0708723b53c901724954cb8c03f7', '01413ea023b7420dafe75c5ece801c51',
            #              '8aaf070872499534017258fb6de10960')
            # 生成6位数验证码
            code = randint(100000, 999999)
            print(code)

            p = conn.pipeline()
            # 手机验证码写入缓存
            p.setex("sms_%s" % mobile, 300, code)
            # 手机验证码1分钟 占位 写入缓存
            p.setex("sms_S_%s" % mobile, 60, 1)
            p.execute()
            # 发送验证码
            # sms.sendMessage('1', mobile, (code, 5))
            # sms_send(mobile, code)

            return JsonResponse({
                'code': 200,
                'errmsg': 'ok'
            })
        else:
            # 如果缓存中有 占位 短信验证码
            return JsonResponse({
                'code': 400,
                'errmsg': '请勿重复发送',
            })
