from collections import deque
from enum import IntEnum

class Debouncer:
    '''finite state machine to debounce triggers with a rolling sum'''

    class State(IntEnum):
        IDLE = -1
        ON = 1
        OFF = 0

    class Transition(IntEnum):
        RISING_EDGE = 1
        NONE = 0 
        FALLING_EDGE = -1

    def __init__(self, buffer_length = 5):

        self.buffer_length = buffer_length
        self.buffer = deque(maxlen = buffer_length)
        self.current_state = self.State.IDLE # initial state

    def set_buffer_length(self, length: int) -> None:
        self.buffer_length = length
        self.buffer = deque(maxlen = length)

    def update(self, input: int) -> 'Debouncer.Transition':

        # check input alphabet
        if input not in {0, 1}:
            raise ValueError("Input must be 0 or 1")

        self.buffer.append(input)
        
        new_state = None
        if sum(self.buffer) == self.buffer_length:
            new_state = self.State.ON
        elif sum(self.buffer) == 0:
            new_state = self.State.OFF
        else:
            return self.Transition.NONE

        transition = self.Transition.NONE
        if self.current_state == self.State.OFF and new_state == self.State.ON:
            transition = self.Transition.RISING_EDGE
        elif self.current_state == self.State.ON and new_state == self.State.OFF:
            transition = self.Transition.FALLING_EDGE
        # ignoring transition from IDLE on purpose

        self.current_state = new_state
        return transition
        
    def get_state(self) -> 'Debouncer.State':
        return self.current_state