import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from PIL import Image, ImageFile
import shutil
from datetime import datetime

# 启用PIL的截断文件加载功能
ImageFile.LOAD_TRUNCATED_IMAGES = True


class EnhancedImageCompressorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("增强版图片批量压缩工具")
        self.root.geometry("900x750")
        self.root.resizable(True, True)

        # 变量初始化
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.quality = tk.IntVar(value=80)
        self.delete_source = tk.BooleanVar(value=False)
        self.simulate_mode = tk.BooleanVar(value=False)
        self.processing = False
        self.total_files = 0
        self.processed_files = 0
        self.skipped_files = 0
        self.failed_files = 0

        self.setup_ui()

    def setup_ui(self):
        """设置用户界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 输入文件夹选择
        ttk.Label(main_frame, text="输入文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(input_frame, textvariable=self.input_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览", command=self.select_input_dir).pack(side=tk.RIGHT, padx=5)

        # 输出文件夹选择（可选）
        ttk.Label(main_frame, text="输出文件夹(可选):").grid(row=1, column=0, sticky=tk.W, pady=5)
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Entry(output_frame, textvariable=self.output_dir, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览", command=self.select_output_dir).pack(side=tk.RIGHT, padx=5)

        # 压缩质量调节
        ttk.Label(main_frame, text="压缩质量:").grid(row=2, column=0, sticky=tk.W, pady=5)
        quality_frame = ttk.Frame(main_frame)
        quality_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        ttk.Scale(quality_frame, from_=0, to=100, variable=self.quality,
                  orient=tk.HORIZONTAL).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(quality_frame, textvariable=self.quality).pack(side=tk.RIGHT, padx=5)

        # 选项框架
        options_frame = ttk.LabelFrame(main_frame, text="处理选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        ttk.Checkbutton(options_frame, text="删除源文件",
                        variable=self.delete_source).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(options_frame, text="模拟运行",
                        variable=self.simulate_mode).grid(row=0, column=1, sticky=tk.W, padx=20)

        # 文件格式信息
        format_frame = ttk.LabelFrame(main_frame, text="支持的文件格式", padding="10")
        format_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        ttk.Label(format_frame, text="来源格式: JPG, PNG, JPEG, BMP").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(format_frame, text="目标格式: JPEG").grid(row=0, column=1, sticky=tk.W, padx=20)

        # 统计信息框架
        stats_frame = ttk.LabelFrame(main_frame, text="处理统计", padding="10")
        stats_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)

        self.stats_label = ttk.Label(stats_frame, text="等待开始处理...")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)

        # 进度条
        ttk.Label(main_frame, text="处理进度:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL,
                                            length=400, mode='determinate')
        self.progress_bar.grid(row=6, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)

        ttk.Button(button_frame, text="开始转换",
                   command=self.start_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="模拟运行",
                   command=self.toggle_simulate).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志",
                   command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="退出",
                   command=self.root.quit).pack(side=tk.LEFT, padx=5)

        # 日志文本框
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.log_text = tk.Text(log_frame, height=12, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                  command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(8, weight=1)

    def select_input_dir(self):
        """选择输入文件夹"""
        directory = filedialog.askdirectory()
        if directory:
            self.input_dir.set(directory)

    def select_output_dir(self):
        """选择输出文件夹"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir.set(directory)

    def toggle_simulate(self):
        """切换模拟运行模式"""
        self.simulate_mode.set(not self.simulate_mode.get())
        mode = "模拟运行" if self.simulate_mode.get() else "实际运行"
        self.log(f"切换到{mode}模式")

    def log(self, message):
        """添加日志信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def update_stats(self):
        """更新统计信息 - 增加总文件数显示"""
        stats_text = f"总文件: {self.total_files} | 已处理: {self.processed_files} | 跳过: {self.skipped_files} | 失败: {self.failed_files}"
        self.stats_label.config(text=stats_text)

    def get_output_path(self, source_path):
        """根据源文件路径获取输出路径，保持相同文件名"""
        input_path = Path(self.input_dir.get())
        relative_path = source_path.relative_to(input_path)

        # 保持相同的文件名，只改变扩展名为.jpeg
        if not self.output_dir.get():
            return source_path.with_suffix('.jpeg')
        else:
            return Path(self.output_dir.get()) / relative_path.with_suffix('.jpeg')

    def fast_walk_directory(self, root_path):
        """快速目录遍历 - 用于嵌套目录"""
        from concurrent.futures import ThreadPoolExecutor
        import queue

        file_queue = queue.Queue()
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

        def scan_directory(path):
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file():
                        file_path = Path(entry.path)
                        if file_path.suffix.lower() in supported_extensions:
                            file_size = entry.stat().st_size
                            if file_size > 2 * 1024 * 1024:
                                file_queue.put(file_path)
                    elif entry.is_dir():
                        scan_directory(entry.path)

        # 使用线程池并行扫描
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.submit(scan_directory, root_path)

        return list(file_queue.queue)

    def is_image_corrupted(self, file_path):
        """检测图片文件是否损坏"""
        try:
            with Image.open(file_path) as img:
                # 尝试加载图片数据
                img.load()
                return False, None
        except Exception as e:
            return True, str(e)

    def collect_image_files(self):
        """优化后的文件收集方法 - 支持多级目录"""
        image_files = []
        input_path = Path(self.input_dir.get())

        self.log("开始快速扫描图片文件...")

        # 使用优化后的多级目录扫描
        file_paths = self.fast_walk_directory(input_path)

        for file_path in file_paths:
            relative_path = file_path.relative_to(input_path)
            output_path = self.get_output_path(file_path)
            file_size = file_path.stat().st_size

            image_files.append({
                'source_path': file_path,
                'relative_path': relative_path,
                'output_path': output_path,
                'size': file_size,
                'modified_time': file_path.stat().st_mtime,
                'extension': file_path.suffix.lower(),
                'is_corrupted': False,  # 延迟检测
                'error_info': None
            })

        self.log(f"快速扫描完成，共找到 {len(image_files)} 个需要压缩的文件")
        return image_files

    def compress_image(self, source_path, target_path, quality):
        """压缩单张图片，支持BMP格式转换和损坏文件处理"""
        try:
            with Image.open(source_path) as img:
                # 转换为RGB模式（确保兼容JPEG）
                if img.mode in ('RGBA', 'LA', 'P'):
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                else:
                    rgb_img = img.convert('RGB')

                # 保存为JPEG格式，使用.jpeg后缀
                rgb_img.save(target_path, 'JPEG', quality=quality, optimize=True)

                # 正确保留源文件的修改日期时间
                stat = source_path.stat()
                os.utime(target_path, (stat.st_atime, stat.st_mtime))

                return True, None
        except Exception as e:
            return False, str(e)

    def handle_corrupted_file(self, file_info):
        """处理损坏的文件"""
        source_path = file_info['source_path']
        target_path = file_info['output_path']
        error_info = file_info['error_info']

        self.log(f"⚠ 检测到损坏文件: {file_info['relative_path']}")
        self.log(f"⚠ 错误信息: {error_info}")

        # 对于损坏的文件，尝试复制而不是压缩
        try:
            shutil.copy2(source_path, target_path)
            self.log(f"✓ 已复制损坏文件（无法压缩）")
            return True, "文件损坏，已复制原文件"
        except Exception as e:
            return False, f"复制失败: {e}"

    def process_images(self):
        """处理所有图片文件"""
        if not self.input_dir.get():
            messagebox.showerror("错误", "请选择输入文件夹")
            return

        try:
            # 收集文件信息
            image_files = self.collect_image_files()
            self.total_files = len(image_files)
            self.processed_files = 0
            self.skipped_files = 0
            self.failed_files = 0

            if self.total_files == 0:
                self.log("没有找到需要压缩的图片文件")
                return

            # 更新进度条
            self.progress_bar['maximum'] = self.total_files
            self.progress_bar['value'] = 0

            # 处理每个文件
            for file_info in image_files:
                if not self.processing:
                    break

                source_path = file_info['source_path']
                relative_path = file_info['relative_path']
                target_path = file_info['output_path']

                # 确保目标目录存在
                target_path.parent.mkdir(parents=True, exist_ok=True)

                if self.simulate_mode.get():
                    self.log(f"[模拟] 处理文件: {relative_path}")
                    if file_info['is_corrupted']:
                        self.log(f"[模拟] 文件损坏，将复制原文件")
                else:
                    self.log(f"正在处理: {relative_path}")

                    # 根据文件是否损坏选择处理方式
                    # if file_info['is_corrupted']:
                    #     success, error = self.handle_corrupted_file(file_info)
                    # else:
                    #     success, error = self.compress_image(source_path, target_path, self.quality.get())

                    # 延迟损坏检测
                    is_corrupted, error = self.is_image_corrupted(source_path)
                    # 根据文件是否损坏选择处理方式
                    if is_corrupted:
                        success, error = self.handle_corrupted_file(file_info)
                    else:
                        success, error = self.compress_image(source_path, target_path, self.quality.get())

                    if success:
                        if file_info['is_corrupted']:
                            # 对于损坏文件，只记录复制操作
                            self.log(f"✓ 处理完成（文件损坏，无法压缩）")
                        else:
                            compressed_size = target_path.stat().st_size
                            reduction = (1 - compressed_size / file_info['size']) * 100
                            self.log(f"✓ 压缩完成: {relative_path} (减少 {reduction:.1f}%)")

                        # 只有当源文件和目标文件不同路径时才删除源文件
                        if self.delete_source.get():
                            if source_path != target_path:
                                source_path.unlink()
                                self.log(f"✓ 删除源文件: {relative_path}")

                    else:
                        self.failed_files += 1
                        self.log(f"✗ 处理失败: {relative_path} - {error}")

                self.processed_files += 1
                self.progress_bar['value'] = self.processed_files
                self.update_stats()
                self.root.update_idletasks()

            # 处理完成
            if self.processing:
                self.log("所有文件处理完成！")
                self.log(
                    f"统计: 总文件 {self.total_files}个，成功 {self.processed_files - self.failed_files}个，失败 {self.failed_files}个")
                messagebox.showinfo("完成",
                                    f"处理完成！\n总文件: {self.total_files}个\n成功: {self.processed_files - self.failed_files}个\n失败: {self.failed_files}个")

        except Exception as e:
            self.log(f"处理过程中发生错误: {e}")
            messagebox.showerror("错误", f"处理失败: {e}")

        finally:
            self.processing = False

    def start_processing(self):
        """开始处理过程"""
        if self.processing:
            return

        self.processing = True
        self.processed_files = 0
        self.skipped_files = 0
        self.failed_files = 0
        self.log("开始图片压缩处理...")

        # 显示输出路径信息
        if not self.output_dir.get():
            self.log("输出目录未设置，将在原文件路径创建压缩文件")
        else:
            self.log(f"输出目录: {self.output_dir.get()}")

        # 在新线程中运行处理过程
        processing_thread = threading.Thread(target=self.process_images)
        processing_thread.daemon = True
        processing_thread.start()


def main():
    root = tk.Tk()
    app = EnhancedImageCompressorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

# ‌主要改进内容：‌
#
# ‌增加总文件数显示‌：在统计信息中明确显示"总文件: X个"，让用户清楚知道总共需要处理的文件数量
#
# ‌完整的统计信息‌：
#
# 总文件数
# 已处理文件数
# 跳过文件数
# 失败文件数
# ‌增强的错误处理‌：
#
# 自动检测损坏的图片文件
# 对损坏文件进行复制而非压缩
# 详细的错误信息记录
# ‌格式兼容性‌：
#
# 支持JPG、PNG、JPEG、BMP四种输入格式
# 统一输出为JPEG格式
# ‌性能优化‌：
#
# 一次性收集所有文件信息
# 启用PIL截断文件加载功能
# 多线程处理避免界面卡顿
# ‌使用说明：‌
#
# 选择输入文件夹（必需）
# 选择输出文件夹（可选，如不选则保存到原文件路径
# 调整压缩质量（0-100）
# 可选择是否删除源文件
# 支持模拟运行模式
# 程序现在提供了完整的文件处理统计信息，包括总文件数，让用户能够清楚地了解处理进度和整体情况。