from rest_framework import serializers
from .models import SystemSettings

class SystemSettingsSerializer(serializers.ModelSerializer):
    """系统设置序列化器"""
    class Meta:
        model = SystemSettings
        fields = ['key', 'value', 'value_type', 'description', 'updated_at']
        read_only_fields = ['updated_at']

class ModelWeightsSerializer(serializers.Serializer):
    """模型权重配置序列化器"""
    local_model_weight = serializers.FloatField(min_value=0.0, max_value=1.0)
    llm_weight = serializers.FloatField(min_value=0.0, max_value=1.0)
    fake_threshold = serializers.FloatField(min_value=0.5, max_value=0.9)
    real_threshold = serializers.FloatField(min_value=0.1, max_value=0.5)
    
    def validate(self, data):
        """验证模型权重总和为1"""
        if abs(data['local_model_weight'] + data['llm_weight'] - 1.0) > 0.001:
            raise serializers.ValidationError("本地模型权重和LLM权重之和必须为1")
        
        if data['real_threshold'] >= data['fake_threshold'] - 0.1:
            raise serializers.ValidationError("真实新闻阈值必须小于虚假新闻阈值至少0.1")
        
        return data

class ApiConfigSerializer(serializers.Serializer):
    """API配置序列化器"""
    openrouter_api_key = serializers.CharField(allow_blank=True, max_length=100, required=False)
    use_gpu = serializers.BooleanField(required=False, default=False)
    
    def validate_openrouter_api_key(self, value):
        """验证API密钥格式"""
        if value and not value.startswith('sk-or-v1-'):
            raise serializers.ValidationError("无效的OpenRouter API密钥格式")
        return value 