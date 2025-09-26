import cv2
import numpy as np
import glob
import os
import re
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

def superimpose_videos(stim_key, files, average=True):
    if not files:
        return None

    # Open first video to get metadata
    cap0 = cv2.VideoCapture(files[0])
    fps = cap0.get(cv2.CAP_PROP_FPS)
    width = int(cap0.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap0.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap0.get(cv2.CAP_PROP_FRAME_COUNT))
    cap0.release()

    # Open all captures
    caps = [cv2.VideoCapture(f) for f in files]

    out_name = f"superimposed_{stim_key}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_name, fourcc, fps, (width, height))

    for i in range(frame_count):
        frames = []
        for cap in caps:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame.astype(np.float32))

        if not frames:
            break

        accum = np.min(frames, axis=0)

        result = np.clip(accum, 0, 255).astype(np.uint8)
        out.write(result)

    for cap in caps:
        cap.release()
    out.release()
    return out_name


def group_files():
    files = glob.glob("stim_*.mp4")
    groups = defaultdict(list)
    pattern = re.compile(r"stim_(.+)_\d+\.mp4")

    for f in files:
        m = pattern.match(os.path.basename(f))
        if m:
            stim_key = m.group(1)  # e.g. BRIGHT_, OKR_-36.0, PHOTOTAXIS_1.0
            groups[stim_key].append(f)
    return groups


if __name__ == "__main__":
    groups = group_files()

    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(superimpose_videos, stim_key, sorted(flist), True): stim_key
            for stim_key, flist in groups.items()
        }

        for fut in as_completed(futures):
            stim_key = futures[fut]
            try:
                out_file = fut.result()
                if out_file:
                    print(f"Saved {out_file}")
            except Exception as e:
                print(f"Error processing {stim_key}: {e}")
