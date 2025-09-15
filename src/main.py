from kivy.app import App
from ui.cube_widget import CubeWidget
from kivy.core.window import Window
Window.clearcolor = (0.7, 0.85, 1.0, 1)


class CubeApp(App):
    def build(self):
        return CubeWidget()


if __name__ == "__main__":
    CubeApp().run()
