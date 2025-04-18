import os
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from PIL import Image, UnidentifiedImageError
from torchvision import transforms
from transformers import AutoTokenizer # Use AutoTokenizer for flexibility
from sklearn.preprocessing import StandardScaler # Example for scaling metadata
import numpy as np
from pathlib import Path
import logging

# Configure logging (optional but helpful)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Adjust these paths and parameters as needed
BASE_DIR = Path(__file__).parent.parent # Assumes script is in 'scripts' folder
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CSV_PATH = PROCESSED_DIR / 'processed_data.csv'
IMAGE_DIR = PROCESSED_DIR / 'images' # This is where process_image saves files

# Model-specific parameters (CHANGE THESE)
TEXT_MODEL_NAME = 'bert-base-chinese' # Or your chosen HuggingFace model
IMAGE_MODEL_INPUT_SIZE = 224 # Common size, e.g., for ResNet, ViT
MAX_TEXT_LEN = 128 # Max sequence length for tokenizer

# ImageNet normalization (common for many pre-trained image models)
IMG_MEAN = [0.485, 0.456, 0.406]
IMG_STD = [0.229, 0.224, 0.225]

# Define the columns containing metadata features
METADATA_COLS = [
    'total_likes', 'total_comments', 'total_reposts', 'total_views',
    'user_followers', 'user_following', 'user_posts', 'user_verified',
    'user_total_favorited'
]

# --- Custom PyTorch Dataset ---

class MultimodalFakeNewsDataset(Dataset):
    """
    Custom PyTorch Dataset for loading multimodal fake news data.
    Handles text, image (if available), metadata, and labels.
    """
    def __init__(self, dataframe, data_dir, tokenizer, image_transform, max_len, metadata_cols, metadata_scaler=None):
        """
        Args:
            dataframe (pd.DataFrame): Pre-loaded and pre-split DataFrame for this dataset part (train/val/test).
            data_dir (Path or str): Path to the base 'data' directory. Needed to construct absolute image paths.
            tokenizer: Initialized HuggingFace tokenizer.
            image_transform: torchvision transforms to apply to images.
            max_len (int): Maximum sequence length for text tokenization.
            metadata_cols (list): List of column names for metadata features.
            metadata_scaler: Optional fitted sklearn scaler for metadata.
        """
        self.data_dir = Path(data_dir)
        self.image_base_dir = self.data_dir / 'processed' / 'images' # Correct base for images
        self.tokenizer = tokenizer
        self.image_transform = image_transform
        self.max_len = max_len
        self.metadata_cols = metadata_cols
        self.metadata_scaler = metadata_scaler

        # logging.info(f"Loading data from: {csv_path}") # No longer reading from csv_path
        logging.info(f"Initializing Dataset with {len(dataframe)} records.")
        try:
            # Use the passed DataFrame directly
            self.df = dataframe.copy() # Use copy to avoid modifying original df outside class
            
            # logging.info(f"Loaded {len(self.df)} records.")
            # Pre-process common issues
            self.df['image_path'] = self.df['image_path'].fillna('') # Replace NaN image paths with empty string
            self.df['text'] = self.df['text'].fillna('') # Replace NaN text with empty string
            # Ensure metadata columns are numeric, fill NaNs with 0 before potential scaling
            for col in self.metadata_cols:
                if col in self.df.columns:
                    self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
                else:
                    logging.warning(f"Metadata column '{col}' not found in DataFrame. Creating it with zeros.")
                    self.df[col] = 0
            
            # --- Metadata Scaling (Important Note) ---
            # It's best practice to FIT the scaler ONLY on the training data
            # and then use the SAME fitted scaler to TRANSFORM train, val, and test sets.
            # If you pass a *fitted* scaler here, it will be applied in __getitem__.
            # If metadata_scaler is None, raw (but cleaned) metadata values will be returned.
            if self.metadata_scaler:
                 logging.info("Applying provided metadata scaler.")
                 # Apply scaler here to the whole relevant part of the dataframe for efficiency,
                 # assuming scaler expects a 2D array.
                 # Ensure columns exist before scaling
                 cols_to_scale = [col for col in self.metadata_cols if col in self.df.columns]
                 if cols_to_scale:
                     scaled_metadata = self.metadata_scaler.transform(self.df[cols_to_scale])
                     # Create new columns for scaled data or overwrite existing ones
                     for i, col in enumerate(cols_to_scale):
                          self.df[f"scaled_{col}"] = scaled_metadata[:, i]
                     self.scaled_metadata_cols = [f"scaled_{col}" for col in cols_to_scale]
                     logging.info("Metadata scaling applied.")
                 else:
                     logging.warning("No valid metadata columns found to apply scaler.")
                     self.scaled_metadata_cols = [] # No scaled cols if none were scaled
            else:
                 logging.warning("No metadata scaler provided. Using raw metadata features.")
                 # Use original columns if no scaler, ensuring they exist
                 self.scaled_metadata_cols = [col for col in self.metadata_cols if col in self.df.columns]

        # except FileNotFoundError: # No longer applicable
        #     logging.error(f"Error: CSV file not found at {csv_path}")
        #     raise
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
        image_path_rel = row['image_path'] # Relative path like 'processed/images/...' or ''

        # --- Text Processing ---
        encoding = self.tokenizer.encode_plus(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_token_type_ids=False, # Not needed for BERT classification usually
            return_attention_mask=True,
            return_tensors='pt',
        )
        input_ids = encoding['input_ids'].flatten()
        attention_mask = encoding['attention_mask'].flatten()

        # --- Image Processing ---
        image_tensor = None
        image_available = False
        # Construct absolute path only if relative path is not empty
        if image_path_rel and isinstance(image_path_rel, str):
            # image_path_rel might be like 'processed/images/mcfend_....jpg'
            # We need the path relative to the IMAGE_DIR defined above
            # Assumes the process_image script saved paths like 'processed/images/...'
            # So, construct path from BASE_DIR
            image_path_abs = self.data_dir / image_path_rel
            try:
                # Check if file actually exists before trying to open
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

        # If image not available or loading failed, create a placeholder tensor
        if not image_available:
            # Placeholder: tensor of zeros with the expected shape (Channels, Height, Width)
            image_tensor = torch.zeros(3, IMAGE_MODEL_INPUT_SIZE, IMAGE_MODEL_INPUT_SIZE)

        # --- Metadata Processing ---
        # Select the appropriate columns (scaled or raw)
        metadata_values = row[self.scaled_metadata_cols].values.astype(np.float32)
        metadata_tensor = torch.tensor(metadata_values, dtype=torch.float)

        # --- Label Processing ---
        # Use float for BCEWithLogitsLoss
        label_tensor = torch.tensor(label, dtype=torch.float)

        return {
            'id': item_id,
            'input_ids': input_ids,
            'attention_mask': attention_mask,
            'image': image_tensor,
            'metadata': metadata_tensor,
            'label': label_tensor,
            'image_available': torch.tensor(image_available, dtype=torch.bool) # Flag if image was loaded
        }

# --- Setup Functions ---

def get_tokenizer(model_name=TEXT_MODEL_NAME):
    """Initializes and returns the tokenizer."""
    logging.info(f"Loading tokenizer: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer

def get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE, mean=IMG_MEAN, std=IMG_STD, augment=False):
    """Defines and returns the image transformations."""
    logging.info("Defining image transforms...")
    # Basic transforms for inference/validation. Add data augmentation for training if needed.
    size = (input_size, input_size) if isinstance(input_size, int) else input_size

    # Standard transforms (Resize, ToTensor, Normalize)
    base_transforms = [
        transforms.Resize(size),
        transforms.ToTensor(), # Converts PIL image to tensor and scales pixels to [0, 1]
        transforms.Normalize(mean=mean, std=std) # Normalize using pre-trained model stats
    ]

    if augment:
        # Add augmentation transforms before ToTensor and Normalize
        augmentation_transforms = [
            transforms.RandomHorizontalFlip(),
            # Add more augmentations as needed, e.g.:
            # transforms.RandomRotation(10),
            # transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.1),
        ]
        # Combine augmentations with base transforms
        transform_list = augmentation_transforms + base_transforms
    else:
        # Use only base transforms for validation/testing
        transform_list = base_transforms

    return transforms.Compose(transform_list)

def get_metadata_scaler(csv_path, metadata_cols):
    """
    Loads data, fits and returns a StandardScaler for metadata.
    IMPORTANT: This should ideally be done ONLY on the training split.
               Returning None here to emphasize fitting should happen outside/beforehand.
    """
    logging.warning("Metadata scaler fitting NOT implemented in this script.")
    logging.warning("Fit a scaler (e.g., StandardScaler) on your TRAINING data metadata "
                    "and pass the *fitted* scaler to the Dataset.")
    # # Example of how you *might* fit it (but do this on training data only):
    # try:
    #     df = pd.read_csv(csv_path)
    #     for col in metadata_cols:
    #          if col in df.columns:
    #              df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    #          else:
    #              df[col] = 0
    #     scaler = StandardScaler()
    #     scaler.fit(df[metadata_cols])
    #     logging.info("Example scaler fitted (use training data only).")
    #     return scaler
    # except Exception as e:
    #      logging.error(f"Could not fit example scaler: {e}")
    return None # Return None to use raw features in the Dataset for now

# --- Main Execution Example ---

if __name__ == '__main__':
    logging.info("--- Starting Data Loader Setup ---")

    # 1. Initialize Tokenizer and Transforms
    tokenizer = get_tokenizer()
    image_transform = get_image_transforms()

    # 2. Prepare Metadata Scaler (Fit on training data separately!)
    # For this example, we'll pass None, meaning the Dataset will use raw values.
    metadata_scaler = get_metadata_scaler(CSV_PATH, METADATA_COLS)

    # 3. Create the Dataset instance
    try:
        dataset = MultimodalFakeNewsDataset(
            dataframe=pd.read_csv(CSV_PATH),
            data_dir=DATA_DIR,
            tokenizer=tokenizer,
            image_transform=image_transform,
            max_len=MAX_TEXT_LEN,
            metadata_cols=METADATA_COLS,
            metadata_scaler=metadata_scaler # Pass the fitted scaler here if available
        )
        logging.info(f"Dataset created successfully with {len(dataset)} samples.")

        # 4. Create DataLoader instance (example for full dataset)
        # In practice, you'd split dataset into train/val/test and create separate DataLoaders
        batch_size = 16 # Adjust as needed
        data_loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True, # Shuffle for training
            num_workers=2 # Adjust based on your system for parallel loading
        )
        logging.info(f"DataLoader created with batch size {batch_size}.")

        # 5. Example: Iterate through one batch
        logging.info("Fetching one batch as an example...")
        try:
            first_batch = next(iter(data_loader))

            print("\n--- Example Batch Contents ---")
            print(f"Batch Keys: {first_batch.keys()}")
            print(f"Item IDs (sample): {first_batch['id'][:4]}...") # Show first few IDs
            print(f"Input IDs Shape: {first_batch['input_ids'].shape}") # [batch_size, max_len]
            print(f"Attention Mask Shape: {first_batch['attention_mask'].shape}") # [batch_size, max_len]
            print(f"Image Tensor Shape: {first_batch['image'].shape}") # [batch_size, 3, H, W]
            print(f"Metadata Tensor Shape: {first_batch['metadata'].shape}") # [batch_size, num_metadata_features]
            print(f"Label Tensor Shape: {first_batch['label'].shape}") # [batch_size]
            print(f"Image Available Flags (sample): {first_batch['image_available'][:4]}...") # [batch_size]
            print("--- End Example Batch ---")

        except StopIteration:
             logging.warning("Could not fetch a batch, is the dataset empty?")
        except Exception as e:
             logging.error(f"Error fetching or displaying batch: {e}", exc_info=True)

    except Exception as e:
         logging.error(f"Failed to initialize Dataset: {e}", exc_info=True)

    logging.info("--- Data Loader Setup Finished ---")