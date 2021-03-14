from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget


class Location(Widget):
    pass


class Map(GridLayout):
    locations = ListProperty()


class ConquestGame(RelativeLayout):
    map = ObjectProperty(None)


class ConquestApp(App):
    def build(self):
        return ConquestGame()


if __name__ == '__main__':
    ConquestApp().run()