from kivy.app import App
from ui.cube_widget import CubeWidget


class CubeApp(App):
    def build(self):
        return CubeWidget()


if __name__ == "__main__":
    CubeApp().run()
