#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据收集与预处理脚本
支持从公开数据集下载和处理多模态虚假新闻数据
"""
import os
import sys
import argparse
import requests
import pandas as pd
import json
from tqdm import tqdm
from pathlib import Path

# 数据源配置
DATA_SOURCES = {
    'fakenewsnet': {
        'url': 'https://github.com/KaiDMML/FakeNewsNet',
        'description': 'FakeNewsNet数据集 - 包含来自PolitiFact和GossipCop的文本和图像多模态数据'
    },
    'multimodealnews': {
        'url': 'https://drive.google.com/drive/folders/1QRkrD5PB8-Hh2n2Y0-XbwN0gABe4Idoa',
        'description': 'MultiModal FakeNews Detection (MMFD)数据集 - 来自ACL 2021的多模态虚假新闻检测数据集'
    },
    'Weibo21': {
        'url': 'https://github.com/yjw1029/Weibo21',
        'description': '微博21数据集 - 包含2020-2021年中文社交媒体多模态虚假新闻数据'
    },
    'mediaevalmemd': {
        'url': 'https://github.com/MKLab-ITI/image-verification-corpus',
        'description': 'MediaEval MEMD数据集 - 包含Twitter图像验证语料库'
    },
    'mvsa': {
        'url': 'https://mcrlab.net/research/mvsa-sentiment-analysis-on-multi-view-social-data/',
        'description': 'MVSA多视角情感分析数据集 - 包含图像和文本的多模态数据'
    },
    'twitter-multimodal': {
        'url': 'https://huggingface.co/datasets/HuggingFaceM4/twitter-multimodal',
        'description': 'Twitter多模态数据集 - HuggingFace提供的图文多模态社交媒体数据'
    }
}

def create_data_dirs():
    """创建数据目录结构"""
    base_dir = Path(__file__).parent.parent / 'data'
    dirs = [
        base_dir / 'raw',
        base_dir / 'raw' / 'images',
        base_dir / 'raw' / 'text',
        base_dir / 'processed',
        base_dir / 'processed' / 'images',
        base_dir / 'processed' / 'text',
        base_dir / 'processed' / 'combined'
    ]
    
    for d in dirs:
        d.mkdir(exist_ok=True, parents=True)
        print(f"创建目录: {d}")
    
    return base_dir

def download_file(url, output_path):
    """下载文件到指定路径"""
    try:
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024
        
        with open(output_path, 'wb') as f, tqdm(
            desc=os.path.basename(output_path),
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                f.write(data)
        
        return True
    except Exception as e:
        print(f"下载文件失败: {e}")
        return False

def download_dataset(dataset_name, output_dir):
    """下载指定数据集"""
    if dataset_name not in DATA_SOURCES:
        print(f"错误: 未知的数据集 '{dataset_name}'")
        return False
    
    dataset = DATA_SOURCES[dataset_name]
    print(f"下载数据集: {dataset['description']}")
    
    # 对于GitHub仓库，我们需要手动克隆或下载
    if 'github.com' in dataset['url']:
        print(f"请手动克隆或下载GitHub仓库: {dataset['url']}")
        print(f"然后将数据保存到: {output_dir}")
        return True
    
    # 对于直接下载链接
    output_path = os.path.join(output_dir, f"{dataset_name}.zip")
    return download_file(dataset['url'], output_path)

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='多模态虚假新闻数据集收集工具')
    parser.add_argument('--dataset', choices=list(DATA_SOURCES.keys()), help='要下载的数据集名称')
    parser.add_argument('--list', action='store_true', help='列出所有可用的数据集')
    parser.add_argument('--output-dir', default=None, help='输出目录')
    return parser.parse_args()

def main():
    """主函数"""
    args = parse_args()
    
    # 创建数据目录
    base_dir = create_data_dirs()
    raw_dir = base_dir / 'raw'
    
    # 列出可用数据集
    if args.list:
        print("可用的数据集:")
        for name, info in DATA_SOURCES.items():
            print(f"- {name}: {info['description']}")
            print(f"  来源: {info['url']}")
        return
    
    # 下载指定数据集
    if args.dataset:
        output_dir = args.output_dir if args.output_dir else raw_dir
        success = download_dataset(args.dataset, output_dir)
        if success:
            print(f"数据集 '{args.dataset}' 下载或设置完成")
        else:
            print(f"数据集 '{args.dataset}' 下载失败")
    else:
        print("请指定要下载的数据集名称，或使用--list查看可用的数据集")

if __name__ == "__main__":
    main() 