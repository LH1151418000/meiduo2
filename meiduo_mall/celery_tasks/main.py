from celery import Celery


# 创建celery对象
celery_app = Celery()
# 加载中间人配置（消息队列）
celery_app.config_from_object("celery_tasks.config")
# 自动获取任务
celery_app.autodiscover_tasks([
    "celery_tasks.sms",

])
