import os

def is_code_file(filename):
    """检查文件是否为代码文件"""
    code_extensions = ['.py', '.js', '.vue', '.html', '.css', '.java', '.c', '.cpp', '.h', '.go', '.php', '.rb', '.sh']
    return any(filename.endswith(ext) for ext in code_extensions)

def get_file_content(filepath):
    """读取文件内容，处理可能的编码问题"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(filepath, 'r', encoding='gbk') as f:
                return f.read()
        except Exception as e:
            return f"<无法读取文件内容，编码错误: {str(e)}>"
    except Exception as e:
        return f"<读取文件出错: {str(e)}>"

def process_directory(root_dir, output_file):
    """处理目录，收集所有代码文件信息"""
    with open(output_file, 'w', encoding='utf-8') as out_f:
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if is_code_file(file):
                    filepath = os.path.join(root, file)
                    relative_path = os.path.relpath(filepath, start=root_dir)
                    
                    # 写入文件信息
                    out_f.write(f"\n\n{'=' * 80}\n")
                    out_f.write(f"文件路径: {relative_path}\n")
                    out_f.write(f"完整路径: {filepath}\n")
                    out_f.write(f"{'=' * 80}\n\n")
                    
                    # 写入文件内容
                    content = get_file_content(filepath)
                    out_f.write(content)

if __name__ == "__main__":
    # 设置输出文件名
    output_filename = "all_code_contents.txt"
    
    # 获取当前目录
    current_dir = os.getcwd()
    
    print(f"开始处理目录: {current_dir}")
    print(f"代码内容将保存到: {output_filename}")
    
    # 处理目录
    process_directory(current_dir, output_filename)
    
    print("处理完成！")

