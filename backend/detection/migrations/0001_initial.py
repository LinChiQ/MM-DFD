# Generated by Django 4.2.9 on 2025-04-19 05:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Detection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='新闻标题')),
                ('content', models.TextField(verbose_name='新闻内容')),
                ('image', models.ImageField(blank=True, null=True, upload_to='news_images/%Y/%m/%d/', verbose_name='新闻图像')),
                ('status', models.CharField(choices=[('pending', '待处理'), ('processing', '处理中'), ('completed', '已完成'), ('failed', '失败')], default='pending', max_length=20, verbose_name='检测状态')),
                ('result', models.CharField(choices=[('fake', '虚假'), ('real', '真实'), ('unknown', '未知')], default='unknown', max_length=20, verbose_name='检测结果')),
                ('confidence_score', models.FloatField(default=0.0, verbose_name='置信度')),
                ('analysis_result', models.JSONField(blank=True, null=True, verbose_name='分析结果')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='完成时间')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='错误信息')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='detections', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '检测记录',
                'verbose_name_plural': '检测记录',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['user', 'created_at'], name='detection_d_user_id_005ef3_idx'), models.Index(fields=['status'], name='detection_d_status_c8cd09_idx'), models.Index(fields=['result'], name='detection_d_result_6448a8_idx')],
            },
        ),
    ]
