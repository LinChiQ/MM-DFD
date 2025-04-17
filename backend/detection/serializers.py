"""
检测应用序列化器
"""
from rest_framework import serializers
from .models import Detection

class DetectionSerializer(serializers.ModelSerializer):
    """
    检测记录序列化器
    """
    user = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    
    class Meta:
        model = Detection
        fields = [
            'id', 'user', 'title', 'content', 'image', 
            'status', 'status_display', 'result', 'result_display',
            'confidence_score', 'analysis_result', 
            'created_at', 'updated_at', 'completed_at', 'error_message'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'status_display', 'result', 'result_display',
            'confidence_score', 'analysis_result', 
            'created_at', 'updated_at', 'completed_at', 'error_message'
        ]

class DetectionCreateSerializer(serializers.ModelSerializer):
    """
    创建检测记录的序列化器
    """
    class Meta:
        model = Detection
        fields = ['title', 'content', 'image']

class DetectionResultSerializer(serializers.ModelSerializer):
    """
    检测结果序列化器
    """
    user = serializers.StringRelatedField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    
    class Meta:
        model = Detection
        fields = [
            'id', 'user', 'title', 'content', 'image', 
            'status', 'status_display', 'result', 'result_display',
            'confidence_score', 'analysis_result', 
            'created_at', 'completed_at'
        ]
        read_only_fields = fields

class DetectionStatSerializer(serializers.Serializer):
    """
    检测统计序列化器
    """
    total_count = serializers.IntegerField()
    fake_count = serializers.IntegerField()
    real_count = serializers.IntegerField()
    pending_count = serializers.IntegerField()
    completed_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    fake_percentage = serializers.FloatField()
    real_percentage = serializers.FloatField()
    average_confidence = serializers.FloatField()
