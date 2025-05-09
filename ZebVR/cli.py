import pickle
from ZebVR.dags import closed_loop_3D
from multiprocessing import Process
import time

with open('test.vr', 'rb') as fp:
    settings = pickle.load(fp)

settings['main']['record'] = False

dag, worker_logger, queue_logger = closed_loop_3D(settings)

p_worker_logger = Process(target=worker_logger.run)
p_queue_logger = Process(target=queue_logger.run)
p_worker_logger.start()
p_queue_logger.start()
dag.start()

try:
    time.sleep(1200)
except KeyboardInterrupt:
    print('stopping')
    pass

dag.stop()
worker_logger.stop()
queue_logger.stop()
p_worker_logger.join()
p_queue_logger.join()