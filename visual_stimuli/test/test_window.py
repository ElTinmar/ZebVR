import pyglet
from multiprocessing import Process, Array 

class Test(pyglet.window.Window):

    def __init__(self, screenid: int = 0) -> None:
        super().__init__()
        display = pyglet.canvas.get_display()
        screens = display.get_screens()
        self.set_fullscreen(fullscreen=True,screen=screens[screenid])
        self.batch = pyglet.graphics.Batch()

    def on_draw(self):
        self.clear()
        self.batch.draw()
    
    def animate(self):
        w,h = self.get_size()
        i = 0 
        while True:
            i = (i+1)%w
            coordinates = [[0,h],[i,h],[i,0],[0,0],[0,h]]
            self.poly = pyglet.shapes.Polygon(*coordinates, color=(255,255,255), batch=self.batch)


Test.register_event_types('animate')