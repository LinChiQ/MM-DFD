from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_initial_admin(apps, schema_editor):
    """
    创建初始管理员用户
    用户名: admin
    密码: admin
    """
    User = apps.get_model('users', 'User')
    
    # 检查admin用户是否已存在
    if not User.objects.filter(username='admin').exists():
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=make_password('admin123456'),  # 设置密码为admin123456
            is_superuser=True,
            is_staff=True,
            is_active=True,
            is_admin=True,
            admin_role='super'
        )
        admin_user.save()
        print("已创建超级管理员账号admin")


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # 确保这个依赖正确指向你的上一个迁移
    ]

    operations = [
        migrations.RunPython(create_initial_admin),
    ] 