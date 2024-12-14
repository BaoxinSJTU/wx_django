from datetime import datetime

from django.db import models


# Create your models here.
class Counters(models.Model):
    id = models.AutoField
    count = models.IntegerField(max_length=11, default=0)
    createdAt = models.DateTimeField(default=datetime.now(), )
    updatedAt = models.DateTimeField(default=datetime.now(),)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'Counters'  # 数据库表名

class State(models.Model):
    id = models.AutoField
    state = models.BooleanField(default=False, verbose_name="状态")

    def __str__(self):
        return f"{'激活' if self.state else '未激活'}"

    class Meta:
        verbose_name = "状态"
        verbose_name_plural = "状态列表"
