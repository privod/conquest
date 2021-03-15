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

    def rendering(self, char_map):
        for char_row in char_map:
            loc_row = []
            for char in char_row:
                if char == 'L':
                    loc_row.append(Land())
                elif char == 'O':
                    loc_row.append(Ocean())
            self.locations.append(loc_row)

    def build(self):
        self.cols = len(self.locations)
        for loc_row in self.locations:
            for loc in loc_row:
                self.add_widget(loc)


class ConquestGame(RelativeLayout):
    map = ObjectProperty(None)

    def start(self):
        self.map.rendering([
             'LLLLLLLL',
             'LLLLLLLL',
             'LLLOOLLL',
             'LLLOLLLL',
             'LLOOLLOL',
             'LOOLLLOL',
             'LLOLLOOO',
             'LLLLOOOO',
        ])
        self.map.build()


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()