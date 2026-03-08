from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.animation import Animation

from game_logic import GameState
from game_data import ORES


class PlayerWidget(Widget):
    image_source = StringProperty("assets/sprites/player/movement/down/1.png")
    render_size = ListProperty([100, 100])
    render_offset = ListProperty([0, 0])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = {
            "up": [f"assets/sprites/player/movement/up/{i}.png" for i in range(1, 10)],
            "down": [f"assets/sprites/player/movement/down/{i}.png" for i in range(1, 10)],
            "left": [f"assets/sprites/player/movement/left/{i}.png" for i in range(1, 10)],
            "right": [f"assets/sprites/player/movement/right/{i}.png" for i in range(1, 10)],
        }
        self.attack_frames = {
            "up": [f"assets/sprites/player/attack/up/{i}.png" for i in range(6)],
            "down": [f"assets/sprites/player/attack/down/{i}.png" for i in range(6)],
            "left": [f"assets/sprites/player/attack/left/{i}.png" for i in range(6)],
            "right": [f"assets/sprites/player/attack/right/{i}.png" for i in range(6)],
        }
        
        # Original sprite sizes for the attack animation frames
        self.attack_frame_sizes = {
            "down": [(39, 52), (47, 51), (46, 49), (55, 49), (81, 68), (76, 65)],
            "up": [(39, 48), (47, 48), (45, 48), (58, 49), (79, 67), (77, 64)],
            "left": [(55, 50), (31, 48), (36, 50), (57, 50), (93, 50), (91, 50)],
            "right": [(55, 50), (31, 48), (36, 50), (57, 50), (93, 50), (91, 50)]
        }
        
        # Base scale to map original 64x65 walk frame to our 100x100 box
        # Scale X = 100 / 64 = 1.5625
        # Scale Y = 100 / 65 = 1.538
        
        self.current_frame = 0
        self.is_moving = False
        self.is_mining = False
        self.direction = "down"
        
        # Timers
        self.anim_timer = 0.0
        self.anim_speed = 0.08
        self.mine_timer = 0.0
        self.mine_speed = 0.05

    def update_animation(self, dt):
        # 1. Handle Mining Animation first (Priority)
        if self.is_mining:
            # Get original sprite size for current frame
            orig_w, orig_h = self.attack_frame_sizes[self.direction][self.current_frame]
            
            # Scale it to match the standard 100x100 walk frame (walk frame orig is ~64x65)
            # We enforce ratio: width * (100/64), height * (100/65)
            scaled_w = orig_w * 1.5625
            scaled_h = orig_h * 1.538
            
            self.render_size = [scaled_w, scaled_h]
            
            # Offset to keep it centered horizontally and anchored at the feet
            # Center X: (100 - scaled_w) / 2
            # Offset Y: 0 (keep feet aligned)
            offset_x = (100 - scaled_w) / 2.0
            
            # For some attacks (like swinging up/down), the sprite might extend above or below. 
            # We align the bottom of the bounding box if the sprite got taller.
            # Default walk is 65 tall -> scaled to 100. If hit is 68 -> scaled to 104.6.
            # We subtract the difference to keep coordinates grounded.
            offset_y = 0.0
            
            self.render_offset = [offset_x, offset_y]
            
            self.mine_timer += dt
            if self.mine_timer >= self.mine_speed:
                self.mine_timer = 0.0
                self.current_frame += 1
                
                # Check if animation finished (6 frames: 0 to 5)
                if self.current_frame > 5:
                    self.is_mining = False
                    self.current_frame = 0
                    self.image_source = self.frames[self.direction][0]  # Back to idle
                    self.render_size = [100, 100]
                    self.render_offset = [0, 0]
                else:
                    self.image_source = self.attack_frames[self.direction][self.current_frame]
            return

        self.render_size = [100, 100]
        self.render_offset = [0, 0]

        # 2. Handle Movement Animation
        if not self.is_moving:
            self.current_frame = 0
            self.image_source = self.frames[self.direction][0]
            return

        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0.0
            self.current_frame = (self.current_frame + 1) % 9
            self.image_source = self.frames[self.direction][self.current_frame]


class OreBlock(Widget):
    """Widget representing a single minable ore block on the map."""
    def __init__(self, grid_x, grid_y, ore_type, **kwargs):
        super().__init__(**kwargs)
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.ore_type = ore_type
        
        ore_data = ORES.get(self.ore_type)
        self.color = (1, 1, 1, 1) 
        self.image_source = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""

        self.size_hint = (None, None)
        self.size = (120, 120)  # ขนาดยังคงเป็น 120x120 เพื่อให้ระยะการขุดและชนยังเท่าเดิม
        self.pos = (self.grid_x * 120, self.grid_y * 120)

        with self.canvas:
            Color(*self.color)
            
            # --- กำหนดขนาดแร่ให้เล็กลง (เช่น 50x50) ---
            visual_size = 80  # ขยายให้ใหญ่ขึ้นจาก 40 เป็น 80
            # คำนวณจุดกึ่งกลางของช่อง 120x120 (ให้อยู่ตรงกลางกริด)
            offset = (120 - visual_size) / 2  
            
            # 1. วาดเงาดำๆ ใต้แร่เพื่อมิติ
            Color(0, 0, 0, 0.3)
            Ellipse(
                pos=(self.pos[0] + offset + 5, self.pos[1] + offset - 10),
                size=(visual_size - 10, visual_size * 0.4)
            )
            
            # 2. วาดตัวภาพแร่
            Color(*self.color)
            if self.image_source:
                self.rect = Rectangle(
                    pos=(self.pos[0] + offset, self.pos[1] + offset), 
                    size=(visual_size, visual_size), 
                    source=self.image_source
                )
            else:
                fallback_color = ore_data.color if ore_data else (1, 1, 1, 1)
                Color(*fallback_color)
                self.rect = Rectangle(
                    pos=(self.pos[0] + offset, self.pos[1] + offset), 
                    size=(visual_size, visual_size)
                )
    def mine(self):
        """Called when the block is mined. Removes itself from the parent."""
        if self.parent:
            self.parent.remove_widget(self)


class ItemDrop(Widget):
    """Widget representing a dropped item flying towards the player"""
    def __init__(self, start_pos, target_player, game_state, map_screen, ore_type, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (40, 40) # Smaller than a block
        self.pos = start_pos
        self.ore_type = ore_type
        self.game_state = game_state
        self.target_player = target_player
        self.map_screen = map_screen

        ore_data = ORES.get(self.ore_type)
        self.image_source = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""

        with self.canvas:
            Color(1, 1, 1, 1)
            if self.image_source:
                self.rect = Rectangle(pos=self.pos, size=self.size, source=self.image_source)
            else:
                fallback_color = ore_data.color if ore_data else (1, 1, 1, 1)
                Color(*fallback_color)
                self.rect = Rectangle(pos=self.pos, size=self.size)

        # Update rect position constantly when moving
        self.bind(pos=self.update_canvas)

    def update_canvas(self, *args):
        self.rect.pos = self.pos

    def animate_to_player(self):
        """Starts the animation flying towards the player widget"""
        target_x = self.target_player.x + (self.target_player.width / 2) - (self.width / 2)
        target_y = self.target_player.y + (self.target_player.height / 2) - (self.height / 2)
        
        anim = Animation(x=target_x, y=target_y, duration=0.4, t='in_out_quad')
        anim.bind(on_complete=self.on_animation_complete)
        anim.start(self)

    def on_animation_complete(self, *args):
        # 1. Add to inventory
        if self.ore_type in self.game_state.inventory:
            self.game_state.inventory[self.ore_type] += 1
        else:
            self.game_state.inventory[self.ore_type] = 1
            
        print(f"Collected {self.ore_type}! Inventory: {self.game_state.inventory}")
        
        # 2. แจก EXP ตามชนิดแร่
        exp_rewards = {
            'stone': 10,
            'coal': 15,
            'copper': 20,
            'iron': 35,
            'gold': 50
        }
        # ดึงค่า EXP ถ้าไม่มีแร่นี้ในดิกชันนารีให้ 10 EXP เป็นค่าเริ่มต้น
        exp_gained = exp_rewards.get(self.ore_type, 10) 
        
        # สั่งบวก EXP เข้า GameState
        is_level_up = self.game_state.add_exp(exp_gained)
        
        if is_level_up:
            print(f"🎉 LEVEL UP! ตอนนี้เลเวล {self.game_state.level} แล้ว! 🎉")
            
        # สั่งอัปเดตหน้าจอ UI
        self.map_screen.update_hud()
        
        # Delete itself (โค้ดลบรูปแร่ทิ้งเหมือนเดิม)
        if self.parent:
            self.parent.remove_widget(self)
        # Delete itself
        if self.parent:
            self.parent.remove_widget(self)
        
        # Update UI if inventory is open
        # We can trigger an update by firing an event or just calling a global or parent method
        # For simplicity, we just check if grandparent is MapScreen (or just let the user toggle to refresh)
        # We can let the toggle handle the refresh to keep it simple.


class InventorySlot(Widget):
    """A visual slot in the inventory holding an item icon and its count."""
    item_image = StringProperty("")
    item_count = StringProperty("0")

    def __init__(self, ore_type, count, **kwargs):
        super().__init__(**kwargs)
        self.ore_type = ore_type
        self.item_count = str(count)
        
        ore_data = ORES.get(self.ore_type)
        self.item_image = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""

class CameraController:
    def __init__(self, zoom=1.0):
        self.zoom = max(1.0, float(zoom))
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, player_pos, player_size, viewport_size, world_size):
        player_x, player_y = player_pos
        player_w, player_h = player_size
        view_w, view_h = viewport_size
        world_w, world_h = world_size

        player_cx = player_x + (player_w / 2.0)
        player_cy = player_y + (player_h / 2.0)
        target_x = (view_w / 2.0) - (player_cx * self.zoom)
        target_y = (view_h / 2.0) - (player_cy * self.zoom)

        scaled_world_w = world_w * self.zoom
        scaled_world_h = world_h * self.zoom

        if scaled_world_w <= view_w:
            self.offset_x = (view_w - scaled_world_w) / 2.0
        else:
            min_x = view_w - scaled_world_w
            self.offset_x = min(0.0, max(min_x, target_x))

        if scaled_world_h <= view_h:
            self.offset_y = (view_h - scaled_world_h) / 2.0
        else:
            min_y = view_h - scaled_world_h
            self.offset_y = min(0.0, max(min_y, target_y))

        return self.offset_x, self.offset_y

    def visible_world_rect(self, viewport_size, world_size):
        view_w, view_h = viewport_size
        world_w, world_h = world_size

        visible_w = view_w / self.zoom
        visible_h = view_h / self.zoom

        if world_w <= visible_w:
            cam_x = 0.0
            cam_w = world_w
        else:
            cam_x = -self.offset_x / self.zoom
            cam_x = min(world_w - visible_w, max(0.0, cam_x))
            cam_w = visible_w

        if world_h <= visible_h:
            cam_y = 0.0
            cam_h = world_h
        else:
            cam_y = -self.offset_y / self.zoom
            cam_y = min(world_h - visible_h, max(0.0, cam_y))
            cam_h = visible_h

        return cam_x, cam_y, cam_w, cam_h


class MinimapRenderer:
    def __init__(self, padding=4, line_width=1.2, min_dot=6, max_dot=12):
        self.padding = padding
        self.line_width = line_width
        self.min_dot = min_dot
        self.max_dot = max_dot

    def draw(self, widget, world_size, camera_rect, player_pos, background_source):
        world_w, world_h = world_size
        cam_x, cam_y, cam_w, cam_h = camera_rect
        player_x, player_y = player_pos

        map_draw_w = max(1, widget.width - self.padding * 2)
        map_draw_h = max(1, widget.height - self.padding * 2)
        base_x = widget.x + self.padding
        base_y = widget.y + self.padding

        scale_x = map_draw_w / world_w
        scale_y = map_draw_h / world_h

        widget.canvas.after.clear()
        with widget.canvas.after:
            Color(1, 1, 1, 1)
            Rectangle(pos=(base_x, base_y), size=(map_draw_w, map_draw_h), source=background_source)

            cam_mx = base_x + (cam_x * scale_x)
            cam_my = base_y + (cam_y * scale_y)
            cam_mw = min(map_draw_w, cam_w * scale_x)
            cam_mh = min(map_draw_h, cam_h * scale_y)

            cam_mx = min(base_x + map_draw_w - cam_mw, max(base_x, cam_mx))
            cam_my = min(base_y + map_draw_h - cam_mh, max(base_y, cam_my))

            Color(1, 1, 1, 0.8)
            Line(rectangle=(cam_mx, cam_my, cam_mw, cam_mh), width=self.line_width)

            player_mx = base_x + (player_x * scale_x)
            player_my = base_y + (player_y * scale_y)
            dot_size = max(self.min_dot, min(self.max_dot, map_draw_w * 0.03))

            Color(1, 0.2, 0.2, 1)
            Ellipse(
                pos=(player_mx - dot_size / 2, player_my - dot_size / 2),
                size=(dot_size, dot_size),
            )


class MenuScreen(Screen):
    pass


class MiningScreen(Screen):
    def new_map(self):
        pass


class MapScreen(Screen):
    camera_zoom = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.move_speed = 200
        self.camera = CameraController(zoom=self.camera_zoom)
        self.minimap_renderer = MinimapRenderer()
        self.game_state = GameState()
        self.ore_blocks_dict = {}  # (grid_x, grid_y) -> OreBlock instance
        self.bind(camera_zoom=self.on_camera_zoom)

    def on_enter(self):
        player = self.ids.player_character
        world = self.ids.world_layer
        player.x = (world.width - player.width) / 2.0
        player.y = (world.height - player.height) / 2.0

        self.render_initial_map()

        Window.bind(on_key_down=self.on_keyboard_down)
        Window.bind(on_key_up=self.on_keyboard_up)
        self.game_loop = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def render_initial_map(self):
        """Draws the ore blocks on the world layer based on game_state.grid_map"""
        world = self.ids.world_layer
        
        # Clear existing blocks if we re-enter the screen
        for block in self.ore_blocks_dict.values():
            if block.parent:
                block.parent.remove_widget(block)
        self.ore_blocks_dict.clear()

        # Iterate through the grid and instantiate OreBlocks
        for y, row in enumerate(self.game_state.grid_map):
            for x, cell in enumerate(row):
                if cell is not None:  # There is an ore here
                    block = OreBlock(grid_x=x, grid_y=y, ore_type=cell)
                    self.ore_blocks_dict[(x, y)] = block
                    # Add to world layer. We add it but want player to render on top
                    # so we insert at the back of the widget tree (index > player index)
                    world.add_widget(block, index=len(world.children))

    def toggle_inventory(self):
        overlay = self.ids.inventory_overlay
        if overlay.disabled:
             # Open Inventory
             overlay.opacity = 1
             overlay.disabled = False
             self.update_inventory_ui()
        else:
             # Close Inventory
             overlay.opacity = 0
             overlay.disabled = True

    def update_hud(self):
        """อัปเดตข้อความ Level และ EXP บนหน้าจอ"""
        self.ids.level_label.text = f"Lv. {self.game_state.level}"
        self.ids.exp_label.text = f"EXP: {self.game_state.current_exp} / {self.game_state.exp_to_next_level}"

    def update_inventory_ui(self):
        grid = self.ids.inventory_grid
        grid.clear_widgets()
        
        # Sort inventory by quantity or just iterate
        for ore_type, count in self.game_state.inventory.items():
            if count > 0:
                slot = InventorySlot(ore_type=ore_type, count=count)
                grid.add_widget(slot)

    def on_leave(self):
        Window.unbind(on_key_down=self.on_keyboard_down)
        Window.unbind(on_key_up=self.on_keyboard_up)
        if hasattr(self, "game_loop"):
            self.game_loop.cancel()
        self.keys_pressed.clear()

    def on_camera_zoom(self, _instance, value):
        self.camera.zoom = max(1.0, float(value))

    def on_keyboard_down(self, _window, key, _scancode, _codepoint, _modifiers):
        # Ignore input if inventory is open, except for closing it
        overlay = self.ids.inventory_overlay
        if not overlay.disabled:
            if _codepoint == 'i' or key == 9: # 'i' or Tab
                self.toggle_inventory()
            return

        self.keys_pressed.add(key)
        
        # Handle 'i' key for inventory toggle
        if _codepoint == 'i' or key == 9:
            self.keys_pressed.discard(key) # Don't get stuck moving
            self.ids.player_character.is_moving = False
            self.toggle_inventory()
            return
            
        # Handle 'E' key for mining (key code 101 or the actual character 'e')
        if key == 101 or _codepoint == 'e':
            player = self.ids.player_character
            if not player.is_mining:
                self.mine_action()

        if _codepoint == 'u' or key == 117:
            self.keys_pressed.discard(key)
            self.ids.player_character.is_moving = False
            self.toggle_upgrade_menu()
            return

        # Dev Tool: กดปุ่ม 'P' เพื่อดูพิกัดที่ตัวละครยืนอยู่
        #if _codepoint == 'p' or key == 112:
        #    player = self.ids.player_character
           # หาจุดกึ่งกลางของตัวละคร
        #    player_cx = player.x + (player.width / 2.0)
        #    player_cy = player.y + (player.height / 2.0)
            
            # แปลงเป็นพิกัด Grid
        #    grid_x = int(player_cx / 120)
        #    grid_y = int(player_cy / 120)
        #    print(f"📍 ตัวละครยืนอยู่ที่พิกัด: ({grid_x}, {grid_y})")

    def mine_action(self):
        player = self.ids.player_character
        
        # Trigger animation state
        player.is_mining = True
        player.is_moving = False
        player.current_frame = 0
        player.mine_timer = 0.0
        
        # Pre-set first frame size immediately to prevent single frame flicker
        orig_w, orig_h = player.attack_frame_sizes[player.direction][0]
        scaled_w = orig_w * 1.5625
        scaled_h = orig_h * 1.538
        player.render_size = [scaled_w, scaled_h]
        player.render_offset = [(100 - scaled_w) / 2.0, 0]
        
        # 1. Determine the target coordinate based on player center and direction
        player_cx = player.x + (player.width / 2.0)
        player_cy = player.y + (player.height / 2.0)
        
        target_x = player_cx
        target_y = player_cy
        
        # Grid tiles are 120x120. Offset by 80 to "reach" into the next tile
        reach_distance = 80
        if player.direction == "up":
            target_y += reach_distance
        elif player.direction == "down":
            target_y -= reach_distance
        elif player.direction == "left":
            target_x -= reach_distance
        elif player.direction == "right":
            target_x += reach_distance
            
        # 2. Convert target pixel coordinates to grid coordinates
        grid_x = int(target_x / 120)
        grid_y = int(target_y / 120)
        
        # Check boundaries
        if 0 <= grid_x < self.game_state.grid_width and 0 <= grid_y < self.game_state.grid_height:
            # 3. Check if there is a block there
            if (grid_x, grid_y) in self.ore_blocks_dict:
                block = self.ore_blocks_dict[(grid_x, grid_y)]
                ore_type = block.ore_type
                
                # Update visual
                block.mine()
                del self.ore_blocks_dict[(grid_x, grid_y)]
                
                # Update GameState backend
                self.game_state.grid_map[grid_y][grid_x] = None
                
                # Add to inventory
                # We spawn an item drop which handles adding to inventory when animation completes
                world = self.ids.world_layer
                drop_x = grid_x * 120 + 40
                drop_y = grid_y * 120 + 40
                
                drop = ItemDrop(
                    start_pos=(drop_x, drop_y),
                    target_player=player,
                    game_state=self.game_state,
                    ore_type=ore_type,
                    map_screen=self
                )
                world.add_widget(drop) # Display on top of ground 
                drop.animate_to_player()
                
                print(f"Mined {ore_type} at ({grid_x}, {grid_y})! Dropping item...")

    def on_keyboard_up(self, _window, key, _scancode):
        self.keys_pressed.discard(key)

    def update(self, dt):
        # Don't update player movement if inventory is open
        if not self.ids.inventory_overlay.disabled:
            return
            
        step = self.move_speed * dt
        player = self.ids.player_character
        world = self.ids.world_layer

        new_x = player.x
        new_y = player.y
        is_moving_now = False

        # Can only move if not currently mining
        if not player.is_mining:
            if 119 in self.keys_pressed or 273 in self.keys_pressed:  # W or Up
                new_y += step
                player.direction = "up"
                is_moving_now = True
            elif 115 in self.keys_pressed or 274 in self.keys_pressed:  # S or Down
                new_y -= step
                player.direction = "down"
                is_moving_now = True

            if 97 in self.keys_pressed or 276 in self.keys_pressed:  # A or Left
                new_x -= step
                player.direction = "left"
                is_moving_now = True
            elif 100 in self.keys_pressed or 275 in self.keys_pressed:  # D or Right
                new_x += step
                player.direction = "right"
                is_moving_now = True

        player.is_moving = is_moving_now
        player.update_animation(dt)

        # --- World boundary clamping ---
        # ผูกขอบเขตแผนที่ให้พอดีกับตาราง Grid (ตารางละ 120px)
        max_x = (self.game_state.grid_width * 120) - player.width
        max_y = (self.game_state.grid_height * 120) - player.height
        
        if new_x < 0:
            new_x = 0
        elif new_x > max_x:
            new_x = max_x

        if new_y < 0:
            new_y = 0
        elif new_y > max_y:
            new_y = max_y

        # --- ระบบตรวจสอบการชน (หิน/แร่/สิ่งกีดขวาง) ---
        # ปรับ Hitbox ตัวละครให้พอดีช่วงล่างของ Sprite มากขึ้น
        inset_x = 35  # บีบด้านซ้ายขวาเข้ามา
        inset_y = 15  # บีบด้านบนล่าง (ให้หัวทับของได้นิดหน่อย)
        pw = player.width - inset_x * 2
        ph = player.height - inset_y * 2

        def hits_solid(px, py):
            """ตรวจสอบว่ากรอบของตัวละครทับซ้อนกับสิ่งกีดขวางหรือไม่"""
            gs = self.game_state
            left = px + inset_x
            right = px + inset_x + pw
            bottom = py + inset_y
            top = py + inset_y + ph
            
            # เช็กจุดทั้ง 4 มุม และจุดกึ่งกลางของกรอบตัวละคร
            for cx in [left, (left + right) / 2, right]:
                for cy in [bottom, (bottom + top) / 2, top]:
                    
                    # 1. เช็กการชนกับน้ำ 
                    if hasattr(gs, 'is_water_tile') and gs.is_water_tile(cx, cy):
                        return True
                        
                    # 2. เช็กการชนกับหินหรือแร่ (ดึงข้อมูลจาก Grid)
                    # แปลงพิกัด Pixel ให้เป็นพิกัด Grid (หารด้วยขนาดบล็อก 120)
                    grid_x = int(cx / 120)
                    grid_y = int(cy / 120)
                    
                    # ตรวจสอบว่าพิกัดยังอยู่ในขอบเขตแผนที่
                    if gs.grid_map[grid_y][grid_x] is not None:
                                # ==========================================
                                # อัปเดตใหม่: ปรับให้สมดุลกับ 80px Visual Size
                                # ==========================================
                                visual_size = 80 
                                offset = (120 - visual_size) / 2
                                
                                # --- ปรับระยะความชิดตรงนี้ครับ ---
                                # ยิ่งใส่เลขเยอะ ยิ่งเดินทะลุเข้าไปใกล้แร่ได้มากขึ้น
                                ore_inset_x = 10  # ยอมให้เดินซ้อนทับด้านซ้าย/ขวา ได้ 10 พิกเซล
                                ore_inset_y = 20  # ยอมให้ทับด้านบน/ล่าง ได้ลึกขึ้น (ตัวละครเดินบังโคนต้นแร่ได้)
                                
                                ore_left = (grid_x * 120) + offset + ore_inset_x
                                ore_right = (grid_x * 120) + offset + visual_size - ore_inset_x
                                ore_bottom = (grid_y * 120) + offset + ore_inset_y
                                ore_top = (grid_y * 120) + offset + visual_size - ore_inset_y
                                
                                # เช็กว่าจุดพิกัด เหยียบโดน Hitbox ที่ถูกบีบแล้วหรือไม่
                                if ore_left <= cx <= ore_right and ore_bottom <= cy <= ore_top:
                                    return True
                                
            return False

        # --- ใช้เทคนิค Wall Sliding (ให้เดินไถกำแพงได้ สมูธขึ้น) ---
        # 1. ทดสอบการขยับแกน X เดี่ยวๆ
        x_col = hits_solid(new_x, player.y)
        # 2. ทดสอบการขยับแกน Y เดี่ยวๆ
        y_col = hits_solid(player.x, new_y)
        # 3. ทดสอบขยับทั้ง 2 แกนพร้อมกัน (ทแยง)
        xy_col = hits_solid(new_x, new_y)

        # ตัดสินใจการเดิน
        if not xy_col:
            # เดินทแยงได้ปกติ
            pass
        elif not x_col and y_col:
            # ติดแกน Y แต่ X ว่าง -> ไถไปตามแกน X
            new_y = player.y
        elif not y_col and x_col:
            # ติดแกน X แต่ Y ว่าง -> ไถไปตามแกน Y
            new_x = player.x
        else:
            # ติดหมด ขยับไม่ได้เลย
            new_x = player.x
            new_y = player.y

        # อัปเดตตำแหน่งจริงของตัวละคร
        player.x = new_x
        player.y = new_y

        # --- Dynamic Z-Index Sorting (Depth Sorting) ---
        # นำ Widget ทั้งหมดใน world (ที่เป็น OreBlock/Player) มาเรียงลำดับวาดใหม่
        # โดยใครยึดแกน Y ต่ำกว่า (อยู่ด้านล่างจอ) ต้องวาดทีหลังเพื่อให้ทับคนอื่น
        # ป้องกันกระตุก: เรียงเฉพาะตอนที่มีการขยับเท่านั้น
        if is_moving_now:
            children = list(world.children)
            # เราจะไม่เรียง widget ที่อาจไม่ใช่ของบนพื้น (เช่น effect บางอย่าง)
            # แต่ปกติใน world ตอนนี้มีแค่ Player, OreBlock, ItemDrop
            # เรียงจากแกน y มาก ไป y น้อย (Kivy วาดจาก index 0 ไป -1)
            # ดังนั้นคน y มากสุด (อยู่ข้างบนสุด) วาดก่อน (index ต้นๆ)
            children.sort(key=lambda w: w.y, reverse=True)
            
            world.clear_widgets()
            for child in children:
                world.add_widget(child)

        # --- อัปเดตกล้องและ Minimap (ระบบเดิมของคุณ) ---
        world.x, world.y = self.camera.update(
            player_pos=(player.x, player.y),
            player_size=(player.width, player.height),
            viewport_size=(self.width, self.height),
            world_size=(world.width, world.height),
        )

        camera_rect = self.camera.visible_world_rect(
            viewport_size=(self.width, self.height),
            world_size=(world.width, world.height),
        )
        self.minimap_renderer.draw(
            widget=self.ids.minimap_widget,
            world_size=(world.width, world.height),
            camera_rect=camera_rect,
            player_pos=(player.x + player.width / 2.0, player.y + player.height / 2.0),
            background_source="ground.png",
        )
        # --- ตัวแปรสำหรับระบบอัปเกรด ---
        self.pickaxe_level = 1
        
        # ตารางราคาอัปเกรด (เลเวลถัดไป : {ชนิดแร่: จำนวนที่ใช้})
        self.upgrade_costs = {
            2: {"stone": 10},                 # อัปเป็น Lv.2 ใช้หิน 10 ก้อน
            3: {"stone": 20, "copper": 5},    # อัปเป็น Lv.3 ใช้หิน 20, ทองแดง 5
            4: {"copper": 20, "iron": 10},
            5: {"iron": 30, "gold": 5}
        }
    def toggle_upgrade_menu(self):
        """เปิด/ปิด หน้าต่างอัปเกรด"""
        overlay = self.ids.upgrade_overlay
        if overlay.disabled:
            overlay.opacity = 1
            overlay.disabled = False
            self.update_upgrade_ui()
        else:
            overlay.opacity = 0
            overlay.disabled = True

    def update_upgrade_ui(self):
        """อัปเดตข้อความราคาในหน้าจอ"""
        next_level = self.pickaxe_level + 1
        
        if next_level in self.upgrade_costs:
            costs = self.upgrade_costs[next_level]
            cost_text = "\n".join([f"- {req_amount} {ore.capitalize()}" for ore, req_amount in costs.items()])
            
            speed_text = f"Speed: {max(0.01, 0.05 - (self.pickaxe_level * 0.01)):.2f}s"
            self.ids.upgrade_info_label.text = f"Pickaxe Lv.{self.pickaxe_level}\n{speed_text}\n\nNext Level Cost:\n{cost_text}"
            self.ids.btn_buy_upgrade.disabled = False
            self.ids.btn_buy_upgrade.text = "UPGRADE NOW"
        else:
            self.ids.upgrade_info_label.text = f"Pickaxe Lv.{self.pickaxe_level}\nMAX LEVEL REACHED!"
            self.ids.btn_buy_upgrade.disabled = True
            self.ids.btn_buy_upgrade.text = "MAXED OUT"

    def buy_upgrade(self):
        """เมื่อกดปุ่มซื้ออัปเกรด"""
        next_level = self.pickaxe_level + 1
        if next_level not in self.upgrade_costs:
            return # เลเวลตันแล้ว

        costs = self.upgrade_costs[next_level]
        
        # 1. เช็กว่าแร่ในกระเป๋ามีพอจ่ายไหม?
        can_afford = True
        for ore, req_amount in costs.items():
            if self.game_state.inventory.get(ore, 0) < req_amount:
                can_afford = False
                break
                
        # 2. ถ้ามีแร่พอ ให้หักแร่และอัปเกรด
        if can_afford:
            for ore, req_amount in costs.items():
                self.game_state.inventory[ore] -= req_amount
                
            self.pickaxe_level += 1
            
            # --- หัวใจสำคัญ: ทำให้ขุดเร็วขึ้น! ---
            player = self.ids.player_character
            # ลดเวลาอนิเมชันตอนขุดลง (ยิ่งค่าน้อย ยิ่งสับจอบไว)
            player.mine_speed = max(0.01, player.mine_speed - 0.01) 
            
            print(f"Upgraded to Level {self.pickaxe_level}! New Speed: {player.mine_speed}")
            self.update_upgrade_ui() # รีเฟรชหน้าจอ
        else:
            # ถ้าแร่ไม่พอ ให้ปุ่มบอกใบ้
            self.ids.btn_buy_upgrade.text = "NOT ENOUGH ORES!"


class MinusOnMineApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(MiningScreen(name="mining"))
        sm.add_widget(MapScreen(name="map"))
        return sm


if __name__ == "__main__":
    MinusOnMineApp().run()
