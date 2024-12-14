from datetime import datetime

from django.db import models


# Create your models here.
class Counters(models.Model):
    id = models.AutoField
    count = models.IntegerField(max_length=11, default=0)
    createdAt = models.DateTimeField(default=datetime.now(), )
    updatedAt = models.DateTimeField(default=datetime.now(),)
    subscribe = models.BooleanField(default=False, verbose_name="订阅")
    def __str__(self):
        return f"计数: {self.count} - {'已订阅' if self.subscribe else '未订阅'}"

    class Meta:
        db_table = 'Counters'  # 数据库表名