import numpy as np
from keras import models as m


T   = 16
ATR = 6

models = []

means = [0, 0, 0] #TODO

def pre_process(data):
    'Remove columns from data'
    for d in data:
        if 'datetime' in d:
            del d['datetime']
        if 'fuel' in d:
            del d['fuel']
        if 'speedLimit' in d:
            del d['speedLimit']        
        if 'acceleration' in d:
            del d['acceleration']
        
    
    if len(data) <= T : return None

    data = np.array([list(row.values()) for row in data[5:]])

    'Window'
    X_samples = []
    overlapsize = T//2

    print('before window shape=', data.shape)  

    for i in range(0, len(data) , T-overlapsize):
        sample_x = data[i:i+T,:]  # grab from i to i+length
        if sample_x.shape[0] == T: 
            # sample_x = np.pad(sample_x, ((0, T - len(sample_x)), (0,0)), mode='constant', constant_values=0)
            X_samples.append(sample_x.tolist()) 

    return np.array(X_samples)


def model_prediction(drivers, data):
    X = pre_process(data) 

    if len(models) == 0:
        for driver in drivers:
            model_file = 'Model_' + driver + '.keras'
            try: 
                model = m.load_model(model_file)
            except FileNotFoundError as e:
                raise FileNotFoundError('Model not found - add the LSTM_model.keras file to the dir.') from e

            models.append((model, driver))

    predicitons = []
    for model, id in models:
        print(f'type = {(model.predict(X)[:,0])}')
        predicitons.append(((model.predict(X)[-1,0]), id))
    predicitons = np.array(predicitons)
    print(f'prediction = {predicitons}')
    values = predicitons[:,0].astype(float)
    
    return 'CAR STOLEN!' if np.max(values) < 0.85 else predicitons[np.argmax(values),1], data[-T+1:]
