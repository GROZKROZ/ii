import numpy as np
import os
from PIL import Image
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import TimeDistributed, Conv2D, MaxPooling2D, LSTM, Dense, Flatten, Dropout, Input
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint

# Определение пути к данным
data_dir = 'C:\\path_to_output\\sequence_data'  # Убедитесь, что этот путь правильный

# Параметры модели
sequence_length = 10  # Количество временных шагов в последовательности
batch_size = 4  # Размер батча для обучения
epochs = 2  # Количество эпох обучения

# Определение формы входных данных
input_shape = (sequence_length, 200, 200, 1)

# Создание модели
model = Sequential([
    TimeDistributed(Conv2D(32, (3, 3), activation='relu'), input_shape=(sequence_length, 200, 200, 1)),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Conv2D(64, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Conv2D(128, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Conv2D(256, (3, 3), activation='relu')),
    TimeDistributed(MaxPooling2D((2, 2))),
    TimeDistributed(Flatten()),  
    LSTM(2048, return_sequences=True),
    TimeDistributed(Dense(4096, activation='relu')),
    Dropout(0.75),
    TimeDistributed(Dense(2048, activation='relu')),
    Dropout(0.10),
    TimeDistributed(Dense(1024, activation='relu')),
    Dropout(0.10),
    TimeDistributed(Dense(50, activation='linear'))  # Применяем Dense ко всем временным шагам
])

# Компиляция модели
model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')

# Сохранение инициализированной модели перед началом обучения
model.save('C:\\path_to_output\\initial_model.keras')

# Функция для загрузки данных из файлов .npy
def load_data(file_path):
    data = np.load(file_path, allow_pickle=True).item()
    return data['X'], data['Y']

# Создаем списки для хранения путей к файлам данных
X_paths = []
Y_paths = []

# Заполняем списки путями к файлам
for i in range(0, 11530, 5):  # Изменено на правильные индексы файлов
    X_paths.append(os.path.join(data_dir, f'sequence_{i}.npy'))
    Y_paths.append(os.path.join(data_dir, f'sequence_{i}.npy'))  # Предполагается, что X и Y хранятся в одном файле

# Создаем генератор данных для подачи данных в модель
def data_generator(X_paths, Y_paths, batch_size):
    while True:
        for i in range(0, len(X_paths), batch_size):
            batch_X_paths = X_paths[i:i+batch_size]
            batch_Y_paths = Y_paths[i:i+batch_size]
            batch_X = []
            batch_Y = []
            for x_path, y_path in zip(batch_X_paths, batch_Y_paths):
                X, Y = load_data(x_path)  # Предполагается, что X и Y хранятся в одном файле
                batch_X.append(X)
                batch_Y.append(Y)
            yield np.array(batch_X), np.array(batch_Y)

# Создаем генератор
train_generator = data_generator(X_paths, Y_paths, batch_size)

# Количество шагов за эпоху
steps_per_epoch = len(X_paths) // batch_size

# Callback для сохранения модели после каждой эпохи в формате Keras
checkpoint_callback = ModelCheckpoint('C:\\path_to_output\\model_{epoch:02d}.keras', save_best_only=False)

# Обучение модели
model.fit(train_generator, steps_per_epoch=steps_per_epoch, epochs=epochs, callbacks=[checkpoint_callback])

# Сохранение модели после обучения в формате Keras
model.save('C:\\path_to_output\\final_model.keras')
print("Модель обучена и сохранена в формате Keras.")