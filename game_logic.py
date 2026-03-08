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
        self.forbidden_grids = [
            (11, 10), (13, 11), (11, 12), (13, 13), 
            (13, 14), (14, 14), (15, 14), (15, 13),
            (9, 9), (9, 10), (10, 10), (9, 11), (10, 11),
            (13, 10), (13, 9), (15, 11), (16, 12), (10, 9),
            (10, 10), (10, 11) 
            ]
        
        self.grid_map = []   # 2D list: None = ว่าง, "stone"/"coal"/... = แร่
        self.generate_map()
        self.level = 1 # ระบบ level
        self.current_exp = 0
        self.exp_to_next_level = 100  # เริ่มต้นใช้ 100 EXP ในการขึ้นเลเวล 2


    def generate_map(self):
        """สุ่มวางแร่บน grid ให้เกิดเป็นกลุ่มๆ (Clustered)"""
        ore_pool = []
        for ore_id, ore_obj in ORES.items():
            ore_pool.append((ore_id, ore_obj.weight))

        # 1. เริ่มต้นด้วยแผนที่ว่างเปล่า (None)
        self.grid_map = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # 2. ฟังก์ชันเช็กว่าตรงนี้วางอะไรได้ไหม (ไม่ติดน้ำ ไม่ต้นไม้)
        def is_valid_tile(rx, ry):
            if rx < 0 or rx >= self.grid_width or ry < 0 or ry >= self.grid_height:
                return False
            if (rx, ry) in self.forbidden_grids:
                return False
                
            # เช็กจุดเกิด (Safe Spawn Zone) ให้ว่างเปล่าเสมอ
            # จุดเกิดคือพิกัด Pixel (1000, 800) -> Grid ประมาณ (8, 6)
            spawn_x, spawn_y = int(1000/120), int(800/120)
            if abs(rx - spawn_x) <= 2 and abs(ry - spawn_y) <= 2:
                return False # ในระยะ 5x5 รอบจุดเกิด ห้ามมีของแร่
            
            # เช็กน้ำ (Water)
            center_px = (rx * 120) + 60
            center_py = (ry * 120) + 60
            safe_margin = 55
            scan_points = [
                (center_px, center_py),
                (center_px - safe_margin, center_py), (center_px + safe_margin, center_py),
                (center_px, center_py - safe_margin), (center_px, center_py + safe_margin)
            ]
            if hasattr(self, 'is_water_tile'):
                for px, py in scan_points:
                    if self.is_water_tile(px, py):
                        return False
            return True

        # 3. สุ่มหา "จุดศูนย์กลาง" (Seeds) ของแต่ละกลุ่มแร่
        num_clusters = 15  # จำนวนกลุ่มแร่ในแผนที่
        for _ in range(num_clusters):
            seed_x = random.randint(0, self.grid_width - 1)
            seed_y = random.randint(0, self.grid_height - 1)
            
            if not is_valid_tile(seed_x, seed_y) or self.grid_map[seed_y][seed_x] is not None:
                continue # หาที่ลงไม่ได้ ข้ามไป
                
            # สุ่มชนิดแร่ที่จะเกิดในกลุ่มนี้
            cluster_ore_type = self._weighted_random_ore(ore_pool)
            
            # วางจุดศูนย์กลาง
            self.grid_map[seed_y][seed_x] = cluster_ore_type
            
            # 4. ขยายกลุ่ม (Grow) รอบๆ จุดศูนย์กลาง
            cluster_size = random.randint(3, 8) # รัศมีการเติบโตหรือจำนวนบล็อกในกลุ่ม
            tiles_to_process = [(seed_x, seed_y)]
            processed_count = 1
            
            while tiles_to_process and processed_count < cluster_size:
                # หยิบ tile มาแพร่เชื้อ
                curr_x, curr_y = tiles_to_process.pop(0)
                
                # เช็ก 4 ทิศ (บน ล่าง ซ้าย ขวา)
                neighbors = [(curr_x, curr_y-1), (curr_x, curr_y+1), (curr_x-1, curr_y), (curr_x+1, curr_y)]
                random.shuffle(neighbors) # สุ่มลำดับทิศทางให้ดูเป็นธรรมชาติ
                
                for nx, ny in neighbors:
                    if is_valid_tile(nx, ny) and self.grid_map[ny][nx] is None:
                        # มีโอกาส 70% ที่จะลามไปช่องนี้
                        if random.random() < 0.70:
                            self.grid_map[ny][nx] = cluster_ore_type
                            tiles_to_process.append((nx, ny))
                            processed_count += 1
                            if processed_count >= cluster_size:
                                break

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

    def add_exp(self, amount):
        """เพิ่ม EXP และเช็กการอัปเลเวล คืนค่า True ถ้ามีการอัปเลเวล"""
        self.current_exp += amount
        leveled_up = False
        
        # เช็กว่า EXP ทะลุหลอดไหม (ใช้ while เผื่อได้ EXP ทีเดียวเยอะๆ แล้วเลเวลอัป 2 ขั้น)
        while self.current_exp >= self.exp_to_next_level:
            self.current_exp -= self.exp_to_next_level
            self.level += 1
            # คำนวณหลอด EXP ถัดไปให้ใช้เยอะขึ้น (เช่น เลเวล * 100)
            self.exp_to_next_level = self.level * 100
            leveled_up = True
            
        return leveled_up
