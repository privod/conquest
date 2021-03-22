from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty, ColorProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from numpy import sign


# --- Locations --------------------------------------------------------------------------------------------------------
class Location(AnchorLayout):
    background_color = ListProperty([0, 1, 0, 0.8])
    geo_pos = ListProperty([0, 0])
    can_go = ObjectProperty(True)
    is_enemy = ObjectProperty(True)
    cost_move_count = ObjectProperty(1)

    def __init__(self, geo_pos,  **kwargs):
        super(Location, self).__init__(**kwargs)
        self.geo_pos = geo_pos

    def get_cell(self):
        return self.parent

    def get_map(self):
        return self.get_cell().parent

    def get_game(self):
        return self.get_map().parent

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            game: ConquestGame = self.get_game()            # game.current_legion.location.remove_widget(game.current_legion)
            game.move(self.geo_pos)


class Land(Location):
    # def on_arrival(self, legion):
    #     legion.on_arriv
    #     legion.battle()
    pass


class Province(Land):
    is_enemy = False


class Ocean(Location):
    can_go = False


# --- Game objects -----------------------------------------------------------------------------------------------------
class GameObject(Label):
    location = ObjectProperty(None)

    def __init__(self, location: Location, **kwargs):
        super(GameObject, self).__init__(**kwargs)
        self.set_location(location)

    def set_location(self, location: Location):
        if self.parent is not None:
            self.location.remove_widget(self)
        self.location = location
        self.location.add_widget(self)

    def get_cell(self):
        return self.location.get_cell()

    def get_map(self):
        return self.location.get_map()

    def get_game(self):
        return self.location.get_game()


class Legion(GameObject):
    background_color = ListProperty([0, 0, 0, 0.8])
    move_count = ObjectProperty(1)

    def calc_dest_location(self, geo_pos):
        cur_x, cur_y = self.location.geo_pos
        dest_x, dest_y = geo_pos

        remove_x = dest_x - cur_x
        remove_y = dest_y - cur_y

        locations = self.get_map().locations
        if abs(remove_x) > abs(remove_y):
            return locations[cur_x + sign(remove_x)][cur_y]
        else:
            return locations[cur_x][cur_y + sign(remove_y)]

    def decrement_move_count(self):
        self.move_count -= self.location.cost_move_count

    def battle(self):
        location_before_battle = self.location
        geo_pos = self.location.geo_pos
        x, y = geo_pos

        location = Province(geo_pos)
        cell = self.get_cell()
        cell.remove_widget(self.location)
        cell.add_widget(location)
        cell.get_map().locations[x][y] = location
        self.set_location(location)

    def move(self, geo_pos):
        dest_location:Location = self.calc_dest_location(geo_pos)
        if not dest_location.can_go:
            return

        self.set_location(dest_location)
        if self.location.is_enemy:
            self.battle()
        self.decrement_move_count()


class Emperor(Legion):
    def decrement_move_count(self):
        if self.location.is_enemy:
            super(Emperor, self).decrement_move_count()


class Capital(GameObject):
    pass


# ----------------------------------------------------------------------------------------------------------------------
class Cell(AnchorLayout):
    def get_map(self):
        return self.parent

    def get_game(self):
        return self.get_map().parent


class Map(GridLayout):
    locations = ListProperty()

    def get_game(self):
        return self.parent

    def rendering(self, char_map):
        for row, char_row in enumerate(char_map):
            loc_row = []
            for col, char in enumerate(char_row):
                if char == 'L':
                    loc_row.append(Land([row, col]))
                elif char == 'O':
                    loc_row.append(Ocean([row, col]))
            self.locations.append(loc_row)

    def build(self):
        self.rows = len(self.locations)
        for loc_row in self.locations:
            for loc in loc_row:
                cell = Cell()
                cell.add_widget(loc)
                self.add_widget(cell)


class ConquestGame(RelativeLayout):
    map = ObjectProperty(None)
    capital = ObjectProperty(None)
    emperor = ObjectProperty(None)
    current_legion = ObjectProperty(None)
    provinces = ListProperty()

    def move(self, geo_pos):
        self.current_legion.move(geo_pos)

        # if self.current_legion.location is :



    def start(self):
        self.map.rendering([
            'LOLLLLLLLL',
            'LLLLLLLLLL',
            'LLLOOLLLLL',
            'LLLOLLLLLL',
            'LLOOLLOLLL',
            'LOOLLLOLLL',
            'LLOLLOOOLL',
            'LLLLOOOOOO',
            'LLLLLLLLLL',
        ])
        self.map.build()
        self.capital = Capital(self.map.locations[2][2])
        self.emperor = Emperor(self.capital.location, text='I')
        self.current_legion = self.emperor


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()