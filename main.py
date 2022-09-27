from random import random
from collections.abc import Generator

from kivy.animation import Animation
from kivy.app import App
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
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
    experience: int = ObjectProperty(0)

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

    def increment_experience(self):
        self.experience += 1

    def battle(self):
        self.decrement_move_count()
        self.get_cell().annex()
        if random() < 0.25:
            self.experience = 0
            if self.__class__ == Emperor:
                print('Имератор погиб в бою')
                self.__class__ = Legion
                self.get_game().civil_war()
            else:
                print('Легат погиб в бою')
        else:
            self.increment_experience()

    def move(self, geo_pos):
        dest_location: Location = self.get_map().get_cell(self.calc_dest(geo_pos)).get_location()

        if dest_location is None or not dest_location.can_go:
            return

        if dest_location == self.get_location():
            self.move_count = 0                     # Оставить легион на месте

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
    army: GridLayout = ObjectProperty(None)


class Move(object):
    anim: Animation
    # _from_: Location
    to: Location
    obj: GameObject

    # def __init__(self, _from_: Location, to: Location):
    def __init__(self, to: Location):
        self.to = to

    def start(self, obj: GameObject):
        self.obj = obj
        self.anim = Animation(x=self.to.x, y=self.to.y, duration=0.3)
        self.anim.on_complete = self.complete
        self.anim.start(self.obj)

    def complete(self, widget: Widget):
        Animation.on_complete(self.anim, widget)


class BarbarianAttack(Move):

    def start(self, obj: GameObject):
        Move.start(self, obj)

    def complete(self, widget: Widget):
        Move.complete(self, widget)
        self.to.get_cell().separation()
        self.obj.parent.remove_widget(self.obj)


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

    def civil_war(self):

        exp_army = sorted(self.army.copy(), key=lambda legion: legion.experience, reverse=True)
        new_emperor = exp_army[0]
        new_emperor.__class__ = Emperor


    def barbarian_raids(self):
        for province in self.provinces:
            if province.is_protected():
                continue

            for land in province.get_border_barbarian_attack():
                if random() < 0.05:
                    barbarian = Barbarian()
                    land.add_widget(barbarian)
                    barbarian.pos = land.pos
                    barbarian_attack = BarbarianAttack(province)
                    barbarian_attack.start(barbarian)
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

        self.info.army.clear_widgets()
        for legion in self.army:
            self.info.army.add_widget(Label(text='{}: {}'.format(legion.label_text, legion.experience)))

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