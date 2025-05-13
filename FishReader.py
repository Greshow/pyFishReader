import tkinter as tk
import tkinter.font as tkFont
import argparse 
import json
import os
import time
from pathlib import Path

class FishReader:
    def __init__(self, text, file_path):
        self.text = text
        self.file_path = os.path.abspath(file_path)
        self.config_file = os.path.expanduser("~/.fishreader.json")
        
        # 加载配置
        self.index = self.load_position()
        self.settings = self.load_settings()
        
        # 自动翻页相关变量
        self.auto_scroll = False
        self.base_speed = self.settings.get("base_speed", 50)  # 基础速度(毫秒/字符)
        self.min_speed = 1000  # 最小停顿时间(毫秒)
        self.max_speed = 7000  # 最大停顿时间(毫秒)
        self.scroll_direction = 1  # 1向下，-1向上
        self.scroll_job = None  # 用于存储after任务
        
        # 初始化UI
        self.root = tk.Tk()
        self.root.title(f"FishReader - {os.path.basename(file_path)} [自动翻页: 关闭↓]")
        
        # 窗口设置
        window_width = 1000
        window_height = 50
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = screen_height - window_height - 50
        
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.configure(bg='black')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.7)

        # 字体和标签
        self.font = tkFont.Font(family="Microsoft YaHei", size=12)
        self.label = tk.Label(
            self.root,
            text='',
            font=self.font,
            fg="white",
            bg="black",
            anchor='nw',
            justify="left",
            padx=20,
        )
        self.label.pack(expand=True, fill='both')
        
        # 绑定事件
        self.root.bind("<Button-1>", self.handle_click)
        self.root.bind("<Button-3>", self.toggle_auto_scroll)  # 右键切换自动翻页
        self.root.bind("<MouseWheel>", self.adjust_scroll_speed)  # 滚轮调整速度
        
        # 开始显示文本
        self.update_text()
        self.root.mainloop()

    def load_position(self):
        """加载该文件的阅读位置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get("positions", {}).get(self.file_path, 0)
        except Exception as e:
            print(f"读取配置文件出错: {e}")
        return 0
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get("settings", {})
        except:
            pass
        return {"base_speed": 50, "auto_scroll": False}
    
    def save_data(self):
        """保存所有数据"""
        try:
            # 读取现有数据
            data = {}
            if os.path.exists(self.config_file):
                try:
                    with open(self.config_file, 'r') as f:
                        data = json.load(f)
                except:
                    pass
            
            # 更新数据
            if "positions" not in data:
                data["positions"] = {}
            data["positions"][self.file_path] = self.index
            data["settings"] = {
                "base_speed": self.base_speed,
                "auto_scroll": self.auto_scroll
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # 写入文件
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"保存数据出错: {e}")

    def update_text(self):
        """更新显示文本"""
        display_text, chars_used = self.get_text_fit_in_window()
        self.label.config(text=display_text)
        self.current_page_len = chars_used
        self.current_chars = len(display_text.replace('\n', ''))  # 计算当前显示的字符数
    
    def get_text_fit_in_window(self):
        """获取适合窗口显示的文本"""
        width = self.root.winfo_width() - 40
        max_lines = 2
        display_text = []
        chars_used = 0
        line_count = 0

        i = self.index
        while i < len(self.text) and line_count < max_lines:
            current_line = ""
            while i < len(self.text):
                char = self.text[i]
                if char == '\n':
                    i += 1
                    chars_used += 1
                    break
                test_line = current_line + char
                if self.font.measure(test_line) > width:
                    break
                current_line = test_line
                i += 1
                chars_used += 1
            
            display_text.append(current_line)
            line_count += 1

        while len(display_text) < max_lines:
            display_text.append("")

        return '\n'.join(display_text), chars_used
        
    def handle_click(self, event):
        """处理鼠标点击"""
        x = event.x
        width = self.root.winfo_width()
        
        if x < width / 3:  # 左三分之一区域
            self.page_up()
        elif x > 2 * width / 3:  # 右三分之一区域
            self.page_down()
        else:  # 中间区域
            self.quit()
    
    def toggle_auto_scroll(self, event=None):
        """切换自动翻页状态"""
        if self.scroll_job:
            self.root.after_cancel(self.scroll_job)
            self.scroll_job = None
            
        self.auto_scroll = not self.auto_scroll
        status = "开启" if self.auto_scroll else "关闭"
        direction = "↓" if self.scroll_direction == 1 else "↑"
        self.root.title(f"FishReader - {os.path.basename(self.file_path)} [自动翻页: {status}{direction}]")
        
        if self.auto_scroll:
            self.scroll_page()
    
    def scroll_page(self):
        """执行翻页并根据字符数量调整停顿时间"""
        if self.auto_scroll:
            if self.scroll_direction == 1:  # 向下
                self.page_down()
            else:  # 向上
                self.page_up()
            
            if self.auto_scroll:  # 检查是否仍然需要自动翻页
                # 根据当前显示的字符数量计算停顿时间
                pause_time = min(max(
                    self.base_speed * self.current_chars,  # 字符数*阅读速度ms/字符
                    self.min_speed
                ), self.max_speed)
                
                self.scroll_job = self.root.after(int(pause_time), self.scroll_page)
    
    def adjust_scroll_speed(self, event):
        """用鼠标滚轮调整基础速度"""
        if event.delta > 0:  # 滚轮向上，加快速度(减少基础速度)
            self.base_speed = max(10, self.base_speed - 1)
        else:  # 滚轮向下，减慢速度(增加基础速度)
            self.base_speed = min(100, self.base_speed + 1)
        
        # 临时显示速度
        original_title = self.root.title()
        self.root.title(f"速度: {self.base_speed}ms/字符")
        self.root.after(1000, lambda: self.root.title(original_title))
    
    def change_scroll_direction(self):
        """改变滚动方向"""
        self.scroll_direction *= -1
        direction = "↓" if self.scroll_direction == 1 else "↑"
        status = "开启" if self.auto_scroll else "关闭"
        self.root.title(f"FishReader - {os.path.basename(self.file_path)} [自动翻页: {status}{direction}]")
    
    def page_up(self):
        """向上翻页"""
        self.index = max(self.index - self.current_page_len, 0)
        self.update_text()
    
    def page_down(self):
        """向下翻页"""
        if self.index + self.current_page_len < len(self.text):
            self.index += self.current_page_len
            self.update_text()
        else:
            self.toggle_auto_scroll()  # 到达末尾停止自动翻页
    
    def quit(self):
        """退出程序"""
        if self.scroll_job:
            self.root.after_cancel(self.scroll_job)
        self.save_data()
        self.root.destroy()

def load_text(file_path):
    """加载文本文件"""
    encodings = ['gb2312', 'utf-8', 'gbk']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding, errors="ignore") as f:
                lines = [line for line in f if line.strip()]
                return ''.join(lines)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"无法解码文件: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FishReader - 摸鱼阅读器')
    parser.add_argument('filename', help='要打开的文本文件路径')
    args = parser.parse_args()
    
    try:
        text = load_text(args.filename)
        FishReader(text, args.filename)
    except FileNotFoundError:
        print(f"错误：文件 {args.filename} 不存在！")
    except Exception as e:
        print(f"打开文件时出错: {e}")