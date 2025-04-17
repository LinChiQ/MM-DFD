import os
import pandas as pd
from PIL import Image, UnidentifiedImageError
import re
from tqdm import tqdm
import logging
import json # Added for reading JSON files
import requests # Added for downloading images from URL
from io import BytesIO # Added for handling image data in memory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(DATA_DIR, 'processed')
IMAGE_OUTPUT_DIR = os.path.join(OUTPUT_DIR, 'images')

# Create output directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

# --- Configuration ---
TARGET_IMAGE_SIZE = (224, 224) # Example size for many CNNs

# --- Text Cleaning Function ---
def clean_text(text):
    """Basic text cleaning: remove URLs, mentions, hashtags, and extra whitespace."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'http\\S+|www\\S+|https\\S+', '', text, flags=re.MULTILINE) # Remove URLs
    text = re.sub(r'\\@\\w+', '', text) # Remove mentions
    text = re.sub(r'#\\w+', '', text) # Remove hashtags
    # Remove specific Weibo artifacts like [超话] markers if needed
    text = re.sub(r'\\[.*?]', '', text) # Remove text within square brackets
    text = re.sub(r'\\s+', ' ', text).strip() # Remove extra whitespace
    # Add more specific cleaning rules if needed
    return text

# --- Image Processing Function ---
def process_image(image_path, output_dir, item_id):
    """Loads, resizes, normalizes (saves), and returns the path to the processed image."""
    # Check if image_path is a URL (simple check)
    is_url = isinstance(image_path, str) and (image_path.startswith('http://') or image_path.startswith('https://'))

    try:
        if is_url:
            # --- Download image from URL --- 
            logging.debug(f"Attempting to download image: {image_path}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Check if it's a sinaimg URL and use Baidu proxy if needed
            download_url = image_path
            if 'sinaimg.cn' in image_path:
                download_url = f"https://image.baidu.com/search/down?url={image_path}"
                logging.debug(f"Using Baidu proxy for sinaimg URL: {download_url}")
            
            try:
                # Use the potentially modified download_url
                response = requests.get(download_url, timeout=20, headers=headers, stream=True) # Increased timeout slightly for proxy
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                
                # Check content type if possible
                content_type = response.headers.get('content-type')
                if content_type and 'image' not in content_type.lower():
                     logging.warning(f"URL content-type doesn't look like an image ({content_type}): {image_path}")
                     # Decide whether to skip or try opening anyway
                     # return None # Option to skip non-image content types

                # Open image from response content
                img = Image.open(BytesIO(response.content)).convert('RGB')
            except requests.exceptions.Timeout:
                logging.error(f"Timeout downloading image {image_path}")
                return None
            except requests.exceptions.RequestException as e:
                logging.error(f"Error downloading image {image_path}: {e}")
                return None
            except UnidentifiedImageError: # Catch error if content is not a valid image format Pillow understands
                 logging.error(f"Downloaded content from {image_path} is not a valid image format.")
                 return None
        else:
            # Assume it's a local path
            if not os.path.exists(image_path):
                 logging.warning(f"Local image path not found: {image_path}")
                 return None
            img = Image.open(image_path).convert('RGB') # Ensure 3 channels

        img_resized = img.resize(TARGET_IMAGE_SIZE, Image.Resampling.LANCZOS)

        # Create a unique filename for the processed image
        base_filename = os.path.basename(image_path)
        # Clean potential query parameters from URL filenames
        if is_url:
             base_filename = base_filename.split('?')[0]
             
        file_ext = os.path.splitext(base_filename)[1]
        # Handle URLs potentially missing extensions or having query params
        if not file_ext or len(file_ext) > 5 : # Basic check for missing or weird extension
             # Try to guess extension from content type if downloaded, or default to .jpg
             if is_url and content_type:
                 if 'jpeg' in content_type.lower() or 'jpg' in content_type.lower(): file_ext = '.jpg'
                 elif 'png' in content_type.lower(): file_ext = '.png'
                 elif 'gif' in content_type.lower(): file_ext = '.gif'
                 elif 'bmp' in content_type.lower(): file_ext = '.bmp'
                 elif 'webp' in content_type.lower(): file_ext = '.webp'
                 else: file_ext = '.jpg' # Default if type is image/* but not recognized
             else:
                 file_ext = '.jpg' # Default extension if local or content type unknown

        # Sanitize item_id if it contains path separators
        sanitized_item_id = item_id.replace(os.path.sep, '_').replace(':','_') # Also replace colons
        output_filename = f"{sanitized_item_id}{file_ext}"
        output_path = os.path.join(output_dir, output_filename)

        img_resized.save(output_path)
        return os.path.join('processed/images', output_filename) # Return relative path for the final DataFrame

    except FileNotFoundError: # Catch case where local file doesn't exist even after check (race condition?)
        logging.warning(f"Image not found (processing local path): {image_path}")
        return None
    except UnidentifiedImageError: # Catch error if local file is not a valid image format
        logging.error(f"Local file {image_path} is not a valid image format.")
        return None
    except Exception as e:
        # Catch other PIL errors or unexpected issues
        logging.error(f"Error processing image {image_path}: {e}", exc_info=True)
        return None

# --- Dataset Specific Loaders ---

def load_mcfend(data_dir, image_output_dir):
    """Loads and preprocesses data from the mcfend dataset using provided structure."""
    logging.info("Processing mcfend dataset with provided structure...")
    processed_data = []
    news_path = os.path.join(data_dir, 'mcfend', 'news.csv')
    context_path = os.path.join(data_dir, 'mcfend', 'social_context.csv')
    user_path = os.path.join(data_dir, 'mcfend', 'user.csv')

    required_files = {'news': news_path, 'context': context_path, 'user': user_path}
    for name, path in required_files.items():
        if not os.path.exists(path):
            logging.error(f"mcfend required file not found: {path} ({name}.csv)")
            return []

    # --- 1. Load User Data --- 
    logging.info("Loading user data...")
    user_df = None
    try:
        # Assuming user.csv is manageable in memory (40MB)
        user_df = pd.read_csv(user_path, index_col='user_id') # Index by user_id for quick lookup
        # Select and rename relevant columns
        user_df = user_df[['follower_count', 'following_count', 'post_count', 'have_verification']]
        user_df.rename(columns={
            'follower_count': 'user_followers',
            'following_count': 'user_following',
            'post_count': 'user_posts',
            'have_verification': 'user_verified'
        }, inplace=True)
        # Convert verification status to numeric (e.g., 1 for verified, 0 otherwise)
        user_df['user_verified'] = user_df['user_verified'].apply(lambda x: 1 if isinstance(x, str) and x.lower() == 'verified' else 0)
        logging.info(f"Loaded {len(user_df)} user records.")
    except Exception as e:
        logging.error(f"Failed to load or process user.csv: {e}")
        return [] # Cannot proceed without user data if we want user features

    # --- 2. Aggregate Social Context Features --- 
    logging.info("Aggregating social context features (this may take time)...")
    social_features = {}
    poster_info = {} # To store the user_id of the original post for each news_id
    context_chunk_size = 50000 # Adjust based on memory
    try:
        for chunk in tqdm(pd.read_csv(context_path, chunksize=context_chunk_size, low_memory=False), desc="Processing context chunks"):
            # Fill NaN in numeric columns needed for aggregation
            num_cols_to_fill = ['like_count', 'cmt_count', 'repost_count', 'view_count']
            for col in num_cols_to_fill:
                 if col in chunk.columns:
                     chunk[col] = pd.to_numeric(chunk[col], errors='coerce').fillna(0)
                 else:
                      logging.warning(f"Column '{col}' not found in context chunk. Filling with 0.")
                      chunk[col] = 0 
            
            # Group by news_id within the chunk
            # Note: Summing view_count might be inaccurate if provided per comment/repost
            # Consider taking max or first value if view_count applies only to original post.
            # For now, we sum, assuming it represents engagement on related items.
            grouped = chunk.groupby('news_id')
            
            # Aggregate counts
            agg_data = grouped.agg({
                'like_count': 'sum',
                'cmt_count': 'sum',
                'repost_count': 'sum',
                'view_count': 'sum' # Or 'max' or custom logic
            })

            # Try to get the user_id of the original post ('posts')
            original_posts = chunk[chunk['type'] == 'posts']
            posters = original_posts.groupby('news_id')['user_id'].first() # Get the first user listed for a news_id post

            # Update the global aggregation dictionaries
            for news_id, features in agg_data.iterrows():
                if news_id not in social_features:
                    social_features[news_id] = features.copy()
                else:
                    social_features[news_id] += features # Add counts from chunk
            
            for news_id, user_id in posters.items():
                 if news_id not in poster_info:
                      poster_info[news_id] = user_id # Store the first identified poster

        # Convert aggregated data to DataFrame for easier merging later
        social_features_df = pd.DataFrame.from_dict(social_features, orient='index')
        social_features_df.rename(columns={
            'like_count': 'total_likes',
            'cmt_count': 'total_comments',
            'repost_count': 'total_reposts',
            'view_count': 'total_views' # Or max_views etc.
        }, inplace=True)
        logging.info(f"Aggregated social features for {len(social_features_df)} news items.")

    except Exception as e:
        logging.error(f"Failed during social context aggregation: {e}")
        # Decide if we want to proceed without social features
        logging.warning("Proceeding without aggregated social context features.")
        social_features_df = pd.DataFrame() # Create empty df

    # --- 3. Process News Data and Merge Features --- 
    logging.info("Processing news data and merging features...")
    news_chunk_size = 10000 # Adjust as needed
    label_map = {'谣言': 1, '事实': 0, '尚无定论': 1} # Map '尚无定论' to 1 (Fake/Rumor)
    
    try:
        for chunk in tqdm(pd.read_csv(news_path, chunksize=news_chunk_size, low_memory=False), desc="Processing news chunks"):
            # Join social features (if available)
            if not social_features_df.empty:
                 chunk = chunk.join(social_features_df, on='news_id')
            else: # Add empty columns if social features failed
                 for col in ['total_likes', 'total_comments', 'total_reposts', 'total_views']:
                      chunk[col] = 0

            # Add user features based on poster_info and user_df
            def get_user_features(news_id):
                poster_user_id = poster_info.get(news_id)
                if poster_user_id and poster_user_id in user_df.index:
                    return user_df.loc[poster_user_id]
                # Return default values if poster not found or user data missing
                return pd.Series({'user_followers': 0, 'user_following': 0, 'user_posts': 0, 'user_verified': 0})

            user_features_chunk = chunk['news_id'].apply(get_user_features)
            chunk = pd.concat([chunk, user_features_chunk], axis=1)

            # Fill NaNs in added feature columns with 0
            feature_cols = ['total_likes', 'total_comments', 'total_reposts', 'total_views',
                            'user_followers', 'user_following', 'user_posts', 'user_verified']
            for col in feature_cols:
                if col in chunk.columns:
                    chunk[col] = chunk[col].fillna(0).astype(int) # Fill NaN and ensure integer type
                else:
                    chunk[col] = 0 # Add column if it wasn't created (e.g., join failed)
            
            # Process each row in the enriched chunk
            for _, row in chunk.iterrows():
                news_id_val = row['news_id']
                # Use 'content' if available, fallback to 'title'?
                text_content_val = row.get('content', row.get('title', '')) 
                label_str = row.get('label', None)
                pic_url_val = row.get('pic_url', None)

                # Map label
                label = label_map.get(label_str)
                if label is None:
                    logging.warning(f"Unknown label '{label_str}' for mcfend news {news_id_val}. Skipping.")
                    continue

                item_id = f"mcfend_{news_id_val}"
                text = clean_text(text_content_val)

                processed_image_rel_path = None
                if pic_url_val and isinstance(pic_url_val, str) and pic_url_val.startswith('http'):
                    # Image processing logic (needs requests + uncommenting in process_image)
                    processed_image_rel_path = process_image(pic_url_val, image_output_dir, item_id)
                
                if text: # Require text
                    data_entry = {
                        'id': item_id,
                        'text': text,
                        'image_path': processed_image_rel_path, # Path or None
                        'label': label,
                        'source': 'mcfend',
                        # Add aggregated features
                        'total_likes': row['total_likes'],
                        'total_comments': row['total_comments'],
                        'total_reposts': row['total_reposts'],
                        'total_views': row['total_views'],
                        'user_followers': row['user_followers'],
                        'user_following': row['user_following'],
                        'user_posts': row['user_posts'],
                        'user_verified': row['user_verified']
                    }
                    processed_data.append(data_entry)
                else:
                    logging.warning(f"Skipping mcfend item {item_id} due to missing text content after cleaning.")
                    
    except Exception as e:
        logging.error(f"Error processing news chunks and merging features: {e}")

    logging.info(f"Finished processing mcfend. Found {len(processed_data)} valid items with features.")
    return processed_data


def load_rumor_acl2017(data_dir, image_output_dir):
    """Loads and preprocesses data from the rumor_detection_acl2017 dataset."""
    logging.info("Processing rumor_detection_acl2017 dataset...")
    processed_data = []
    base_path = os.path.join(data_dir, 'rumor_detection_acl2017')
    subsets = ['twitter15', 'twitter16']

    label_map = {'non-rumor': 0, 'false': 1, 'true': 1, 'unverified': 1} # Mapping based on common conventions, adjust if needed

    for subset in subsets:
        subset_path = os.path.join(base_path, subset)
        label_file = os.path.join(subset_path, 'label.txt')
        tweet_file = os.path.join(subset_path, 'source_tweets.txt')

        if not os.path.exists(label_file) or not os.path.exists(tweet_file):
            logging.warning(f"Skipping subset {subset}: missing label.txt or source_tweets.txt")
            continue

        logging.info(f"Processing subset: {subset}")

        # Load labels into a dictionary {tweet_id: label}
        labels = {}
        try:
            with open(label_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        label_str, tweet_id_str = line.strip().split(':')
                        # Map string label to integer using label_map
                        numeric_label = label_map.get(label_str.lower())
                        if numeric_label is not None:
                           labels[tweet_id_str] = numeric_label
                        else:
                           logging.warning(f"Unknown label '{label_str}' for tweet {tweet_id_str} in {subset}. Skipping.")
                    except ValueError:
                        logging.warning(f"Malformed line in {label_file}: {line.strip()}. Skipping.")
        except Exception as e:
             logging.error(f"Error reading label file {label_file}: {e}")
             continue # Skip this subset if labels can't be read

        # Load tweets and combine with labels
        try:
            with open(tweet_file, 'r', encoding='utf-8') as f:
                for line in tqdm(f, desc=f"Processing {subset} tweets"):
                    try:
                        tweet_id_str, text_content = line.strip().split('\t', 1)
                    except ValueError:
                         logging.warning(f"Malformed line in {tweet_file}: {line.strip()}. Skipping.")
                         continue

                    if tweet_id_str in labels:
                        item_id = f"acl2017_{subset}_{tweet_id_str}"
                        text = clean_text(text_content)
                        label = labels[tweet_id_str]

                        # This dataset has no images according to README
                        processed_image_rel_path = None

                        if text: # Only need text and label here
                            processed_data.append({
                                'id': item_id,
                                'text': text,
                                'image_path': processed_image_rel_path, # Will be None
                                'label': label,
                                'source': f'acl2017_{subset}'
                            })
                    else:
                        # This case should ideally not happen if files are consistent
                        logging.warning(f"Tweet ID {tweet_id_str} found in tweets but not in labels for {subset}. Skipping.")
        except Exception as e:
             logging.error(f"Error reading tweet file {tweet_file}: {e}")
             continue # Skip this subset if tweets can't be read

    logging.info(f"Finished processing rumor_detection_acl2017. Found {len(processed_data)} valid items.")
    return processed_data


def load_socialnet(data_dir, image_output_dir):
    """Loads and preprocesses data from the SocialNet dataset (TikTok, Weibo V1, Weibo V2)."""
    logging.info("Processing SocialNet dataset (TikTok, Weibo V1, Weibo V2)...")
    processed_data = []
    socialnet_base = os.path.join(data_dir, 'SocialNet')

    platforms = {
        'TikTok': {'path': os.path.join(socialnet_base, 'TikTok')},
        'Weibo': {'path': os.path.join(socialnet_base, 'Weibo')}
    }

    for platform_name, platform_info in platforms.items():
        platform_path = platform_info['path']
        if not os.path.isdir(platform_path):
            logging.warning(f"Platform directory not found: {platform_path}")
            continue
        logging.info(f"--- Processing Platform: {platform_name} ---")

        # Check for Weibo V1/V2 structure
        versions = [''] # Default for TikTok or if no V1/V2 folders
        if platform_name == 'Weibo':
            if os.path.isdir(os.path.join(platform_path, 'V1')) or os.path.isdir(os.path.join(platform_path, 'V2')):
                versions = [v for v in ['V1', 'V2'] if os.path.isdir(os.path.join(platform_path, v))]
                logging.info(f"Found Weibo versions: {versions}")
            else:
                logging.warning(f"Could not find V1 or V2 subdirectories in {platform_path}. Skipping Weibo.")
                continue

        for version in versions:
            version_path = os.path.join(platform_path, version) # version might be empty for TikTok
            logging.info(f"Processing {platform_name} {version}...")
            
            categories = {'real_news': 0, 'fake_news': 1}
            for category, label in categories.items():
                category_path = os.path.join(version_path, category)
                if not os.path.isdir(category_path):
                    logging.warning(f"Category directory not found: {category_path}")
                    continue

                logging.info(f"Scanning category: {category}")
                item_ids = [d for d in os.listdir(category_path) if os.path.isdir(os.path.join(category_path, d))]

                for item_dir_name in tqdm(item_ids, desc=f"Processing {platform_name} {version} {category}"):
                    item_path = os.path.join(category_path, item_dir_name)
                    # Corrected filename for Weibo (and assuming TikTok also uses news.json or new.json)
                    json_filename = 'new.json' if platform_name == 'Weibo' else 'news.json' # Use new.json for Weibo
                    json_file_path = os.path.join(item_path, json_filename)
                    item_id = f"socialnet_{platform_name.lower()}{version.lower()}_{item_dir_name}"

                    if not os.path.exists(json_file_path):
                        logging.warning(f"{json_filename} not found in {item_path}. Skipping.")
                        continue

                    try:
                        with open(json_file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # Initialize common fields
                        text = ""
                        processed_image_rel_path = None
                        features = {
                            'total_likes': 0, 'total_comments': 0, 'total_reposts': 0, 'total_views': 0,
                            'user_followers': 0, 'user_following': 0, 'user_posts': 0, 'user_verified': 0,
                            'user_total_favorited': 0 # TikTok specific?
                        }

                        # --- Platform/Version Specific Parsing ---
                        if platform_name == 'TikTok':
                            aweme = data.get('aweme_detail', {})
                            text = clean_text(aweme.get('desc', ''))
                            
                            # Image: Use video cover
                            video_info = aweme.get('video')
                            if video_info and isinstance(video_info, dict):
                                cover_info = video_info.get('cover')
                                if cover_info and isinstance(cover_info, dict) and cover_info.get('url_list'):
                                     raw_image_path = cover_info['url_list'][0]
                                     if isinstance(raw_image_path, str) and raw_image_path.startswith('http'):
                                          logging.debug(f"Found TikTok video cover URL for {item_id}: {raw_image_path}")
                                          processed_image_rel_path = process_image(raw_image_path, image_output_dir, f"{item_id}_cover")
                            
                            # Features
                            author_info = aweme.get('author', {})
                            stats_info = aweme.get('statistics', {})
                            features['user_followers'] = int(author_info.get('follower_count', 0))
                            features['user_following'] = int(author_info.get('following_count', 0))
                            features['user_total_favorited'] = int(author_info.get('total_favorited', 0)) # Author's total favorited count
                            # User verification status seems complex or missing in example, default to 0
                            features['total_likes'] = int(stats_info.get('digg_count', 0))
                            features['total_comments'] = int(stats_info.get('comment_count', 0))
                            features['total_reposts'] = int(stats_info.get('share_count', 0)) # Map shares to reposts

                        elif platform_name == 'Weibo':
                            if version == 'V1':
                                text = clean_text(data.get('context', '')) # Needs careful cleaning
                                # No image info in V1 example
                                features['total_likes'] = int(str(data.get('like_num', '0')).replace('\'','')) # Handle potential quotes
                                features['total_comments'] = int(str(data.get('comment_num', '0')).replace('\'',''))
                                # Other features missing

                            elif version == 'V2':
                                text = clean_text(data.get('text_raw', ''))
                                
                                # Image: Prioritize pic_ids if available, else page_pic
                                pic_ids = data.get('pic_ids')
                                pic_infos = data.get('pic_infos')
                                
                                if pic_ids and isinstance(pic_ids, list) and len(pic_ids) > 0 and pic_infos and isinstance(pic_infos, dict):
                                    first_pic_id = pic_ids[0]
                                    if first_pic_id in pic_infos:
                                        info = pic_infos[first_pic_id]
                                        # Prioritize larger image sizes
                                        image_url = None
                                        for size_key in ['largest', 'large', 'mw2000', 'original', 'bmiddle', 'thumbnail']:
                                            if size_key in info and info[size_key].get('url'):
                                                image_url = info[size_key]['url']
                                                logging.debug(f"Found Weibo V2 image URL (size: {size_key}) for pic_id {first_pic_id}: {image_url}")
                                                break # Stop at the first found URL in priority order
                                        
                                        if image_url and isinstance(image_url, str) and image_url.startswith('http'):
                                            # Pass the extracted URL to process_image
                                            # process_image will handle the Baidu proxy if needed
                                            processed_image_rel_path = process_image(image_url, image_output_dir, f"{item_id}_pic0")
                                        else:
                                            logging.warning(f"Could not extract a valid URL for pic_id {first_pic_id} from pic_infos.")
                                    else:
                                        logging.warning(f"pic_id {first_pic_id} not found in pic_infos for {item_id}.")
                                # Remove the old placeholder warning
                                # logging.warning(f"Found pic_ids for {item_id}, but URL construction logic is missing. Skipping image from pic_ids.")

                                # If no image processed from pic_ids, check page_info for video preview ('page_pic')
                                if not processed_image_rel_path and 'page_info' in data and isinstance(data['page_info'], dict):
                                    page_info = data['page_info']
                                    if page_info.get('object_type') == 'video' and 'page_pic' in page_info:
                                        raw_image_path = page_info['page_pic'] # This is likely a URL
                                        if isinstance(raw_image_path, str) and raw_image_path.startswith('http'):
                                            logging.debug(f"Found Weibo V2 video preview image URL for {item_id}: {raw_image_path}")
                                            processed_image_rel_path = process_image(raw_image_path, image_output_dir, f"{item_id}_preview")
                                        else:
                                            logging.warning(f"Found page_pic for {item_id}, but it's not a valid URL: {raw_image_path}")
                                
                                # Features
                                user_info = data.get('user', {})
                                features['user_followers'] = int(user_info.get('followers_count', 0))
                                features['user_following'] = int(user_info.get('friends_count', 0)) # Weibo uses 'friends_count'
                                features['user_posts'] = int(user_info.get('statuses_count', 0))
                                features['user_verified'] = 1 if user_info.get('verified', False) else 0
                                features['total_likes'] = int(data.get('attitudes_count', 0))
                                features['total_comments'] = int(data.get('comments_count', 0))
                                features['total_reposts'] = int(data.get('reposts_count', 0))
                                # total_views missing in V2 JSON
                        # --- End Platform Specific Parsing ---

                        if text: # Require at least text
                            data_entry = {
                                'id': item_id,
                                'text': text,
                                'image_path': processed_image_rel_path, # Path or None
                                'label': label,
                                'source': f'socialnet_{platform_name.lower()}{version.lower()}_{category}'
                            }
                            data_entry.update(features) # Add all extracted features
                            processed_data.append(data_entry)
                        else:
                            logging.warning(f"Skipping {item_id} due to missing text content after cleaning.")

                    except json.JSONDecodeError:
                        logging.error(f"Error decoding JSON: {json_file_path}")
                    except Exception as e:
                         logging.error(f"Error processing item {item_dir_name} in {category_path}: {e}", exc_info=True)

    logging.info(f"Finished processing SocialNet. Found {len(processed_data)} potentially valid items.")
    return processed_data


# --- Main Execution ---
if __name__ == "__main__":
    all_data = []

    # Load and process each dataset
    all_data.extend(load_mcfend(DATA_DIR, IMAGE_OUTPUT_DIR))
    all_data.extend(load_rumor_acl2017(DATA_DIR, IMAGE_OUTPUT_DIR))
    all_data.extend(load_socialnet(DATA_DIR, IMAGE_OUTPUT_DIR))

    if not all_data:
        logging.warning("No data successfully processed from any source. Exiting.")
    else:
        # Convert to DataFrame
        df_processed = pd.DataFrame(all_data)

        # --- Data Cleaning/Filtering Post-Processing ---
        # Define all potential feature columns from all sources
        feature_cols = [
            'total_likes', 'total_comments', 'total_reposts', 'total_views',
            'user_followers', 'user_following', 'user_posts', 'user_verified',
            'user_total_favorited' # Added from TikTok
        ]
        # Fill NaNs in feature columns that might exist only in some sources
        for col in feature_cols:
             if col in df_processed.columns:
                 # Fill NaN first, then convert to int. Handle potential non-numeric gracefully.
                 df_processed[col] = pd.to_numeric(df_processed[col].fillna(0), errors='coerce').fillna(0).astype(int)
             else: # Add column with 0 if it doesn't exist
                  df_processed[col] = 0

        initial_count = len(df_processed)
        # Optional: Remove rows where image processing failed if an image is strictly required
        # df_processed = df_processed.dropna(subset=['image_path']) 
        # logging.info(f"Removed {initial_count - len(df_processed)} items with missing/failed images.")

        # Remove rows with empty text
        df_processed = df_processed[df_processed['text'].astype(str).str.len() > 0]
        logging.info(f"Removed {len(df_processed) - initial_count} items with empty text after cleaning.") # Corrected log message

        # Ensure correct types for final output (optional but good practice)
        df_processed['label'] = df_processed['label'].astype(int)
        # image_path can be object/string (contains None/paths)

        # Save the processed data manifest
        output_csv_path = os.path.join(OUTPUT_DIR, 'processed_data.csv')
        try:
            # Use utf-8-sig for better Excel compatibility with Chinese characters
            df_processed.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
            logging.info(f"Successfully processed and saved {len(df_processed)} items.")
            logging.info(f"Processed data manifest saved to: {output_csv_path}")
            logging.info(f"Processed images (if any) saved in: {IMAGE_OUTPUT_DIR}")
        except Exception as e:
             logging.error(f"Failed to save processed data to CSV: {e}")

        # Display basic statistics
        if not df_processed.empty:
            logging.info("\n--- Final Data Statistics ---")
            logging.info(f"Total items: {len(df_processed)}")
            logging.info("Label distribution:")
            logging.info(df_processed['label'].value_counts())
            logging.info("\nSource distribution:")
            logging.info(df_processed['source'].value_counts())
            # Add stats for new features
            logging.info("\nFeature statistics (mean):")
            # Calculate mean only for existing columns to avoid errors if a feature column is all 0s
            existing_feature_cols = [col for col in feature_cols if col in df_processed.columns]
            if existing_feature_cols:
                 logging.info(df_processed[existing_feature_cols].mean().to_string())
            else:
                 logging.info("No feature columns found to calculate statistics.")
            logging.info("---------------------------\n")
        else:
             logging.warning("Final DataFrame is empty. No statistics to display.")

    logging.info("Data preprocessing script finished.") 