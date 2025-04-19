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
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
from pathlib import Path
import logging
import time
from tqdm import tqdm

# Import the modified Dataset (不包含 metadata)
from data_loader import MultimodalFakeNewsDataset, get_tokenizer, get_image_transforms

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration (移除 Metadata 相关) ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CSV_PATH = PROCESSED_DIR / 'processed_data.csv'
OUTPUT_DIR = BASE_DIR / 'models' 
OUTPUT_DIR.mkdir(exist_ok=True)
# SCALER_PATH = OUTPUT_DIR / 'metadata_scaler.joblib' # 移除 Scaler 路径
# BEST_MODEL_PATH = OUTPUT_DIR / 'best_multimodal_model.pth' # 可以重命名，避免覆盖旧模型
BEST_MODEL_PATH = OUTPUT_DIR / 'best_text_image_model.pth' 

TEXT_MODEL_NAME = 'bert-base-chinese'
IMAGE_MODEL_NAME = 'resnet50'
IMAGE_MODEL_INPUT_SIZE = 224
MAX_TEXT_LEN = 128
# NUM_METADATA_FEATURES = 0 # 移除
IMG_EMBEDDING_DIM = 2048 
TEXT_EMBEDDING_DIM = 768 
# METADATA_EMBEDDING_DIM = 0 # 移除
FUSION_OUTPUT_DIM = 256 

EPOCHS = 20 
BATCH_SIZE = 32 
LEARNING_RATE_ENCODERS = 1e-5 
LEARNING_RATE_HEAD = 1e-4 
WEIGHT_DECAY = 0.01
VALIDATION_SPLIT = 0.15 
TEST_SPLIT = 0.15 
RANDOM_SEED = 42
EARLY_STOPPING_PATIENCE = 3 
LR_SCHEDULER_PATIENCE = 1 
LR_SCHEDULER_FACTOR = 0.1 

# --- Model Definition (移除 MetadataEncoder 和相关逻辑) ---

# 移除 MetadataEncoder 类
# class MetadataEncoder(nn.Module): ...

class MultimodalFakeNewsModel(nn.Module):
    """
    Multimodal model combining text and image.
    (Modified to exclude metadata)
    """
    # 移除 num_metadata_features, metadata_embedding_dim 参数
    def __init__(self, text_model_name, image_model_name,
                 text_embedding_dim, img_embedding_dim,
                 fusion_output_dim, freeze_encoders=False):
        super().__init__()
        logging.info("Initializing Text-Image Multimodal Model...")

        # Text Encoder (保持不变)
        logging.info(f"Loading text model: {text_model_name}")
        self.text_encoder = AutoModel.from_pretrained(text_model_name)

        # Image Encoder (保持不变)
        logging.info(f"Loading image model: {image_model_name}")
        if image_model_name == 'resnet50':
            weights = ResNet50_Weights.IMAGENET1K_V2
            self.image_encoder = resnet50(weights=weights)
            self.image_encoder.fc = nn.Identity()
            self.img_embedding_dim = IMG_EMBEDDING_DIM
            self.image_transform = weights.transforms()
            self.image_input_size = 224
            logging.info(f"Using standard ResNet50 transforms (input size {self.image_input_size})")
        else:
            raise ValueError(f"Image model '{image_model_name}' not currently supported.")
        
        # 移除 Metadata Encoder 初始化
        # logging.info("Initializing metadata encoder (MLP)...")
        # self.metadata_encoder = MetadataEncoder(num_metadata_features, metadata_embedding_dim)

        # Freeze encoders if requested (保持不变)
        if freeze_encoders:
            logging.info("Freezing text and image encoders.")
            for param in self.text_encoder.parameters():
                 param.requires_grad = False
            for param in self.image_encoder.parameters():
                 param.requires_grad = False

        # Fusion Layer (调整输入维度)
        logging.info("Initializing fusion layer...")
        # 新的融合维度只包含文本和图像
        self.fusion_dim = text_embedding_dim + self.img_embedding_dim 
        self.fusion_layer = nn.Sequential(
            nn.Linear(self.fusion_dim, fusion_output_dim),
            nn.ReLU(),
            nn.Dropout(0.5) 
        )

        # Classifier Head (保持不变)
        logging.info("Initializing classifier head...")
        self.classifier = nn.Linear(fusion_output_dim, 1)

    # 移除 forward 方法中的 metadata 参数
    def forward(self, input_ids, attention_mask, image, image_available):
        # Text Features (保持不变)
        text_outputs = self.text_encoder(input_ids=input_ids, attention_mask=attention_mask)
        text_features = text_outputs.last_hidden_state[:, 0, :]

        # Image Features (保持不变)
        batch_size = image.shape[0]
        image_features = torch.zeros(batch_size, self.img_embedding_dim, device=image.device)
        valid_image_mask = image_available.bool()
        if valid_image_mask.any():
            valid_images = image[valid_image_mask]
            valid_image_features = self.image_encoder(valid_images)
            image_features[valid_image_mask] = valid_image_features

        # 移除 Metadata Features 处理
        # metadata_features = self.metadata_encoder(metadata)

        # Fusion (只融合文本和图像)
        fused_features = torch.cat((text_features, image_features), dim=1)
        fused_output = self.fusion_layer(fused_features)

        # Classification (保持不变)
        logits = self.classifier(fused_output)
        return logits.squeeze(-1)

# --- Training and Evaluation Functions (移除 metadata 相关) ---

def train_epoch(model, data_loader, loss_fn, optimizer, device):
    model.train()
    total_loss = 0
    all_preds = []
    all_labels = []

    for batch in tqdm(data_loader, desc="Training"):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        images = batch['image'].to(device)
        # metadata = batch['metadata'].to(device) # 移除
        labels = batch['label'].to(device)
        image_available = batch['image_available'].to(device)

        optimizer.zero_grad()

        # 移除 forward 调用中的 metadata
        outputs = model(input_ids, attention_mask, images, image_available)
        loss = loss_fn(outputs, labels)

        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        preds = torch.sigmoid(outputs).detach().cpu().numpy()
        all_preds.extend(preds)
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(data_loader)
    all_preds_binary = (np.array(all_preds) >= 0.5).astype(int)
    accuracy = accuracy_score(all_labels, all_preds_binary)
    precision, recall, f1, _ = precision_recall_fscore_support(all_labels, all_preds_binary, average='binary', zero_division=0)
    logging.info(f"Train Epoch Summary: Avg Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}")
    return avg_loss, f1

def evaluate_epoch(model, data_loader, loss_fn, device):
    model.eval()
    total_loss = 0
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Evaluating"):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            images = batch['image'].to(device)
            # metadata = batch['metadata'].to(device) # 移除
            labels = batch['label'].to(device)
            image_available = batch['image_available'].to(device)

            # 移除 forward 调用中的 metadata
            outputs = model(input_ids, attention_mask, images, image_available)
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
        auc = roc_auc_score(all_labels, all_preds)
    except ValueError:
        auc = 0.0
        logging.warning("AUC calculation failed (likely only one class present in labels). Setting AUC to 0.0")

    logging.info(f"Eval Summary: Avg Loss: {avg_loss:.4f}, Accuracy: {accuracy:.4f}, Precision: {precision:.4f}, Recall: {recall:.4f}, F1: {f1:.4f}, AUC: {auc:.4f}")
    return avg_loss, accuracy, precision, recall, f1, auc

# --- Main Training Orchestration (移除 metadata 相关) ---

# 移除 METADATA_COLS 定义
# METADATA_COLS = [...] 

def main():
    logging.info("--- Starting Model Training (Metadata Excluded) ---")
    start_time = time.time()

    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(RANDOM_SEED)

    # 1. Load Data and Split (保持不变)
    logging.info("Loading and splitting data...")
    try:
        df = pd.read_csv(CSV_PATH)
        train_val_df, test_df = train_test_split(df, test_size=TEST_SPLIT, random_state=RANDOM_SEED, stratify=df['label'])
        train_df, val_df = train_test_split(train_val_df, test_size=VALIDATION_SPLIT/(1-TEST_SPLIT), random_state=RANDOM_SEED, stratify=train_val_df['label'])
        logging.info(f"Data split: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    except FileNotFoundError:
        logging.error(f"FATAL: Processed CSV not found at {CSV_PATH}. Run preprocess script first.")
        return
    except Exception as e:
         logging.error(f"FATAL: Error loading or splitting data: {e}")
         return

    # 2. 移除 Metadata Scaler 相关逻辑
    # logging.info("Fitting metadata scaler on training data...")
    # metadata_scaler = StandardScaler()
    # ... (移除检查和 scaler.fit, joblib.dump 等)
    # logging.info(f"Metadata scaler fitting skipped.")

    # 3. Setup Datasets and DataLoaders (移除 metadata 相关参数)
    logging.info("Creating Datasets and DataLoaders...")
    tokenizer = get_tokenizer(TEXT_MODEL_NAME)
    image_transform = get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE)
    train_image_transform = get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE, augment=True)

    try:
        # 移除 metadata_cols 和 metadata_scaler 参数
        train_dataset = MultimodalFakeNewsDataset(train_df, DATA_DIR, tokenizer, train_image_transform, MAX_TEXT_LEN)
        val_dataset = MultimodalFakeNewsDataset(val_df, DATA_DIR, tokenizer, image_transform, MAX_TEXT_LEN)
        test_dataset = MultimodalFakeNewsDataset(test_df, DATA_DIR, tokenizer, image_transform, MAX_TEXT_LEN)

        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=2, pin_memory=True)
        val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
        test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=2, pin_memory=True)
        logging.info("DataLoaders created.")
    except Exception as e:
         logging.error(f"FATAL: Error creating Datasets or DataLoaders: {e}", exc_info=True)
         return

    # 4. Setup Model, Optimizer, Loss (移除 metadata 相关参数)
    logging.info("Setting up model, optimizer, and loss...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")

    # 移除 num_metadata_features, metadata_embedding_dim 参数
    model = MultimodalFakeNewsModel(
        text_model_name=TEXT_MODEL_NAME,
        image_model_name=IMAGE_MODEL_NAME,
        text_embedding_dim=TEXT_EMBEDDING_DIM,
        img_embedding_dim=IMG_EMBEDDING_DIM,
        fusion_output_dim=FUSION_OUTPUT_DIM,
        freeze_encoders=False 
    ).to(device)

    # 移除 metadata_encoder 参数组
    optimizer = optim.AdamW([
        {'params': model.text_encoder.parameters(), 'lr': LEARNING_RATE_ENCODERS},
        {'params': model.image_encoder.parameters(), 'lr': LEARNING_RATE_ENCODERS},
        # {'params': model.metadata_encoder.parameters(), 'lr': LEARNING_RATE_HEAD}, # 移除
        {'params': model.fusion_layer.parameters(), 'lr': LEARNING_RATE_HEAD},
        {'params': model.classifier.parameters(), 'lr': LEARNING_RATE_HEAD}
    ], weight_decay=WEIGHT_DECAY)

    loss_fn = nn.BCEWithLogitsLoss()
    scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=LR_SCHEDULER_FACTOR, patience=LR_SCHEDULER_PATIENCE, verbose=True)

    # 5. Training Loop (逻辑不变, 但调用 train/evaluate 时 model 不处理 metadata)
    logging.info("--- Starting Training Loop ---")
    best_val_f1 = -1.0
    epochs_no_improve = 0
    best_epoch = 0

    for epoch in range(EPOCHS):
        epoch_start_time = time.time()
        logging.info(f"Epoch {epoch + 1}/{EPOCHS}")

        train_loss, train_f1 = train_epoch(model, train_loader, loss_fn, optimizer, device)
        val_loss, val_acc, val_prec, val_rec, val_f1, val_auc = evaluate_epoch(model, val_loader, loss_fn, device)

        epoch_duration = time.time() - epoch_start_time
        logging.info(f"Epoch {epoch + 1} duration: {epoch_duration:.2f} seconds")
        scheduler.step(val_f1)

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_epoch = epoch + 1
            # 使用新的模型路径
            torch.save(model.state_dict(), BEST_MODEL_PATH) 
            logging.info(f"*** New best model saved to {BEST_MODEL_PATH} with Val F1: {best_val_f1:.4f} at epoch {best_epoch} ***")
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            logging.info(f"Validation F1 did not improve for {epochs_no_improve} epoch(s). Current best F1: {best_val_f1:.4f} at epoch {best_epoch}.")

        if epochs_no_improve >= EARLY_STOPPING_PATIENCE:
            logging.info(f"--- Early stopping triggered after {epoch + 1} epochs. ---")
            break

    logging.info("--- Training Finished ---")

    # 6. Final Evaluation on Test Set (逻辑不变)
    logging.info(f"--- Evaluating on Test Set using Best Model ({BEST_MODEL_PATH}) ---")
    try:
        if os.path.exists(BEST_MODEL_PATH):
            model.load_state_dict(torch.load(BEST_MODEL_PATH))
            logging.info(f"Loaded best model from epoch {best_epoch} ({BEST_MODEL_PATH}) with Val F1: {best_val_f1:.4f}")
            test_loss, test_acc, test_prec, test_rec, test_f1, test_auc = evaluate_epoch(model, test_loader, loss_fn, device)
            logging.info(f"Test Set Performance: Loss: {test_loss:.4f}, Accuracy: {test_acc:.4f}, Precision: {test_prec:.4f}, Recall: {test_rec:.4f}, F1: {test_f1:.4f}, AUC: {test_auc:.4f}")
        else:
             logging.error(f"Could not find best model at {BEST_MODEL_PATH} for final testing. Evaluating with the model from the last epoch.")
             test_loss, test_acc, test_prec, test_rec, test_f1, test_auc = evaluate_epoch(model, test_loader, loss_fn, device)
             logging.info(f"Test Set Performance (last epoch model): Loss: {test_loss:.4f}, Accuracy: {test_acc:.4f}, Precision: {test_prec:.4f}, Recall: {test_rec:.4f}, F1: {test_f1:.4f}, AUC: {test_auc:.4f}")

    except Exception as e:
         logging.error(f"Error during final test evaluation: {e}")

    total_duration = time.time() - start_time
    logging.info(f"Total script duration: {total_duration / 60:.2f} minutes")

if __name__ == '__main__':
    main()