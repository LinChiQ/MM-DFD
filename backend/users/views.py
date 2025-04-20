"""
用户视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
# 导入 django-filter backend
from django_filters.rest_framework import DjangoFilterBackend 
from .serializers import (
    UserSerializer, UserRegistrationSerializer, 
    UserDetailSerializer, PasswordChangeSerializer
)

User = get_user_model()

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    对象级权限，只允许对象的所有者编辑，但管理员可以编辑任何对象。
    """
    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 管理员具有所有写入权限
        if request.user and request.user.is_staff:
            return True
            
        # 写入权限只允许对象的所有者
        return obj == request.user

class UserViewSet(viewsets.ModelViewSet):
    """
    用户视图集，处理用户相关操作
    """
    queryset = User.objects.all().order_by('-date_joined') # 默认按加入时间降序
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    # 添加过滤后端和过滤字段
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'email', 'is_active'] # 允许按这些字段过滤
    
    def get_serializer_class(self):
        """
        根据不同操作返回不同的序列化器
        """
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return UserDetailSerializer
        elif self.action == 'change_password':
            return PasswordChangeSerializer
        return UserSerializer
    
    def get_permissions(self):
        """
        根据不同操作设置不同的权限
        """
        if self.action == 'create':
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        """
        用户注册
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"message": "用户注册成功", "user": serializer.data},
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request, pk=None):
        """
        修改密码
        """
        user = self.get_object()
        if user != request.user:
            return Response(
                {"detail": "您没有权限修改此用户的密码"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 检查旧密码
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {"old_password": ["旧密码不正确"]},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 设置新密码
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({"message": "密码修改成功"})
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        获取当前用户信息
        """
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        获取用户统计信息（仅管理员可用）
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "您没有权限访问此资源"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        return Response({
            "total_users": total_users,
            "active_users": active_users,
        })
