import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout, Conv1D, MaxPooling1D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

# Load and normalize data
file_paths = [
    'fake_drive_data_1_1.csv', 'fake_drive_data_1_2.csv', 'fake_drive_data_1_3.csv', 
    'fake_drive_data_1_4.csv', 'fake_drive_data_1_5.csv', 'fake_drive_data_2_1.csv',
    'fake_drive_data_2_2.csv', 'fake_drive_data_2_3.csv', 
    'fake_drive_data_2_4.csv', 'fake_drive_data_2_5.csv',
    'fake_drive_data_3_1.csv', 'fake_drive_data_3_2.csv', 
    'fake_drive_data_3_3.csv', 'fake_drive_data_3_4.csv', 
    'fake_drive_data_3_5.csv'
]

dfs = [pd.read_csv(file_path) for file_path in file_paths]
data = pd.concat(dfs)
data_normalized = (data - data.min()) / (data.max() - data.min())

# Prepare data for LSTM model
def create_sequences(data, seq_length=10):
    sequences = []
    for i in range(len(data) - seq_length):
        seq = data[i:i+seq_length]
        label = data.iloc[i+seq_length]
        sequences.append((seq, label))
    return sequences

seq_length = 10
sequences = create_sequences(data_normalized, seq_length)
X = np.array([seq[0] for seq in sequences])
y = np.array([seq[1] for seq in sequences])

# Split data into training and validation sets
split = int(0.8 * len(X))
X_train, X_val = X[:split], X[split:]
y_train, y_val = y[:split], y[split:]

# Build LSTM model
model = Sequential()
model.add(Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=(seq_length, X.shape[2])))
model.add(MaxPooling1D(pool_size=2))
model.add(LSTM(100, return_sequences=True))
model.add(Dropout(0.3))
model.add(LSTM(50, return_sequences=True))
model.add(Dropout(0.3))
model.add(LSTM(50, return_sequences=False))
model.add(Dropout(0.3))
model.add(Dense(y.shape[1], activation='softmax'))

optimizer = Adam(learning_rate=0.001)
model.compile(optimizer=optimizer, loss='categorical_crossentropy', metrics=['accuracy'])

# Callbacks
early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
model_checkpoint = ModelCheckpoint('best_model.keras', save_best_only=True)

# Train model
history = model.fit(
    X_train, y_train, 
    epochs=50, 
    batch_size=32,  # נסה להגדיל או להקטין את הערך הזה
    validation_data=(X_val, y_val), 
    callbacks=[early_stopping, model_checkpoint],
    verbose=1
)

# Plot training history
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.plot(history.history['loss'], label='loss')
plt.plot(history.history['val_loss'], label='val_loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.title('Model Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['accuracy'], label='accuracy')
plt.plot(history.history['val_accuracy'], label='val_accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.title('Model Accuracy')
plt.legend()

plt.show()
