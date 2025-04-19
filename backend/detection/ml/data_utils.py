# backend/detection/ml/data_utils.py

import torch
from transformers import AutoTokenizer
from torchvision import transforms
from torchvision.models import ResNet50_Weights
from PIL import Image
import logging
from django.conf import settings # Import settings

logger = logging.getLogger(__name__)

# --- Tokenizer Function (Copied from data_loader.py) ---
def get_tokenizer(model_name=settings.TEXT_MODEL_NAME):
    """ Returns a tokenizer for the specified model. """
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        logger.info(f"Tokenizer loaded for {model_name}")
        return tokenizer
    except Exception as e:
        logger.error(f"Failed to load tokenizer for {model_name}: {e}")
        raise

# --- Image Transform Function (Adapted from data_loader.py) ---
def get_image_transforms(model_name=settings.IMAGE_MODEL_NAME, input_size=settings.IMAGE_MODEL_INPUT_SIZE):
    """ Returns appropriate image transforms for evaluation. """
    if model_name == 'resnet50':
        # Use standard weights for ResNet50 V2 for transforms
        try:
            weights = ResNet50_Weights.IMAGENET1K_V2
            transform = weights.transforms()
            logger.info(f"Using standard ResNet50 V2 transforms (input size {input_size})")
            # Ensure the resize matches the expected input size if different from standard
            if input_size != 224: # Standard ResNet input is 224
                # Overwrite the resize/center crop part if needed
                transform = transforms.Compose([
                    transforms.Resize(input_size + 32), # Standard practice: resize slightly larger
                    transforms.CenterCrop(input_size),
                    transforms.ToTensor(),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
                ])
                logger.warning(f"Overriding standard ResNet transforms for input size {input_size}")
            return transform
        except Exception as e:
             logger.error(f"Failed to get ResNet50 V2 weights/transforms: {e}. Falling back to basic transforms.")
             # Fallback if weights unavailable
             return transforms.Compose([
                transforms.Resize((input_size, input_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])

    else:
        # Basic transforms for other/unknown models
        logger.warning(f"Using basic image transforms for model {model_name}")
        return transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            # Standard ImageNet normalization, adjust if your model used different ones
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

# --- Preprocessing Function for Single Item --- #
def preprocess_input(text, image_path, tokenizer, image_transform, scaler, device):
    """
    Preprocesses text, image, and metadata for a single detection item.
    Handles missing image and metadata.
    Returns a dictionary suitable for model input.
    """
    # 1. Text Processing
    encoding = tokenizer(text,
                         add_special_tokens=True,
                         max_length=settings.MAX_TEXT_LEN,
                         padding='max_length',
                         truncation=True,
                         return_attention_mask=True,
                         return_tensors='pt')

    input_ids = encoding['input_ids'].flatten().unsqueeze(0).to(device) # Add batch dim
    attention_mask = encoding['attention_mask'].flatten().unsqueeze(0).to(device) # Add batch dim

    # 2. Image Processing
    image_tensor = torch.zeros((1, 3, settings.IMAGE_MODEL_INPUT_SIZE, settings.IMAGE_MODEL_INPUT_SIZE)).to(device)
    image_available = torch.tensor([False]).to(device)
    if image_path and image_path.is_file():
        try:
            image = Image.open(image_path).convert('RGB')
            image_tensor = image_transform(image).unsqueeze(0).to(device) # Add batch dim
            image_available = torch.tensor([True]).to(device)
        except Exception as e:
            logger.warning(f"Could not process image {image_path}: {e}. Skipping image.")

    # 3. Metadata Processing (Using Placeholders)
    # Create a placeholder array of zeros for metadata features
    metadata_features = torch.zeros((1, settings.NUM_METADATA_FEATURES), dtype=torch.float32)

    # Apply the scaler if it exists
    # --- 临时修改：跳过对零向量的 scaler 处理，直接使用零 --- 
    # if scaler:
    #     try:
    #         # Scale the zero array (note: this might not be meaningful, but matches training pipeline)
    #         scaled_metadata = scaler.transform(metadata_features.numpy())
    #         logger.info(f"Scaled metadata (from zeros): {scaled_metadata}") 
    #         metadata_tensor = torch.tensor(scaled_metadata, dtype=torch.float32).to(device)
    #         logger.debug("Applied scaler to placeholder metadata.")
    #     except Exception as e:
    #         logger.error(f"Failed to apply scaler to metadata: {e}. Using zeros.")
    #         metadata_tensor = metadata_features.to(device)
    # else:
    #     logger.warning("Metadata scaler not found or skipped. Using zeros for metadata features.")
    metadata_tensor = metadata_features.to(device) # 直接使用全零 Tensor
    logger.info("Using zero vector directly for metadata (temporary fix).")
    # --- 结束临时修改 ---

    return {
        'input_ids': input_ids,
        'attention_mask': attention_mask,
        'image': image_tensor,
        'metadata': metadata_tensor,
        'image_available': image_available
    } 