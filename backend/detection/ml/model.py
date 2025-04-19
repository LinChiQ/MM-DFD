# backend/detection/ml/model.py

import torch
import torch.nn as nn
from torchvision.models import resnet50, ResNet50_Weights
from transformers import AutoModel
import logging
from django.conf import settings # Import settings

logger = logging.getLogger(__name__)

# --- Model Definitions (Modified to exclude metadata) ---

class MultimodalFakeNewsModel(nn.Module):
    """
    Multimodal model combining text and image.
    (Structure must match the saved best_text_image_model.pth weights)
    """
    def __init__(self, text_model_name=settings.TEXT_MODEL_NAME,
                 image_model_name=settings.IMAGE_MODEL_NAME,
                 text_embedding_dim=settings.TEXT_EMBEDDING_DIM,
                 img_embedding_dim=settings.IMG_EMBEDDING_DIM,
                 fusion_output_dim=settings.FUSION_OUTPUT_DIM):
        super().__init__()
        logger.info("Initializing Text-Image Multimodal Model for Inference...")

        # Text Encoder
        try:
            logger.info(f"Loading text model: {text_model_name}")
            self.text_encoder = AutoModel.from_pretrained(text_model_name)
        except Exception as e:
            logger.error(f"Failed to load text model {text_model_name}: {e}")
            raise

        # Image Encoder
        logger.info(f"Loading image model: {image_model_name}")
        if image_model_name == 'resnet50':
            self.image_encoder = resnet50(weights=None)
            self.image_encoder.fc = nn.Identity() # Remove classifier
            self.img_embedding_dim = img_embedding_dim # Use dim from settings
        else:
            raise ValueError(f"Image model '{image_model_name}' not currently supported for inference setup.")

        # Fusion Layer
        logger.info("Initializing fusion layer...")
        self.fusion_dim = text_embedding_dim + self.img_embedding_dim
        self.fusion_layer = nn.Sequential(
            nn.Linear(self.fusion_dim, fusion_output_dim),
            nn.ReLU(),
            nn.Dropout(0.5) # Match dropout from training
        )

        # Classifier Head
        logger.info("Initializing classifier head...")
        self.classifier = nn.Linear(fusion_output_dim, 1)

    def forward(self, input_ids, attention_mask, image, image_available):
        # Text Features
        text_outputs = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        text_features = text_outputs.last_hidden_state[:, 0, :]

        # Image Features
        batch_size = image.shape[0]
        image_features = torch.zeros(batch_size, self.img_embedding_dim, device=image.device)
        valid_image_mask = image_available.bool()
        if valid_image_mask.any():
            valid_images = image[valid_image_mask]
            if valid_images.shape[2] != settings.IMAGE_MODEL_INPUT_SIZE or valid_images.shape[3] != settings.IMAGE_MODEL_INPUT_SIZE:
                 logger.warning(f"Input image size {valid_images.shape[2:]} doesn't match expected {settings.IMAGE_MODEL_INPUT_SIZE}. Ensure transforms are correct.")
            valid_image_features = self.image_encoder(valid_images)
            image_features[valid_image_mask] = valid_image_features

        # Fusion
        fused_features = torch.cat((text_features, image_features), dim=1)
        fused_output = self.fusion_layer(fused_features)

        # Classification
        logits = self.classifier(fused_output)
        return logits.squeeze(-1) 