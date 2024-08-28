# OBDII-Data

OBDII-Data is part of the Car Driver Project. This repository contains Python scripts and classes for handling OBD-II (On-Board Diagnostics) data, GPS data, and driving pattern analysis. It is designed to be integrated with other components in the project to detect potential vehicle theft by analyzing driver behavior and vehicle data in real-time.

## Features

- OBD-II data retrieval and parsing.
- GPS data handling through a custom Python class.
- Listener functionality to monitor incoming data.
- Machine learning integration for driver behavior analysis.

## Technologies Used

- **Python**: Main programming language.
- **OBD-II**: For vehicle diagnostics data.
- **Machine Learning**: To identify driving patterns.

## How to Use

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Segev955/OBDII-Data.git
    ```

2. **Install necessary dependencies**:
    Ensure you have Python installed, and install required libraries using:
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the scripts**:
    You can run the OBD-II and GPS scripts independently, or as part of the larger Car Driver project.

4. **GPS and OBD-II Classes**:
    - `GPS_class.py`: Contains the class for managing GPS data.
    - `Obd_class.py`: Contains the class for handling OBD-II data retrieval and parsing.

5. **Machine Learning Integration**:
    The `Machine Learning` folder includes scripts for processing driving data and making predictions based on driving behavior.

## Project Structure

- `GPS_class.py`: Handles GPS data.
- `Obd_class.py`: Handles OBD-II data.
- `Listener.py`: Monitors incoming data from the car's system.
- `Machine Learning/`: Contains machine learning scripts for analyzing driver behavior.

## Contributors

- **Segev Tzabar**
- **Yasmin Cohen**
- **Sali Sharfman**
