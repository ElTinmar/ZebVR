import multiprocessing
from psychopy import core, visual, event

def test():
    win = visual.Window(fullscr=True, screen=1, units='pix')
    event.waitKeys()
    core.quit()

if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')

    p = multiprocessing.Process(target=test)
    p.start()
    p.join()