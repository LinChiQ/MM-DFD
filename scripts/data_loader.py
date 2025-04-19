import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image, UnidentifiedImageError
from torchvision import transforms
from transformers import AutoTokenizer
import numpy as np
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CSV_PATH = PROCESSED_DIR / 'processed_data.csv'
IMAGE_DIR = PROCESSED_DIR / 'images'

TEXT_MODEL_NAME = 'bert-base-chinese'
IMAGE_MODEL_INPUT_SIZE = 224
MAX_TEXT_LEN = 128

IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]

# --- Custom PyTorch Dataset (No Metadata) ---

class MultimodalFakeNewsDataset(Dataset):
    """
    Custom PyTorch Dataset for loading multimodal fake news data.
    Handles text, image (if available), and labels.
    (Modified to exclude metadata)
    """
    def __init__(self, dataframe, data_dir, tokenizer, image_transform, max_len):
        self.data_dir = Path(data_dir)
        self.image_base_dir = self.data_dir / 'processed' / 'images'
        self.tokenizer = tokenizer
        self.image_transform = image_transform
        self.max_len = max_len

        logging.info(f"Initializing Dataset with {len(dataframe)} records (metadata excluded).")
        try:
            self.df = dataframe.copy()
            self.df['image_path'] = self.df['image_path'].fillna('') 
            self.df['text'] = self.df['text'].fillna('') 
            
        except Exception as e:
            logging.error(f"Error initializing Dataset from DataFrame: {e}")
            raise

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]

        item_id = row['id']
        text = str(row['text'])
        label = int(row['label'])
        image_path_rel = row['image_path']

        # --- Text Processing ---
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_token_type_ids=False,
            return_attention_mask=True,
            return_tensors='pt',
        )
        input_ids = encoding['input_ids'].flatten()
        attention_mask = encoding['attention_mask'].flatten()

        # --- Image Processing ---
        image_tensor = torch.zeros(3, IMAGE_MODEL_INPUT_SIZE, IMAGE_MODEL_INPUT_SIZE)
        image_available = False
        if image_path_rel and isinstance(image_path_rel, str):
            image_path_abs = self.data_dir / image_path_rel
            try:
                if image_path_abs.is_file():
                    image = Image.open(image_path_abs).convert('RGB')
                    image_tensor = self.image_transform(image)
                    image_available = True
                else:
                    logging.debug(f"Image file not found for item {item_id} at {image_path_abs}")
            except UnidentifiedImageError:
                logging.warning(f"Could not read image file (unidentified format) for item {item_id} at {image_path_abs}")
            except Exception as e:
                logging.warning(f"Error loading image for item {item_id} at {image_path_abs}: {e}")

        # --- Label Processing ---
        label_tensor = torch.tensor(label, dtype=torch.float)

        return {
            'id': item_id,
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'image': image_tensor,
            'label': label_tensor,
            'image_available': torch.tensor(image_available, dtype=torch.bool)
        }

# --- Setup Functions ---

def get_tokenizer(model_name=TEXT_MODEL_NAME):
    logging.info(f"Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer

def get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE, mean=IMG_MEAN, std=IMG_STD, augment=False):
    logging.info("Defining image transforms...")
    size = (input_size, input_size) if isinstance(input_size, int) else input_size
    base_transforms = [
        transforms.Resize(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=mean, std=std)
    ]
    if augment:
        augmentation_transforms = [
            transforms.RandomHorizontalFlip(),
        ]
        transform_list = augmentation_transforms + base_transforms
    else:
        transform_list = base_transforms
    return transforms.Compose(transform_list)

# --- Main Execution Example (移除 metadata 相关) ---

if __name__ == '__main__':
    logging.info("--- Starting Data Loader Setup (Metadata Excluded) ---")

    tokenizer = get_tokenizer()
    image_transform = get_image_transforms()

    try:
        dataset = MultimodalFakeNewsDataset(
            dataframe=pd.read_csv(CSV_PATH),
            data_dir=DATA_DIR,
            tokenizer=tokenizer,
            image_transform=image_transform,
            max_len=MAX_TEXT_LEN,
        )
        logging.info(f"Dataset created successfully with {len(dataset)} samples.")

        batch_size = 16
        data_loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)
        logging.info(f"DataLoader created with batch size {batch_size}.")

        logging.info("Fetching one batch as an example...")
        try:
            first_batch = next(iter(data_loader))
            print("\n--- Example Batch Contents ---")
            print(f"Batch Keys: {first_batch.keys()}")
            print(f"Item IDs (sample): {first_batch['id'][:4]}...")
            print(f"Input IDs Shape: {first_batch['input_ids'].shape}")
            print(f"Attention Mask Shape: {first_batch['attention_mask'].shape}")
            print(f"Image Tensor Shape: {first_batch['image'].shape}")
            print(f"Label Tensor Shape: {first_batch['label'].shape}")
            print(f"Image Available Flags (sample): {first_batch['image_available'][:4]}...")
            print("--- End Example Batch ---")
        except StopIteration:
             logging.warning("Could not fetch a batch, is the dataset empty?")
        except Exception as e:
             logging.error(f"Error fetching or displaying batch: {e}", exc_info=True)

    except Exception as e:
         logging.error(f"Failed to initialize Dataset: {e}", exc_info=True)

    logging.info("--- Data Loader Setup Finished ---")