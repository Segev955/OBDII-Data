import os
import seaborn as sns
import pandas as pd
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.utils import shuffle
import matplotlib as mpl
mpl.style.use('ggplot')

from sklearn.preprocessing import StandardScaler
import firebase_admin
from firebase_admin import credentials, storage

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from keras.utils import to_categorical
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, BatchNormalization, LSTM, Dropout, Input, Flatten, LayerNormalization
from keras import layers, models
from keras.optimizers import Adam
tf.random.set_seed(0)


def gpu():
    devices = tf.config.list_physical_devices()
    print("\nDevices: ", devices)

    gpus = tf.config.list_physical_devices('GPU')
    print("\nGPU: ", gpus)

    if gpus:
        details = tf.config.experimental.get_device_details(gpus[0])
        print("GPU details: ", details)



def performance_plot(train_history):
    # Plotting the training and validation accuracy
    plt.figure(figsize=(12, 5))

    # Plot accuracy
    plt.subplot(1, 2, 1)
    plt.plot(train_history.history['accuracy'], label='Train Accuracy')
    # plt.plot(train_history.history['val_accuracy'], label='Validation Accuracy')
    plt.title('Accuracy Over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()

    # Plot loss
    plt.subplot(1, 2, 2)
    plt.plot(train_history.history['loss'], label='Train Loss')
    # plt.plot(train_history.history['val_loss'], label='Validation Loss')
    plt.title('Loss Over Epochs')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()

    # Show the plots
    plt.tight_layout()
    plt.savefig('training_history.png') 
    plt.show()

def plot_data(x,y):
    df = x
    df['driver'] = y
    features = x.columns # List of features to plot

    # Create a FacetGrid with 6 plots (one for each feature)
    g = sns.FacetGrid(x.melt(id_vars=['timestamp', 'driver'], value_vars=features), 
                    col="variable", hue="driver", col_wrap=3, height=4)

    # Map the scatterplot to each facet
    g.map(sns.scatterplot, "timestamp", "value", alpha=0.7)


    g.add_legend()
    g.set_axis_labels("Time", "Feature Value")
    g.set_titles(col_template="{col_name}")

    plt.savefig('dataset_facet_grid_plot.png', dpi=300, bbox_inches='tight')
    plt.show()



    '''
    # Assuming you have a DataFrame `df` with columns 'time', 'label', and feature columns 'f1', 'f2', ...
    labels = y.unique()

    for col in X.columns:
        print(X[col].head())

    for feature in X.columns:
        plt.figure(figsize=(10, 6))
        for label in labels:
            subset =df[df['l abel'] == label]
            plt.plot(subset['timestamp'], subset[feature], label=f'Label {label}')
        plt.title(f'Feature {feature} over Time')
        plt.xlabel('Time')
        plt.ylabel(feature)
        plt.legend()
        plt.show()
    '''

    


def download_firebase_train():
    storage_dir = [f"drives/2W5Nq5aZ4cP9VA6zEWBbi7FicxE2/", f"drives/lT3ip6zL8gU34vuoONy5UTmWwPg1", f"drives/vcAN0KURuBYtNhztFCJJR9y4EhR2"] # Add new directories (people) here
    local_path = f"/Users/arnoldcheskis/Documents/Projects/Archive/LimudNaim/Driving_project_lesson-LimudNaim/data/"

    'Initialize Firebase Admin SDK'
    cred = credentials.Certificate(f"{os.getcwd()}/car-driver-bc91f-firebase-adminsdk-xhkyn-214c09b623.json")
    firebase_admin.initialize_app(cred, {'storageBucket': 'car-driver-bc91f.appspot.com'})

    bucket  = storage.bucket()
    for dir_num, dir in enumerate(storage_dir):
        blobs   = bucket.list_blobs(prefix=dir)
        os.makedirs(local_path + str(dir_num))
        for i, blob in enumerate(blobs):
            local = local_path + str(dir_num) + '/' + str(i) + '.csv'
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
        csv_data.append(person)
    return csv_data

def pre_process_encoder():
    files = parse_files() #extract objects from files
    X = pd.DataFrame()
    y = []
    'Features and labels'
    for i, person in enumerate(files):
        for data in person:
            df = pd.DataFrame(data)
            # df['timestamp'] = df['timestamp']*(10**3)%(10**7)
            # df['timestamp'] = df['timestamp']-df['timestamp'].min() #TODO delete these 2 lines

            # x_sample = df.drop(columns=['datetime', 'fuel'] ).dropna()
            x_sample = df.drop(columns=['datetime', 'fuel', 'speedLimit', 'acceleration', 'timestamp'] ).dropna()

            y_sample = [i for _ in range(len(x_sample))]

            if "Car_Id" in X.columns:
                x_sample.drop('Car_Id', axis=1, inplace=True)
            if 'Trip' in X.columns:
                x_sample.drop('Trip', axis=1, inplace=True)

            X = pd.concat([X, x_sample], ignore_index=True)
            y += y_sample


    return X,y  



'Split the data set into window samples'
def window(X1, y1):
    X_samples = []
    y_samples = []
    
    # encoder = LabelEncoder() #TODO used to convert string, or other labels to integers
    # encoder.fit(y1)
    # y1 = encoder.transform(y1)
    
    Xt = np.array(X1)
    yt= np.array(y1).reshape(-1,1)

    overlapsize = T//2
    n = yt.size    

    # for over the 263920  310495 in jumps of 64
    for i in range(0, n , T-overlapsize):
        # grab from i to i+length
        sample_x = Xt[i:i+T,:]
        if sample_x.shape[0] == T: 
            X_samples.append(sample_x)

        sample_y = yt[i:i+T]
        if sample_y.shape[0] == T: 
            y_samples.append(sample_y)

    return np.array(X_samples),  np.array(y_samples)


def rnn_dimension(X,y, train_size):
    df= X.copy() #TODO

    # (X - E(X))/σ(X)
    std_scale = StandardScaler()
    std_scale.fit(X)
    x = std_scale.transform(X)

    #range between (0,1)
    zero1_scaler = MinMaxScaler(feature_range=(0, 1))
    x = zero1_scaler.fit_transform(X)

    # df[:]= x
    # df['timestamp'] = X['timestamp']

    # plot_data(df,y)


    X_samples, y_samples = window(x, y)
    y_samples_cat = to_categorical(np.array(y_samples))
    
    X_train_rnn, X_test_rnn, y_train_rnn, y_test_rnn = train_test_split(X_samples, y_samples_cat, train_size=train_size, shuffle=False) #TODO shuffle?
    # X_train_rnn, X_test_rnn, y_train_rnn, y_test_rnn = train_test_split(x, to_categorical(np.array(y)), train_size=train_size, shuffle=True) #TODO shuffle?
    
    return X_train_rnn, y_train_rnn, X_test_rnn, y_test_rnn



        


def mlp_model(y):
    mlp = Sequential()
    #TODO Do not pass an `input_shape`/`input_dim` argument to a layer. When using Sequential models, prefer using an `Input(shape)` object as the first layer in the model instead.
    mlp.add(Input(shape=(T,PROPS)))
    mlp.add(Dense(160, activation='relu'))
    mlp.add(layers.BatchNormalization())
    mlp.add(layers.Dropout(0.5))
    mlp.add(Dense(120, activation='relu'))
    mlp.add(layers.BatchNormalization())
    mlp.add(Dense(3, activation='softmax'))
    return mlp



def deep_lstm_model(y):
    model = Sequential(
        [
            Input(shape=(T, PROPS)), #ragged=True
            # LSTM(64, return_sequences=True),
            Dense(120, activation='relu'),
            LayerNormalization(),
            # LSTM(128, return_sequences=True),
            Dense(200, activation='relu'),
            LayerNormalization(),
            # Flatten(),
            # Dense(256, activation='relu'), # kernel_initializer='glorot_uniform', bias_initializer='zeros'
            Dense(3, activation='softmax') #TODO : why y.shape[0] == 16 ?
        ]
    )    
    return model



PROPS       = 5 #TODO X.shape[1] #Properties of the drivers
T           = 16
LR          = 0.1
EPOCHS      = 50
TRAIN_SIZE  = 0.85
BATCH_SIZE  = T

def main():
    
    # download_firebase_train() #Call only once to get contents from Firebase
    X, y = pre_process_encoder() #get raw data in pd.Frame

    # plot_data(X,y)

    X_train, y_train, X_test, y_test  = rnn_dimension(X,y, TRAIN_SIZE)



    model_file = 'mlp_model.keras'
    if os.path.isfile(model_file):
        mlp = models.load_model(model_file)
    if True:
    # else:
        # mlp = deep_lstm_model(y_test)
        mlp = mlp_model(y_train)
        optimizer = Adam(learning_rate=LR) #TODO add clipvalue=1.0 ?
        mlp.compile(loss='categorical_crossentropy', optimizer=optimizer, metrics=['accuracy']) #loss
        mlp_history = mlp.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE)
        mlp.save(model_file)
        performance_plot(mlp_history)



    # TODO turn to a function
    score = mlp.evaluate(X_test, y_test) # batch_size=50

    print('Test loss:', score[0])
    print('Test accuracy:', score[1])

    #TODO ! - next time- merge data to make SEQUENTIAL - the model should know it's related!
    df = [[pd.read_csv('test.csv')]]
    user_props, _ = pre_process_encoder()
    user = [1 for _ in range(len(user_props)-1)]
    x, _, _, _ = rnn_dimension(user_props,user, 0.5)
    x[-1].reshape(1, 16, 8)
    x[0].reshape(1, 16, 8)
    print(f'output after training = {mlp.predict(x[-1])} \n {mlp.predict(x[0])}')




if __name__ == '__main__':
    main()
