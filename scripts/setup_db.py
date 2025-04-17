#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""
import os
import sys
import MySQLdb
import getpass
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 默认配置
DEFAULT_CONFIG = {
    'HOST': os.getenv('DATABASE_HOST', 'localhost'),
    'PORT': int(os.getenv('DATABASE_PORT', 3306)),
    'USER': os.getenv('DATABASE_USER', 'root'),
    'PASSWORD': os.getenv('DATABASE_PASSWORD', 'root'),
    'DB_NAME': os.getenv('DATABASE_NAME', 'mmdfd'),
    'CHARSET': 'utf8mb4'
}

def create_database(config):
    """创建数据库和用户"""
    try:
        # 连接到MySQL服务器
        conn = MySQLdb.connect(
            host=config['HOST'],
            port=config['PORT'],
            user=config['USER'],
            password=config['PASSWORD']
        )
        cursor = conn.cursor()
        
        # 创建数据库
        print(f"创建数据库: {config['DB_NAME']}...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['DB_NAME']} DEFAULT CHARACTER SET {config['CHARSET']}")
        
        # 创建用户并授权
        if config['USER'] != 'root':
            cursor.execute(f"CREATE USER IF NOT EXISTS '{config['USER']}'@'%' IDENTIFIED BY '{config['PASSWORD']}'")
            cursor.execute(f"GRANT ALL PRIVILEGES ON {config['DB_NAME']}.* TO '{config['USER']}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
        
        print("数据库初始化成功！")
        conn.close()
        return True
    except MySQLdb.Error as e:
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    print("==== 多模态深度学习社交媒体虚假新闻检测系统 - 数据库初始化 ====")
    
    # 使用默认配置或询问用户输入
    config = DEFAULT_CONFIG.copy()
    if '--interactive' in sys.argv:
        config['HOST'] = input(f"MySQL主机地址 [{config['HOST']}]: ") or config['HOST']
        port_input = input(f"MySQL端口 [{config['PORT']}]: ") or str(config['PORT'])
        config['PORT'] = int(port_input)
        config['USER'] = input(f"MySQL用户名 [{config['USER']}]: ") or config['USER']
        config['PASSWORD'] = getpass.getpass(f"MySQL密码: ") or config['PASSWORD']
        config['DB_NAME'] = input(f"数据库名称 [{config['DB_NAME']}]: ") or config['DB_NAME']
    
    # 创建数据库
    success = create_database(config)
    
    # 将配置保存到.env文件供Django使用
    if success and '--save-env' in sys.argv:
        with open('../backend/.env', 'w', encoding='utf-8') as f:
            f.write(f"DATABASE_HOST={config['HOST']}\n")
            f.write(f"DATABASE_PORT={config['PORT']}\n")
            f.write(f"DATABASE_NAME={config['DB_NAME']}\n")
            f.write(f"DATABASE_USER={config['USER']}\n")
            f.write(f"DATABASE_PASSWORD={config['PASSWORD']}\n")
        print("配置已保存到 backend/.env 文件")

if __name__ == "__main__":
    main() 