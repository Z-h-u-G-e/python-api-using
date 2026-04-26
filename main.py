import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import requests
import threading

# ================= 配置 =================
API_URL = "https://api.siliconflow.cn/v1/chat/completions"
API_KEY = ""
MODEL = "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B"
TIMEOUT = 180  # 超时时间 180 秒，足够长
# =======================================

class ChatApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepSeek-R1-0528-Qwen3-8B")
        self.root.geometry("800x600")

        self.messages = []            # 对话历史
        self.waiting = False          # 是否正在等待回复

        self.create_widgets()
        self.input_text.bind("<Control-Return>", lambda e: self.send_message())

    def create_widgets(self):
        # 显示区域
        display_frame = ttk.LabelFrame(self.root, text="对话记录", padding=5)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.display_text = scrolledtext.ScrolledText(
            display_frame, wrap=tk.WORD, font=("Consolas", 10), state=tk.DISABLED
        )
        self.display_text.pack(fill=tk.BOTH, expand=True)
        self.display_text.tag_config("user", foreground="blue", font=("Consolas", 10, "bold"))
        self.display_text.tag_config("assistant", foreground="green", font=("Consolas", 10, "bold"))

        # 输入区域
        input_frame = ttk.LabelFrame(self.root, text="输入消息 (Ctrl+Enter 发送)", padding=5)
        input_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        self.input_text = tk.Text(input_frame, height=5, font=("Consolas", 10), wrap=tk.WORD)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)

        self.send_btn = ttk.Button(button_frame, text="发送", command=self.send_message)
        self.send_btn.pack(pady=5)
        self.clear_btn = ttk.Button(button_frame, text="清空对话", command=self.clear_conversation)
        self.clear_btn.pack(pady=5)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def append_message(self, role, content):
        """添加一条消息到显示区域"""
        self.display_text.config(state=tk.NORMAL)
        if role == "user":
            self.display_text.insert(tk.END, f"你：\n{content}\n\n", ("user",))
        else:
            self.display_text.insert(tk.END, f"DeepSeek：\n{content}\n\n", ("assistant",))
        self.display_text.see(tk.END)
        self.display_text.config(state=tk.DISABLED)

    def send_message(self):
        if self.waiting:
            messagebox.showwarning("提示", "请等待当前回复完成")
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            return
        self.input_text.delete("1.0", tk.END)

        # 显示用户消息
        self.append_message("user", user_input)
        self.messages.append({"role": "user", "content": user_input})

        # 开始请求
        self.waiting = True
        self.send_btn.config(state=tk.DISABLED)
        self.status_var.set("正在请求 API ... (最长等待 3 分钟)")

        # 启动线程
        threading.Thread(target=self.call_api, daemon=True).start()

    def call_api(self):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": MODEL,
            "messages": self.messages,
            "temperature": 0.7,
            "max_tokens": 1024,
            "response_format": {"type": "text"}
        }
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=TIMEOUT)
            response.raise_for_status()
            result = response.json()
            assistant_reply = result['choices'][0]['message']['content']
            # 更新界面
            self.root.after(0, self.on_success, assistant_reply)
        except Exception as e:
            # 打印详细错误到控制台，方便调试
            import traceback
            traceback.print_exc()
            self.root.after(0, self.on_error, str(e))

    def on_success(self, reply):
        self.messages.append({"role": "assistant", "content": reply})
        self.append_message("assistant", reply)
        self.waiting = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_var.set("就绪")

    def on_error(self, error_msg):
        # 移除未成功的用户消息（保持历史一致）
        if self.messages and self.messages[-1]["role"] == "user":
            self.messages.pop()
        messagebox.showerror("API 错误", f"请求失败：{error_msg}\n\n请检查 API Key 和网络连接。")
        self.waiting = False
        self.send_btn.config(state=tk.NORMAL)
        self.status_var.set("就绪")

    def clear_conversation(self):
        if self.waiting:
            messagebox.showwarning("提示", "请等待当前回复完成")
            return
        if messagebox.askyesno("确认", "清空所有对话记录吗？"):
            self.messages.clear()
            self.display_text.config(state=tk.NORMAL)
            self.display_text.delete("1.0", tk.END)
            self.display_text.config(state=tk.DISABLED)
            self.status_var.set("对话已清空")

if __name__ == "__main__":
    root = tk.Tk()
    app = ChatApplication(root)
    root.mainloop()