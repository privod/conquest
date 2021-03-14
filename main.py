from kivy.app import App
from kivy.properties import ListProperty
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget


class Location(Widget):
    pass


class Map(Widget):
    locations = ListProperty()


class ConquestGame(Widget):
    pass


class ConquestApp(App):
    def build(self):
        return ConquestGame()


if __name__ == '__main__':
    ConquestApp().run()