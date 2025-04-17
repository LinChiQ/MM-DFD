"""
检测应用模型定义
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class Detection(models.Model):
    """
    新闻检测记录模型
    """
    # 检测状态常量
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, _('待处理')),
        (STATUS_PROCESSING, _('处理中')),
        (STATUS_COMPLETED, _('已完成')),
        (STATUS_FAILED, _('失败')),
    ]
    
    # 检测结果常量
    RESULT_FAKE = 'fake'
    RESULT_REAL = 'real'
    RESULT_UNKNOWN = 'unknown'
    
    RESULT_CHOICES = [
        (RESULT_FAKE, _('虚假')),
        (RESULT_REAL, _('真实')),
        (RESULT_UNKNOWN, _('未知')),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='detections',
        verbose_name=_('用户')
    )
    
    title = models.CharField(_('新闻标题'), max_length=255)
    content = models.TextField(_('新闻内容'))
    
    # 图像存储路径
    image = models.ImageField(_('新闻图像'), upload_to='news_images/%Y/%m/%d/', blank=True, null=True)
    
    # 检测状态与结果
    status = models.CharField(
        _('检测状态'), 
        max_length=20, 
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )
    
    result = models.CharField(
        _('检测结果'), 
        max_length=20, 
        choices=RESULT_CHOICES,
        default=RESULT_UNKNOWN
    )
    
    # 置信度分数 (0-1范围内的浮点数)
    confidence_score = models.FloatField(_('置信度'), default=0.0)
    
    # 详细分析结果 (JSON格式存储)
    analysis_result = models.JSONField(_('分析结果'), blank=True, null=True)
    
    # 检测任务创建和完成时间
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    completed_at = models.DateTimeField(_('完成时间'), blank=True, null=True)
    
    # 检测错误信息
    error_message = models.TextField(_('错误信息'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('检测记录')
        verbose_name_plural = _('检测记录')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['result']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_result_display()}"
    
    def is_completed(self):
        """
        检查检测是否已完成
        """
        return self.status == self.STATUS_COMPLETED
    
    def is_fake(self):
        """
        检查新闻是否被判断为虚假
        """
        return self.result == self.RESULT_FAKE
    
    def is_real(self):
        """
        检查新闻是否被判断为真实
        """
        return self.result == self.RESULT_REAL
