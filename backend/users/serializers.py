"""
用户序列化器
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    用户基本信息序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                'avatar', 'bio', 'total_detections', 'fake_detections', 
                'real_detections', 'date_joined', 'is_active', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'total_detections', 'fake_detections', 
                        'real_detections', 'date_joined', 'is_active', 'is_staff', 'is_superuser']

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    """
    用户详细信息序列化器
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 
                'avatar', 'bio', 'total_detections', 'fake_detections', 
                'real_detections', 'date_joined', 'is_active', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'username', 'total_detections', 
                        'fake_detections', 'real_detections', 'date_joined', 'is_superuser']

class PasswordChangeSerializer(serializers.Serializer):
    """
    密码修改序列化器
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "两次输入的新密码不一致"})
        return attrs
