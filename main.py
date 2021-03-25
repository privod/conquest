from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty, ColorProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
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
    pass


class Province(Land):
    is_enemy: bool = ObjectProperty(False)
    tax: int = ObjectProperty(1)


class Ocean(Location):
    can_go: bool = ObjectProperty(False)


# --- Game objects -----------------------------------------------------------------------------------------------------
class GameObject(Label):

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
    cost: int = ObjectProperty(5)

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

    def battle(self):
        location_before_battle = self.get_location()
        self.decrement_move_count()
        self.get_cell().annex()

    def move(self, geo_pos):
        dest_location: Location = self.get_map().get_cell(self.calc_dest(geo_pos)).get_location()

        if not dest_location.can_go:
            return

        self.set_location(dest_location)
        if self.get_location().is_enemy:
            self.battle()
        else:
            self.decrement_move_count()


class Emperor(Legion):
    def decrement_move_count(self):
        if self.get_location().is_enemy:
            super(Emperor, self).decrement_move_count()


class Capital(GameObject):
    tax: int = ObjectProperty(4)


# ----------------------------------------------------------------------------------------------------------------------
class Cell(AnchorLayout):
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

    def annex(self):
        location_before_annex = self.get_location()
        new_province: Province = Province()
        self.set_location(new_province)
        for obj in location_before_annex.children:
            obj.set_location(new_province)
        self.get_game().provinces.append(new_province)


class Info(BoxLayout):
    year: ObjectProperty(0)
    taxes: ObjectProperty(0)


class Map(GridLayout):
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


class ConquestGame(BoxLayout):
    map: Map = ObjectProperty(None)
    info: Info = ObjectProperty(None)
    capital: Capital = ObjectProperty(None)
    emperor: Emperor = ObjectProperty(None)
    current_legion: Legion = ObjectProperty(None)
    army: list[Legion] = ListProperty([])
    army_move: list[Legion] = ListProperty([])
    provinces: list[Province] = ListProperty()

    def round(self):
        army_cost: int = 0
        for legion in self.army:
            legion.move_count = legion.__class__.move_count.defaultvalue
            army_cost += legion.cost

        self.info.taxes = self.capital.tax
        for province in self.provinces:
            self.info.taxes += province.tax

        free_tax = self.info.taxes - army_cost
        if free_tax < 0:
            self.army.pop()
        elif free_tax >= 5:
            new_legion = Legion(self.capital.get_location(), text=str(len(self.army) + 1))
            self.army.append(new_legion)

        self.army_move = self.army.copy()

        self.info.year += 1

    def move(self, geo_pos):
        self.current_legion.move(geo_pos)
        if self.current_legion.move_count == 0:
            self.army_move.remove(self.current_legion)
        if len(self.army_move) > 0:
            self.current_legion = self.army_move[0]
        else:
            self.round()

    def set_capital(self, geo_pos):
        cell: Cell = self.map.get_cell(geo_pos)
        cell.annex()
        location: Location = cell.get_location()
        self.capital = Capital(location)
        self.emperor = Emperor(location, text='I')
        self.army.append(self.emperor)
        self.current_legion = self.emperor
        self.round()

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
            # 'LLLLLLLLLL',
        ])
        self.set_capital([2, 3])


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()