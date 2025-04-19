# backend/news/views.py

import os
import json
import asyncio
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import logging

from .services import NewsVerificationService

# 初始化验证服务
verification_service = NewsVerificationService()

@method_decorator(csrf_exempt, name='dispatch')
class NewsVerificationView(View):
    """处理新闻验证请求的 API 视图"""
    
    async def post(self, request):
        """处理 POST 请求，验证新闻文本和图片"""
        try:
            # 获取文本
            text = request.POST.get('text', '')
            if not text:
                json_data = json.loads(request.body)
                text = json_data.get('text', '')
            
            if not text:
                return JsonResponse({"error": "请提供新闻文本"}, status=400)
            
            # 处理图片上传
            image_path = None
            if 'image' in request.FILES:
                image = request.FILES['image']
                # 生成唯一文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"temp_upload_{timestamp}_{image.name}"
                
                # 保存到临时目录
                upload_path = os.path.join('uploads', filename)
                path = default_storage.save(upload_path, ContentFile(image.read()))
                image_path = os.path.join(settings.MEDIA_ROOT, path)
            
            # 调用验证服务
            result = await verification_service.verify_news(text, image_path)
            
            # 清理临时图片
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    logging.warning(f"清理临时图片失败: {e}")
            
            return JsonResponse(result)
        
        except Exception as e:
            logging.error(f"处理验证请求失败: {e}")
            return JsonResponse({"error": str(e)}, status=500)