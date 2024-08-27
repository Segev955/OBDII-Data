import os
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib as mpl
import firebase_admin
import seaborn as sns

from keras.models import Sequential
from keras.layers import Dense, BatchNormalization, LSTM, Dropout, Input
from keras.optimizers import Adam
from keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler
from sklearn.preprocessing import StandardScaler, MinMaxScaler,LabelEncoder
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from enum import Enum
from firebase_admin import credentials, storage
from sklearn.utils import shuffle
from keras import layers
from keras import models as m
mpl.style.use('ggplot')
tf.random.set_seed(0)



def performance_plot(train_history, driver, plot_all=True, metric='accuracy'):

    plt.figure(figsize=(12, 5))

    if plot_all:
 
        plt.subplot(1, 3, 1)
        plt.plot(train_history.history['accuracy'], label='Train Accuracy')
        plt.plot(train_history.history.get('val_accuracy', []), label='Validation Accuracy') 
        plt.title('Accuracy Over Epochs')
        plt.xlabel('Epochs')
        plt.ylabel('Accuracy')
        plt.grid()
        plt.legend()

        plt.subplot(1, 3, 2)
        plt.plot(train_history.history['loss'], label='Train Loss')
        plt.plot(train_history.history.get('val_loss', []), label='Validation Loss') 
        plt.title('Loss Over Epochs')
        plt.xlabel('Epochs')
        plt.ylabel('Loss')
        plt.grid()
        plt.legend()

        if 'f1' in train_history.history:
            plt.subplot(1, 3, 3)
            plt.plot(train_history.history['f1'], label='Train F1')
            plt.plot(train_history.history.get('val_f1', []), label='Validation F1') 
            plt.title('F1 Score Over Epochs')
            plt.xlabel('Epochs')
            plt.ylabel('F1 Score')
            plt.grid()
            plt.legend()

        plt.tight_layout()
        plt.savefig('training_history_' + driver + '.png')
        plt.show()
    
    else:

        plt.figure(figsize=(6, 4))
        if metric == 'accuracy':
            plt.plot(train_history.history['accuracy'], label='Train Accuracy')
            plt.plot(train_history.history.get('val_accuracy', []), label='Validation Accuracy')
            plt.ylabel('Accuracy')
        elif metric == 'loss':
            plt.plot(train_history.history['loss'], label='Train Loss')
            plt.plot(train_history.history.get('val_loss', []), label='Validation Loss')
            plt.ylabel('Loss')
        elif metric == 'f1' and 'f1' in train_history.history:
            plt.plot(train_history.history['f1'], label='Train F1')
            plt.plot(train_history.history.get('val_f1', []), label='Validation F1')
            plt.ylabel('F1 Score')

        plt.title(f'{metric.capitalize()} Over Epochs')
        plt.xlabel('Epochs')
        plt.grid()
        plt.legend()
        plt.show()



def plot_data(x, y):

    flattened_x = x.reshape(-1, x.shape[2]) 
    

    num_samples_per_driver = x.shape[1] 
    

    if len(flattened_x) == len(y) * num_samples_per_driver:
        repeated_y = np.repeat(y, num_samples_per_driver) 
        df = pd.DataFrame(flattened_x)
        df['driver'] = repeated_y
    else:
        print(f"Error: Mismatched sizes between x ({len(flattened_x)}) and y ({len(y)})")
        return

    features = df.columns[:-1]
    df['time'] = range(1, len(df) + 1)


    g = sns.FacetGrid(df.melt(id_vars=['time', 'driver'], value_vars=features), 
                      col="variable", hue="driver", col_wrap=3, height=4)

 
    g.map(sns.scatterplot, "time", "value", alpha=0.7)

    g.add_legend()
    g.set_axis_labels("Time", "Feature Value")
    g.set_titles(col_template="{col_name}")

    plt.savefig('dataset_facet_grid_plot.png', dpi=300, bbox_inches='tight')
    plt.show()



def download_firebase_train():
    local_path = f"/Users/arnoldcheskis/Documents/Projects/Archive/LimudNaim/Driving_project_lesson-LimudNaim/data/"

    'Initialize Firebase Admin SDK'
    cred = credentials.Certificate(f"{os.getcwd()}/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
    firebase_admin.initialize_app(cred, {'storageBucket': 'car-driver-bc91f.appspot.com'})

    bucket  = storage.bucket()
    for driver in Drivers:
        dir = "drives/" + driver.value
        blobs   = bucket.list_blobs(prefix=dir)
        os.makedirs(local_path + str(driver.value))
        for i, blob in enumerate(blobs):
            local = local_path + str(driver.value) + '/' + str(i) + '.csv'
            blob.download_to_filename(local)



def parse_files():
    csv_data    = []
    current_dir = os.getcwd() + '/data'
    for dir in os.listdir(current_dir):
        data_dir    = os.path.join(current_dir, dir)
        person      = []       

        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(data_dir, filename)
                with open(file_path, 'r') as csvfile:
                    if os.path.getsize(file_path) > 0:
                        df = pd.read_csv(csvfile)
                        person.append(df)
        id = os.path.basename(data_dir) #person's ID
        csv_data.append((person, id))
    return csv_data


def normalization_no_val(X_train, X_test, type='min-max'):
    if type == 'min-max':
        for i in range(len(X_train[0, 0])):
            train_min, train_max = X_train[:, 0, i].min(), X_train[:, 0, i].max()
            X_train[:, 0, i] = (X_train[:, 0, i] - train_min) / (train_max - train_min)
            X_test[:, 0, i] = (X_test[:, 0, i] - train_min) / (train_max - train_min)
    elif type == 'standardization':
        for i in range(len(X_train[0, 0])):
            train_mean, train_std = X_train[:, 0, i].mean(), X_train[:, 0, i].std()
            X_train[:, 0, i] = (X_train[:, 0, i] - train_mean) / train_std
            X_test[:, 0, i] = (X_test[:, 0, i] - train_mean) / train_std
    return X_train, X_test

def normalization(X_train, X_val, X_test, type='min-max'):
    if type == 'min-max':
        for i in range(len(X_train[0, 0])):
            train_min, train_max = X_train[:, 0, i].min(), X_train[:, 0, i].max()
            X_train[:, 0, i] = (X_train[:, 0, i] - train_min) / (train_max - train_min)
            X_val[:, 0, i] = (X_val[:, 0, i] - train_min) / (train_max - train_min)
            X_test[:, 0, i] = (X_test[:, 0, i] - train_min) / (train_max - train_min)
    elif type == 'standardization':
        for i in range(len(X_train[0, 0])):
            train_mean, train_std = X_train[:, 0, i].mean(), X_train[:, 0, i].std()
            X_train[:, 0, i] = (X_train[:, 0, i] - train_mean) / train_std
            X_val[:, 0, i] = (X_val[:, 0, i] - train_mean) / train_std
            X_test[:, 0, i] = (X_test[:, 0, i] - train_mean) / train_std
    return X_train, X_val, X_test


def window(X1, y1, T):
    X_samples = []
    y_samples = []
    Xt = np.array(X1)
    yt = np.array(y1).reshape(-1, 1)
    overlapsize = T // 2
    n = yt.size
    for i in range(0, n, T - overlapsize):
        sample_x = Xt[i:i+T, :]
        if sample_x.shape[0] == T:
            X_samples.append(sample_x)
        sample_y = yt[i:i+T]
        if sample_y.shape[0] == T:
            y_samples.append(sample_y)
    return np.array(X_samples), np.array(y_samples)



def deep_model(input_shape):
    model = Sequential(
        [
            Input(shape=(T, PROPS), batch_size=BATCH),
            LSTM(units=160, stateful=True, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            LSTM(units=160, stateful=True, return_sequences=True),
            Dropout(0.2),
            BatchNormalization(),
            LSTM(units=160, stateful=True, return_sequences=False),
            Dropout(0.2),
            BatchNormalization(),
            Dense(units=2, activation='sigmoid')
        ]
    )
    return model


def callbacks_function(name):
    early_stop = EarlyStopping(monitor='val_loss', patience=10, verbose=0, mode='min', restore_best_weights=True)
    monitor = ModelCheckpoint(name, monitor='val_loss', verbose=0, save_best_only=True, save_weights_only=False, mode='min')


    def scheduler(epoch, lr):
        if epoch % 5 == 0:
            lr = lr / 2
        return lr

    lr_schedule = LearningRateScheduler(scheduler, verbose=0)
    return [early_stop, monitor, lr_schedule]


def model_comiple_run(model, X_train, Y_train, X_val, Y_val, model_name):
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    callbacks = callbacks_function(model_name)
    print(f'{X_train.shape}  {X_val.shape}  {Y_train.shape}  {(type(Y_val))}')
    
    # Create a Dataset from your training data
    train_dataset = tf.data.Dataset.from_tensor_slices((X_train, Y_train))
    val_dataset = tf.data.Dataset.from_tensor_slices((X_val, Y_val))

    # Apply batching with `drop_remainder=True` to ensure consistent batch sizes
    train_dataset = train_dataset.batch(BATCH, drop_remainder=True)
    val_dataset = val_dataset.batch(BATCH, drop_remainder=True)

    model_history = model.fit(train_dataset, batch_size=BATCH, epochs=50, validation_data=val_dataset, callbacks=callbacks, verbose=1) 
    return model_history

def pre_process_encoder(files, driver, T):
    X = pd.DataFrame()
    y = []
    

    

    for person, id in files:
        if id == driver:  # 
            #print(f"Processing data for driver {id} (current driver ID matches)")
            for data in person:
                df = pd.DataFrame(data)
                x_sample = df.drop(columns=['datetime', 'fuel', 'speedLimit', 'timestamp']).dropna()
                y_sample = [1 for _ in range(len(x_sample))] 
                X = pd.concat([X, x_sample], ignore_index=True)
                y += y_sample
        else: 
            #print(f"Processing data for driver {id} (not the current driver)")
            for data in person:
                df = pd.DataFrame(data)
                x_sample = df.drop(columns=['datetime', 'fuel', 'speedLimit', 'timestamp']).dropna()
                y_sample = [0 for _ in range(len(x_sample))]  
                X = pd.concat([X, x_sample], ignore_index=True)
                y += y_sample
                

    #print(f"Data shape for driver {driver}: X shape = {X.shape}, y shape = {len(y)}")
    

    X_samples, y_samples = window(X, y, T)
    y_samples = np.array(y_samples)[:, -1]  

    #print(f"Data after windowing for driver {driver}: X_samples shape = {X_samples.shape}, y_samples shape = {y_samples.shape}")
    
    return X_samples, y_samples


# def prediction(models, x):
#     detections = []
#     for model, driver_id in models:
#         prediction = model.predict(x)
#         print(f"Predicted probabilities for {driver_id}: {prediction}")
#         if prediction[1] >= 0.85: 
#             detections.append(driver_id)
#     return detections

def prediction(models, x):
    predicitons = []
    for model, id in models:
        print(f' {id} = {model.predict(x[-10:])[:,1]}')
        print(f' {id} = {model.predict(x[0:])[-10:,1]}')
        predicitons.append((model.predict(x)[-2,1], id))
    print(f'prediction = {predicitons}')
    predicitons = np.array(predicitons)
    values = predicitons[:,0].astype(float)
    return 'CAR STOLEN!' if np.max(values) < 0.85 else predicitons[np.argmax(values),1]

def evaluate_model_on_test_data(model, X_test, y_test, driver_name):
    print(f"--- Evaluating model for driver {driver_name} ---")

    loss, accuracy = model.evaluate(X_test, y_test, verbose=1)
    print(f"Accuracy for driver {driver_name}: {accuracy * 100:.2f}%\n")
    return accuracy


def input(fielname):
    df = pd.read_csv(fielname)

    df = df.drop(columns=['datetime', 'fuel', 'speedLimit', 'timestamp']).dropna()
    
    data = np.array(df.values)

    'Window'
    X_samples = []
    overlapsize = T//2

    for i in range(0, len(data) , T-overlapsize):
        sample_x = data[i:i+T,:]  # grab from i to i+length
        if sample_x.shape[0] != T: 
            sample_x = np.pad(sample_x, ((0, T - len(sample_x)), (0,0)), mode='constant', constant_values=0)
        X_samples.append(sample_x.tolist()) #TODO why is it less than 884?
    
    return np.array(X_samples)


def main():
    files = parse_files()  # extract objects from files
    
    testx = input('test.csv')

    
    models = []
    for driver in Drivers:
        # print(f"--- Preparing data for driver {driver.value} ---")
        X, y = pre_process_encoder(files, driver.value, T)
     
        
        X_train, X_test, y_train, y_test = train_test_split(X, to_categorical(y), train_size=TRAIN_SIZE, shuffle=True)    
        X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, train_size=TRAIN_SIZE, shuffle=True)


        X_train, X_val, X_test = normalization(X_train, X_val, X_test, type='min-max')
        input_shape = (X_train.shape[1], X_train.shape[2])
        

        model_name = f"Model_{driver.value}.keras"

        if os.path.isfile(model_name):
            # print(f"Loading model for driver {driver.value} from {model_name}")
            model = m.load_model(model_name)
            
            evaluate_model_on_test_data(model, X_test, y_test,driver.value)

        else:
            # print(f"Training and saving model for driver {driver.value}")
            model = deep_model(input_shape)
            model_history = model_comiple_run(model, X_train, y_train, X_val, y_val, model_name)
            print('checkpoint after')
            model.save(model_name)  

            performance_plot(model_history, driver.value)
        
        models.append((model, driver.value)) 

        # print(f"The test was originally labeled for driver: {label}")


        testx = np.expand_dims(testx[-1], axis=0)
    _, testx = normalization_no_val(x_train_copy, testx)
    print(prediction(models, testx))
    
        # if detections:
        #     print(f"The driver is correctly identified as {detections}. No theft detected.")
        # else:
        #     print("CAR STOLEN!")
    

PROPS = 6
T = 16
TRAIN_SIZE = 0.85
BATCH = 16

class Drivers(Enum):
    d1 = '2W5Nq5aZ4cP9VA6zEWBbi7FicxE2'
    d2 = 'lT3ip6zL8gU34vuoONy5UTmWwPg1'
    d3 = 'vcAN0KURuBYtNhztFCJJR9y4EhR2'

if __name__ == '__main__':
    main()
