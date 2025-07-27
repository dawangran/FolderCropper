# FolderCropper

一个用于裁剪信号数据文件的命令行工具，支持.csv和.npy格式，提供断点续跑和报告生成功能。

## 功能特点
- 批量处理.csv和.npy格式的信号文件
- 支持手动选择裁剪区域
- 断点续跑功能，避免重复工作
- 生成裁剪报告（TXT和HTML格式）
- 命令行交互界面

## 安装要求
- Python 3.6+
- 依赖库：numpy, pandas, scipy

## 安装方法
```bash
pip install -r requirements.txt
# 或
python setup.py install
```

## 使用方法
```bash
# 基本用法
python handle_signal.py <输入文件夹路径> --output_folder <输出文件夹路径>

# 完整参数
python handle_signal.py ./data \ 
  --output_folder ./cropped \ 
  --checkpoint ./checkpoint.json \ 
  --max_points 2000000
```

## 操作说明
运行程序后，会逐个处理文件，支持以下操作：
- 裁剪(c)：手动输入起始和结束索引进行裁剪
- 跳过(s)：跳过当前文件
- 退出(q)：退出程序并保存进度

## 许可证
本项目采用MIT许可证 - 详见LICENSE文件