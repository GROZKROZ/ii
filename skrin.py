import numpy as np
import datetime
import os
import pyautogui
from PIL import Image, ImageDraw, ImageGrab
import threading
from pynput import mouse
import time
import tkinter as tk
from tkinter import filedialog
from threading import Thread
from screeninfo import get_monitors

# Глобальное событие для управления выполнением программы
running_event = threading.Event()

# Функция для загрузки количества сделанных скриншотов
def load_screenshot_count():
    try:
        with open('screenshot_count.txt', 'r') as file:
            return int(file.read().strip())
    except FileNotFoundError:
        return 0

# Функция для сохранения количества сделанных скриншотов
def save_screenshot_count(count):
    with open('screenshot_count.txt', 'w') as file:
        file.write(str(count))

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

def draw_cross_on_screenshot(screenshot, cursor_position, line_length=20, color='red'):
    draw = ImageDraw.Draw(screenshot)
    x, y = cursor_position
    draw.line((x - line_length, y, x + line_length, y), fill=color, width=3)
    draw.line((x, y - line_length, x, y + line_length), fill=color, width=3)
    return screenshot

def write_data_to_file(filepath, data):
    with open(filepath, 'w') as file:
        file.write(data)

# Обработчик событий мыши
buttons_state = {'Button.left': 0, 'Button.right': 0, 'Button.middle': 0}

def on_click(x, y, button, pressed):
    global buttons_state
    button_name = str(button)
    if pressed:
        if button_name in buttons_state:
            buttons_state[button_name] = 1
    else:
        if button_name in buttons_state:
            buttons_state[button_name] = 0

# Функция для получения информации о всех мониторах с использованием screeninfo
def get_screens_info():
    monitors = get_monitors()
    all_monitors = [(monitor.x, monitor.y, monitor.width, monitor.height) for monitor in monitors]
    return all_monitors

def get_monitor_for_position(x, y, monitors_info):
    for monitor in monitors_info:
        mx, my, mwidth, mheight = monitor
        if mx <= x < mx + mwidth and my <= y < my + mheight:
            return monitor
    return None

def correct_bbox_for_screens(bbox, monitors_info):
    left, top, right, bottom = bbox
    for monitor in monitors_info:
        mx, my, mwidth, mheight = monitor
        if left < mx:
            left = mx
        if top < my:
            top = my
        if right > mx + mwidth:
            right = mx + mwidth
        if bottom > my + mheight:
            bottom = my + mheight
    return (left, top, right, bottom)

# Функция для преобразования координат курсора в единую систему отсчета
def convert_to_global_coordinates(x, y, leftmost, topmost):
    global_x = x - leftmost
    global_y = y - topmost
    return global_x, global_y

def collect_cursor_data(screenshot_dir, coordinates_dir, running_event):
    monitors_info = get_screens_info()
    main_monitor = monitors_info[0]  # предполагаем, что основной монитор - это первый в списке
    mx, my, mwidth, mheight = main_monitor
    screenshot_count = load_screenshot_count()
    prev_x, prev_y = None, None  # инициализируем предыдущее положение курсора
    mouse_listener = mouse.Listener(on_click=on_click)
    mouse_listener.start()

    while running_event.is_set():
        x, y = pyautogui.position()
        if prev_x == x and prev_y == y:
            # Если курсор не двигался, пропускаем итерацию.
            time.sleep(0.1)
            continue
        
        prev_x, prev_y = x, y
        monitor = get_monitor_for_position(x, y, monitors_info)
        if monitor is None:
            # Курсор находится вне границ основного монитора, ждем его возвращения
            time.sleep(0.1)
            continue

        mx, my, mwidth, mheight = monitor
        global_x, global_y = convert_to_global_coordinates(x, y, mx, my)
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')

        # Сохраняем полный скриншот в папку 'full'
        full_size_dir = os.path.join(screenshot_dir, "full")
        create_directory(full_size_dir)
        full_screenshot_filename = os.path.join(full_size_dir, f"screenshot_{timestamp}.png")
        full_screenshot = ImageGrab.grab(bbox=(mx, my, mx + mwidth, my + mheight))
        full_screenshot_with_cross = draw_cross_on_screenshot(full_screenshot, (global_x, global_y))
        full_screenshot_with_cross.save(full_screenshot_filename)

            # Создаем скриншот размером 1000x1000, если курсор находится в пределах допустимой области
        # Создаем и сохраняем скриншот размером 1000x1000.
        size = 1000
        half_size = size // 2
        left = max(global_x - half_size, mx)
        top = max(global_y - half_size, my)
        right = min(global_x + half_size, mx + mwidth)
        bottom = min(global_y + half_size, my + mheight)

        # Если область захвата выходит за пределы экрана, корректируем ее
        if right - left < size:
            if left == mx:
                right = left + size
            else:
                left = right - size
        if bottom - top < size:
            if top == my:
                bottom = top + size
            else:
                top = bottom - size

        bbox = (left, top, right, bottom)
        screenshot = ImageGrab.grab(bbox)
        screenshot_with_cross = draw_cross_on_screenshot(screenshot, (global_x - left, global_y - top))

        # Здесь мы сохраняем скриншот размером 1000x1000
        size_dir = os.path.join(screenshot_dir, f"{size}x{size}")
        create_directory(size_dir)
        screenshot_filename = os.path.join(size_dir, f"screenshot_{size}_{timestamp}.png")
        screenshot_with_cross.save(screenshot_filename)

        # Формируем список из состояний кнопок и записываем данные в файл в папке coordinates
        buttons_list = [buttons_state['Button.left'], buttons_state['Button.right'], buttons_state['Button.middle']]
        info = f"Coordinates: {global_x},{global_y}\nTime: {timestamp}\nClick: {buttons_list}\n"
        coordinates_filename = os.path.join(coordinates_dir, f"coordinates_{timestamp}.txt")
        write_data_to_file(coordinates_filename, info)

        screenshot_count += 1
        save_screenshot_count(screenshot_count)

        time.sleep(0.1)

    mouse_listener.stop()

def stop(running_event):
    running_event.clear()  # Сигнализируем о необходимости остановить программу

def main(output_dir, running_event):
    screenshot_dir = os.path.join(output_dir, "screenshots")
    coordinates_dir = os.path.join(output_dir, "coordinates")

    create_directory(output_dir)
    create_directory(screenshot_dir)
    create_directory(coordinates_dir)
    
    running_event.set()  # Устанавливаем событие в состояние "включено"
    collect_cursor_data(screenshot_dir, coordinates_dir, running_event)
    running_event.clear()  # После остановки сбора данных очищаем событие

program_thread = None
output_dir = "C:\\path_to_output"  # Исходный путь для сохранения файлов

# Функция для загрузки сохраненного пути из файла конфигурации
def load_output_dir():
    config_file = 'config.txt'
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return file.read().strip()
    return "C:\\path_to_output"  # Возвращаем путь по умолчанию, если файл конфигурации не найден

# Функция для сохранения пути в файл конфигурации
def save_output_dir(output_dir):
    config_file = 'config.txt'
    with open(config_file, 'w') as file:
        file.write(output_dir)

def run_gui():
    root = tk.Tk()
    root.title("Program Control")
    root.geometry("250x150")  # Увеличиваем размер окна, чтобы уместить новые элементы

    main_frame = tk.Frame(root)
    main_frame.pack(expand=True, fill='both')

    def start_program():
        global program_thread, output_dir
        if not program_thread or not program_thread.is_alive():
            running_event.set()  # Активируем событие перед запуском потока
            program_thread = Thread(target=main, args=(output_dir, running_event))
            program_thread.start()

    def stop_program():
        if program_thread is not None:
            stop(running_event)
            program_thread.join()

    def change_output_dir():
        global output_dir
        new_dir = filedialog.askdirectory()  # Позволяет пользователю выбрать новую директорию
        if new_dir:  # Если пользователь выбрал директорию
            output_dir = new_dir
            save_output_dir(output_dir)  # Сохраняем новый путь в файл конфигурации
            directory_label.config(text=f"Расположение файлов: {output_dir}")

    def on_close():
        if program_thread is not None:
            stop(running_event)
            program_thread.join()
        root.destroy()

    screenshot_count = load_screenshot_count()  # Загрузка количества скриншотов
    screenshot_count_label = tk.Label(root, text=f"Скриншотов сделано: {screenshot_count}")
    screenshot_count_label.pack(pady=5)

    # Метка для отображения текущего пути сохранения файлов
    directory_label = tk.Label(main_frame, text=f"Расположение файлов: {output_dir}")
    directory_label.pack(pady=5)

    # Кнопка для изменения пути сохранения файлов
    change_button = tk.Button(main_frame, text="Изменить", command=change_output_dir)
    change_button.pack(pady=5)

    # Кнопки "Старт" и "Стоп" в отдельном фрейме для горизонтального расположения
    buttons_frame = tk.Frame(main_frame)
    buttons_frame.pack(pady=5)

    start_button = tk.Button(buttons_frame, text="Старт", command=start_program, height=2, width=10)
    start_button.pack(side='left', padx=5, pady=5)

    stop_button = tk.Button(buttons_frame, text="Стоп", command=stop_program, height=2, width=10)
    stop_button.pack(side='right', padx=5, pady=5)

    # Обработчик закрытия окна
    root.protocol("WM_DELETE_WINDOW", on_close)

    # Запускаем главный цикл обработки событий
    root.mainloop()

if __name__ == "__main__":
    output_dir = load_output_dir()
    run_gui()