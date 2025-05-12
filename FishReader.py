import tkinter as tk
import tkinter.font as tkFont
import argparse 


class FishReader:
    def __init__(self, text):
        self.text = text
        self.index = 0

        self.root = tk.Tk()
        self.root.title("FishReader")
        
        # 窗口尺寸
        window_width = 1000
        window_height = 50
        
        # 计算窗口位置（水平居中，垂直底部）
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2  # 水平居中
        y = screen_height - window_height - 50  # 距离底部 50 像素
        
        # 设置窗口位置
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.root.configure(bg='black')
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.7)

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
        self.root.bind("<Button-1>", self.handle_click)

        self.root.after(100, self.update_text)
        self.root.mainloop()


    def update_text(self):
        display_text, chars_used = self.get_text_fit_in_window()
        self.label.config(text=display_text)
        self.current_page_len = chars_used

    def get_text_fit_in_window(self):
        width = self.root.winfo_width() - 40  # 减去 padx 的宽度影响
        max_lines = 2  # 固定显示两行
        display_text = []
        chars_used = 0
        line_count = 0

        i = self.index
        while i < len(self.text) and line_count < max_lines:
            current_line = ""
            # 构建当前行，直到达到宽度限制或遇到换行符
            while i < len(self.text):
                char = self.text[i]
                # 遇到换行符时，结束当前行
                if char == '\n':
                    i += 1
                    chars_used += 1
                    break
                # 检查当前行宽度是否超出限制
                test_line = current_line + char
                if self.font.measure(test_line) > width:
                    break
                current_line = test_line
                i += 1
                chars_used += 1
            
            display_text.append(current_line)
            line_count += 1

        # 确保返回两行（如果剩余文本不足，第二行可能为空）
        while len(display_text) < max_lines:
            display_text.append("")

        return '\n'.join(display_text), chars_used
        
    
    def handle_click(self, event):
        x = event.x
        width = self.root.winfo_width()
        if x < width / 3:
            self.page_up()
        elif x > 2 * width / 3:
            self.page_down()
        else:
            self.quit()

    def page_up(self):
        self.index = max(self.index - self.current_page_len, 0)
        self.update_text()

    def page_down(self):
        if self.index + self.current_page_len < len(self.text):
            self.index += self.current_page_len
            self.update_text()

    def quit(self):
        self.root.destroy()


def load_text(file_path):
    with open(file_path, 'r', encoding="gb2312", errors="ignore") as f:
        lines = [line for line in f if line.strip()]
        return ''.join(lines)


if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='FishReader - 迷你文本阅读器')
    parser.add_argument('filename', help='要打开的文本文件路径')
    args = parser.parse_args()
    
    try:
        text = load_text(args.filename)  # 从参数获取文件名
        FishReader(text)
    except FileNotFoundError:
        print(f"错误：文件 {args.filename} 不存在！")
    except Exception as e:
        print(f"打开文件时出错: {e}")
        