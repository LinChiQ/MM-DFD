"""
用户信号处理
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    用户创建后的处理
    """
    if created:
        # 可以在这里添加自定义的用户创建后操作
        pass
