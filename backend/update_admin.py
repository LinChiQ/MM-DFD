#!/usr/bin/env python
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError

User = get_user_model()

def update_admin_user():
    """更新或创建管理员用户"""
    
    # 尝试查找用户名为root的用户
    try:
        user = User.objects.get(username='root')
        # 更新现有用户
        user.is_staff = True
        user.is_superuser = True
        user.set_password('root123456')
        user.save()
        print(f"已将用户 '{user.username}' 设置为管理员并更新密码为 'root123456'")
    except User.DoesNotExist:
        # 创建新的超级用户
        User.objects.create_superuser('root', 'admin@example.com', 'root123456')
        print("已创建新的管理员账号 'root'，密码为 'root123456'")
    
    # 验证设置
    user = User.objects.get(username='root')
    print(f"用户状态: is_staff={user.is_staff}, is_superuser={user.is_superuser}")

if __name__ == '__main__':
    update_admin_user() 