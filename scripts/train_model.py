# scripts/train_model.py

import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchvision.models import resnet50, ResNet50_Weights
from transformers import AutoModel, AutoTokenizer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from pathlib import Path
import logging
import time
import joblib # For saving the scaler
from tqdm import tqdm # Import tqdm

# Import the custom Dataset from data_loader.py
from data_loader import MultimodalFakeNewsDataset, get_tokenizer, get_image_transforms

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CSV_PATH = PROCESSED_DIR / 'processed_data.csv'
OUTPUT_DIR = BASE_DIR / 'models' # Directory to save models and scaler
OUTPUT_DIR.mkdir(exist_ok=True)
SCALER_PATH = OUTPUT_DIR / 'metadata_scaler.joblib'
BEST_MODEL_PATH = OUTPUT_DIR / 'best_multimodal_model.pth'

# Model Parameters (Adjust as needed)
TEXT_MODEL_NAME = 'bert-base-chinese'
IMAGE_MODEL_NAME = 'resnet50' # Using ResNet50 as an example
IMAGE_MODEL_INPUT_SIZE = 224
MAX_TEXT_LEN = 128
NUM_METADATA_FEATURES = 9 # Update if METADATA_COLS changes in data_loader
IMG_EMBEDDING_DIM = 2048 # Output dim of ResNet50 before final layer
TEXT_EMBEDDING_DIM = 768 # Output dim of bert-base-chinese hidden state
METADATA_EMBEDDING_DIM = 64 # Example dimension for MLP output
FUSION_OUTPUT_DIM = 256 # Example dimension after fusion

# Training Hyperparameters (Adjust as needed)
EPOCHS = 20 # Increase epochs slightly to allow for early stopping
BATCH_SIZE = 32 # Adjust based on GPU memory
LEARNING_RATE_ENCODERS = 1e-5 # Lower LR for pre-trained encoders
LEARNING_RATE_HEAD = 1e-4 # Higher LR for newly added layers
WEIGHT_DECAY = 0.01
VALIDATION_SPLIT = 0.15 # Use 15% of data for validation
TEST_SPLIT = 0.15 # Use 15% of data for testing
RANDOM_SEED = 42
EARLY_STOPPING_PATIENCE = 3 # Number of epochs to wait for improvement before stopping
LR_SCHEDULER_PATIENCE = 1 # Number of epochs to wait for improvement before reducing LR
LR_SCHEDULER_FACTOR = 0.1 # Factor by which the learning rate will be reduced

# --- Model Definition ---

class MetadataEncoder(nn.Module):
    """ Simple MLP for processing metadata features. """
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, input_dim * 2)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.4) # Increased dropout rate
        self.fc2 = nn.Linear(input_dim * 2, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        return x

class MultimodalFakeNewsModel(nn.Module):
    """
    Multimodal model combining text, image, and metadata.
    Uses simple concatenation for fusion as a starting point.
    """
    def __init__(self, text_model_name, image_model_name, num_metadata_features,
                 text_embedding_dim, img_embedding_dim, metadata_embedding_dim,
                 fusion_output_dim, freeze_encoders=False):
        super().__init__()
        logging.info("Initializing Multimodal Model...")

        # Text Encoder
        logging.info(f"Loading text model: {text_model_name}")
        self.text_encoder = AutoModel.from_pretrained(text_model_name)

        # Image Encoder
        logging.info(f"Loading image model: {image_model_name}")
        if image_model_name == 'resnet50':
            weights = ResNet50_Weights.IMAGENET1K_V2 # Use recommended weights
            self.image_encoder = resnet50(weights=weights)
            # Remove the final classification layer of ResNet
            self.image_encoder.fc = nn.Identity()
            self.img_embedding_dim = IMG_EMBEDDING_DIM # ResNet50 output feature dim
            self.image_transform = weights.transforms() # Get standard transforms for this model
            self.image_input_size = 224 # ResNet50 expects 224x224
            logging.info(f"Using standard ResNet50 transforms (input size {self.image_input_size})")
        else:
            # Add logic for other image models if needed
            raise ValueError(f"Image model '{image_model_name}' not currently supported.")
            # Example for a generic CNN:
            # self.image_encoder = ...
            # self.img_embedding_dim = ... # Set appropriate dim
            # self.image_transform = get_image_transforms(IMAGE_MODEL_INPUT_SIZE) # Use basic transforms
            # self.image_input_size = IMAGE_MODEL_INPUT_SIZE

        # Metadata Encoder
        logging.info("Initializing metadata encoder (MLP)...")
        self.metadata_encoder = MetadataEncoder(num_metadata_features, metadata_embedding_dim)

        # Freeze encoders if requested
        if freeze_encoders:
             logging.info("Freezing text and image encoders.")
             for param in self.text_encoder.parameters():
                 param.requires_grad = False
             for param in self.image_encoder.parameters():
                 param.requires_grad = False

        # Fusion Layer (Simple Concatenation + MLP)
        logging.info("Initializing fusion layer...")
        self.fusion_dim = text_embedding_dim + self.img_embedding_dim + metadata_embedding_dim
        self.fusion_layer = nn.Sequential(
            nn.Linear(self.fusion_dim, fusion_output_dim),
            nn.ReLU(),
            nn.Dropout(0.5) # Increased dropout rate
        )

        # Classifier Head
        logging.info("Initializing classifier head...")
        self.classifier = nn.Linear(fusion_output_dim, 1) # Output a single logit for binary classification

    def forward(self, input_ids, attention_mask, image, metadata, image_available):
        # Text Features
        text_outputs = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        # Use the [CLS] token embedding (or mean pooling)
        text_features = text_outputs.last_hidden_state[:, 0, :] # Shape: [batch_size, text_embedding_dim]

        # Image Features
        # Process only images that were successfully loaded
        # Create a placeholder for image features
        batch_size = image.shape[0]
        image_features = torch.zeros(batch_size, self.img_embedding_dim, device=image.device)
        
        valid_image_mask = image_available.bool() # Ensure it's boolean
        if valid_image_mask.any(): # Only process if at least one image is valid
            valid_images = image[valid_image_mask]
            valid_image_features = self.image_encoder(valid_images) # Shape: [num_valid_images, img_embedding_dim]
            image_features[valid_image_mask] = valid_image_features

        # Metadata Features
        metadata_features = self.metadata_encoder(metadata) # Shape: [batch_size, metadata_embedding_dim]

        # Fusion
        # Concatenate features along the feature dimension (dim=1)
        fused_features = torch.cat((text_features, image_features, metadata_features), dim=1)
        fused_output = self.fusion_layer(fused_features)

        # Classification
        logits = self.classifier(fused_output) # Shape: [batch_size, 1]
        return logits.squeeze(-1) # Return shape: [batch_size] for BCEWithLogitsLoss

# --- Training and Evaluation Functions ---

def train_epoch(model, data_loader, loss_fn, optimizer, device): # Removed scheduler argument for now
    """ Trains the model for one epoch. """
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for batch in tqdm(data_loader, desc="Training"):
        # Move batch to device
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        images = batch['image'].to(device)
        metadata = batch['metadata'].to(device)
        labels = batch['label'].to(device)
        image_available = batch['image_available'].to(device)

        optimizer.zero_grad()

        # Forward pass
        outputs = model(input_ids, attention_mask, images, metadata, image_available)
        loss = loss_fn(outputs, labels)

        # Backward pass and optimize
        loss.backward()
        optimizer.step()
        # Remove scheduler step from here if using ReduceLROnPlateau
        # if scheduler:
        #     scheduler.step() # Optional: learning rate scheduler

        total_loss += loss.item()

        # Store predictions and labels for epoch metrics
        preds = torch.sigmoid(outputs).detach().cpu().numpy() # Get probabilities
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(data_loader)
    # Calculate metrics based on probabilities (e.g., threshold at 0.5)
    all_preds_binary = (np.array(all_preds) >= 0.5).astype(int)
    accuracy = accuracy_score(all_labels, all_preds_binary)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds_binary, average='binary', zero_division=0)

    logging.info(f"Train Epoch Summary: Avg Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    return avg_loss, f1


def evaluate_epoch(model, data_loader, loss_fn, device):
    """ Evaluates the model on the validation/test set. """
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            images = batch['image'].to(device)
            metadata = batch['metadata'].to(device)
            labels = batch['label'].to(device)
            image_available = batch['image_available'].to(device)

            outputs = model(input_ids, attention_mask, images, metadata, image_available)
            loss = loss_fn(outputs, labels)
            total_loss += loss.item()

            preds = torch.sigmoid(outputs).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(data_loader)
    all_preds_binary = (np.array(all_preds) >= 0.5).astype(int)
    accuracy = accuracy_score(all_labels, all_preds_binary)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds_binary, average='binary', zero_division=0)
    try:
        auc = roc_auc_score(all_labels, all_preds) # AUC uses probabilities
    except ValueError: # Handle case where only one class is present in batch/dataset
        auc = 0.0
        logging.warning("AUC calculation failed (likely only one class present in labels). Setting AUC to 0.0")


    logging.info(f"Eval Summary: Avg Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}, AUC: {auc:.4f}")
    # Return all metrics
    return avg_loss, accuracy, precision, recall, f1, auc

# --- Main Training Orchestration ---

# Ensure METADATA_COLS is defined in the global scope before main uses it
# (Ideally, keep this definition in the Configuration section at the top,
# but defining it here ensures it's available for the fix)
METADATA_COLS = [
    'total_likes', 'total_comments', 'total_reposts', 'total_views',
    'user_followers', 'user_following', 'user_posts', 'user_verified',
    'user_total_favorited'
]

def main():
    logging.info("--- Starting Model Training ---")
    start_time = time.time()

    # Set random seed for reproducibility
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(RANDOM_SEED)

    # 1. Load Data and Split
    logging.info("Loading and splitting data...")
    try:
        df = pd.read_csv(CSV_PATH)
        # Stratified split based on labels to maintain distribution
        train_val_df, test_df = train_test_split(df, test_size=TEST_SPLIT, random_state=RANDOM_SEED, stratify=df['label'])
        train_df, val_df = train_test_split(train_val_df, test_size=VALIDATION_SPLIT/(1-TEST_SPLIT), random_state=RANDOM_SEED, stratify=train_val_df['label']) # Adjust validation split size
        logging.info(f"Data split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    except FileNotFoundError:
        logging.error(f"FATAL: Processed CSV not found at {CSV_PATH}. Run preprocess script first.")
        return
    except Exception as e:
         logging.error(f"FATAL: Error loading or splitting data: {e}")
         return

    # 2. Metadata Scaler
    logging.info("Fitting metadata scaler on training data...")
    metadata_scaler = StandardScaler()
    # Ensure metadata columns exist and handle potential NaNs before fitting
    for col in METADATA_COLS:
         if col not in train_df.columns:
             logging.warning(f"Metadata column '{col}' not found in training data! Adding with zeros.")
             train_df[col] = 0
             val_df[col] = 0
             test_df[col] = 0
         else:
             # Ensure conversion to numeric before filling NaN
             train_df[col] = pd.to_numeric(train_df[col], errors='coerce').fillna(0)
             val_df[col] = pd.to_numeric(val_df[col], errors='coerce').fillna(0)
             test_df[col] = pd.to_numeric(test_df[col], errors='coerce').fillna(0)

    try:
        metadata_scaler.fit(train_df[METADATA_COLS])
        joblib.dump(metadata_scaler, SCALER_PATH) # Save the fitted scaler
        logging.info(f"Metadata scaler fitted and saved to {SCALER_PATH}")
    except ValueError as e:
        logging.error(f"FATAL: Error fitting scaler. Check if all metadata columns contain valid numeric data after processing. Error: {e}")
        return
    except Exception as e:
         logging.error(f"FATAL: Error fitting or saving scaler: {e}")
         return


    # 3. Setup Datasets and DataLoaders
    logging.info("Creating Datasets and DataLoaders...")
    tokenizer = get_tokenizer(TEXT_MODEL_NAME)
    # Use basic transforms for now, add augmentation for training later
    # Consider adding image augmentation for the training set here
    image_transform = get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE) # Same transform for val/test
    train_image_transform = get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE, augment=True) # Add augment=True flag for training transforms

    try:
        # Create datasets for each split, passing the FITTED scaler
        # Use augmented transforms for training dataset
        train_dataset = MultimodalFakeNewsDataset(train_df, DATA_DIR, tokenizer, train_image_transform, MAX_TEXT_LEN, METADATA_COLS, metadata_scaler)
        val_dataset = MultimodalFakeNewsDataset(val_df, DATA_DIR, tokenizer, image_transform, MAX_TEXT_LEN, METADATA_COLS, metadata_scaler)
        test_dataset = MultimodalFakeNewsDataset(test_df, DATA_DIR, tokenizer, image_transform, MAX_TEXT_LEN, METADATA_COLS, metadata_scaler)

        # Create DataLoaders
        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True) # Added pin_memory
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
        logging.info("DataLoaders created.")
    except Exception as e:
         logging.error(f"FATAL: Error creating Datasets or DataLoaders: {e}", exc_info=True)
         return

    # 4. Setup Model, Optimizer, Loss
    logging.info("Setting up model, optimizer, and loss...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")

    model = MultimodalFakeNewsModel(
        text_model_name=TEXT_MODEL_NAME,
        image_model_name=IMAGE_MODEL_NAME,
        num_metadata_features=NUM_METADATA_FEATURES,
        text_embedding_dim=TEXT_EMBEDDING_DIM,
        img_embedding_dim=IMG_EMBEDDING_DIM,
        metadata_embedding_dim=METADATA_EMBEDDING_DIM,
        fusion_output_dim=FUSION_OUTPUT_DIM,
        freeze_encoders=False # Set to True to freeze pre-trained parts initially
    ).to(device)

    # Use different learning rates for encoders vs head (optional but common)
    optimizer = optim.AdamW([
        {'params': model.text_encoder.parameters(), 'lr': LEARNING_RATE_ENCODERS},
        {'params': model.image_encoder.parameters(), 'lr': LEARNING_RATE_ENCODERS},
        {'params': model.metadata_encoder.parameters(), 'lr': LEARNING_RATE_HEAD},
        {'params': model.fusion_layer.parameters(), 'lr': LEARNING_RATE_HEAD},
        {'params': model.classifier.parameters(), 'lr': LEARNING_RATE_HEAD}
    ], weight_decay=WEIGHT_DECAY)

    # Loss function
    loss_fn = nn.BCEWithLogitsLoss()

    # Learning Rate Scheduler (Optional but Recommended)
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=LR_SCHEDULER_FACTOR, patience=LR_SCHEDULER_PATIENCE, verbose=True)

    # 5. Training Loop with Early Stopping
    logging.info("--- Starting Training Loop ---")
    best_val_f1 = -1.0
    epochs_no_improve = 0
    best_epoch = 0 # Track the epoch of the best model

    for epoch in range(EPOCHS):
        epoch_start_time = time.time()
        logging.info(f"Epoch {epoch + 1}/{EPOCHS}")

        train_loss, train_f1 = train_epoch(model, train_loader, loss_fn, optimizer, device)
        val_loss, val_acc, val_prec, val_rec, val_f1, val_auc = evaluate_epoch(model, val_loader, loss_fn, device)

        epoch_duration = time.time() - epoch_start_time
        logging.info(f"Epoch {epoch + 1} duration: {epoch_duration:.2f} seconds")

        # Learning rate scheduler step (based on validation F1)
        scheduler.step(val_f1)

        # Early Stopping Check and Save Best Model
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch + 1
            torch.save(model.state_dict(), BEST_MODEL_PATH)
            logging.info(f"*** New best model saved with Val F1: {best_val_f1:.4f} at epoch {best_epoch} ***")
            epochs_no_improve = 0 # Reset counter
        else:
            epochs_no_improve += 1
            logging.info(f"Validation F1 did not improve for {epochs_no_improve} epoch(s). Current best F1: {best_val_f1:.4f} at epoch {best_epoch}.")

        if epochs_no_improve >= EARLY_STOPPING_PATIENCE:
            logging.info(f"--- Early stopping triggered after {epoch + 1} epochs. ---")
            break # Exit the training loop

    logging.info("--- Training Finished ---")

    # 6. Final Evaluation on Test Set
    logging.info("--- Evaluating on Test Set using Best Model ---")
    try:
        # Load the best model weights saved during training
        if os.path.exists(BEST_MODEL_PATH):
            model.load_state_dict(torch.load(BEST_MODEL_PATH))
            logging.info(f"Loaded best model from epoch {best_epoch} ({BEST_MODEL_PATH}) with Val F1: {best_val_f1:.4f}")
            # Receive all metrics from evaluate_epoch
            test_loss, test_acc, test_prec, test_rec, test_f1, test_auc = evaluate_epoch(model, test_loader, loss_fn, device)
            # Log all received metrics
            logging.info(f"Test Set Performance: Loss: {test_loss:.4f}, Accuracy: {test_acc:.4f}, Precision: {test_prec:.4f}, Recall: {test_rec:.4f}, F1: {test_f1:.4f}, AUC: {test_auc:.4f}")
        else:
             logging.error(f"Could not find best model at {BEST_MODEL_PATH} for final testing. Evaluating with the model from the last epoch.")
             # Optionally evaluate with the model state at the end of the loop
             test_loss, test_acc, test_prec, test_rec, test_f1, test_auc = evaluate_epoch(model, test_loader, loss_fn, device)
             logging.info(f"Test Set Performance (last epoch model): Loss: {test_loss:.4f}, Accuracy: {test_acc:.4f}, Precision: {test_prec:.4f}, Recall: {test_rec:.4f}, F1: {test_f1:.4f}, AUC: {test_auc:.4f}")

    except Exception as e:
         logging.error(f"Error during final test evaluation: {e}")

    total_duration = time.time() - start_time
    logging.info(f"Total script duration: {total_duration / 60:.2f} minutes")


if __name__ == '__main__':
    main()