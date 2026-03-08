import random

from game_data import (
    COLLISION_GRID_SIZE,
    COLLISION_TILE_SIZE,
    MAP_HEIGHT,
    MAP_WIDTH,
    ORES,
    WATER_MAP,
)


class GameState:
    """Store the shared gameplay state."""

    def __init__(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.money = 0
        self.inventory = {}
        self.forbidden_grids = [
            (11, 10), (13, 11), (11, 12), (13, 13),
            (13, 14), (14, 14), (15, 14), (15, 13),
            (9, 9), (9, 10), (10, 10), (9, 11), (10, 11),
            (13, 10), (13, 9), (15, 11), (16, 12), (10, 9),
            (10, 10), (10, 11),
        ]

        self.grid_map = []
        self.generate_map()

        self.level = 1
        self.current_exp = 0
        self.exp_to_next_level = 100
        self.max_stamina = 100
        self.current_stamina = 100

        self.current_capacity = 0
        self.max_capacity = 20

        self.torch_count = 0
        self.torch_time_left = 0.0
        self.base_vision_radius = 210
        self.torch_vision_radius = 560
        self.torch_duration_seconds = 180
        self.torch_price = 75

    def add_to_inventory(self, ore_type):
        if self.current_capacity < self.max_capacity:
            self.inventory[ore_type] = self.inventory.get(ore_type, 0) + 1
            self.current_capacity += 1
            return True
        return False

    def has_active_torch(self):
        return self.torch_time_left > 0

    def can_use_torch(self):
        return self.torch_count > 0

    def use_torch(self):
        if not self.can_use_torch():
            return False

        # à¸«à¸¢à¸´à¸šà¸„à¸šà¹€à¸žà¸¥à¸´à¸‡à¸¡à¸²à¹€à¸£à¸´à¹ˆà¸¡à¹ƒà¸Šà¹‰
        self.torch_count -= 1
        self.torch_time_left = float(self.torch_duration_seconds)
        return True

    def tick_torch(self, dt):
        if not self.has_active_torch():
            return False

        # à¸™à¸±à¸šà¹€à¸§à¸¥à¸²à¸„à¸šà¹€à¸žà¸¥à¸´à¸‡à¸—à¸µà¹ˆà¹€à¸«à¸¥à¸·à¸­
        self.torch_time_left = max(0.0, self.torch_time_left - dt)
        return self.torch_time_left <= 0

    def get_vision_radius(self):
        if self.has_active_torch():
            return self.torch_vision_radius
        # à¹„à¸¡à¹ˆà¸¡à¸µà¸„à¸šà¹€à¸žà¸¥à¸´à¸‡à¸à¹‡à¸¢à¸±à¸‡à¹€à¸«à¹‡à¸™à¹ƒà¸à¸¥à¹‰ à¹†
        return self.base_vision_radius

    def buy_torch(self):
        if self.money < self.torch_price:
            return False

        self.money -= self.torch_price
        self.torch_count += 1
        return True

    def generate_map(self):
        ore_pool = []
        for ore_id, ore_obj in ORES.items():
            ore_pool.append((ore_id, ore_obj.weight))

        self.grid_map = []
        for y in range(self.grid_height):
            row = []
            for x in range(self.grid_width):
                center_px = (x * 120) + 60
                center_py = (y * 120) + 60

                if (x, y) in self.forbidden_grids:
                    row.append(None)
                    continue

                safe_margin = 55
                scan_points = [
                    (center_px, center_py),
                    (center_px - safe_margin, center_py),
                    (center_px + safe_margin, center_py),
                    (center_px, center_py - safe_margin),
                    (center_px, center_py + safe_margin),
                ]

                is_near_water = False
                for px, py in scan_points:
                    if self.is_water_tile(px, py):
                        is_near_water = True
                        break

                if is_near_water:
                    row.append(None)
                elif random.random() < 0.6:
                    row.append(self._weighted_random_ore(ore_pool))
                else:
                    row.append(None)

            self.grid_map.append(row)

    def _weighted_random_ore(self, ore_pool):
        total_weight = sum(weight for _, weight in ore_pool)
        random_weight = random.uniform(0, total_weight)
        current_weight = 0

        for ore_key, weight in ore_pool:
            current_weight += weight
            if random_weight <= current_weight:
                return ore_key

        return ore_pool[0][0]

    def get_tile(self, x, y):
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.grid_map[y][x]
        return None

    def is_water_tile(self, px, py):
        col = int(px / COLLISION_TILE_SIZE)
        row = int(py / COLLISION_TILE_SIZE)
        if 0 <= col < COLLISION_GRID_SIZE and 0 <= row < COLLISION_GRID_SIZE:
            return WATER_MAP[row][col] == 1
        return True

    def add_exp(self, amount):
        self.current_exp += amount
        leveled_up = False

        while self.current_exp >= self.exp_to_next_level:
            self.current_exp -= self.exp_to_next_level
            self.level += 1
            self.exp_to_next_level = self.level * 100
            leveled_up = True

        return leveled_up

    def consume_stamina(self, amount):
        """à¸¥à¸”à¸„à¹ˆà¸² Stamina à¸–à¹‰à¸²à¸¡à¸µà¸žà¸­à¹ƒà¸«à¹‰à¸¥à¸” à¸„à¸·à¸™à¸„à¹ˆà¸² True, à¸–à¹‰à¸²à¹„à¸¡à¹ˆà¸žà¸­ à¸„à¸·à¸™à¸„à¹ˆà¸² False"""
        if self.current_stamina >= amount:
            self.current_stamina -= amount
            return True
        return False

    def regenerate_stamina(self, amount):
        """à¸Ÿà¸·à¹‰à¸™à¸Ÿà¸¹ Stamina à¸„à¸·à¸™à¸„à¹ˆà¸² True à¸–à¹‰à¸²à¸¡à¸µà¸à¸²à¸£à¸Ÿà¸·à¹‰à¸™à¸Ÿà¸¹ (à¸¢à¸±à¸‡à¹„à¸¡à¹ˆà¹€à¸•à¹‡à¸¡à¸«à¸¥à¸­à¸”)"""
        if self.current_stamina < self.max_stamina:
            self.current_stamina += amount
            # à¸”à¸±à¸à¹„à¸§à¹‰à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰à¸žà¸¥à¸±à¸‡à¸‡à¸²à¸™à¸¥à¹‰à¸™à¹€à¸à¸´à¸™à¸«à¸¥à¸­à¸” (Max)
            if self.current_stamina > self.max_stamina:
                self.current_stamina = self.max_stamina
            return True
        return False
    def regenerate_stamina(self, amount):
        """à¸Ÿà¸·à¹‰à¸™à¸Ÿà¸¹ Stamina à¸„à¸·à¸™à¸„à¹ˆà¸² True à¸–à¹‰à¸²à¸¡à¸µà¸à¸²à¸£à¸Ÿà¸·à¹‰à¸™à¸Ÿà¸¹ (à¸¢à¸±à¸‡à¹„à¸¡à¹ˆà¹€à¸•à¹‡à¸¡à¸«à¸¥à¸­à¸”)"""
        if self.current_stamina < self.max_stamina:
            self.current_stamina += amount
            # à¸”à¸±à¸à¹„à¸§à¹‰à¹„à¸¡à¹ˆà¹ƒà¸«à¹‰à¸žà¸¥à¸±à¸‡à¸‡à¸²à¸™à¸¥à¹‰à¸™à¹€à¸à¸´à¸™à¸«à¸¥à¸­à¸” (Max)
            if self.current_stamina > self.max_stamina:
                self.current_stamina = self.max_stamina
            return True
        return False
