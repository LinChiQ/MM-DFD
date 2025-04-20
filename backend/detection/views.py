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
from django.db.models.functions import TruncDate
from datetime import timedelta, datetime

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
        
        # 添加按日期分组的数据统计
        # 获取过去7天的日期范围
        today = timezone.now().date()
        dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
        
        # 按日期分组查询数据 - 修复日期查询逻辑
        # 不再使用日期过滤，而是分别计算每个日期的记录数
        date_counts = {}
        for date in dates:
            start_date = datetime.combine(date, datetime.min.time())
            end_date = datetime.combine(date, datetime.max.time())
            start_date = timezone.make_aware(start_date)
            end_date = timezone.make_aware(end_date)
            
            # 计算当天的检测数量
            count = detections.filter(created_at__gte=start_date, created_at__lte=end_date).count()
            date_counts[date.strftime('%Y-%m-%d')] = count
        
        # 如果所有日期的计数都是0，我们可能需要查看所有检测记录的日期分布
        if all(count == 0 for count in date_counts.values()) and total_count > 0:
            # 获取最早和最晚的检测记录日期
            earliest = detections.order_by('created_at').first()
            latest = detections.order_by('-created_at').first()
            
            if earliest and latest:
                earliest_date = earliest.created_at.date()
                latest_date = latest.created_at.date()
                
                # 计算所有检测记录的日期分布
                real_date_counts = {}
                date_range = []
                for date in (earliest_date + timedelta(days=n) for n in range((latest_date - earliest_date).days + 1)):
                    date_range.append(date)
                    start_date = datetime.combine(date, datetime.min.time())
                    end_date = datetime.combine(date, datetime.max.time())
                    start_date = timezone.make_aware(start_date)
                    end_date = timezone.make_aware(end_date)
                    count = detections.filter(created_at__gte=start_date, created_at__lte=end_date).count()
                    real_date_counts[date.strftime('%Y-%m-%d')] = count
                
                # 使用真实的日期分布，取最多7天数据
                if len(date_range) > 0:
                    # 最多取7天数据，优先取最近的数据
                    if len(date_range) > 7:
                        date_range = date_range[-7:]
                    
                    date_counts = {date.strftime('%Y-%m-%d'): real_date_counts.get(date.strftime('%Y-%m-%d'), 0) for date in date_range}
                    dates = date_range
        
        # 生成最近日期的统计数据
        weekly_trend = []
        for date in dates:
            date_str = date.strftime('%Y-%m-%d')
            if date == today:
                display_name = '今天'
            elif date == today - timedelta(days=1):
                display_name = '昨天'
            else:
                display_name = date_str
                
            weekly_trend.append({
                'date': display_name,
                'count': date_counts.get(date_str, 0)
            })
        
        # 计算今日检测量
        today_detections = date_counts.get(today.strftime('%Y-%m-%d'), 0)
        
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
            'average_confidence': avg_confidence,
            'weekly_trend': weekly_trend,
            'today_detections': today_detections,
            'result_distribution': [
                { 'name': '真实新闻', 'value': real_count },
                { 'name': '虚假新闻', 'value': fake_count }
            ]
        }
        
        return Response(stats)
