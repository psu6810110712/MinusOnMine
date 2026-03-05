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
        self.max_capacity = 20
        self.current_capacity = 0
        
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
        ore_pool = []
        for ore_id, ore_obj in ORES.items():
            ore_pool.append((ore_id, ore_obj.weight))

        self.grid_map = []
        for y in range(self.grid_height):
            row = []
            for x in range(self.grid_width):
                
                center_px = (x * 120) + 60
                center_py = (y * 120) + 60

                # 1. เช็ก Blacklist ต้นไม้/ทางเดิน
                if (x, y) in self.forbidden_grids:
                    row.append(None)
                    continue # ข้ามไปทำช่องถัดไปเลย
                
                safe_margin = 55  # ระยะห่างจากน้ำ (ตัวเลขยิ่งเยอะ แร่งยิ่งห่างน้ำ)
                
                # สร้างจุดสแกน 5 จุด (ตรงกลาง, ซ้าย, ขวา, บน, ล่าง)
                scan_points = [
                    (center_px, center_py),
                    (center_px - safe_margin, center_py),
                    (center_px + safe_margin, center_py),
                    (center_px, center_py - safe_margin),
                    (center_px, center_py + safe_margin)
                ]
                
                is_near_water = False
                if hasattr(self, 'is_water_tile'):
                    for px, py in scan_points:
                        if self.is_water_tile(px, py):
                            is_near_water = True
                            break # ถ้าระยะแตะน้ำปุ๊บ สั่งยกเลิกทันที
                
                # ถ้าอยู่ใกล้ขอบน้ำเกินไป ให้ข้ามช่องนี้ไป
                if is_near_water:
                    row.append(None)
                else:
                    # 3. ถ้าเป็นพื้นที่ปลอดภัยจริงๆ ให้สุ่มเกิดแร่ 60%
                    if random.random() < 0.6:
                        ore = self._weighted_random_ore(ore_pool)
                        row.append(ore)
                    else:
                        row.append(None)
                        
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

    def add_to_inventory(self, ore_type):
        """Adds item to inventory if there is capacity. Returns True if successful."""
        if self.current_capacity >= self.max_capacity:
            return False # Backpack full
            
        if ore_type in self.inventory:
            self.inventory[ore_type] += 1
        else:
            self.inventory[ore_type] = 1
            
        self.current_capacity += 1
        return True
