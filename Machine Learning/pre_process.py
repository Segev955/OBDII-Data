import numpy as np

T   = 16
ATR = 8

def pre_process(data):
    'Remove columns from data'
    for d in data:
        if 'datetime' in d:
            del d['datetime']
        if 'fuel' in d:
            del d['fuel']
    
    if len(data) <= 5 : return np.array([[[0.0 for _ in range(ATR)] for _ in range(T)]])

    data = np.array([list(row.values()) for row in data[5:]])

    'Window'
    X_samples = []
    overlapsize = T//2

    for i in range(0, len(data) , T-overlapsize):
        sample_x = data[i:i+T,:]  # grab from i to i+length
        sample_x = np.pad(sample_x, ((0, T - len(sample_x)), (0,0)), mode='constant', constant_values=0)
        if (sample_x.shape[0]) == T: 
            X_samples.append(sample_x.tolist())
    
    return np.array(X_samples)
