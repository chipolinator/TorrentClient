import os
from tkinter import filedialog
from torrent_operations import *
import tkinter as tk
from tkinter import messagebox as mb
import libtorrent as lt
from tkinter import ttk
import time
import threading

class View:
    class UPframe(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)
            self.draw_menu()
            self.torrent_arr = []

        def show_location_window(self):
            '''
            Открываем торрент файл и создаем окно для ввода имени файла и расположения
            '''
            self.torrent_name, self.torrent_path = None, None
            file_path = filedialog.askopenfilename(filetypes=[("Torrent Files", "*.torrent")])
            if file_path:
                location_window = tk.Toplevel(self)
                location_window.title("Location and Name")
                location_window.attributes("-topmost", True)

                tk.Label(location_window, text="Torrent Name:").pack(side=tk.TOP)
                self.torrent_name_entry = tk.Entry(location_window)
                self.torrent_name_entry.pack(side=tk.TOP)

                tk.Label(location_window, text="Torrent Path:").pack(side=tk.TOP)
                self.torrent_path_entry = tk.Entry(location_window)
                self.torrent_path_entry.pack(side=tk.TOP)
                tk.Button(location_window, text="Folders", command=self.ask_directory).pack(side=tk.TOP)

                tk.Button(location_window, text="Save", command=lambda: self.check_errors(location_window, file_path)).pack(side=tk.TOP)

        def ask_directory(self):
            directory = filedialog.askdirectory()
            self.torrent_path_entry.delete(0, tk.END)
            self.torrent_path_entry.insert(0, directory)

        def check_errors(self, location_window, file_path):
            self.torrent_name = self.torrent_name_entry.get().strip()
            self.torrent_path = self.torrent_path_entry.get()

            if not self.torrent_name or not self.torrent_path:
                mb.showerror("Ошибка", "Для загрузки торрент файла необходимо указать имя папки и путь к ней")
                return
            elif not all(c.isalnum() or c in (' ', '_', '-') for c in self.torrent_name):
                mb.showerror("Ошибка", f"Некорректное имя папки: {self.torrent_name}")
                return
            elif not os.path.exists(self.torrent_path):
                mb.showerror("Ошибка", f"Некорректный путь: {self.torrent_path}")
                return
            else:
                location_window.destroy()
                # Создаем новый поток
                threading.Thread(target=self.download_torrent_file, args=(file_path,)).start()

        def show_torrent_info(self, torrent_name, index):
            info_frame = tk.Frame(self)
            info_frame.pack(side=tk.TOP, pady=5)

            tk.Label(info_frame, text=f"Torrent Name: {torrent_name}", width=15).pack(side=tk.LEFT, padx=5)
            progress_bar = ttk.Progressbar(info_frame, orient="horizontal", length=200, mode="determinate")
            progress_bar.pack(side=tk.LEFT, padx=5)
            self.torrent_arr[index] = (self.torrent_arr[index][0], self.torrent_arr[index][1], progress_bar)

            download_speed_label = tk.Label(info_frame, text="Download Speed: 0.00 MB/s")
            download_speed_label.pack(side=tk.LEFT, padx=5)
            self.torrent_arr[index] = (*self.torrent_arr[index], download_speed_label)

            downloaded_volume_label = tk.Label(info_frame, text="Downloaded Volume: 0.00 MB")
            downloaded_volume_label.pack(side=tk.LEFT, padx=5)
            self.torrent_arr[index] = (*self.torrent_arr[index], downloaded_volume_label)

        def update_progress_bar(self, index, progress):
            self.torrent_arr[index][2]['value'] = progress

        def download_torrent_file(self, file_path):
            try:
                ses = lt.session()
                info = lt.torrent_info(file_path)
                h = ses.add_torrent({"ti": info, "save_path": self.torrent_path})

                index = len(self.torrent_arr)
                self.torrent_arr.append((ses, h, None, None, 0.0))  # Added a placeholder for downloaded volume
                mb.showinfo("Успех", f"Торрент-файл {self.torrent_name} успешно загружен.")

                self.show_torrent_info(self.torrent_name, index)
                initial_downloaded = h.status().total_done

                while not h.is_seed():
                    status = h.status()
                    progress = status.progress * 100
                    self.update_progress_bar(index, progress)

                    current_downloaded = status.total_done
                    download_speed = (current_downloaded - initial_downloaded) / 1024  # in MB/s

                    # Update the download speed label
                    download_speed_label = self.torrent_arr[index][3]
                    download_speed_label.config(text=f"Скорость: {download_speed:.2f} MB/s")

                    # Update the downloaded volume label
                    downloaded_volume = current_downloaded / 1024  # in MB
                    downloaded_volume_label = self.torrent_arr[index][4]
                    downloaded_volume_label.config(text=f"Сколько осталось: {downloaded_volume:.2f} MB")

                    initial_downloaded = current_downloaded

                    time.sleep(1)

            except Exception as e:
                mb.showerror("Ошибка", f"Произошла ошибка при загрузке торрент-файла: {str(e)}")


        def draw_menu(self):
            '''
            Функция выводит меню
            '''
            menu_bar = tk.Menu(self.master)

            file_menu = tk.Menu(menu_bar, tearoff=0)
            file_menu.add_command(label="Открыть", command=self.show_location_window)
            file_menu.add_separator()
            file_menu.add_command(label="Выйти", command=self.exit)

            info_menu = tk.Menu(menu_bar, tearoff=0)
            info_menu.add_command(label="О приложении", command=self.show_info)

            menu_bar.add_cascade(label="Файл", menu=file_menu)
            menu_bar.add_cascade(label="Справка", menu=info_menu)
            self.master.config(menu=menu_bar)

        def exit(self):
            '''
            Функция вызывающаяся после того как мы приняли решение выйти (через меню)
            '''
            choice = mb.askyesno("Выход", "Вы уверены, что хотите выйти?")
            if choice:
                for torrent in self.torrent_arr:
                    ses, h, progress_bar = torrent
                    if not h.is_seed():
                        ses.remove_torrent(h)
                        mb.showinfo("Информация", f"Скачивание торрента {self.torrent_name} прекращено.")
                    else:
                        mb.showinfo("Информация", f"Торрент {self.torrent_name} был загружен полностью.")

                self.master.destroy()

        def show_info(self):
            '''
            Выводит информацию после нажатии на кнопку "Справка"
            '''
            mb.showinfo("Информация", "Любительский торрент клиент")



    class LEFTframe(tk.Frame):
        def __init__(self, parent):
            super().__init__(parent)

            self['bg'] = '#07ED7E'
            self.text_font = ("Segoe UI", 11)

            self.put_widgets()

        def icons(self):
            global ico1, ico2, ico3, ico4, ico5

            ico1 = tk.PhotoImage(file="icons/ico1.png")
            ico2 = tk.PhotoImage(file="icons/ico2.png")
            ico3 = tk.PhotoImage(file="icons/ico3.png")
            ico4 = tk.PhotoImage(file="icons/ico4.png")
            ico5 = tk.PhotoImage(file="icons/ico5.png")

            icons_list = [ico1, ico2, ico3, ico4, ico5]

            # for icon in icons_list:
            # Label(ICONSframe, bg=self.colors[0],
            # image=icon).pack(anchor=W, fill=X, pady=7.5)

        def put_left_btns(self):
            for i in range(5):
                btn_text = ['Все                 ', 'Загружаются  ', 'Раздаются      ', 'Завершены    ',
                            'С ошибкой     ']

                btn = tk.Button(self, activeforeground='#1f1f1f', activebackground=self['bg'],
                                relief=tk.FLAT, text=btn_text[i], fg='#1f1f1f', font=self.text_font,
                                bg=self['bg'])
                btn.pack(anchor=W, fill=X, padx=5)

        def put_widgets(self):
            Label(self, text="Статус", background=self['bg'], fg="black", font=("Segoe UI", 12)).pack(
                anchor=N, fill=BOTH, pady=10)

            self.icons()
            self.put_left_btns()


