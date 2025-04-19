from django.shortcuts import render
import os
import logging
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
