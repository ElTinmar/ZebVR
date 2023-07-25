from multiprocessing import Event, Process

class Worker:
    def pre_loop(self):
        '''setup resources that must be initialized inside the new process'''

    def post_loop(self):
        '''free resources initialized inside the new process'''

    def post_send(self):
        pass

    def process(self):
        pass

    def _receive(self):
        pass
    
    def _send(self):
        pass

    def _loop(self, stop_execution: Event):
        '''main loop, run in a separate process'''

        self.pre_loop()

        while not stop_execution.is_set():
            data = self._receive()
            results = self.process(data)
            self._send(results)
            self.post_send()

        self.post_loop()

    def start(self):
        # start the loop in a separate process
        self.process = Process(
            target = self._loop, 
            args = (self.stop_loop,)
        )
        self.process.start()
        
    def stop(self):
        # stop the loop
        self.stop_loop.set()
        self.process.join()
