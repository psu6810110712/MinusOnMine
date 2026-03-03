# game_logic.py - Core game state และ map generation
# สำหรับเกม MinusOnMine (Top-Down Mining RPG)

import random
from game_data import ORES, MAP_WIDTH, MAP_HEIGHT, WATER_MAP, COLLISION_GRID_SIZE, COLLISION_TILE_SIZE


class GameState:
    """เก็บสถานะเกมทั้งหมด: map, ผู้เล่น, เงิน, inventory"""

    def __init__(self):
        self.grid_width = MAP_WIDTH
        self.grid_height = MAP_HEIGHT
        self.money = 0
        self.inventory = {}  # {"stone": 3, "gold": 1, ...}
        
        # ==========================================
        # 1. เพิ่ม Blacklist: พิกัด (X, Y) ที่ห้ามแร่เกิด (ต้นไม้, ทางเดิน)
        # ==========================================
        self.forbidden_grids = [
            (11, 10), (13, 11), (11, 12), (13, 13), 
            (13, 14), (14, 14), (15, 14), (15, 13),
            (9, 9), (9, 10), (10, 10), (9, 11), (10, 11),
            (13, 10), (13, 9), (15, 11), (16, 12), (10, 9),
            (10, 10), (10, 11)

            # *** คุณต้องเดินสำรวจในเกมแล้วเอาเลขพิกัดมาเติมตรงนี้นะครับ ***
        ]
        
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
                # ==========================================
                # 2. เช็คพิกัดก่อนว่าโดนแบน (อยู่ใน Blacklist) ไหม?
                # ==========================================
                if (x, y) in self.forbidden_grids:
                    # ถ้าเป็นต้นไม้/ทางเดิน ให้ปล่อยช่องนี้ให้ว่าง (None)
                    row.append(None)
                else:
                    # ถ้าเป็นพื้นที่ปกติ (หญ้า) ให้สุ่ม 60% โอกาสเกิดแร่ตามโค้ดเดิม
                    if random.random() < 0.6:
                        ore = self._weighted_random_ore(ore_pool)
                        row.append(ore)
                    else:
                        row.append(None)  # ทางเดินว่างๆ บนพื้นหญ้า
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

    def is_water_tile(self, px, py):
        """เช็คว่าพิกัด pixel (px, py) อยู่บน water tile หรือไม่"""
        col = int(px / COLLISION_TILE_SIZE)
        row = int(py / COLLISION_TILE_SIZE)
        if 0 <= col < COLLISION_GRID_SIZE and 0 <= row < COLLISION_GRID_SIZE:
            return WATER_MAP[row][col] == 1
        return True  # นอกแผนที่ = blocked
