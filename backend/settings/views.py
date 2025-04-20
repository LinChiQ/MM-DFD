from django.shortcuts import render
import os
import logging
import glob
from django.conf import settings as django_settings
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import SystemSettings
from .serializers import (
    SystemSettingsSerializer, ModelWeightsSerializer, 
    ApiConfigSerializer
)

logger = logging.getLogger(__name__)

# Create your views here.

# 权限类
class IsAdminUser(permissions.BasePermission):
    """
    只允许管理员访问的权限类
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

class SettingsViewSet(viewsets.ViewSet):
    """
    系统设置视图集
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    
    # 设置键名常量
    LOCAL_MODEL_WEIGHT = 'local_model_weight'
    LLM_WEIGHT = 'llm_weight'
    FAKE_THRESHOLD = 'fake_threshold'
    REAL_THRESHOLD = 'real_threshold'
    OPENROUTER_API_KEY = 'openrouter_api_key'
    USE_GPU = 'use_gpu'
    
    # 默认值
    DEFAULT_LOCAL_MODEL_WEIGHT = 0.4
    DEFAULT_LLM_WEIGHT = 0.6
    DEFAULT_FAKE_THRESHOLD = 0.65
    DEFAULT_REAL_THRESHOLD = 0.35
    
    @action(detail=False, methods=['get'])
    def model_weights(self, request):
        """
        获取模型权重设置
        """
        # 获取当前设置
        local_model_weight = SystemSettings.get_value(self.LOCAL_MODEL_WEIGHT, self.DEFAULT_LOCAL_MODEL_WEIGHT)
        llm_weight = SystemSettings.get_value(self.LLM_WEIGHT, self.DEFAULT_LLM_WEIGHT)
        fake_threshold = SystemSettings.get_value(self.FAKE_THRESHOLD, self.DEFAULT_FAKE_THRESHOLD)
        real_threshold = SystemSettings.get_value(self.REAL_THRESHOLD, self.DEFAULT_REAL_THRESHOLD)
        openrouter_api_key = os.environ.get('OPENROUTER_API_KEY', '')  # 从环境变量获取API密钥
        use_gpu = getattr(django_settings, 'DEVICE', '') == 'cuda'
        
        data = {
            'local_model_weight': local_model_weight,
            'llm_weight': llm_weight,
            'fake_threshold': fake_threshold,
            'real_threshold': real_threshold,
            'openrouter_api_key': openrouter_api_key,
            'use_gpu': use_gpu
        }
        
        return Response(data)
    
    @model_weights.mapping.post
    def update_model_weights(self, request):
        """
        更新模型权重设置
        """
        serializer = ModelWeightsSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            # 保存设置到数据库
            SystemSettings.set_value(
                self.LOCAL_MODEL_WEIGHT, 
                data['local_model_weight'], 
                'float',
                '本地模型权重'
            )
            SystemSettings.set_value(
                self.LLM_WEIGHT, 
                data['llm_weight'], 
                'float',
                'LLM模型权重'
            )
            SystemSettings.set_value(
                self.FAKE_THRESHOLD, 
                data['fake_threshold'], 
                'float',
                '虚假新闻阈值'
            )
            SystemSettings.set_value(
                self.REAL_THRESHOLD, 
                data['real_threshold'], 
                'float',
                '真实新闻阈值'
            )
            
            # 记录日志
            logger.info(
                f"更新模型权重设置: 本地模型={data['local_model_weight']}, LLM={data['llm_weight']}, "
                f"虚假阈值={data['fake_threshold']}, 真实阈值={data['real_threshold']}"
            )
            
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def logs(self, request):
        """
        获取系统日志
        """
        try:
            # 获取日志文件路径
            log_dir = getattr(django_settings, 'LOG_DIR', os.path.join(django_settings.BASE_DIR, 'logs'))
            log_files = glob.glob(os.path.join(log_dir, '*.log'))
            
            if not log_files:
                return Response({'logs': []})
            
            # 默认读取最新的日志文件
            latest_log = max(log_files, key=os.path.getmtime)
            
            # 读取日志文件内容
            log_entries = []
            with open(latest_log, 'r', encoding='utf-8', errors='replace') as f:
                for line in f.readlines()[-500:]:  # 只读取最后500行
                    try:
                        # 尝试解析日志行
                        # 实际格式示例: INFO 2025-04-19 18:39:39,699 basehttp "GET /static/admin/css/responsive.css HTTP/1.1" 200 18559
                        line = line.strip()
                        parts = line.split(' ', 3)  # 最多分割3次，得到级别、时间戳+日志源、消息
                        
                        if len(parts) >= 2:
                            level = parts[0]  # 第一部分是日志级别
                            
                            # 处理第二部分（时间戳）和第三部分（日志源）
                            if len(parts) >= 3:
                                # 时间戳通常是固定格式：YYYY-MM-DD HH:MM:SS,SSS
                                timestamp_parts = parts[1].split(' ', 1)
                                if len(timestamp_parts) == 1 and len(parts) >= 3:
                                    # 日期和时间可能被分开了
                                    date_part = parts[1]
                                    time_part = parts[2].split(' ', 1)[0]
                                    timestamp = f"{date_part} {time_part}"
                                    
                                    # 日志源在时间后面
                                    log_source_parts = parts[2].split(' ', 1)
                                    if len(log_source_parts) > 1:
                                        log_source = log_source_parts[1]
                                        message = parts[3] if len(parts) >= 4 else ""
                                    else:
                                        log_source = log_source_parts[0]
                                        message = parts[3] if len(parts) >= 4 else ""
                                else:
                                    # 时间戳是一个完整的部分
                                    timestamp = parts[1]
                                    log_source = parts[2]
                                    message = parts[3] if len(parts) >= 4 else ""
                            else:
                                # 只有级别和内容，没有时间戳和日志源
                                timestamp = ""
                                log_source = ""
                                message = parts[1] if len(parts) >= 2 else ""
                        else:
                            # 无法解析，将整行作为消息
                            level = "INFO"
                            timestamp = ""
                            log_source = ""
                            message = line
                        
                        log_entries.append({
                            'timestamp': timestamp,
                            'level': level,
                            'logger': log_source,
                            'message': message
                        })
                    except Exception as e:
                        # 解析失败时添加原始行
                        log_entries.append({
                            'timestamp': '',
                            'level': 'ERROR',
                            'logger': 'log_parser',
                            'message': f'解析失败: {line.strip()}'
                        })
            
            return Response({'logs': log_entries})
        
        except Exception as e:
            logger.exception(f"获取日志失败: {str(e)}")
            return Response(
                {'error': f'获取日志失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def api_config(self, request):
        """
        获取API配置
        """
        openrouter_api_key = os.environ.get('OPENROUTER_API_KEY', '')
        use_gpu = getattr(django_settings, 'DEVICE', '') == 'cuda'
        
        data = {
            'openrouter_api_key': openrouter_api_key,
            'use_gpu': use_gpu
        }
        
        return Response(data)
    
    @api_config.mapping.post
    def update_api_config(self, request):
        """
        更新API配置
        """
        serializer = ApiConfigSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            try:
                # 获取.env文件路径
                env_path = os.path.join(django_settings.BASE_DIR, '.env')
                
                # 读取当前.env文件内容
                env_content = []
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        env_content = f.read().splitlines()
                
                # 更新或添加环境变量
                updated_env = []
                openrouter_key_found = False
                use_gpu_found = False
                
                for line in env_content:
                    if line.startswith('OPENROUTER_API_KEY='):
                        updated_env.append(f'OPENROUTER_API_KEY={data.get("openrouter_api_key", "")}')
                        openrouter_key_found = True
                    elif line.startswith('USE_GPU='):
                        updated_env.append(f'USE_GPU={str(data.get("use_gpu", False)).lower()}')
                        use_gpu_found = True
                    else:
                        updated_env.append(line)
                
                # 如果没找到相应的环境变量，添加它们
                if not openrouter_key_found:
                    updated_env.append(f'OPENROUTER_API_KEY={data.get("openrouter_api_key", "")}')
                
                if not use_gpu_found:
                    updated_env.append(f'USE_GPU={str(data.get("use_gpu", False)).lower()}')
                
                # 写回.env文件
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(updated_env))
                
                # 更新当前进程的环境变量
                os.environ['OPENROUTER_API_KEY'] = data.get('openrouter_api_key', '')
                
                # 记录日志
                logger.info(f"更新API配置: OPENROUTER_API_KEY已更新, USE_GPU={data.get('use_gpu', False)}")
                
                return Response({
                    'openrouter_api_key': data.get('openrouter_api_key', ''),
                    'use_gpu': data.get('use_gpu', False)
                })
            except Exception as e:
                logger.exception(f"更新API配置失败: {str(e)}")
                return Response(
                    {'error': f'更新API配置失败: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
