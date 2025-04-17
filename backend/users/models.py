"""
用户模型定义
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """
    自定义用户模型
    """
    email = models.EmailField(_('邮箱地址'), unique=True)
    phone = models.CharField(_('手机号码'), max_length=15, blank=True, null=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_('个人简介'), blank=True, null=True)
    
    # 用于记录检测历史统计
    total_detections = models.PositiveIntegerField(_('检测总次数'), default=0)
    fake_detections = models.PositiveIntegerField(_('虚假新闻检测次数'), default=0)
    real_detections = models.PositiveIntegerField(_('真实新闻检测次数'), default=0)
    
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        """
        返回用户全名
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.username
    
    def update_detection_stats(self, is_fake):
        """
        更新用户的检测统计
        """
        self.total_detections += 1
        if is_fake:
            self.fake_detections += 1
        else:
            self.real_detections += 1
        self.save(update_fields=['total_detections', 'fake_detections', 'real_detections'])
