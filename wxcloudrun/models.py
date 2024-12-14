from datetime import datetime

from django.db import models


# Create your models here.
class Counters(models.Model):
    id = models.AutoField
    count = models.IntegerField(max_length=11, default=0)
    createdAt = models.DateTimeField(default=datetime.now(), )
    updatedAt = models.DateTimeField(default=datetime.now(),)
    subscribe = models.BooleanField(default=False, verbose_name="订阅")
    test = models.BooleanField(default=True, verbose_name="测试用")
    def __str__(self):
        return f"计数: {self.count} - {'已订阅' if self.subscribe else '未订阅'}"

    class Meta:
        db_table = 'Counters'  # 数据库表名

class WeChatUser(models.Model):
    openid = models.CharField(max_length=100, unique=True, verbose_name="微信用户 OpenID")
    last_access_time = models.DateTimeField(auto_now=True, verbose_name="上一次访问时间")
    is_subscribed = models.BooleanField(default=False, verbose_name="是否订阅")

    def __str__(self):
        return f"OpenID: {self.openid} - {'已订阅' if self.is_subscribed else '未订阅'}"

    class Meta:
        db_table = 'WeChatUser'
        verbose_name = "微信用户"
        verbose_name_plural = "微信用户列表"