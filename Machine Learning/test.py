# import torch
# import time
# import tensorflow as tf

# from keras.models import load_model
# from keras import layers, models
# from keras.layers import Dense, BatchNormalization, LSTM, Dropout, Input, Flatten, LayerNormalization
# from keras.models import Sequential
# import numpy as np
# import matplotlib.pyplot as plt


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
tf.random.set_seed(7)

def plot(train_history):
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




def gpu():
    devices = tf.config.list_physical_devices()
    print("\nDevices: ", devices)

    gpus = tf.config.list_physical_devices('GPU')
    print("\nGPU: ", gpus)

    if gpus:
        details = tf.config.experimental.get_device_details(gpus[0])
        print("GPU details: ", details)


    # #check for gpu
    # if torch.backends.mps.is_available():
    #     mps_device = torch.device("mps")
    #     x = torch.ones(1, device=mps_device)
    #     print (x)
    # else:
    #     print ("MPS device not found.")


    # # GPU
    # start_time = time.time()

    # # syncrocnize time with cpu, otherwise only time for oflaoding data to gpu would be measured
    # torch.mps.synchronize()

    # a = torch.ones(4000,4000, device="mps")
    # for _ in range(200):
    #     a +=a

    # elapsed_time = time.time() - start_time
    # print( "GPU Time: ", elapsed_time)

def simple_run():
    # model = Sequential(
    #     [
    #         LSTM(512, input_shape=(None, 4), return_sequences=True),
    #         LayerNormalization(),
    #         LSTM(512, return_sequences=True),
    #         LayerNormalization(),
    #         # Flatten(),
    #         # Dense(256, activation='relu'), # kernel_initializer='glorot_uniform', bias_initializer='zeros'
    #         Dense(2, activation='softmax')
    #     ]
        # model = Sequential()
        # model.add(LSTM(64, input_shape=(None,4), return_sequences=True))
        # model.add(Dense(4, activation='linear'))
    # )  
    # convert an array of values into a dataset matrix
    def create_dataset(dataset, look_back=1):
        dataX, dataY = [], []
        for i in range(len(dataset)-look_back-1):
            a = dataset[i:(i+look_back), 0]
            dataX.append(a)
            dataY.append(dataset[i + look_back, 0])
        return np.array(dataX), np.array(dataY)
    
    dataframe = pd.read_csv('test.csv', usecols=[1], engine='python')
    plt.plot(dataframe)
    plt.show()
    dataset = dataframe.values
    dataset = dataset.astype('float32')
    # normalize the dataset
    scaler = MinMaxScaler(feature_range=(0, 1))
    dataset = scaler.fit_transform(dataset)

    train_size = int(len(dataset) * 0.67)
    test_size = len(dataset) - train_size
    train, test = dataset[0:train_size,:], dataset[train_size:len(dataset),:]
    print(len(train), len(test))
    look_back = 1
    trainX, trainY = create_dataset(train, look_back)
    testX, testY = create_dataset(test, look_back)
    # reshape input to be [samples, time steps, features]
    trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
    testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

    model = Sequential()
    model.add(LSTM(4, input_shape=(1, look_back)))
    model.add(Dense(1))
    model.compile(loss='mean_squared_error', optimizer='adam')
    model.fit(trainX, trainY, epochs=100, batch_size=1, verbose=2)


    
    # make predictions
    trainPredict = model.predict(trainX)
    testPredict = model.predict(testX)
    # invert predictions
    trainPredict = scaler.inverse_transform(trainPredict)
    trainY = scaler.inverse_transform([trainY])
    testPredict = scaler.inverse_transform(testPredict)
    testY = scaler.inverse_transform([testY])
    # calculate root mean squared error
    trainScore = np.sqrt(mean_squared_error(trainY[0], trainPredict[:,0]))
    print('Train Score: %.2f RMSE' % (trainScore))
    testScore = np.sqrt(mean_squared_error(testY[0], testPredict[:,0]))
    print('Test Score: %.2f RMSE' % (testScore))


    # shift train predictions for plotting
    trainPredictPlot = np.empty_like(dataset)
    trainPredictPlot[:, :] = np.nan
    trainPredictPlot[look_back:len(trainPredict)+look_back, :] = trainPredict
    # shift test predictions for plotting
    testPredictPlot = np.empty_like(dataset)
    testPredictPlot[:, :] = np.nan
    testPredictPlot[len(trainPredict)+(look_back*2)+1:len(dataset)-1, :] = testPredict
    # plot baseline and predictions
    plt.plot(scaler.inverse_transform(dataset))
    plt.plot(trainPredictPlot)
    plt.plot(testPredictPlot)
    plt.show()




simple_run()

#TODO - very useful : https://machinelearningmastery.com/time-series-prediction-lstm-recurrent-neural-networks-python-keras/


def model_load():
    pass
    # Replace 'your_model.h5' with the path to your .h5 file
    # model = load_model('your_model.h5')


