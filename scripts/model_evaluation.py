# scripts/model_evaluation.py

import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
from pathlib import Path
import logging
import time
import joblib
from tqdm import tqdm
import argparse
import matplotlib.pyplot as plt
import seaborn as sns

# Import necessary classes and functions
try:
    # Import only the necessary classes from train_model
    from train_model import MultimodalFakeNewsModel, MetadataEncoder
    # Import necessary functions from data_loader
    from data_loader import (
        MultimodalFakeNewsDataset,
        get_tokenizer,
        get_image_transforms
    )
except ImportError as e:
    logging.error(f"Could not import necessary components. Make sure train_model.py and data_loader.py are in the path. Error: {e}")
    exit(1)


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration (Mirrored from train_model.py for consistency) ---
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
CSV_PATH = PROCESSED_DIR / 'processed_data.csv'
OUTPUT_DIR = BASE_DIR / 'models'
DEFAULT_MODEL_PATH = OUTPUT_DIR / 'best_multimodal_model.pth'
DEFAULT_SCALER_PATH = OUTPUT_DIR / 'metadata_scaler.joblib'
RESULTS_DIR = BASE_DIR / 'evaluation_results' # Directory to save evaluation outputs
RESULTS_DIR.mkdir(exist_ok=True)

# Model Parameters (Ensure these match the trained model's config)
TEXT_MODEL_NAME = 'bert-base-chinese'
IMAGE_MODEL_NAME = 'resnet50'
IMAGE_MODEL_INPUT_SIZE = 224
MAX_TEXT_LEN = 128
NUM_METADATA_FEATURES = 9
IMG_EMBEDDING_DIM = 2048
TEXT_EMBEDDING_DIM = 768
METADATA_EMBEDDING_DIM = 64
FUSION_OUTPUT_DIM = 256

# Metadata Columns (Ensure this matches the scaler and data)
METADATA_COLS = [
    'total_likes', 'total_comments', 'total_reposts', 'total_views',
    'user_followers', 'user_following', 'user_posts', 'user_verified',
    'user_total_favorited'
]

# Data Split Parameters (Must match training split)
TEST_SPLIT = 0.15
RANDOM_SEED = 42

# Evaluation specific batch size (can be larger than training if memory allows)
# Inherit training BATCH_SIZE as a default or set a new one
EVAL_BATCH_SIZE = 32 * 2 # Example: double the training batch size

# --- Evaluation Function ---

def evaluate(model, data_loader, device):
    """ Runs model inference on the data_loader and calculates metrics. """
    model.eval()
    all_preds_proba = []
    all_labels = []
    all_ids = []

    logging.info("Starting evaluation...")
    with torch.no_grad():
        for batch in tqdm(data_loader, desc="Evaluating"):
            # Move batch to device
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            images = batch['image'].to(device)
            metadata = batch['metadata'].to(device)
            labels = batch['label'].to(device)
            image_available = batch['image_available'].to(device)
            item_ids = batch['id'] # Keep track of IDs if needed

            # Forward pass
            outputs = model(input_ids, attention_mask, images, metadata, image_available)
            probabilities = torch.sigmoid(outputs).cpu().numpy()

            all_preds_proba.extend(probabilities)
            all_labels.extend(labels.cpu().numpy())
            all_ids.extend(item_ids) # Store IDs

    logging.info("Evaluation loop finished. Calculating metrics...")

    # --- Calculate Metrics ---
    all_labels = np.array(all_labels)
    all_preds_proba = np.array(all_preds_proba)
    all_preds_binary = (all_preds_proba >= 0.5).astype(int)

    accuracy = accuracy_score(all_labels, all_preds_binary)
    precision = precision_score(all_labels, all_preds_binary, zero_division=0)
    recall = recall_score(all_labels, all_preds_binary, zero_division=0)
    f1 = f1_score(all_labels, all_preds_binary, zero_division=0)
    try:
        auc = roc_auc_score(all_labels, all_preds_proba) # AUC uses probabilities
    except ValueError:
        auc = 0.0
        logging.warning("AUC calculation failed (likely only one class present in labels). Setting AUC to 0.0")

    cm = confusion_matrix(all_labels, all_preds_binary)
    class_report = classification_report(all_labels, all_preds_binary, zero_division=0, target_names=['Real', 'Fake']) # Assuming 0: Real, 1: Fake

    metrics = {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1 Score": f1,
        "AUC": auc,
        "Confusion Matrix": cm,
        "Classification Report": class_report
    }

    # Optionally return predictions and IDs for further analysis
    # predictions_df = pd.DataFrame({'id': all_ids, 'label': all_labels, 'prediction_proba': all_preds_proba, 'prediction_binary': all_preds_binary})

    return metrics #, predictions_df


def plot_confusion_matrix(cm, class_names, output_path):
    """ Plots and saves the confusion matrix. """
    try:
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names)
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        logging.info(f"Confusion matrix saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to plot or save confusion matrix: {e}")

# --- Argument Parser ---
def parse_args():
    parser = argparse.ArgumentParser(description="Evaluate a trained Multimodal Fake News Model.")
    parser.add_argument('--model_path', type=str, default=str(DEFAULT_MODEL_PATH),
                        help=f"Path to the trained model state dictionary (default: {DEFAULT_MODEL_PATH})")
    parser.add_argument('--scaler_path', type=str, default=str(DEFAULT_SCALER_PATH),
                        help=f"Path to the saved metadata scaler (default: {DEFAULT_SCALER_PATH})")
    parser.add_argument('--csv_path', type=str, default=str(CSV_PATH),
                        help=f"Path to the processed data CSV file (default: {CSV_PATH})")
    parser.add_argument('--batch_size', type=int, default=EVAL_BATCH_SIZE,
                        help=f"Batch size for evaluation (default: {EVAL_BATCH_SIZE})")
    parser.add_argument('--results_dir', type=str, default=str(RESULTS_DIR),
                        help=f"Directory to save evaluation results (default: {RESULTS_DIR})")
    return parser.parse_args()


# --- Main Evaluation Logic ---
def main():
    args = parse_args()
    eval_start_time = time.time()

    # Ensure results directory exists
    results_path = Path(args.results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    # 1. Setup Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logging.info(f"Using device: {device}")

    # 2. Load Data and Split (Reproduce the test split)
    logging.info(f"Loading data from {args.csv_path}...")
    try:
        df = pd.read_csv(args.csv_path)
        # Perform the *exact same* split as in training
        # We only need the test_df here
        _, test_df = train_test_split(
            df,
            test_size=TEST_SPLIT,
            random_state=RANDOM_SEED,
            stratify=df['label'] # Ensure stratification is the same
        )
        logging.info(f"Test set size: {len(test_df)}")
    except FileNotFoundError:
        logging.error(f"FATAL: Processed CSV not found at {args.csv_path}. Cannot perform evaluation.")
        return
    except Exception as e:
         logging.error(f"FATAL: Error loading or splitting data: {e}")
         return

    # 3. Load Scaler
    logging.info(f"Loading metadata scaler from {args.scaler_path}...")
    try:
        metadata_scaler = joblib.load(args.scaler_path)
    except FileNotFoundError:
        logging.error(f"FATAL: Metadata scaler not found at {args.scaler_path}. Evaluation requires the scaler used during training.")
        # Option: Proceed without scaling metadata (might give poor results)
        # metadata_scaler = None
        # logging.warning("Proceeding without metadata scaling.")
        return # Exit if scaler is essential
    except Exception as e:
         logging.error(f"FATAL: Error loading scaler: {e}")
         return

    # 4. Setup Tokenizer and Transforms
    logging.info("Setting up tokenizer and image transforms...")
    tokenizer = get_tokenizer(TEXT_MODEL_NAME)
    # Use non-augmented transforms for evaluation
    image_transform = get_image_transforms(input_size=IMAGE_MODEL_INPUT_SIZE, augment=False)

    # 5. Create Test Dataset and DataLoader
    logging.info("Creating test Dataset and DataLoader...")
    try:
        test_dataset = MultimodalFakeNewsDataset(
            dataframe=test_df,
            data_dir=DATA_DIR, # Pass the base data dir
            tokenizer=tokenizer,
            image_transform=image_transform,
            max_len=MAX_TEXT_LEN, # Now uses the constant defined in this file
            metadata_cols=METADATA_COLS, # Now uses the constant defined in this file
            metadata_scaler=metadata_scaler # Use the loaded scaler (Corrected keyword argument)
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=args.batch_size,
            shuffle=False, # No shuffling for evaluation
            num_workers=2, # Adjust based on system
            pin_memory=True
        )
        logging.info("Test DataLoader created.")
    except Exception as e:
         logging.error(f"FATAL: Error creating test Dataset or DataLoader: {e}", exc_info=True)
         return

    # 6. Load Model
    logging.info("Loading model...")
    # Use the constants defined in this file to initialize the model structure
    model = MultimodalFakeNewsModel(
        text_model_name=TEXT_MODEL_NAME,
        image_model_name=IMAGE_MODEL_NAME,
        num_metadata_features=NUM_METADATA_FEATURES,
        text_embedding_dim=TEXT_EMBEDDING_DIM,
        img_embedding_dim=IMG_EMBEDDING_DIM,
        metadata_embedding_dim=METADATA_EMBEDDING_DIM,
        fusion_output_dim=FUSION_OUTPUT_DIM
    )

    logging.info(f"Loading model state from: {args.model_path}")
    try:
        model.load_state_dict(torch.load(args.model_path, map_location=device)) # Load to target device
        model.to(device)
        logging.info("Model loaded successfully.")
    except FileNotFoundError:
        logging.error(f"FATAL: Model file not found at {args.model_path}. Cannot perform evaluation.")
        return
    except Exception as e:
        logging.error(f"FATAL: Error loading model state: {e}")
        return

    # 7. Perform Evaluation
    metrics = evaluate(model, test_loader, device)

    # 8. Display and Save Results
    logging.info("\n--- Test Set Evaluation Results ---")
    print(f"Accuracy: {metrics['Accuracy']:.4f}")
    print(f"Precision: {metrics['Precision']:.4f}")
    print(f"Recall: {metrics['Recall']:.4f}")
    print(f"F1 Score: {metrics['F1 Score']:.4f}")
    print(f"AUC: {metrics['AUC']:.4f}")
    print("\nClassification Report:")
    print(metrics['Classification Report'])
    print("\nConfusion Matrix:")
    print(metrics['Confusion Matrix'])
    logging.info("------------------------------------")

    # Save results to files
    results_file_path = results_path / "evaluation_metrics.txt"
    cm_plot_path = results_path / "confusion_matrix.png"

    try:
        with open(results_file_path, "w", encoding="utf-8") as f:
            f.write("--- Test Set Evaluation Results ---\n")
            f.write(f"Model Path: {args.model_path}\n")
            f.write(f"Scaler Path: {args.scaler_path}\n")
            f.write(f"Data CSV: {args.csv_path}\n")
            f.write(f"Evaluation Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("------------------------------------\n")
            f.write(f"Accuracy: {metrics['Accuracy']:.4f}\n")
            f.write(f"Precision: {metrics['Precision']:.4f}\n")
            f.write(f"Recall: {metrics['Recall']:.4f}\n")
            f.write(f"F1 Score: {metrics['F1 Score']:.4f}\n")
            f.write(f"AUC: {metrics['AUC']:.4f}\n\n")
            f.write("Classification Report:\n")
            f.write(metrics['Classification Report'])
            f.write("\n\nConfusion Matrix:\n")
            f.write(np.array2string(metrics['Confusion Matrix']))
        logging.info(f"Evaluation metrics saved to {results_file_path}")

        # Plot and save confusion matrix
        plot_confusion_matrix(metrics['Confusion Matrix'], class_names=['Real', 'Fake'], output_path=cm_plot_path)

    except Exception as e:
        logging.error(f"Error saving evaluation results: {e}")

    eval_duration = time.time() - eval_start_time
    logging.info(f"Total evaluation script duration: {eval_duration / 60:.2f} minutes")


if __name__ == '__main__':
    main()