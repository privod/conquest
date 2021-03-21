from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty, ColorProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget


class Location(AnchorLayout):
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            game: ConquestGame = self.parent.parent

            # game.current_legion.location.remove_widget(game.current_legion)
            map: Map = game.map
            map.locations[2][2].remove_widget(game.emperor)
            game.map.locations[1][1].add_widget(game.emperor)


class Land(Location):
    pass


class Province(Land):
    pass


class Ocean(Location):
    pass


class GameObject(Label):
    location = ObjectProperty(None)

    def __init__(self, location, **kwargs):
        super(GameObject, self).__init__(**kwargs)
        self.location = location
        self.location.add_widget(self)


class Legion(GameObject):
    background_color = ListProperty([0, 0, 0, 0.8])


class Emperor(Legion):
    pass


class Capital(GameObject):
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
    capital = ObjectProperty(None)
    emperor = ObjectProperty(None)
    current_legion = ObjectProperty(None)

    def start(self):
        self.map.rendering([
             'LOLLLLLL',
             'LLLLLLLL',
             'LLLOOLLL',
             'LLLOLLLL',
             'LLOOLLOL',
             'LOOLLLOL',
             'LLOLLOOO',
             'LLLLOOOO',
        ])
        self.capital = Capital(self.map.locations[2][2])
        self.emperor = Emperor(self.map.locations[2][1], text='I')
        self.current_legion = self.emperor
        self.map.build()


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()