import os
import time

def run(cmd):
    print("Running:", cmd)
    os.system(cmd)
    time.sleep(0.5)

# ----------------- COMMIT 1 -----------------
with open('game_logic.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'self.grid_map = []   # 2D list: None = ว่าง, "stone"/"coal"/... = แร่\n        self.generate_map()',
    'self.surface_map = []\n        self.underground_map = []\n        self.current_depth = 0  # 0 = Surface, 1 = Underground\n        self.generate_maps()'
)
src = src.replace(
    'self.exp_to_next_level = 100  # เริ่มต้นใช้ 100 EXP ในการขึ้นเลเวล 2\n\n\n    def generate_map(self):',
    'self.exp_to_next_level = 100  # เริ่มต้นใช้ 100 EXP ในการขึ้นเลเวล 2\n\n    @property\n    def grid_map(self):\n        """คืนค่าแผนที่ อิงตามความลึก (0: บนดิน, 1: ใต้ดิน)"""\n        return self.surface_map if self.current_depth == 0 else self.underground_map\n\n    def generate_maps(self):'
)
with open('game_logic.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add game_logic.py')
run('git commit -m "refactor: extract map array logic in GameState to support multiple map layers (Surface and Underground)"')

# ----------------- COMMIT 2 -----------------
with open('game_logic.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'self.grid_map = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]',
    'self.surface_map = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]\n        self.underground_map = [[None for _ in range(self.grid_width)] for _ in range(self.grid_height)]'
)
src = src.replace('self.grid_map[seed_y][seed_x]', 'self.underground_map[seed_y][seed_x]')
src = src.replace('self.grid_map[ny][nx]', 'self.underground_map[ny][nx]')
src = src.replace('self.grid_map[ry][path_x]', 'self.underground_map[ry][path_x]')
src = src.replace('self.grid_map[ry][path_x+1]', 'self.underground_map[ry][path_x+1]')
src = src.replace('self.grid_map[path_y][rx]', 'self.underground_map[path_y][rx]')
src = src.replace('self.grid_map[path_y+1][rx]', 'self.underground_map[path_y+1][rx]')
with open('game_logic.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add game_logic.py')
run('git commit -m "feat: restrict cellular automata ore generation exclusively to the Underground map layer"')

# ----------------- COMMIT 3 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
mine_entrance_code = """
class MineEntrance(Widget):
    \"\"\"Widget representing the stairs or hole leading down to the Underground map.\"\"\"
    def __init__(self, grid_x, grid_y, **kwargs):
        super().__init__(**kwargs)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.size_hint = (None, None)
        self.size = (120, 120)
        self.pos = (self.grid_x * 120, self.grid_y * 120)

        with self.canvas:
            visual_size = 90
            offset = (120 - visual_size) / 2
            
            # วาดกรอบทางลงเหมือง (สีน้ำตาล/เทาเข้ม)
            Color(0.4, 0.3, 0.2, 1)
            self.rect = Rectangle(
                pos=(self.pos[0] + offset, self.pos[1] + offset), 
                size=(visual_size, visual_size)
            )
            # เงาดำตรงกลางจำลองหลุมลึก
            Color(0, 0, 0, 0.8)
            self.inner_rect = Rectangle(
                pos=(self.pos[0] + offset + 15, self.pos[1] + offset + 15), 
                size=(visual_size - 30, visual_size - 30)
            )

class ItemDrop"""
src = src.replace('class ItemDrop', mine_entrance_code)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: implement MineEntrance widget class for visual representation on the map"')

# ----------------- COMMIT 4 -----------------
with open('game_logic.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'self.underground_map[path_y+1][rx] = None\n\n    def _weighted_random_ore',
    'self.underground_map[path_y+1][rx] = None\n\n        # 6. วางทางเข้าเหมืองบนแผนที่บนดิน (Surface Map)\n        # ให้ไว้ใกล้ๆ จุดเกิด สมมติว่าเป็นพิกัด (10, 8)\n        self.surface_map[8][10] = "entrance"\n\n    def _weighted_random_ore'
)
with open('game_logic.py', 'w', encoding='utf-8') as f: f.write(src)
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
replace_target = """                if cell is not None:  # There is an ore here
                    block = OreBlock(grid_x=x, grid_y=y, ore_type=cell)
                    self.ore_blocks_dict[(x, y)] = block"""
replace_with = """                if cell is not None:  
                    if cell == "entrance":
                        block = MineEntrance(grid_x=x, grid_y=y)
                    else:
                        block = OreBlock(grid_x=x, grid_y=y, ore_type=cell)
                    
                    self.ore_blocks_dict[(x, y)] = block"""
src = src.replace(replace_target, replace_with)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add game_logic.py main.py')
run('git commit -m "feat: spawn MineEntrance at a fixed location (e.g. near spawn) on the Surface map only"')

# ----------------- COMMIT 5 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'if (grid_x, grid_y) in self.ore_blocks_dict:\n                block = self.ore_blocks_dict[(grid_x, grid_y)]\n                ore_type = block.ore_type',
    'if (grid_x, grid_y) in self.ore_blocks_dict:\n                block = self.ore_blocks_dict[(grid_x, grid_y)]\n                \n                if isinstance(block, MineEntrance):\n                    print("Found Mine Entrance! Descending to Underground...")\n                    self.enter_mine()\n                    return\n                \n                ore_type = block.ore_type'
)
src = src.replace(
    'print(f"Mined {ore_type} at ({grid_x}, {grid_y})! Dropping item...")\n\n    def on_keyboard_up',
    'print(f"Mined {ore_type} at ({grid_x}, {grid_y})! Dropping item...")\n\n    def enter_mine(self):\n        # Placeholder for transitioning to underground\n        pass\n\n    def on_keyboard_up'
)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: add interaction detection (pressing E) to the MineEntrance bounding box"')

# ----------------- COMMIT 6 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'self.game_state = GameState()\n        self.ore_blocks_dict',
    'self.game_state = GameState()\n        self.surface_coords = (0, 0)\n        self.ore_blocks_dict'
)
src = src.replace(
    'def enter_mine(self):\n        # Placeholder for transitioning to underground\n        pass',
    'def enter_mine(self):\n        player = self.ids.player_character\n        \n        # 1. Save surface coordinates\n        self.surface_coords = (player.x, player.y)\n        \n        # 2. Change depth and reload map\n        self.game_state.current_depth = 1\n        self.render_initial_map()\n        \n        print("Descended to the mine layer.")'
)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: add state tracking for current depth (Surface=0, Mine=1) and map reloading logic to MapScreen"')

# ----------------- COMMIT 7 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'self.render_initial_map()\n        \n        print("Descended to the mine layer.")',
    'self.render_initial_map()\n        \n        # 3. Spawn player at a safe starting point in the mine (e.g. center)\n        world = self.ids.world_layer\n        player.x = (world.width - player.width) / 2.0\n        player.y = (world.height - player.height) / 2.0\n        \n        print("Descended to the mine layer.")'
)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: physically move player to a new underground starting coordinate when descending"')

# ----------------- COMMIT 8 -----------------
with open('minusonmine.kv', 'r', encoding='utf-8') as f:
    src = f.read()
kv_btn = """        Button:
            text: 'Back to Menu'
            font_name: 'assets/fonts/PixelifySans-Bold.ttf'
            size_hint: None, None
            size: 150, 50
            pos_hint: {'right': 0.98, 'top': 0.98}
            background_color: 0.8, 0.2, 0.2, 1
            on_press: root.manager.current = 'menu'

        # ปุ่มออกจากเหมือง (ซ่อนไว้จนกว่าจะกดลงเหมือง)
        Button:
            id: btn_exit_mine
            text: 'Exit Mine'
            font_name: 'assets/fonts/PixelifySans-Bold.ttf'
            size_hint: None, None
            size: 150, 50
            pos_hint: {'right': 0.98, 'top': 0.88}
            background_color: 0.2, 0.2, 0.8, 1
            opacity: 0
            disabled: True
            on_press: root.exit_mine()"""
src = src.replace("""        Button:
            text: 'Back to Menu'
            font_name: 'assets/fonts/PixelifySans-Bold.ttf'
            size_hint: None, None
            size: 150, 50
            pos_hint: {'right': 0.98, 'top': 0.98}
            background_color: 0.8, 0.2, 0.2, 1
            on_press: root.manager.current = 'menu'""", kv_btn)
with open('minusonmine.kv', 'w', encoding='utf-8') as f: f.write(src)
run('git add minusonmine.kv')
run('git commit -m "feat: add \'Exit Mine\' Button widget to the top-right of MapScreen HUD"')

# ----------------- COMMIT 9 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'player.y = (world.height - player.height) / 2.0\n        \n        print("Descended to the mine layer.")',
    'player.y = (world.height - player.height) / 2.0\n        \n        # 4. Show the "Exit Mine" button\n        btn = self.ids.btn_exit_mine\n        btn.opacity = 1\n        btn.disabled = False\n        \n        print("Descended to the mine layer.")\n\n    def exit_mine(self):\n        # Placeholder\n        pass'
)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: dynamically toggle \'Exit Mine\' button visibility based on the current depth layer"')

# ----------------- COMMIT 10 -----------------
with open('main.py', 'r', encoding='utf-8') as f:
    src = f.read()
src = src.replace(
    'def exit_mine(self):\n        # Placeholder\n        pass',
    'def exit_mine(self):\n        player = self.ids.player_character\n        \n        # 1. Change depth back to Surface and reload map\n        self.game_state.current_depth = 0\n        self.render_initial_map()\n        \n        # 2. Restore previous surface coordinates so player appears exactly where they descended\n        player.x, player.y = self.surface_coords\n        \n        # 3. Hide the "Exit Mine" button\n        btn = self.ids.btn_exit_mine\n        btn.opacity = 0\n        btn.disabled = True\n        \n        print("Returned to the surface.")'
)
with open('main.py', 'w', encoding='utf-8') as f: f.write(src)
run('git add main.py')
run('git commit -m "feat: implement \'Exit Mine\' button callback to transition player back to the Surface and restore previous coordinates"')

print("Done committing!")
