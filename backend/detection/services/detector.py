"""
虚假新闻检测核心服务
"""
import os
import time
import logging
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from ..models import Detection

logger = logging.getLogger(__name__)

class FakeNewsDetector:
    """
    虚假新闻检测器类
    
    支持多种检测模式:
    1. 文本模式: 仅分析新闻文本内容
    2. 图像模式: 仅分析新闻图像
    3. 多模态模式: 同时分析文本和图像内容
    """
    
    # 检测模式
    MODE_TEXT = 'text'
    MODE_IMAGE = 'image'
    MODE_MULTIMODAL = 'multimodal'
    
    def __init__(self, detection_id, mode=MODE_MULTIMODAL):
        """
        初始化检测器
        
        Args:
            detection_id: 检测记录ID
            mode: 检测模式，默认为多模态
        """
        self.detection_id = detection_id
        self.mode = mode
        self.detection = Detection.objects.get(id=detection_id)
        
        # 更新检测状态为处理中
        self.update_status(Detection.STATUS_PROCESSING)
        
        # 检查模型路径
        self.model_path = Path(settings.MODEL_STORAGE_PATH)
        if not self.model_path.exists():
            logger.error(f"模型路径不存在: {self.model_path}")
            raise FileNotFoundError(f"模型路径不存在: {self.model_path}")
    
    def update_status(self, status, error_message=None):
        """
        更新检测状态
        
        Args:
            status: 新状态
            error_message: 错误信息（如果有）
        """
        self.detection.status = status
        
        if error_message:
            self.detection.error_message = error_message
        
        if status == Detection.STATUS_COMPLETED:
            self.detection.completed_at = timezone.now()
            
            # 更新用户的检测统计
            if self.detection.result == Detection.RESULT_FAKE:
                self.detection.user.update_detection_stats(is_fake=True)
            elif self.detection.result == Detection.RESULT_REAL:
                self.detection.user.update_detection_stats(is_fake=False)
        
        self.detection.save()
    
    def detect(self):
        """
        执行检测流程
        
        Returns:
            检测结果对象
        """
        try:
            # 根据模式执行不同的检测
            if self.mode == self.MODE_TEXT:
                result = self._detect_text()
            elif self.mode == self.MODE_IMAGE:
                result = self._detect_image()
            else:  # 多模态
                result = self._detect_multimodal()
            
            # 更新检测结果
            self.detection.result = result['result']
            self.detection.confidence_score = result['confidence']
            self.detection.analysis_result = result['analysis']
            
            # 更新状态为已完成
            self.update_status(Detection.STATUS_COMPLETED)
            
            return result
            
        except Exception as e:
            logger.exception(f"检测过程中发生错误: {str(e)}")
            self.update_status(Detection.STATUS_FAILED, str(e))
            return {
                'result': Detection.RESULT_UNKNOWN,
                'confidence': 0.0,
                'analysis': {'error': str(e)},
                'error': str(e)
            }
    
    def _detect_text(self):
        """
        仅文本检测
        
        Returns:
            检测结果字典
        """
        logger.info(f"开始文本检测, ID: {self.detection_id}")
        
        # TODO: 实现实际的文本检测模型调用
        # 这里使用示例逻辑，实际应当加载和调用文本检测模型
        
        text = f"{self.detection.title} {self.detection.content}"
        
        # 模拟模型处理延时
        time.sleep(1)
        
        # 简单示例逻辑: 标题或内容中包含"假"或"虚假"的词汇被视为虚假新闻
        # 实际项目中应该替换为真实的模型调用
        fake_words = ['假', '虚假', '谣言', '造谣', '不实', '假新闻']
        fake_score = sum([1 for word in fake_words if word in text]) / len(fake_words)
        
        # 简化示例结果
        is_fake = fake_score > 0.3
        confidence = 0.5 + fake_score / 2  # 简单置信度计算
        
        return {
            'result': Detection.RESULT_FAKE if is_fake else Detection.RESULT_REAL,
            'confidence': confidence,
            'analysis': {
                'text_features': {
                    'fake_words_count': fake_score * len(fake_words),
                    'text_length': len(text),
                    'score': fake_score
                }
            }
        }
    
    def _detect_image(self):
        """
        仅图像检测
        
        Returns:
            检测结果字典
        """
        logger.info(f"开始图像检测, ID: {self.detection_id}")
        
        # 检查是否有图像
        if not self.detection.image:
            logger.warning(f"检测记录没有图像: {self.detection_id}")
            return {
                'result': Detection.RESULT_UNKNOWN,
                'confidence': 0.0,
                'analysis': {'error': '没有提供图像'}
            }
        
        # TODO: 实现实际的图像检测模型调用
        # 这里使用示例逻辑，实际应当加载和调用图像检测模型
        
        # 模拟模型处理延时
        time.sleep(1.5)
        
        # 随机生成检测结果(示例)
        # 实际项目中应该替换为真实的模型调用
        np.random.seed(int(self.detection_id))
        fake_score = np.random.random()
        
        is_fake = fake_score > 0.5
        
        return {
            'result': Detection.RESULT_FAKE if is_fake else Detection.RESULT_REAL,
            'confidence': fake_score if is_fake else (1 - fake_score),
            'analysis': {
                'image_features': {
                    'manipulation_score': fake_score,
                    'image_path': str(self.detection.image)
                }
            }
        }
    
    def _detect_multimodal(self):
        """
        多模态检测（文本+图像）
        
        Returns:
            检测结果字典
        """
        logger.info(f"开始多模态检测, ID: {self.detection_id}")
        
        # 获取文本和图像的检测结果
        text_result = self._detect_text()
        
        # 如果有图像，则进行图像检测
        if self.detection.image:
            image_result = self._detect_image()
            has_image = True
        else:
            image_result = {
                'result': Detection.RESULT_UNKNOWN,
                'confidence': 0.0,
                'analysis': {}
            }
            has_image = False
        
        # 融合文本和图像的结果
        # 此处使用简单加权平均，实际项目中应该使用更复杂的融合策略
        text_weight = 0.7
        image_weight = 0.3
        
        if not has_image:
            # 如果没有图像，则只使用文本结果
            confidence = text_result['confidence']
            result = text_result['result']
        else:
            # 文本和图像结果融合
            if text_result['result'] == image_result['result']:
                # 如果两者判断一致，增强置信度
                confidence = (text_result['confidence'] * text_weight + 
                             image_result['confidence'] * image_weight)
                result = text_result['result']
            else:
                # 如果两者判断不一致，选择置信度较高的结果
                if text_result['confidence'] > image_result['confidence']:
                    confidence = text_result['confidence'] * 0.9  # 略微降低置信度
                    result = text_result['result']
                else:
                    confidence = image_result['confidence'] * 0.9  # 略微降低置信度
                    result = image_result['result']
        
        # 合并分析结果
        analysis = {
            'text_analysis': text_result['analysis'],
            'image_analysis': image_result['analysis'] if has_image else {'status': 'no_image'},
            'fusion': {
                'text_weight': text_weight,
                'image_weight': image_weight if has_image else 0,
                'text_confidence': text_result['confidence'],
                'image_confidence': image_result['confidence'] if has_image else 0,
                'final_confidence': confidence
            }
        }
        
        return {
            'result': result,
            'confidence': confidence,
            'analysis': analysis
        } 