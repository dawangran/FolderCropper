# Developer: Dawn
# Email: 605547565@qq.com
# Project: FolderCropper
# Version: 1.0.0
# Date: 2025-7-27
# ------------------------------------------------------------
#  简化版 FolderCropper
#  支持 .csv / .npy，键盘快捷键，主题切换，日志导出，进度持久化，报告生成
# ------------------------------------------------------------
import os
import json
import datetime as dt
import re
import logging
import warnings
import numpy as np
import pandas as pd
import scipy.signal as sg
import ipywidgets as widgets
from IPython.display import display, HTML, clear_output
import plotly.graph_objects as go
import sys
from ipyevents import Event as IPyEvent  # 键盘事件
from pathlib import Path

# 日志配置
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
logfile = LOG_DIR / f"cropper_{dt.datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(logfile, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FolderCropper")

# ------------------------------------------------------------
class FolderCropper:
    """
    简化版信号裁剪器
    ---------------
    功能列表：
    1. 支持 .csv / .npy 单/双通道
    2. 键盘快捷键（Ctrl+S 保存，Ctrl+D 跳过，Space 下一条）
    3. 亮色 / 暗色 Plotly 主题切换
    4. 滚动日志文件
    5. 断点续跑（JSON 进度保存）
    6. 生成裁剪报告（.txt 和 .html 格式）
    """
    def __init__(self,
                 input_folder: str,
                 output_folder: str = "./cropped",
                 max_points: int = 2_000_000,
                 theme: str = "plotly_white",
                 checkpoint: str = "./checkpoint.json"):
        self.t0 = dt.datetime.now()
        self.max_points = max_points
        self.theme_dark = False
        self.theme = theme
        self.checkpoint_file = Path(checkpoint)
        self.input_folder = Path(input_folder).expanduser().resolve()
        self.output_folder = Path(output_folder).expanduser().resolve()
        self.output_folder.mkdir(parents=True, exist_ok=True)

        logger.info("初始化 FolderCropper")
        logger.info(f"输入目录: {self.input_folder}")
        logger.info(f"输出目录: {self.output_folder}")

        # 扫描文件
        self._scan_files()
        self.total_files = len(self.files)
        if self.total_files == 0:
            raise RuntimeError("未找到任何 .csv / .npy 文件")
        logger.info(f"共发现 {self.total_files} 个文件")

        # 加载信号
        self.signals = {}
        self.meta = {}
        self._load_all()

        # 断点续跑
        self._load_progress()

        # 状态
        self.cur_idx = 0
        self.cur_key = self.files[self.cur_idx].name
        self.sig = self.signals[self.cur_key]

        # 裁剪记录
        self.clip_history = []

        # GUI
        self._build_gui()
        self._bind_shortcuts()
        self._draw_main()

    # --------------------------------------------------------
    def _scan_files(self):
        exts = {'.csv', '.npy'}
        self.files = sorted([p for p in self.input_folder.iterdir()
                             if p.suffix.lower() in exts])
        logger.debug(f"文件列表: {[p.name for p in self.files]}")

    def _load_all(self):
        for p in self.files:
            try:
                if p.suffix.lower() == '.csv':
                    arr = pd.read_csv(p, header=None).to_numpy()
                else:  # .npy
                    arr = np.load(p)
                if arr.ndim == 1:
                    arr = arr[:, None]  # 转为 2-D 列向量
                if arr.ndim != 2:
                    raise ValueError("维度错误")
                if arr.shape[0] > self.max_points:
                    raise ValueError("点数超限")
                self.signals[p.name] = arr.astype(np.float32)
                self.meta[p.name] = {"shape": arr.shape, "type": p.suffix}
                logger.debug(f"加载 {p.name} 成功")
            except Exception as e:
                logger.warning(f"[跳过] {p.name}: {e}")
                self.files.remove(p)

    # --------------------------------------------------------
    def _load_progress(self):
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.cur_idx = min(data.get("index", 0), self.total_files - 1)
                logger.info(f"从断点恢复，index={self.cur_idx}")
            except Exception as e:
                logger.warning(f"断点文件损坏: {e}")
                self.cur_idx = 0
        else:
            self.cur_idx = 0

    def _save_progress(self):
        try:
            with open(self.checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({"index": self.cur_idx, "time": str(dt.datetime.now())}, f)
        except Exception as e:
            logger.error(f"保存断点失败: {e}")

    # --------------------------------------------------------
    def _build_gui(self):
        style = {"description_width": "initial"}
        self.out_main = widgets.Output(layout={"width": "100%", "height": "450px"})
        self.out_prev = widgets.Output(layout={"width": "100%", "height": "200px"})

        self.btn_save = widgets.Button(description="保存 (Ctrl+S)", button_style="info")
        self.btn_skip = widgets.Button(description="跳过 (Ctrl+D)", button_style="warning")
        self.btn_next = widgets.Button(description="下一条 (Space)")
        self.btn_theme = widgets.Button(description="主题切换")
        self.btn_report = widgets.Button(description="生成报告")

        self.tag = widgets.Text(value="", placeholder="标记前缀")
        self.progress = widgets.IntProgress(
            value=self.cur_idx, min=0, max=self.total_files,
            description="进度:", layout=widgets.Layout(width="auto", flex="1"))
        self.label_done = widgets.Label(value=f"{self.cur_idx}/{self.total_files}")

        controls = widgets.HBox([
            self.btn_save, self.btn_skip, self.btn_next,
            self.btn_theme, self.tag, self.progress, self.label_done, self.btn_report
        ], layout=widgets.Layout(flex_flow="wrap"))

        display(widgets.VBox([
            widgets.Label("FolderCropper | 快捷键 Ctrl+S / Ctrl+D / Space | 日志↓"),
            controls,
            self.out_main,
            self.out_prev
        ]))

    # --------------------------------------------------------
    def _bind_shortcuts(self):
        self.kb = IPyEvent(source=self.out_main, watched_events=["keydown"])
        self.kb.on_dom_event(self._handle_key)

    def _handle_key(self, event):
        if event.get("ctrlKey"):
            if event.get("key") == "s":
                self._save_blue(None)
            elif event.get("key") == "d":
                self._skip_file(None)
        elif event.get("key") == " ":
            self._next_file(None)

    # --------------------------------------------------------
    def _draw_main(self):
        idx = np.arange(self.sig.shape[0])
        data = []
        colors = ["#1f77b4", "#ff7f0e"]
        for ch in range(self.sig.shape[1]):
            data.append(go.Scatter(
                x=idx, y=self.sig[:, ch],
                mode="lines", line=dict(color=colors[ch % len(colors)]),
                name=f"CH{ch}"
            ))
        layout = go.Layout(
            title=f"{self.cur_key}  |  {self.sig.shape}",
            xaxis_title="sample index", yaxis_title="amplitude",
            dragmode="select", hovermode="x unified",
            template=self.theme,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        self.main_fig = go.FigureWidget(data=data, layout=layout)
        self.main_fig.data[0].on_selection(self._on_rect)
        with self.out_main:
            self.out_main.clear_output(wait=True)
            display(self.main_fig)

    def _on_rect(self, trace, points, selector):
        if selector.xrange:
            x0, x1 = map(int, selector.xrange)
            self.x0, self.x1 = x0, x1
            self.cropped = self.sig[x0:x1 + 1]
            self._draw_preview()

    def _draw_preview(self):
        idx = np.arange(self.cropped.shape[0])
        data = []
        colors = ["#d62728", "#9467bd"]
        for ch in range(self.cropped.shape[1]):
            data.append(go.Scatter(
                x=idx, y=self.cropped[:, ch],
                mode="lines", line=dict(color=colors[ch % len(colors)]),
                name=f"CH{ch}"
            ))
        layout = go.Layout(
            title=f"预览 {self.cropped.shape}",
            xaxis_title="sample index", yaxis_title="amplitude",
            template=self.theme,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        with self.out_prev:
            self.out_prev.clear_output(wait=True)
            display(go.Figure(data=data, layout=layout))

    # --------------------------------------------------------
    def _save_blue(self, _):
        if not hasattr(self, "cropped"):
            logger.warning("未框选区域")
            return
        tag = re.sub(r'\W+', '_', self.tag.value.strip())
        prefix = f"{tag}_" if tag else ""
        base = f"{prefix}{Path(self.cur_key).stem}_x{self.x0}_{self.x1}.npy"
        out_path = self.output_folder / base
        np.save(out_path, self.cropped)
        logger.info(f"已保存 → {out_path}")
        self.clip_history.append({
            "file_name": self.cur_key,
            "start_index": self.x0,
            "end_index": self.x1,
            "save_path": str(out_path),
            "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        self._next_file(None)

    def _skip_file(self, _):
        logger.info("用户跳过")
        self._next_file(None)

    def _next_file(self, _):
        if self.cur_idx < self.total_files - 1:
            self.cur_idx += 1
            self.cur_key = self.files[self.cur_idx].name
            self.sig = self.signals[self.cur_key]
            self.progress.value = self.cur_idx + 1  # 更新进度条
            self.label_done.value = f"{self.cur_idx + 1}/{self.total_files}"  # 更新已完成数量
            self._save_progress()
            self._draw_main()
        else:
            logger.info("全部完成")
            with self.out_main:
                self.out_main.clear_output()
                display(HTML("<h2>🎉 全部文件已处理完成</h2>"))

    # --------------------------------------------------------
    def _toggle_theme(self, _):
        self.theme_dark = not self.theme_dark
        self.theme = "plotly_dark" if self.theme_dark else "plotly_white"
        logger.info(f"切换主题 → {self.theme}")
        self._draw_main()

    # --------------------------------------------------------
    def _generate_report(self, _):
        report_path_txt = self.output_folder / "cropping_report.txt"
        report_path_html = self.output_folder / "cropping_report.html"

        # 生成 TXT 报告
        with open(report_path_txt, "w", encoding="utf-8") as f:
            f.write("裁剪报告\n")
            f.write("========\n\n")
            for entry in self.clip_history:
                f.write(f"文件名: {entry['file_name']}\n")
                f.write(f"起始索引: {entry['start_index']}\n")
                f.write(f"结束索引: {entry['end_index']}\n")
                f.write(f"保存路径: {entry['save_path']}\n")
                f.write(f"时间戳: {entry['timestamp']}\n")
                f.write("\n")

        # 生成 HTML 报告
        html_content = """
        <html>
        <head>
            <title>裁剪报告</title>
            <style>
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
            </style>
        </head>
        <body>
            <h1>裁剪报告</h1>
            <table>
                <tr>
                    <th>文件名</th>
                    <th>起始索引</th>
                    <th>结束索引</th>
                    <th>保存路径</th>
                    <th>时间戳</th>
                </tr>
        """
        for entry in self.clip_history:
            html_content += f"""
                <tr>
                    <td>{entry['file_name']}</td>
                    <td>{entry['start_index']}</td>
                    <td>{entry['end_index']}</td>
                    <td>{entry['save_path']}</td>
                    <td>{entry['timestamp']}</td>
                </tr>
            """
        html_content += """
            </table>
        </body>
        </html>
        """
        with open(report_path_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"报告已生成并保存到 {report_path_txt} 和 {report_path_html}")

    # --------------------------------------------------------
    def run(self):
        """运行主循环"""
        self.btn_save.on_click(self._save_blue)
        self.btn_skip.on_click(self._skip_file)
        self.btn_next.on_click(self._next_file)
        self.btn_theme.on_click(self._toggle_theme)
        self.btn_report.on_click(self._generate_report)
        logger.info("FolderCropper 已就绪")


# ============================================================
# 在 Notebook 中执行：
# cropper = FolderCropper("./data")
# cropper.run()