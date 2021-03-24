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
    can_go: bool = ObjectProperty(True)
    is_enemy: bool = ObjectProperty(True)
    cost_move_count: int = ObjectProperty(1)

    def get_cell(self) -> "Cell":
        return self.parent

    def get_map(self) -> "Map":
        return self.get_cell().parent

    def get_game(self) -> "ConquestGame":
        return self.get_map().parent

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            game: ConquestGame = self.get_game()            # game.current_legion.location.remove_widget(game.current_legion)
            game.move(self.get_cell().get_geo_pos())


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
    # location = ObjectProperty(None)

    def __init__(self, location: Location, **kwargs):
        super(GameObject, self).__init__(**kwargs)
        self.set_location(location)

    def get_location(self) -> Location:
        return self.parent

    def set_location(self, location: Location):
        if self.get_location() is not None:
            self.get_location().remove_widget(self)
        location.add_widget(self)

    def get_cell(self) -> "Cell":
        return self.get_location().get_cell()

    def get_map(self) -> "Map":
        return self.get_location().get_map()

    def get_game(self) -> "ConquestGame":
        return self.get_location().get_game()


class Legion(GameObject):
    background_color = ListProperty([0, 0, 0, 0.8])
    move_count: int = ObjectProperty(1)

    def calc_dest(self, geo_pos):
        cur_x, cur_y = self.get_cell().get_geo_pos()
        dest_x, dest_y = geo_pos

        remove_x = dest_x - cur_x
        remove_y = dest_y - cur_y

        if abs(remove_x) > abs(remove_y):
            return [cur_x + sign(remove_x), cur_y]
        else:
            return [cur_x, cur_y + sign(remove_y)]

    def decrement_move_count(self):
        self.move_count -= self.get_location().cost_move_count

    # def annex(self):    # TODO: Должно бы не сдесь, по видимому в Cell
    #     location = Province(self.get_location().geo_pos)
    #     self.get_cell().set_location(location)
    #     self.set_location(location)

    def battle(self):
        location_before_battle = self.get_location()
        self.get_cell().annex()

    def move(self, geo_pos):
        dest_location: Location = self.get_map().get_cell(self.calc_dest(geo_pos)).get_location()

        if not dest_location.can_go:
            return

        self.set_location(dest_location)
        if self.get_location().is_enemy:
            self.battle()
        self.decrement_move_count()


class Emperor(Legion):
    def decrement_move_count(self):
        if self.get_location().is_enemy:
            super(Emperor, self).decrement_move_count()


class Capital(GameObject):
    pass


# ----------------------------------------------------------------------------------------------------------------------
class Cell(AnchorLayout):
    # geo_pos = ListProperty([0, 0])

    def get_map(self) -> "Map":
        return self.parent

    def get_game(self) -> "ConquestGame":
        return self.get_map().parent

    def get_location(self) -> Location:
        return self.children[0]

    def get_geo_pos(self):
        map: Map = self.get_map()
        for index, cell in enumerate(reversed(map.children)):
            if self == cell:
                y = (index // map.cols) + 1
                x = (index % map.cols) + 1
                return [x, y]

    def set_location(self, location: Location):
        if self.get_location() is not None:
            self.remove_widget(self.get_location())
        self.add_widget(location)

        # x, y = self.get_location().get_geo_pos()
        # self.get_map().locations[x][y] = location

    def annex(self):
        location_before_annex = self.get_location()
        self.set_location(Province())
        for obj in location_before_annex.children:
            obj.set_location(self.get_location())


class Map(GridLayout):
    # locations = ListProperty()

    # def get_game(self):
    #     return self.parent

    def get_cell(self, geo_pos) -> Cell:
        x, y = geo_pos
        num = len(self.children) - ((y - 1) * self.cols + x)
        return self.children[num]

    def build(self, char_map):
        for char_row in char_map:
            self.cols = len(char_row)
            for char in char_row:
                if char == 'L':
                    location = Land()
                elif char == 'O':
                    location = Ocean()
                else:
                    location = Location()
                cell = Cell()
                cell.add_widget(location)
                self.add_widget(cell)

    # def add_cell(self):
    #     cell = Cell()
    #     self.add_widget(cell)
    #     cell.geo_pos = [x, y]
    #     return cell

    # def build(self):
    #     self.cols = len(self.locations[0])
    #     for loc_row in self.locations:
    #         for loc in loc_row:
    #             cell = self.add_cell()
    #             cell.add_widget(loc)


class ConquestGame(RelativeLayout):
    map: Map = ObjectProperty(None)
    capital: Capital = ObjectProperty(None)
    emperor: Emperor = ObjectProperty(None)
    current_legion: Legion = ObjectProperty(None)
    provinces = ListProperty()

    def move(self, geo_pos):
        self.current_legion.move(geo_pos)

    def set_capital(self, geo_pos):
        cell: Cell = self.map.get_cell(geo_pos)
        cell.annex()
        location: Location = cell.get_location()
        self.capital = Capital(location)
        self.emperor = Emperor(location, text='I')
        self.current_legion = self.emperor


    def start(self):
        self.map.build([
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
        self.set_capital([2, 3])


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()