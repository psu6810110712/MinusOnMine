# game_logic.py - Core game state และ map generation
# สำหรับเกม MinusOnMine (Top-Down Mining RPG)

import random
from game_data import ORES, MAP_WIDTH, MAP_HEIGHT


class GameState:
    """เก็บสถานะเกมทั้งหมด: map, ผู้เล่น, เงิน, inventory"""

    def __init__(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.money = 0
        self.inventory = {}  # {"stone": 3, "gold": 1, ...}
        self.grid_map = []   # 2D list: None = ว่าง, "stone"/"coal"/... = แร่
        self.generate_map()

    def generate_map(self):
        """สุ่มวางแร่บน grid ตาม weight ใน ORES"""
        # สร้าง list ของแร่ทั้งหมดพร้อม weight
        ore_pool = []
        for ore_id, ore_obj in ORES.items():
            ore_pool.append((ore_id, ore_obj.weight))  # เข้าถึง object.weight แทน dict["weight"]

        self.grid_map = []
        for y in range(self.grid_height):
            row = []
            for x in range(self.grid_width):
                # 60% โอกาสเป็นหิน/แร่, 40% เป็นทางเดิน
                if random.random() < 0.6:
                    ore = self._weighted_random_ore(ore_pool)
                    row.append(ore)
                else:
                    row.append(None)  # ทางเดิน
            self.grid_map.append(row)

    def _weighted_random_ore(self, ore_pool):
        """สุ่มเลือกแร่ตาม weight (weight สูง = ได้บ่อย)"""
        total_weight = sum(w for _, w in ore_pool)
        r = random.uniform(0, total_weight)
        current = 0
        for ore_key, weight in ore_pool:
            current += weight
            if r <= current:
                return ore_key
        return ore_pool[0][0]  # fallback

    def get_tile(self, x, y):
        """ดูว่า tile (x, y) เป็นอะไร (None = ว่าง, str = ชื่อแร่)"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            return self.grid_map[y][x]
        return None
