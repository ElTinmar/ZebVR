import json

if __name__ == '__main__':

    CALIBRATION_FILE = 'calibration.json'

    with open(CALIBRATION_FILE,'r') as f:
        calibration = json.load(f)

    