import os
from tkinter import *
from tkinter import filedialog
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
            #self.torrent_arr[index] = (self.torrent_arr[index][0], self.torrent_arr[index][1], progress_bar)
            #


        def show_location_window(self):
            '''
            Открывает торрент файл и создает окно для ввода имени файла и расположения
            '''
            self.torrent_name, self.torrent_path = None, None
            file_path = filedialog.askopenfilename(filetypes=[("Torrent Files", "*.torrent")])
            if file_path:
                location_window = tk.Toplevel(self)
                location_window.geometry("500x200")
                location_window.title("Location and Name")
                location_window.attributes("-topmost", True)

                tk.Label(location_window, text="Torrent Name:").pack(side=tk.TOP)
                self.torrent_name_entry = tk.Entry(location_window)
                self.torrent_name_entry.pack(side=tk.TOP, fill=X, pady=5)

                tk.Label(location_window, text="Torrent Path:").pack(side=tk.TOP)
                self.torrent_path_entry = tk.Entry(location_window)
                self.torrent_path_entry.pack(side=tk.TOP, fill=X, pady=5)

                tk.Button(location_window, text="Folders", width=15,
                          command=self.ask_directory).pack(side=tk.TOP)
                tk.Button(location_window, text="Save", width=15,
                          command=lambda: self.check_errors(location_window, file_path)).pack(side=tk.TOP)

        def ask_directory(self):
            '''
            Спрашивает путь который будет иметь наш торрент файл
            и вводит его в поле ввода
            '''
            directory = filedialog.askdirectory()
            self.torrent_path_entry.delete(0, tk.END)
            self.torrent_path_entry.insert(0, directory)

        def check_errors(self, location_window, file_path):
            '''
            Проверяем на корректность ввод данных пользователя
            и если он хорош удаляем экран и создаем поток для скачивания торрент файла
            '''
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
                threading.Thread(target=self.download_torrent_file, args=(file_path, len(self.torrent_arr))).start()

        def show_torrent_info(self, torrent_name, index):
            '''
            Разметка торрент виджетов
            '''

            info_frame = tk.Frame(self, bg='#e1e1e1')
            info_frame.pack(side=tk.TOP, pady=5, padx=5, anchor=tk.W, fill=X)

            name_label = tk.Label(info_frame, text=f"{torrent_name}", width=15, anchor=tk.W, bg='#e1e1e1')
            name_label.pack(side=tk.TOP, padx=5, anchor=tk.W)

            progress_bar = ttk.Progressbar(info_frame, orient="horizontal", mode="determinate")
            progress_bar.pack(side=tk.TOP, padx=5, anchor=tk.W, fill=BOTH)
            self.torrent_arr[index] = (self.torrent_arr[index][0], self.torrent_arr[index][1], progress_bar)

            speed_volume_frame = tk.Frame(info_frame, bg='#e1e1e1')
            speed_volume_frame.pack(side=tk.TOP, anchor=tk.W, padx=5)

            download_speed_label = tk.Label(speed_volume_frame, text="", bg='#e1e1e1')
            download_speed_label.pack(side=tk.LEFT)

            downloaded_volume_label = tk.Label(speed_volume_frame, text="", bg='#e1e1e1')
            downloaded_volume_label.pack(side=tk.LEFT, padx=5)

            self.torrent_arr[index] = (*self.torrent_arr[index], download_speed_label, downloaded_volume_label)

            path_button = tk.Button(speed_volume_frame, text="!!!", command=lambda i=index: self.show_torrent_path(i), bg='#e1e1e1')
            path_button.pack(side=tk.LEFT, padx=5)

        def show_torrent_path(self, index):
            '''
            Показывает путь до торрент файла
            '''
            torrent_path = self.torrent_arr[index][1].status().save_path
            mb.showinfo("Торрент-путь", f"Путь к торрент-файлу {self.torrent_arr[index][1].name()}: {torrent_path}")

        def update_progress_bar(self, index, progress, current_downloaded, total_size):
            '''
            Функция обновляющая прогресбар
            '''
            self.torrent_arr[index][2]['value'] = progress

            downloaded_volume_label = self.torrent_arr[index][4]
            downloaded_volume = current_downloaded / 1024 / 1024 / 1024
            downloaded_volume_label.config(text=f"{downloaded_volume:.2f} ГB / {total_size / 1024 / 1024 / 1024:.2f} ГB")

        def download_torrent_file(self, file_path, index):
            '''
            Функция отвечающая за скачивание торрент файла
            '''
            try:
                ses = lt.session()
                info = lt.torrent_info(file_path)
                h = ses.add_torrent({"ti": info, "save_path": os.path.join(self.torrent_path, self.torrent_name)})

                total_size = h.status().total_wanted

                self.torrent_arr.append((ses, h, None, None, 0.0, total_size))
                mb.showinfo("Успех", f"Торрент-файл {self.torrent_name} успешно загружен.")

                self.show_torrent_info(self.torrent_name, index)
                initial_downloaded = h.status().total_done

                while not h.is_seed():
                    status = h.status()
                    progress = status.progress * 100

                    current_downloaded = status.total_done
                    self.update_progress_bar(index, progress, current_downloaded, total_size)

                    current_downloaded = status.total_done
                    download_speed = (current_downloaded - initial_downloaded) / 1024 / 1024  # in MB/s

                    # Update the download speed label
                    download_speed_label = self.torrent_arr[index][3]
                    download_speed_label.config(text=f"{download_speed:.2f} MB/s")

                    initial_downloaded = current_downloaded

                    time.sleep(1)

                download_speed_label.config(text="0.00 MB/s")

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
            info_menu.add_command(label="загруженные", command=self.show_info1)
            info_menu.add_command(label="все", command=self.show_info1)
            info_menu.add_command(label="загружаются", command=self.show_info2)


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



        def show_info1(self):
            '''
            все
            '''
            # Удаление всех виджетов
            self.clear_screen()

            # Отображение всех элементов torrent_arr
            for index, torrent_info in enumerate(self.torrent_arr):
                self.show_torrent_info(torrent_info[0], index)


        def show_info1(self):
            '''
            все
            '''
            # Удаление всех виджетов
            self.clear_screen()

            # Отображение всех элементов torrent_arr
            for index, torrent_info in enumerate(self.torrent_arr):
                self.show_torrent_info(torrent_info[1].name(), index)

        def show_info2(self):
            '''
            загружаются
            '''
            # Удаление всех виджетов
            self.clear_screen()

            # Отображение только тех элементов torrent_arr, у которых torrent_arr[i][4] != 0.0
            for index, torrent_info in enumerate(self.torrent_arr):
                if torrent_info[4] != 0.0:
                    self.show_torrent_info(torrent_info[1].name(), index)

        def clear_screen(self):
            '''
            Очищает экран от виджетов
            '''
            for widget in self.winfo_children():
                widget.destroy()



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

        def put_left_btns(self):
            btn_text = ['Все                 ', 'Загружаются  ', 'Раздаются      ', 'Завершены    ', 'С ошибкой     ']

            for i in range(5):
                btn = tk.Button(self, activeforeground='#1f1f1f', activebackground=self['bg'],
                                relief=tk.FLAT, text=btn_text[i], fg='#1f1f1f', font=self.text_font,
                                bg=self['bg'], command=lambda i=i: self.show_torrents(i))
                btn.pack(anchor=W, fill=X, padx=5)
        def put_widgets(self):

            tk.Label(self, text="Статус", background=self['bg'], fg="black", font=("Segoe UI", 12)).pack(
                anchor=N, fill=BOTH, pady=10)

            self.icons()
            self.put_left_btns()
