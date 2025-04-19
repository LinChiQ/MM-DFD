import os
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from settings.models import SystemSettings

class Command(BaseCommand):
    help = '初始化系统设置'

    def handle(self, *args, **options):
        # 模型权重设置
        defaults = [
            {
                'key': 'local_model_weight',
                'value': '0.4',
                'value_type': 'float',
                'description': '本地模型权重'
            },
            {
                'key': 'llm_weight',
                'value': '0.6',
                'value_type': 'float',
                'description': 'LLM模型权重'
            },
            {
                'key': 'fake_threshold',
                'value': '0.65',
                'value_type': 'float',
                'description': '虚假新闻阈值'
            },
            {
                'key': 'real_threshold',
                'value': '0.35',
                'value_type': 'float',
                'description': '真实新闻阈值'
            }
        ]
        
        for setting in defaults:
            _, created = SystemSettings.objects.update_or_create(
                key=setting['key'],
                defaults={
                    'value': setting['value'],
                    'value_type': setting['value_type'],
                    'description': setting['description']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created setting: {setting['key']}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated existing setting: {setting['key']}"))
        
        self.stdout.write(self.style.SUCCESS('系统设置初始化完成')) 