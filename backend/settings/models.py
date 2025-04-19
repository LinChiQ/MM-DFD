from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemSettings(models.Model):
    """
    系统设置模型，用于存储全局设置
    使用键值对方式存储设置项
    """
    key = models.CharField(_('设置键名'), max_length=50, unique=True)
    value = models.TextField(_('设置值'))
    value_type = models.CharField(_('值类型'), max_length=20, choices=[
        ('string', _('字符串')),
        ('integer', _('整数')),
        ('float', _('浮点数')),
        ('boolean', _('布尔值')),
        ('json', _('JSON对象'))
    ], default='string')
    description = models.CharField(_('描述'), max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('系统设置')
        verbose_name_plural = _('系统设置')
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"
    
    @classmethod
    def get_value(cls, key, default=None):
        """
        获取指定键的设置值
        
        Args:
            key: 设置键名
            default: 默认值，如果设置不存在返回此值
            
        Returns:
            根据值类型转换后的设置值
        """
        try:
            setting = cls.objects.get(key=key)
            if setting.value_type == 'integer':
                return int(setting.value)
            elif setting.value_type == 'float':
                return float(setting.value)
            elif setting.value_type == 'boolean':
                return setting.value.lower() in ('true', 'yes', '1')
            elif setting.value_type == 'json':
                import json
                return json.loads(setting.value)
            else:
                # 字符串类型
                return setting.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_value(cls, key, value, value_type=None, description=None):
        """
        设置指定键的值
        
        Args:
            key: 设置键名
            value: 设置值
            value_type: 值类型，如果为None则自动推断
            description: 设置描述
            
        Returns:
            设置实例
        """
        # 自动推断值类型
        if value_type is None:
            if isinstance(value, bool):
                value_type = 'boolean'
                value = str(value).lower()
            elif isinstance(value, int):
                value_type = 'integer'
                value = str(value)
            elif isinstance(value, float):
                value_type = 'float'
                value = str(value)
            elif isinstance(value, (dict, list)):
                value_type = 'json'
                import json
                value = json.dumps(value)
            else:
                value_type = 'string'
                value = str(value)
        
        # 获取或创建设置
        setting, created = cls.objects.update_or_create(
            key=key,
            defaults={
                'value': value,
                'value_type': value_type
            }
        )
        
        # 如果提供了描述，则更新
        if description is not None:
            setting.description = description
            setting.save()
        
        return setting
