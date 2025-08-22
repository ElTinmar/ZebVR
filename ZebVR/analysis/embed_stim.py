from pathlib import Path
import pandas as pd
import cv2
import json

STIM_FILE = Path('stim_00_07dpf_Test_PreyCap_Thu_21_Aug_2025_15h47min54sec.json')
VIDEO_TIMESTAMPS_FILE = Path('00_07dpf_Test_PreyCap_Thu_21_Aug_2025_15h47min48sec.csv')
VIDEO_FILE = '00_07dpf_Test_PreyCap_Thu_21_Aug_2025_15h47min48sec.mp4'

def load_stim(stim_path: Path) -> list:
    events = []
    with stim_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events

if __name__ == '__main__':

    stimuli = load_stim(STIM_FILE)
    video_info = pd.read_csv(VIDEO_TIMESTAMPS_FILE)

    events = []

    for stim in stimuli:
        timestamp = stim['timestamp']
        value = stim['foreground_color']
        index = video_info[video_info['timestamp'] > timestamp]['index'].iloc[0]
        events.append((index, value))

        
    reader = cv2.VideoCapture(VIDEO_FILE)
    writer = cv2.VideoWriter('uv_prey_capture.mp4', cv2.VideoWriter_fourcc(*'XVID'), 100, (2048,2048), True)
    counter = 0
    current_text = ''
    while reader.isOpened():

        ret, frame = reader.read()
        if not ret:
            break

        counter += 1
        print(counter)
        
        for idx, color in events[::-1]:
            if counter >= idx:
                break
        
        if color in ([0.0, 0.0, 0.2, 1.0], [0.0, 0.0, 0.25, 1.0]): 
            frame = cv2.putText(frame, 'UV prey ON', (10,50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2, cv2.LINE_AA)
        writer.write(frame)
    writer.release()


