from collections import Iterable, Generator
from random import random

from kivy.animation import Animation
from kivy.app import App
from kivy.graphics.vertex_instructions import Triangle
from kivy.properties import ListProperty, ObjectProperty, ColorProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from numpy import sign
from roman import toRoman


# --- Locations --------------------------------------------------------------------------------------------------------
class Location(AnchorLayout):
    background_color = ListProperty([0, 0, 0, 0])
    can_go: bool = ObjectProperty(True)
    is_enemy: bool = ObjectProperty(True)
    cost_move_count: int = ObjectProperty(1)
    can_barbarian_attack: bool = ObjectProperty(False)

    def get_cell(self) -> "Cell":
        return self.parent

    def get_map(self) -> "Map":
        return self.get_cell().parent

    def get_game(self) -> "ConquestGame":
        return self.get_map().parent

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            game: ConquestGame = self.get_game()
            game.move(self.get_cell().get_geo_pos())

    def get_border_lands(self) -> Generator["Location"]:
        x, y = self.get_cell().get_geo_pos()
        # print('geo pos: {}'.format([x, y]))
        for dx, dy in [[0, -1], [1, 0], [0, 1], [-1, 0]]:
            # print('delta: {}'.format([dx, dy]))
            cell = self.get_map().get_cell([x + dx, y + dy])
            if cell is not None:
                yield cell.get_location()

    def get_border_barbarian_attack(self) -> Generator["Location"]:
        for location in self.get_border_lands():
            if location.can_barbarian_attack:
                yield location

    def get_located_objects(self) -> Generator["GameObject"]:
        for game_object in self.children:
            yield game_object

    def is_protected(self) -> bool:
        for game_object in self.get_located_objects():
            if game_object.protects:
                return True
        return False


class Land(Location):
    can_barbarian_attack: bool = ObjectProperty(True)


class Province(Land):
    is_enemy: bool = ObjectProperty(False)
    tax: int = ObjectProperty(1)
    can_barbarian_attack: bool = ObjectProperty(False)


class Ocean(Location):
    can_go: bool = ObjectProperty(False)


# --- Game objects -----------------------------------------------------------------------------------------------------
class GameObject(AnchorLayout):
    background_color = ListProperty([0, 0, 0, 0])
    label_text: str = ObjectProperty('')
    protects: bool = ObjectProperty(True)

    def __init__(self, location: Location, label_text: str = '', **kwargs):
        super(GameObject, self).__init__(**kwargs)
        self.set_location(location)
        self.label_text = label_text

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
    move_count: int = ObjectProperty(1)
    cost: int = ObjectProperty(5)

    def __init__(self, location: Location, num: int, **kwargs):
        super(Legion, self).__init__(location, toRoman(num), **kwargs)

    def is_turn(self) -> bool:
        return self.get_game().turn_legion.get() == self

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

        if dest_location is None or not dest_location.can_go:
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


class Barbarian(AnchorLayout):
    pass


# --- Свойства ---------------------------------------------------------------------------------------------------------
class TurnLegionFlag(Widget):
    pass


class TurnLegion(object):
    flag: TurnLegionFlag
    legion: Legion

    def __init__(self):
        self.flag = TurnLegionFlag()

    def set(self, legion: Legion):
        if self.flag.parent is not None:
            self.legion.remove_widget(self.flag)
        self.legion = legion
        self.legion.add_widget(self.flag)

    def get(self) -> Legion:
        return self.legion


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
        new_province: Province = Province()
        for obj in self.get_location().children:
            obj.set_location(new_province)
        self.set_location(new_province)
        self.get_game().provinces.append(new_province)

    def separation(self):
        self.get_game().provinces.remove(self.get_location())
        land: Land = Land()
        for obj in self.get_location().children:
            obj.set_location(land)
        self.set_location(land)


class Info(BoxLayout):
    year = ObjectProperty(0)
    taxes = ObjectProperty(0)


class BarbarianAttack(object):
    anim: Animation
    land_from: Land
    province_to: Province
    barbarian: Barbarian

    def __init__(self, land_from: Land, province_to: Province):
        self.land_from = land_from
        self.province_to = province_to

    def start(self):
        self.barbarian = Barbarian()
        self.land_from.add_widget(self.barbarian)
        self.barbarian.pos = self.land_from.pos

        self.anim = Animation(x=self.province_to.x, y=self.province_to.y, duration=0.2)
        self.anim.on_complete = self.complete
        self.anim.start(self.barbarian)

    def complete(self, widget: Widget):
        Animation.on_complete(self.anim, widget)
        self.province_to.get_cell().separation()
        self.land_from.remove_widget(self.barbarian)



class Map(GridLayout):
    def get_cell(self, geo_pos) -> Cell:
        x, y = geo_pos

        if x <= 0 or x > self.cols or y <= 0 or y > (len(self.children) / self.cols):
            return None

        num = len(self.children) - ((y - 1) * self.cols + x)
        if len(self.children) > num:
            return self.children[num]
        else:
            return None

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
    turn_legion: TurnLegion = ObjectProperty(None)
    # current_legion_flag: CurrentLegionFlag = ObjectProperty(CurrentLegionFlag())
    army: list[Legion] = ListProperty([])
    army_move: list[Legion] = ListProperty([])
    provinces: list[Province] = ListProperty()

    def set_capital(self, geo_pos):
        cell: Cell = self.map.get_cell(geo_pos)
        cell.annex()
        location: Location = cell.get_location()
        self.capital = Capital(location)
        self.emperor = Emperor(location, 1)
        self.army.append(self.emperor)
        self.turn_legion.set(self.emperor)
        self.round()

    # def set_turn_legion(self, legion:Legion):
    #     self.turn_legion = legion
    #     self.turn_legion.add_widget(self.current_legion_flag)

    def barbarian_raids(self):
        for province in self.provinces:
            if province.is_protected():
                continue

            for land in province.get_border_barbarian_attack():
                rnd = random()
                if rnd < 0.05:
                    barbarian_attack = BarbarianAttack(land, province)
                    barbarian_attack.start()
                    print('Нападение варваров!')
                    print('Разарена провинция {}'.format(province.get_cell().get_geo_pos()))
                    print('Нападегние из локации {}'.format(land.get_cell().get_geo_pos()))
                    # barbarian_attack = Barbarian()
                    # land.add_widget(barbarian_attack)
                    # # province.get_cell().get_location().canvas.add(Triangle(size=()))
                    #
                    # province.get_cell().separation()
                    # # anim = Animation(x=province.x, y=province.y)
                    # # anim.start(barbarian_attack)
                    break

    def round(self):
        self.barbarian_raids()

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
            new_legion = Legion(self.capital.get_location(), num=len(self.army) + 1)
            self.army.append(new_legion)

        self.army_move = self.army.copy()

        self.info.year += 1

    def move(self, geo_pos):
        self.turn_legion.get().move(geo_pos)
        if self.turn_legion.get().move_count == 0:
            self.army_move.remove(self.turn_legion.get())
        if len(self.army_move) == 0:
            self.round()

        self.turn_legion.set(self.army_move[0])

    def start(self):
        self.map.build([
            'LOLLLLLLLLLLLLLLLLLL',
            'LLLLLLLLLLLLLLLOLLLL',
            'LLLOOLLLLLLLLLOOOLLL',
            'LLLOLLLLLLLLLLLLOOLL',
            'LLOOLLOLLLLLLLLLLLLL',
            'LOOLLLOLLLLLLLLLLLLL',
            'LLOLLOOOLLLLLLLLLLLL',
            'LLLLLLLLLLLLLLLLOLLL',
            'LLLLLLLLLLLLLLLOOLLL',
            'LLLLLLLLLLLLLOOLLLLL',
            'LLLLLLLLOOOOOOOOOOOO',
            'LLLLLLLLLOOOOLLLLLLL',
            'LLLLLLLLLLLOOLLLLLLL',
            'LLLLLLLLLLLLLLLLLLLL',
            'LLLLLLLLLLLLLLLLLLLL',
            'LLOLLOOOLLLLLLLLLLLL',
            'LLLLOOOOOOOOOOOOOOOO',
        ])
        self.turn_legion = TurnLegion()
        self.set_capital([3, 16])


class ConquestApp(App):
    def build(self):
        game = ConquestGame()
        game.start()
        return game


if __name__ == '__main__':
    ConquestApp().run()