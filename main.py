from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget


class Location(Widget):
    pass


class Land(Location):
    pass


class Ocean(Location):
    pass


class Map(GridLayout):
    locations = ListProperty()

    def build(self):
        self.locations.append(Land())
        self.locations.append(Land())
        self.locations.append(Land())
        self.locations.append(Ocean())
        self.locations.append(Ocean())
        self.locations.append(Ocean())
        self.locations.append(Land())
        self.locations.append(Land())

        self.cols = 5
        for loc in self.locations:
            self.add_widget(loc)


class ConquestGame(RelativeLayout):
    map = ObjectProperty(None)

    def start(self):
        self.map.build()


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()