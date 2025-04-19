"""
检测应用视图
"""
import logging
from django.db.models import Count, Avg, Q, F, Sum, Case, When, Value, IntegerField
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Detection
from .serializers import (
    DetectionSerializer, DetectionCreateSerializer, 
    DetectionResultSerializer, DetectionStatSerializer
)
from .services.detector import FakeNewsDetector

logger = logging.getLogger(__name__)

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    对象级权限，只允许对象的所有者编辑
    """
    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 管理员具有所有权限
        if request.user.is_staff:
            return True
            
        # 写入权限只允许对象的所有者
        return obj.user == request.user

class DetectionViewSet(viewsets.ModelViewSet):
    """
    检测记录视图集
    """
    queryset = Detection.objects.all()
    serializer_class = DetectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """
        根据用户过滤检测记录
        """
        user = self.request.user
        # 管理员可以查看所有记录，普通用户只能查看自己的记录
        if user.is_staff:
            return Detection.objects.all()
        return Detection.objects.filter(user=user)
    
    def get_serializer_class(self):
        """
        根据不同操作返回不同的序列化器
        注意：对于 create 操作，我们虽然用 DetectionCreateSerializer 验证输入，
              但在 create 方法的响应中，我们会用 DetectionSerializer 返回完整数据。
        """
        if self.action == 'create':
            return DetectionCreateSerializer
        if self.action == 'get_stats':
            return DetectionStatSerializer
        # 对于 list, retrieve, update, partial_update, destroy 等，使用默认的 DetectionSerializer
        return DetectionSerializer

    # 覆盖 create 方法以确保返回完整序列化数据
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 调用 perform_create 来保存对象并触发检测
        self.perform_create(serializer)
        # 使用 DetectionSerializer 序列化创建的对象以包含所有字段
        response_serializer = DetectionSerializer(serializer.instance, context=self.get_serializer_context())
        headers = self.get_success_headers(response_serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        创建检测记录时设置用户, 并启动检测任务
        """
        detection = serializer.save(user=self.request.user)
        
        # 启动异步检测任务 (当前是同步的)
        try:
            detector = FakeNewsDetector(detection.id)
            detector.detect()
        except Exception as e:
            logger.exception(f"检测任务启动失败: {str(e)}")
            detection.status = Detection.STATUS_FAILED
            detection.error_message = f"检测任务启动失败: {str(e)}"
            detection.save()
    
    @action(detail=True, methods=['get'])
    def result(self, request, pk=None):
        """
        获取检测结果
        """
        detection = self.get_object()
        serializer = DetectionResultSerializer(detection)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_detections(self, request):
        """
        获取当前用户的所有检测记录
        """
        detections = Detection.objects.filter(user=request.user).order_by('-created_at')
        page = self.paginate_queryset(detections)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(detections, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def get_stats(self, request):
        """
        获取检测统计信息
        """
        user = request.user
        
        # 确定统计范围
        if user.is_staff and request.query_params.get('all') == 'true':
            # 管理员可以查看所有统计
            detections = Detection.objects.all()
        else:
            # 普通用户只能查看自己的统计
            detections = Detection.objects.filter(user=user)
        
        # 计算基本统计量
        total_count = detections.count()
        
        # 如果没有检测记录，返回空统计
        if total_count == 0:
            return Response({
                'total_count': 0,
                'fake_count': 0,
                'real_count': 0,
                'pending_count': 0,
                'completed_count': 0,
                'failed_count': 0,
                'fake_percentage': 0,
                'real_percentage': 0,
                'average_confidence': 0
            })
        
        # 计算各类型数量
        fake_count = detections.filter(result=Detection.RESULT_FAKE).count()
        real_count = detections.filter(result=Detection.RESULT_REAL).count()
        pending_count = detections.filter(status=Detection.STATUS_PENDING).count()
        completed_count = detections.filter(status=Detection.STATUS_COMPLETED).count()
        failed_count = detections.filter(status=Detection.STATUS_FAILED).count()
        
        # 计算百分比
        fake_percentage = (fake_count / total_count) * 100 if total_count > 0 else 0
        real_percentage = (real_count / total_count) * 100 if total_count > 0 else 0
        
        # 计算平均置信度
        avg_confidence = detections.filter(
            status=Detection.STATUS_COMPLETED
        ).aggregate(avg=Avg('confidence_score'))['avg'] or 0
        
        # 构建统计响应
        stats = {
            'total_count': total_count,
            'fake_count': fake_count,
            'real_count': real_count,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'failed_count': failed_count,
            'fake_percentage': fake_percentage,
            'real_percentage': real_percentage,
            'average_confidence': avg_confidence
        }
        
        return Response(stats)
