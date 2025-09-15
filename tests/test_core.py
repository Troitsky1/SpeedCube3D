from kivy.app import App
from kivy.uix.widget import Widget
from kivy.graphics import Mesh, PushMatrix, PopMatrix, Translate

class TestWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            PushMatrix()
            Translate(self.center_x, self.center_y, -5)  # move it in front
            # Simple quad
            Mesh(
                vertices=[-1,-1,0, 1,0,0,1, -1,1,0, 0,1,0,1, 1,-1,0, 0,0,1,1, 1,1,0, 1,1,1,1],
                indices=[0,1,2, 1,3,2],
                mode='triangles',
                vertex_format='v3c4'
            )
            PopMatrix()

class TestApp(App):
    def build(self):
        return TestWidget()

TestApp().run()

