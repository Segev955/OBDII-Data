import pandas as pd
import numpy as np

def create_fake_data(num_samples, speed_range, accel_range, throttle_range, rpm_range, steering_range, brake_range):
    data = {
        'Speed': np.random.uniform(*speed_range, num_samples),
        'Acceleration': np.random.uniform(*accel_range, num_samples),
        'Throttle_Position': np.random.uniform(*throttle_range, num_samples),
        'RPM': np.random.uniform(*rpm_range, num_samples),
        'Steering_Angle': np.random.uniform(*steering_range, num_samples),
        'Brake_Pressure': np.random.uniform(*brake_range, num_samples)
    }
    return pd.DataFrame(data)

# טווחים שונים לכל נהג
driver_1_ranges = {
    'speed_range': (0, 50),
    'accel_range': (-5, 5),
    'throttle_range': (0, 50),
    'rpm_range': (500, 3000),
    'steering_range': (-20, 20),
    'brake_range': (0, 50)
}

driver_2_ranges = {
    'speed_range': (20, 70),
    'accel_range': (-7, 7),
    'throttle_range': (10, 70),
    'rpm_range': (1000, 4000),
    'steering_range': (-30, 30),
    'brake_range': (10, 60)
}

driver_3_ranges = {
    'speed_range': (40, 100),
    'accel_range': (-10, 10),
    'throttle_range': (20, 100),
    'rpm_range': (2000, 5000),
    'steering_range': (-45, 45),
    'brake_range': (20, 100)
}

# יצירת נתונים חדשים לכל קובץ
for i in range(1, 6):
    df = create_fake_data(300, **driver_1_ranges)
    df.to_csv(f'fake_drive_data_1_{i}.csv', index=False)
    
for i in range(1, 6):
    df = create_fake_data(300, **driver_2_ranges)
    df.to_csv(f'fake_drive_data_2_{i}.csv', index=False)
    
for i in range(1, 6):
    df = create_fake_data(300, **driver_3_ranges)
    df.to_csv(f'fake_drive_data_3_{i}.csv', index=False)
