import numpy as np
import os
from PIL import Image
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Flatten, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint

# Убедитесь, что у вас есть доступный графический процессор
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    try:
        # Установка ограничений памяти на GPU, если необходимо
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        print("Доступные устройства:", gpus)
    except RuntimeError as e:
        print(e)
        
# Определение пути к данным
data_dir = 'N:\\data\\8\\screenshots\\data'  # Измените на ваш путь

# Параметры модели
batch_size = 32  # Размер батча для обучения
epochs = 10  # Количество эпох обучения

# Создание модели
model = Sequential([
    Input(shape=(200, 1000, 1)),
    Conv2D(32, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(64, activation='relu'),
    Dense(31)  # Количество выходных значений равно размеру нумпай массива
])

# Компиляция модели
model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

# Функция для загрузки данных для обучения
def load_data(data_dir):
    # Сортировка файлов по числу в названии и загрузка данных
    files = sorted(os.listdir(data_dir), key=lambda x: int(x.split('.')[0]))
    for file in files:
        if file.endswith('.png'):
            image_path = os.path.join(data_dir, file)
            npy_path = image_path.replace('.png', '.npy')
            # Проверка на существование файла перед загрузкой
            if os.path.exists(npy_path):
                image = Image.open(image_path).convert('L')
                image = np.array(image).reshape(200, 1000, 1) / 255.0  # Нормализация
                labels = np.load(npy_path)
                yield image, labels
            else:
                print(f"Файл {npy_path} не найден.")
                
# Создание генератора данных
def data_generator(data_dir, batch_size):
    data_gen = load_data(data_dir)
    while True:
        batch_X, batch_Y = [], []
        for _ in range(batch_size):
            try:
                X, Y = next(data_gen)
                # Убедитесь, что X и Y имеют нужную форму
                # Например, если вы хотите привести изображение к размеру (200, 1000, 1)
                X = np.resize(X, (200, 1000, 1))
                # Убедитесь, что Y имеет нужную форму, например, (31,)
                Y = np.resize(Y, (31,))
                batch_X.append(X)
                batch_Y.append(Y)
            except StopIteration:
                break
        if len(batch_X) > 0 and len(batch_Y) > 0:
            yield np.array(batch_X), np.array(batch_Y)

# Создаем генератор
train_generator = data_generator(data_dir, batch_size)

# Callback для сохранения модели после каждой эпохи
checkpoint_callback = ModelCheckpoint('N:\\data\\8\\model_{epoch:02d}.keras', save_best_only=True)

# Обучение модели
model.fit(train_generator, steps_per_epoch=100, epochs=epochs, callbacks=[checkpoint_callback])

# Сохранение модели после обучения
model.save('N:\\data\\8\\final_model.h5')
print("Модель обучена и сохранена.")