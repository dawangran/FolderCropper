# FolderCropper

一个基于JupyterLab的信号数据裁剪工具，提供交互式可视化界面，支持.csv和.npy格式文件的手动裁剪、断点续跑和报告生成功能。

## 功能特点
- ✅ 交互式可视化界面，支持鼠标框选裁剪区域
- ✅ 批量处理.csv和.npy格式的信号文件
- ✅ 键盘快捷键操作（Ctrl+S保存/Ctrl+D跳过/空格下一条）
- ✅ 亮色/暗色主题切换
- ✅ 断点续跑功能，避免重复工作
- ✅ 生成裁剪报告（TXT和HTML格式）
- ✅ 实时日志输出和进度显示

## 安装要求
- Python 3.6+
- JupyterLab 3.0+
- 依赖库：numpy, pandas, plotly, ipywidgets, ipyevents

## 安装方法
```bash
# 安装依赖
pip install -r requirements.txt

# 启用Jupyter widgets扩展
jupyter labextension install @jupyter-widgets/jupyterlab-manager

# 如果使用老版本Jupyter Notebook
jupyter nbextension enable --py widgetsnbextension
```

## 在JupyterLab中使用
1. 启动JupyterLab
```bash
jupyter lab
```

2. 创建新的Notebook，输入以下代码：
```python
from FolderCropper import FolderCropper

# 初始化裁剪器
cropper = FolderCropper(
    input_folder="./data",        # 输入文件夹路径
    output_folder="./cropped",   # 输出文件夹路径
    max_points=2_000_000,         # 最大点数限制
    theme="plotly_white",         # 初始主题
    checkpoint="./checkpoint.json"
)

# 启动交互界面
cropper.run()
```

## 操作指南
### 界面组成
- 📊 主信号图：显示当前文件的信号波形，支持框选区域
- 🔍 预览图：显示裁剪区域的放大预览
- 🎛️ 控制栏：包含保存、跳过、下一条、主题切换等按钮
- 📝 标记输入框：可为裁剪文件添加前缀标记
- ⏳ 进度条：显示当前处理进度

### 快捷键
- `Ctrl+S`：保存当前裁剪区域
- `Ctrl+D`：跳过当前文件
- `空格`：直接进入下一个文件
- 主题切换按钮：在亮色/暗色主题间切换
- 生成报告按钮：处理完成后生成裁剪记录报告

## 数据格式
- 支持单通道/多通道信号
- CSV文件：每行代表一个样本点，多列代表多通道
- NPY文件：需为2D数组格式 (n_samples, n_channels)

## 许可证
本项目采用MIT许可证 - 详见LICENSE文件