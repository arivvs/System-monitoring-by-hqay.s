import customtkinter as ctk
import psutil
import threading
import time
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

ctk.set_appearance_mode("dark") # Можно поменять на light
ctk.set_default_color_theme("green") # Можно поменять на blue/dark-blue/green

try:
    import GPUtil

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False


class SystemMonitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("System monitoring by hqay.s")
        self.geometry("950x600")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Боковая панель ---
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(self.sidebar, text="monitoring", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=30)

        self.add_menu_btn("Общая информация", "main")
        self.add_menu_btn("Процессы CPU", "cpu")
        self.add_menu_btn("Статистика GPU", "gpu")
        self.add_menu_btn("Процессы RAM", "ram")

        ctk.CTkButton(self.sidebar, text="ВЫХОД", fg_color="#922b21", hover_color="#7b241c", command=self.quit).pack(
            side="bottom", pady=20, padx=20, fill="x")

        # --- Контент ---
        self.container = ctk.CTkFrame(self, corner_radius=15)
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.header = ctk.CTkLabel(self.container, text="Загрузка...", font=ctk.CTkFont(size=24, weight="bold"))
        self.header.pack(pady=15)

        self.display_box = ctk.CTkTextbox(self.container, font=("Consolas", 16), text_color="#3498db", wrap="none")
        self.display_box.pack(expand=True, fill="both", padx=20, pady=20)

        self.current_tab = "main"
        psutil.cpu_percent(interval=None)

        threading.Thread(target=self.update_loop, daemon=True).start()

    def add_menu_btn(self, name, target):
        btn = ctk.CTkButton(self.sidebar, text=name, command=lambda: self.switch_tab(target))
        btn.pack(pady=10, padx=20, fill="x")
        return btn

    def switch_tab(self, tab):
        self.current_tab = tab

    def get_bar(self, percent, length=20):
        percent = min(max(percent, 0), 100)
        filled = int(length * percent / 100)
        bar = "█" * filled + "-" * (length - filled)
        return f"[{bar}] {percent:>5.1f}%"

    def update_loop(self):
        while True:
            text = ""
            # Общие замеры
            total_cpu = psutil.cpu_percent()
            total_ram = psutil.virtual_memory()
            total_disk = psutil.disk_usage('/')

            if self.current_tab == "main":
                self.header.configure(text="Общая информация")
                text += f"CPU Total:   {self.get_bar(total_cpu)}\n\n"
                text += f"RAM Total:   {self.get_bar(total_ram.percent)}\n"
                text += f"             ({total_ram.used // 1024 ** 2}MB / {total_ram.total // 1024 ** 2}MB)\n\n"
                text += f"Disk Space:  {self.get_bar(total_disk.percent)}"

            elif self.current_tab in ["cpu", "ram"]:
                label = "ЦПУ" if self.current_tab == "cpu" else "ОЗУ (RAM)"
                self.header.configure(text=f"Процессы {label}")

                if self.current_tab == "cpu":
                    text += f"Общая нагрузка на CPU: {self.get_bar(total_cpu)}\n"
                else:
                    text += f"Общая нагрузка на RAM: {self.get_bar(total_ram.percent)} ({total_ram.used // 1024 ** 2}MB)\n"

                text += "=" * 50 + "\n"
                text += f"{'Название процесса':<28} | {'Нагрузка':<10}\n"
                text += "-" * 50 + "\n"

                grouped_procs = {}

                for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                    try:
                        info = p.info
                        name = info['name']
                        if name.lower() in ['idle', 'system idle process', 'system']:
                            continue
                        if self.current_tab == "cpu":
                            val = info['cpu_percent'] / psutil.cpu_count()
                        else:
                            val = info['memory_percent']

                        # Суммируем, если такой же уже есть
                        if name in grouped_procs:
                            grouped_procs[name] += val
                        else:
                            grouped_procs[name] = val

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Фильтруем процессы менее 0.1%
                final_procs = [
                    {'name': name, 'val': val}
                    for name, val in grouped_procs.items()
                    if val >= 0.1
                ]

                top = sorted(final_procs, key=lambda x: x['val'], reverse=True)[:15]

                for p in top:
                    name = p['name']
                    if len(name) > 27: name = name[:24] + "..."
                    text += f"{name:<28} | {p['val']:>7.1f}%\n"

            elif self.current_tab == "gpu":
                self.header.configure(text="Видеокарта (GPU)")
                if not GPU_AVAILABLE:
                    text = "Библиотека GPUtil не найдена."
                else:
                    gpus = GPUtil.getGPUs()
                    if not gpus: text = "GPU не найден."
                    for g in gpus:
                        text += f"Модель: {g.name}\n"
                        text += f"Нагрузка: {self.get_bar(g.load * 100)}\n"
                        text += f"Температура: {int(g.temperature)}°C\n"
                        text += f"Память: {int(g.memoryUsed)}MB / {int(g.memoryTotal)}MB"

            try:
                self.display_box.configure(state="normal")
                self.display_box.delete("1.0", "end")
                self.display_box.insert("1.0", text)
                self.display_box.configure(state="disabled")
            except:
                break

            # Обновление раз в 2 секунды
            time.sleep(2)


if __name__ == "__main__":
    app = SystemMonitorApp()
    app.mainloop()
