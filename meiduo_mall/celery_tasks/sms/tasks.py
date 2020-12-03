from ronglian_sms_sdk import SmsSDK
from celery_tasks.main import celery_app


# 创建发送短信任务
@celery_app.task(name="sms_send")
def sms_send(mobile, sms_code):
    sms = SmsSDK('8aaf0708723b53c901724954cb8c03f7', '01413ea023b7420dafe75c5ece801c51',
                 '8aaf070872499534017258fb6de10960')
    sms.sendMessage('1', mobile, (sms_code, 5))
    return sms
