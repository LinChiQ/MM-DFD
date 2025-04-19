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

# --- Preprocessing Function for Single Item (Metadata Excluded) --- #
def preprocess_input(text, image_path, tokenizer, image_transform, device):
    """
    Preprocesses text and image for a single detection item.
    Handles missing image.
    Returns a dictionary suitable for the text-image model input.
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

    # 3. 移除 Metadata Processing
    # metadata_features = torch.zeros(...) 
    # metadata_tensor = ...

    # 返回不含 metadata 的字典
    return {
        'input_ids': input_ids,
        'attention_mask': attention_mask,
        'image': image_tensor,
        'image_available': image_available
    }

# --- 移除 Scaler Loading Function --- #
# def _load_scaler(scaler_path):
#     """ Loads the metadata scaler. """
#     ... (移除整个函数) 