"""
虚假新闻检测核心服务
"""
import os
import time
import logging
import json
import numpy as np
import torch
import joblib
import asyncio
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from ..models import Detection
from .llm_verifier import verify_news_with_llms_async # Import the async LLM verifier
from ..ml.model import MultimodalFakeNewsModel # Import your model definition
from ..ml.data_utils import get_tokenizer, get_image_transforms, preprocess_input # Import utils

# 导入SystemSettings模型
from settings.models import SystemSettings

logger = logging.getLogger(__name__)

class FakeNewsDetector:
    """
    虚假新闻检测器类
    整合自训练的多模态模型和LLM交叉验证。
    """

    def __init__(self, detection_id):
        """
        初始化检测器
        - 加载自训练模型和scaler
        - 加载tokenizer和图像变换器
        - 获取Detection实例
        """
        self.detection_id = detection_id
        try:
            self.detection = Detection.objects.get(id=detection_id)
        except Detection.DoesNotExist:
            logger.error(f"Detection record with ID {detection_id} not found.")
            raise

        self.device = torch.device(settings.DEVICE)
        logger.info(f"Using device: {self.device}")

        # 加载自训练模型
        self.model = self._load_model()
        if self.model:
             self.model.to(self.device)
             self.model.eval() # Set model to evaluation mode

        # 移除加载元数据Scaler
        # self.scaler = self._load_scaler()
        self.scaler = None # Explicitly set to None

        # 加载Tokenizer和图像变换
        self.tokenizer = get_tokenizer()
        self.image_transform = get_image_transforms()

        # 更新状态为处理中
        self._update_status(Detection.STATUS_PROCESSING)

    def _load_model(self):
        """ 加载 PyTorch 模型 """
        model_path = settings.MODEL_PATH
        if not Path(model_path).exists():
            logger.error(f"自训练模型文件未找到: {model_path}")
            return None
        try:
            model = MultimodalFakeNewsModel() # Initialize model structure
            # Load state dict, ensuring map_location handles CPU/GPU
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            logger.info(f"自训练模型加载成功: {model_path}")
            return model
        except Exception as e:
            logger.exception(f"加载自训练模型失败 {model_path}: {e}")
            return None

    def _update_status(self, status, error_message=None):
        """ 更新检测记录的状态 """
        self.detection.status = status
        if error_message:
            self.detection.error_message = str(error_message)[:1000] # Limit error message length
        if status == Detection.STATUS_COMPLETED:
            self.detection.completed_at = timezone.now()
        elif status == Detection.STATUS_FAILED:
             self.detection.completed_at = timezone.now() # Mark completion time even on failure
        
        self.detection.save()
        logger.info(f"Detection {self.detection_id} status updated to {status}.")
    
    def detect(self):
        """
        执行检测流程:
        1. 预处理文本和图像 (包括处理元数据缺失)
        2. 使用自训练模型进行预测
        3. 使用LLM进行交叉验证 (异步)
        4. 融合结果
        5. 更新数据库记录
        """
        start_time = time.time()
        logger.info(f"--- 开始检测 ID: {self.detection_id} ---")
        
        # 准备文本和图像路径
        text_content = f"{self.detection.title} {self.detection.content}"
        image_path = None
        if self.detection.image:
            try:
                # Ensure MEDIA_ROOT is correctly configured
                full_image_path = Path(settings.MEDIA_ROOT) / self.detection.image.name
                if full_image_path.is_file():
                    image_path = full_image_path
                else:
                    logger.warning(f"图像文件在路径 {full_image_path} 未找到。")
            except Exception as e:
                logger.error(f"获取图像路径时出错: {e}")

        # --- 1. 自训练模型预测 --- #
        local_model_result = {
                'result': Detection.RESULT_UNKNOWN,
                'confidence': 0.0,
            'error': None
        }
        if self.model:
            try:
                # 预处理输入
                processed_input = preprocess_input(
                    text=text_content,
                    image_path=image_path,
                    tokenizer=self.tokenizer,
                    image_transform=self.image_transform,
                    # scaler=self.scaler, # 移除 scaler 参数
                    device=self.device
                )

                # 模型推理
                with torch.no_grad():
                    # 调用模型时移除 metadata
                    logits = self.model(input_ids=processed_input['input_ids'], 
                                         attention_mask=processed_input['attention_mask'], 
                                         image=processed_input['image'], 
                                         image_available=processed_input['image_available'])
                    probability = torch.sigmoid(logits).item() # 获取概率值 (0-1)

                # 结果转换
                # 假设概率 > 0.5 为 Fake (需要根据你的模型训练目标确认)
                local_model_result['result'] = Detection.RESULT_FAKE if probability >= 0.5 else Detection.RESULT_REAL
                # 置信度可以基于概率与0.5的距离
                local_model_result['confidence'] = probability if probability >= 0.5 else (1 - probability)
                logger.info(f"本地模型预测结果: {local_model_result['result']}, 原始概率: {probability:.4f}, 置信度: {local_model_result['confidence']:.4f}")

            except Exception as e:
                logger.exception(f"本地模型推理失败: {e}")
                local_model_result['error'] = f"本地模型推理失败: {str(e)}"
        else:
            local_model_result['error'] = "本地模型未加载"
            logger.error("本地模型未加载，跳过推理。")

        # --- 2. LLM 交叉验证 --- #
        llm_result = {
            'overall_verdict': 'Skipped',
            'aggregated_confidence': 0.0,
            'error': None,
            'details': None
        }
        if settings.OPENROUTER_API_KEY:
            try:
                # 在同步代码中运行异步LLM验证函数
                llm_raw_result = asyncio.run(verify_news_with_llms_async(text_content, image_path))

                if llm_raw_result and not llm_raw_result.get('error'):
                     llm_result['overall_verdict'] = llm_raw_result.get('overall_verdict', 'Parsing Error')
                     llm_result['aggregated_confidence'] = llm_raw_result.get('aggregated_confidence', 0.0)
                     llm_result['details'] = llm_raw_result # Store full details
                     logger.info(f"LLM 验证结果: {llm_result['overall_verdict']}, 置信度: {llm_result['aggregated_confidence']:.4f}")
                else:
                     llm_result['error'] = llm_raw_result.get('error', 'Unknown LLM error')
                     llm_result['details'] = llm_raw_result
                     logger.error(f"LLM 验证失败: {llm_result['error']}")

            except Exception as e:
                logger.exception(f"LLM 验证过程中发生异常: {e}")
                llm_result['error'] = f"LLM 验证异常: {str(e)}"
        else:
             llm_result['error'] = "OpenRouter API Key 未配置"
             logger.warning("OpenRouter API Key 未配置，跳过 LLM 验证。")

        # --- 3. 结果融合 --- #
        final_result = Detection.RESULT_UNKNOWN
        final_confidence = 0.0
        fusion_strategy = "N/A"
        fusion_details = [] # 用于记录融合过程细节
        weighted_score = None # 初始化加权分数

        # --- 获取并映射模型结果 ---
        llm_verdict_mapped = Detection.RESULT_UNKNOWN
        llm_conf = llm_result.get('aggregated_confidence', 0.0)
        llm_overall_verdict_str = llm_result.get('overall_verdict', '').lower()
        if "fake" in llm_overall_verdict_str:
            llm_verdict_mapped = Detection.RESULT_FAKE
        elif "true" in llm_overall_verdict_str:
            llm_verdict_mapped = Detection.RESULT_REAL
        # 其他 (uncertain, mixed, skipped, error) 保持 unknown

        local_verdict = local_model_result.get('result', Detection.RESULT_UNKNOWN)
        local_conf = local_model_result.get('confidence', 0.0)
        local_error = local_model_result.get('error')
        llm_error = llm_result.get('error')
        
        # --- 从数据库获取模型权重 ---
        # 定义设置键名和默认值
        LOCAL_MODEL_WEIGHT_KEY = 'local_model_weight'
        LLM_WEIGHT_KEY = 'llm_weight'
        FAKE_THRESHOLD_KEY = 'fake_threshold'
        REAL_THRESHOLD_KEY = 'real_threshold'
        
        DEFAULT_LOCAL_MODEL_WEIGHT = 0.4
        DEFAULT_LLM_WEIGHT = 0.6
        DEFAULT_FAKE_THRESHOLD = 0.65
        DEFAULT_REAL_THRESHOLD = 0.35
        
        # 从数据库获取设置，如果不存在则使用默认值
        LOCAL_MODEL_WEIGHT = SystemSettings.get_value(LOCAL_MODEL_WEIGHT_KEY, DEFAULT_LOCAL_MODEL_WEIGHT)
        LLM_WEIGHT = SystemSettings.get_value(LLM_WEIGHT_KEY, DEFAULT_LLM_WEIGHT)
        FAKE_THRESHOLD = SystemSettings.get_value(FAKE_THRESHOLD_KEY, DEFAULT_FAKE_THRESHOLD)
        REAL_THRESHOLD = SystemSettings.get_value(REAL_THRESHOLD_KEY, DEFAULT_REAL_THRESHOLD)
        
        logger.info(f"使用模型权重设置: 本地模型={LOCAL_MODEL_WEIGHT}, LLM={LLM_WEIGHT}, " 
                   f"虚假阈值={FAKE_THRESHOLD}, 真实阈值={REAL_THRESHOLD}")
        
        # --- 数值化判断结果 (Real=0, Fake=1, Unknown=0.5) ---
        def verdict_to_score(verdict_str):
            if verdict_str == Detection.RESULT_REAL:
                return 0.0
            elif verdict_str == Detection.RESULT_FAKE:
                return 1.0
            else:
                return 0.5
        
        llm_numeric_score = verdict_to_score(llm_verdict_mapped)
        local_numeric_score = verdict_to_score(local_verdict)

        # --- 检查模型有效性 ---
        local_model_active = local_error is None and local_verdict != Detection.RESULT_UNKNOWN
        # LLM 只有在无错误且判断明确 (Fake/Real) 时才算 active
        llm_active = llm_error is None and llm_verdict_mapped != Detection.RESULT_UNKNOWN 

        # --- 计算融合结果 --- 
        if local_model_active and llm_active:
            # Case 1: 两个模型都有效
            effective_local_weight = LOCAL_MODEL_WEIGHT
            effective_llm_weight = LLM_WEIGHT
            total_weight = effective_local_weight + effective_llm_weight
            
            # 计算加权分数
            weighted_score = ((local_numeric_score * effective_local_weight) + 
                             (llm_numeric_score * effective_llm_weight)) / total_weight
            # 计算加权置信度
            weighted_confidence = ((local_conf * effective_local_weight) + 
                                (llm_conf * effective_llm_weight)) / total_weight

            # 根据加权分数和阈值决定最终结果
            if weighted_score >= FAKE_THRESHOLD:
                final_result = Detection.RESULT_FAKE
                final_confidence = 0.5 + (weighted_score - 0.5) 
                final_confidence = final_confidence * weighted_confidence 
            elif weighted_score <= REAL_THRESHOLD:
                final_result = Detection.RESULT_REAL
                final_confidence = 0.5 + (0.5 - weighted_score)
                final_confidence = final_confidence * weighted_confidence
            else:
                final_result = Detection.RESULT_UNKNOWN
                final_confidence = 0.0  # 对于未知结果，置信度始终为0
            
            fusion_strategy = f"Weighted Average (Both Active - Local W: {effective_local_weight:.2f}, LLM W: {effective_llm_weight:.2f}), Score: {weighted_score:.3f}"
            fusion_details = [
                f"Local model active (Verdict: {local_verdict}, Conf: {local_conf:.3f})",
                f"LLM active (Mapped Verdict: {llm_verdict_mapped}, Conf: {llm_conf:.3f}, Raw: {llm_overall_verdict_str})"
            ]

        elif local_model_active:
            # Case 2: 只有本地模型有效
            fusion_strategy = f"Local Model Only (LLM Inactive/Uncertain)"
            final_result = local_verdict
            final_confidence = local_conf * 0.8 # 置信度折减
            fusion_details = [
                f"Local model active (Verdict: {local_verdict}, Conf: {local_conf:.3f})",
                f"LLM inactive/uncertain (Error: {llm_error}, Mapped Verdict: {llm_verdict_mapped}, Raw: {llm_overall_verdict_str})",
                f"Confidence adjusted due to LLM inactivity/uncertainty. Original local: {local_conf:.3f}"
            ]
            weighted_score = local_numeric_score # 记录分数以便分析

        elif llm_active:
            # Case 3: 只有 LLM 有效
            fusion_strategy = f"LLM Only (Local Inactive/Uncertain)"
            final_result = llm_verdict_mapped
            final_confidence = llm_conf * 0.8 # 置信度折减
            fusion_details = [
                f"Local model inactive (Error: {local_error}, Verdict: {local_verdict})",
                f"LLM active (Mapped Verdict: {llm_verdict_mapped}, Conf: {llm_conf:.3f}, Raw: {llm_overall_verdict_str})",
                f"Confidence adjusted due to Local inactivity. Original LLM: {llm_conf:.3f}"
            ]
            weighted_score = llm_numeric_score # 记录分数以便分析

        else:
            # Case 4: 两个模型都无效/不确定
            fusion_strategy = "Both Models Failed/Unknown/Uncertain"
            final_result = Detection.RESULT_UNKNOWN
            final_confidence = 0.0  # 对于未知结果，置信度始终为0
            fusion_details = [
                f"Local model inactive (Error: {local_error}, Verdict: {local_verdict})",
                f"LLM inactive/uncertain (Error: {llm_error}, Mapped Verdict: {llm_verdict_mapped}, Raw: {llm_overall_verdict_str})"
            ]
            weighted_score = 0.5 # 默认为中性分数

        # 确保最终置信度在 [0, 1] 范围内
        final_confidence = max(0.0, min(1.0, final_confidence))

        logger.info(f"融合结果: {final_result}, 置信度: {final_confidence:.4f} (策略: {fusion_strategy})")
        logger.info(f"融合详情: {fusion_details}")

        # --- 4. 更新数据库 --- #
        analysis = {
            'timestamp': timezone.now().isoformat(),
            'local_model': local_model_result,
            'llm_verification': llm_result,
            'fusion': {
                'strategy': fusion_strategy,
                'details': fusion_details, 
                'weighted_score': weighted_score, 
                'final_verdict': final_result,
                'final_confidence': final_confidence
            }
        }
        self.detection.result = final_result
        self.detection.confidence_score = final_confidence
        self.detection.analysis_result = analysis
        self._update_status(Detection.STATUS_COMPLETED)

        end_time = time.time()
        logger.info(f"--- 检测完成 ID: {self.detection_id} (耗时: {end_time - start_time:.2f} 秒) ---")
        
        return {
            'result': final_result,
            'confidence': final_confidence,
            'analysis': analysis
        } 