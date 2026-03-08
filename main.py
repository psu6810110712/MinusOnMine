from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.animation import Animation
from kivy.factory import Factory

from kivy.metrics import dp
from game_logic import GameState
from game_data import ORES
from widgets import FloatText, NPCWidget, SellItemRow, SellOverlay, ExplosionEffect

# Registering custom widgets with the Factory so that the .kv file can find them
Factory.register('SellOverlay', cls=SellOverlay)
Factory.register('SellItemRow', cls=SellItemRow)
Factory.register('NPCWidget', cls=NPCWidget)
Factory.register('FloatText', cls=FloatText)
Factory.register('ExplosionEffect', cls=ExplosionEffect)


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
        self.size = (120, 120)  # à¸‚à¸™à¸²à¸”à¸¢à¸±à¸‡à¸„à¸‡à¹€à¸›à¹‡à¸™ 120x120 à¹€à¸žà¸·à¹ˆà¸­à¹ƒà¸«à¹‰à¸£à¸°à¸¢à¸°à¸à¸²à¸£à¸‚à¸¸à¸”à¹à¸¥à¸°à¸Šà¸™à¸¢à¸±à¸‡à¹€à¸—à¹ˆà¸²à¹€à¸”à¸´à¸¡
        self.pos = (self.grid_x * 120, self.grid_y * 120)

        with self.canvas:
            Color(*self.color)
            
            # --- à¸à¸³à¸«à¸™à¸”à¸‚à¸™à¸²à¸”à¹à¸£à¹ˆà¹ƒà¸«à¹‰à¹€à¸¥à¹‡à¸à¸¥à¸‡ (à¹€à¸Šà¹ˆà¸™ 50x50) ---
            visual_size = 40
            # à¸„à¸³à¸™à¸§à¸“à¸ˆà¸¸à¸”à¸à¸¶à¹ˆà¸‡à¸à¸¥à¸²à¸‡à¸‚à¸­à¸‡à¸Šà¹ˆà¸­à¸‡ 120x120 (à¹ƒà¸«à¹‰à¸­à¸¢à¸¹à¹ˆà¸•à¸£à¸‡à¸à¸¥à¸²à¸‡à¸à¸£à¸´à¸”)
            offset = (120 - visual_size) / 2  
            
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
        added = self.game_state.add_to_inventory(self.ore_type)
        if added:
            print(f"Collected {self.ore_type}! Inventory: {self.game_state.inventory}")
        else:
            print(f"Inventory full! Cannot collect {self.ore_type}")
        
        # 2. à¹à¸ˆà¸ EXP à¸•à¸²à¸¡à¸Šà¸™à¸´à¸”à¹à¸£à¹ˆ
        exp_rewards = {
            'stone': 10,
            'coal': 15,
            'copper': 20,
            'iron': 35,
            'gold': 50
        }
        # à¸”à¸¶à¸‡à¸„à¹ˆà¸² EXP à¸–à¹‰à¸²à¹„à¸¡à¹ˆà¸¡à¸µà¹à¸£à¹ˆà¸™à¸µà¹‰à¹ƒà¸™à¸”à¸´à¸à¸Šà¸±à¸™à¸™à¸²à¸£à¸µà¹ƒà¸«à¹‰ 10 EXP à¹€à¸›à¹‡à¸™à¸„à¹ˆà¸²à¹€à¸£à¸´à¹ˆà¸¡à¸•à¹‰à¸™
        exp_gained = exp_rewards.get(self.ore_type, 10) 
        
        # à¸ªà¸±à¹ˆà¸‡à¸šà¸§à¸ EXP à¹€à¸‚à¹‰à¸² GameState
        is_level_up = self.game_state.add_exp(exp_gained)
        
        if is_level_up:
            print(f"ðŸŽ‰ LEVEL UP! à¸•à¸­à¸™à¸™à¸µà¹‰à¹€à¸¥à¹€à¸§à¸¥ {self.game_state.level} à¹à¸¥à¹‰à¸§! ðŸŽ‰")
            
        # à¸ªà¸±à¹ˆà¸‡à¸­à¸±à¸›à¹€à¸”à¸•à¸«à¸™à¹‰à¸²à¸ˆà¸­ UI
        self.map_screen.update_hud()
        
        # Delete itself (à¹‚à¸„à¹‰à¸”à¸¥à¸šà¸£à¸¹à¸›à¹à¸£à¹ˆà¸—à¸´à¹‰à¸‡à¹€à¸«à¸¡à¸·à¸­à¸™à¹€à¸”à¸´à¸¡)
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
    ore_type = StringProperty("")

    def __init__(self, ore_type, count, parent_screen=None, **kwargs):
        super().__init__(**kwargs)
        self.ore_type = ore_type
        self.item_count = str(count)
        self.parent_screen = parent_screen
        
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
        
        # --- à¸£à¸°à¸šà¸šà¸­à¸±à¸›à¹€à¸à¸£à¸” (à¸¢à¹‰à¸²à¸¢à¸¡à¸²à¹„à¸§à¹‰à¸—à¸µà¹ˆà¸™à¸µà¹ˆà¹€à¸žà¸·à¹ˆà¸­à¹ƒà¸«à¹‰à¸„à¹ˆà¸²à¹„à¸¡à¹ˆà¸«à¸²à¸¢) ---
        self.pickaxe_level = 1
        self.upgrade_costs = {
            2: {"stone": 10},
            3: {"stone": 20, "copper": 5},
            4: {"copper": 20, "iron": 10},
            5: {"iron": 30, "gold": 5}
        }

    def on_enter(self):
        player = self.ids.player_character
        world = self.ids.world_layer
        player.x = (world.width - player.width) / 2.0
        player.y = (world.height - player.height) / 2.0
        
        # Spawn NPC slightly off center
        if not hasattr(self, 'npc'):
            self.npc = NPCWidget(pos=(player.x + 200, player.y + 200))
            world.add_widget(self.npc, index=len(world.children))

        self.render_initial_map()
        self.auto_use_torch_if_needed()
        self.update_hud()
        self.update_fog_overlay()

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

    def auto_use_torch_if_needed(self):
        if self.game_state.has_active_torch():
            return

        self.game_state.use_torch()

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

    def format_torch_time(self):
        total_seconds = max(0, int(self.game_state.torch_time_left))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def update_hud(self):
        self.ids.level_label.text = f"Lv. {self.game_state.level}"
        self.ids.exp_label.text = f"EXP: {self.game_state.current_exp} / {self.game_state.exp_to_next_level}"
        self.ids.hud_money_label.text = f"Money: ${int(self.game_state.money)}"
        self.ids.hud_torch_label.text = f"Torch: {self.game_state.torch_count} | {self.format_torch_time()}"

    def update_inventory_ui(self):
        # Update Header Labels
        cap_label = self.ids.inventory_capacity_label
        money_label = self.ids.inventory_money_label
        
        cap_label.text = f"Capacity: {self.game_state.current_capacity} / {self.game_state.max_capacity}"
        
        # We need to calculate total money from game_state
        # For this prototype, if money isn't tracked in GameState yet, we default to 0
        if not hasattr(self.game_state, 'money'):
            self.game_state.money = 0
            
        # Update capacity color (red if full)
        if self.game_state.current_capacity >= self.game_state.max_capacity:
            cap_label.color = (1, 0.3, 0.3, 1)
        else:
            cap_label.color = (0.8, 0.8, 0.8, 1)
            
        money_label.text = f"Money: ${self.game_state.money}"
    
        grid = self.ids.inventory_grid
        grid.clear_widgets()
        
        # Sort inventory by quantity or just iterate
        for ore_type, count in self.game_state.inventory.items():
            if count > 0:
                slot = InventorySlot(ore_type=ore_type, count=count, parent_screen=self)
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

        # Handle 'u' key for upgrades
        if _codepoint == 'u' or key == 117:
            self.keys_pressed.discard(key)
            self.ids.player_character.is_moving = False
            self.toggle_upgrade_menu()
            return

        # Handle 'F' key for NPC interaction
        if _codepoint == 'f' or key == 102:
            self.keys_pressed.discard(key)
            self.ids.player_character.is_moving = False
            self.interact_action()
            return

        # Dev Tool: à¸à¸”à¸›à¸¸à¹ˆà¸¡ 'P' à¹€à¸žà¸·à¹ˆà¸­à¸”à¸¹à¸žà¸´à¸à¸±à¸”à¸—à¸µà¹ˆà¸•à¸±à¸§à¸¥à¸°à¸„à¸£à¸¢à¸·à¸™à¸­à¸¢à¸¹à¹ˆ
        #if _codepoint == 'p' or key == 112:
        #    player = self.ids.player_character
           # à¸«à¸²à¸ˆà¸¸à¸”à¸à¸¶à¹ˆà¸‡à¸à¸¥à¸²à¸‡à¸‚à¸­à¸‡à¸•à¸±à¸§à¸¥à¸°à¸„à¸£
        #    player_cx = player.x + (player.width / 2.0)
        #    player_cy = player.y + (player.height / 2.0)
            
            # à¹à¸›à¸¥à¸‡à¹€à¸›à¹‡à¸™à¸žà¸´à¸à¸±à¸” Grid
        #    grid_x = int(player_cx / 120)
        #    grid_y = int(player_cy / 120)
        #    print(f"ðŸ“ à¸•à¸±à¸§à¸¥à¸°à¸„à¸£à¸¢à¸·à¸™à¸­à¸¢à¸¹à¹ˆà¸—à¸µà¹ˆà¸žà¸´à¸à¸±à¸”: ({grid_x}, {grid_y})")

    def interact_action(self):
        """Check distance to NPC and open Sell UI if close enough"""
        if not hasattr(self, 'npc'): return

        player = self.ids.player_character
        # Center of player
        px = player.x + (player.width / 2.0)
        py = player.y + (player.height / 2.0)
        
        # Center of NPC
        nx = self.npc.x + (self.npc.width / 2.0)
        ny = self.npc.y + (self.npc.height / 2.0)

        # Basic distance check (e.g. within 150 pixels)
        distance = ((px - nx)**2 + (py - ny)**2)**0.5
        
        if distance < 180:
            print("Talking to NPC...")
            self.toggle_sell_menu()
        else:
            print("NPC is too far away.")

    def toggle_sell_menu(self):
        """à¹€à¸›à¸´à¸”/à¸›à¸´à¸” à¸«à¸™à¹‰à¸²à¸•à¹ˆà¸²à¸‡à¸‚à¸²à¸¢à¸‚à¸­à¸‡"""
        overlay = self.ids.sell_overlay
        if overlay.disabled:
             overlay.opacity = 1
             overlay.disabled = False
             # Force overlay to front by re-adding it
             if overlay.parent:
                 overlay.parent.remove_widget(overlay)
             self.add_widget(overlay)
             self.update_sell_ui()
        else:
             overlay.opacity = 0
             overlay.disabled = True

    def update_sell_ui(self):
        """Populate the sell menu with current inventory"""
        container = self.ids.sell_items_container
        container.clear_widgets()
        
        has_items = False
        for ore_type, count in self.game_state.inventory.items():
            if count > 0:
                has_items = True
                ore_data = ORES.get(ore_type)
                price = ore_data.value if ore_data else 1
                row = SellItemRow(
                    ore_type=ore_type,
                    max_amount=count,
                    price_per_unit=price,
                    parent_menu=self
                )
                # Ensure height is rigidly set so Scrollview knows how big it is
                row.size_hint_y = None
                row.height = dp(80) 
                
                container.add_widget(row)

        if not has_items:
            empty_lbl = Label(
                text="You have nothing to sell.",
                font_name='assets/fonts/PixelifySans-Medium.ttf',
                font_size='20sp',
                color=(0.7, 0.7, 0.7, 1),
                size_hint_y=None,
                height=50
            )
            container.add_widget(empty_lbl)

        self.recalculate_total_sell()

    def recalculate_total_sell(self):
        """Calculate and update the total price label"""
        total = 0
        container = self.ids.sell_items_container
        for child in container.children:
            if isinstance(child, SellItemRow):
                total += child.subtotal
                
        self.ids.total_sell_label.text = f"Total Earned: ${total}"

    def confirm_sell(self):
        """Perform the transaction and close the menu"""
        container = self.ids.sell_items_container
        total_earned = 0
        items_sold = 0
        
        for child in container.children:
            if isinstance(child, SellItemRow) and child.current_selected_amount > 0:
                ore = child.ore_type
                amount = child.current_selected_amount
                earned = child.subtotal
                
                # Update GameState
                self.game_state.inventory[ore] -= amount
                self.game_state.current_capacity -= amount
                total_earned += earned
                items_sold += amount

        if total_earned > 0:
            self.game_state.money += total_earned
            print(f"Sold {items_sold} items for ${total_earned}!")
            
            # Show floating text near NPC
            if hasattr(self, 'npc'):
                pos = self.npc.to_window(self.npc.x, self.npc.y + 50)
                ft = FloatText(text=f"+${total_earned}", color=(0.2, 1, 0.4, 1), pos=pos)
                self.add_widget(ft)
                
            self.update_inventory_ui()
            # Update HUD so money reflects immediately if we have money on HUD
            # Or just rely on inventory overlay updating
            self.update_hud()

        self.toggle_sell_menu()

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
                world.add_widget(drop) 
                drop.animate_to_player()

                # Spawn Explosion Effect AFTER drop so it renders ON TOP
                explode_x = (grid_x * 120) - 4
                explode_y = (grid_y * 120) - 4
                explosion = ExplosionEffect(pos=(explode_x, explode_y))
                world.add_widget(explosion)
                
                print(f"Mined {ore_type} at ({grid_x}, {grid_y})! Dropping item...")

    def on_keyboard_up(self, _window, key, _scancode):
        self.keys_pressed.discard(key)

    def update_torch_state(self, dt):
        torch_expired = self.game_state.tick_torch(dt)
        if torch_expired:
            self.auto_use_torch_if_needed()

        self.update_hud()

    def update_fog_overlay(self):
        fog_overlay = self.ids.fog_overlay
        player = self.ids.player_character
        center_x, center_y = player.to_window(player.center_x, player.center_y)
        outer_radius = self.game_state.get_vision_radius()
        inner_radius = max(120, outer_radius * 0.55)

        def draw_band(left, right, bottom, top, alpha):
            clipped_left = max(fog_overlay.x, left)
            clipped_right = min(fog_overlay.right, right)
            clipped_bottom = max(fog_overlay.y, bottom)
            clipped_top = min(fog_overlay.top, top)

            if clipped_left >= clipped_right or clipped_bottom >= clipped_top:
                return

            Color(0, 0, 0, alpha)
            Rectangle(
                pos=(fog_overlay.x, fog_overlay.y),
                size=(max(0, clipped_left - fog_overlay.x), fog_overlay.height),
            )
            Rectangle(
                pos=(clipped_right, fog_overlay.y),
                size=(max(0, fog_overlay.right - clipped_right), fog_overlay.height),
            )
            Rectangle(
                pos=(clipped_left, fog_overlay.y),
                size=(max(0, clipped_right - clipped_left), max(0, clipped_bottom - fog_overlay.y)),
            )
            Rectangle(
                pos=(clipped_left, clipped_top),
                size=(max(0, clipped_right - clipped_left), max(0, fog_overlay.top - clipped_top)),
            )

        fog_overlay.canvas.after.clear()
        with fog_overlay.canvas.after:
            draw_band(
                center_x - outer_radius,
                center_x + outer_radius,
                center_y - outer_radius,
                center_y + outer_radius,
                0.78,
            )
            draw_band(
                center_x - inner_radius,
                center_x + inner_radius,
                center_y - inner_radius,
                center_y + inner_radius,
                0.35,
            )

    def update(self, dt):
        self.update_torch_state(dt)
        self.update_fog_overlay()

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
        if new_x < 0:
            new_x = 0
        elif new_x > world.width - player.width:
            new_x = world.width - player.width

        if new_y < 0:
            new_y = 0
        elif new_y > world.height - player.height:
            new_y = world.height - player.height

        # --- à¸£à¸°à¸šà¸šà¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸à¸²à¸£à¸Šà¸™ (à¸«à¸´à¸™/à¹à¸£à¹ˆ/à¸ªà¸´à¹ˆà¸‡à¸à¸µà¸”à¸‚à¸§à¸²à¸‡) ---
        inset_x = 25  
        inset_y = 20  
        pw = player.width - inset_x * 2
        ph = player.height - inset_y * 2

        def hits_solid(px, py):
            """à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸§à¹ˆà¸²à¸à¸£à¸­à¸šà¸‚à¸­à¸‡à¸•à¸±à¸§à¸¥à¸°à¸„à¸£à¸—à¸±à¸šà¸‹à¹‰à¸­à¸™à¸à¸±à¸šà¸ªà¸´à¹ˆà¸‡à¸à¸µà¸”à¸‚à¸§à¸²à¸‡à¸«à¸£à¸·à¸­à¹„à¸¡à¹ˆ"""
            gs = self.game_state
            left = px + inset_x
            right = px + inset_x + pw
            bottom = py + inset_y
            top = py + inset_y + ph
            
            # à¹€à¸Šà¹‡à¸à¸ˆà¸¸à¸”à¸—à¸±à¹‰à¸‡ 4 à¸¡à¸¸à¸¡ à¹à¸¥à¸°à¸ˆà¸¸à¸”à¸à¸¶à¹ˆà¸‡à¸à¸¥à¸²à¸‡à¸‚à¸­à¸‡à¸à¸£à¸­à¸šà¸•à¸±à¸§à¸¥à¸°à¸„à¸£
            for cx in [left, (left + right) / 2, right]:
                for cy in [bottom, (bottom + top) / 2, top]:
                    
                    # 1. à¹€à¸Šà¹‡à¸à¸à¸²à¸£à¸Šà¸™à¸à¸±à¸šà¸™à¹‰à¸³ 
                    if hasattr(gs, 'is_water_tile') and gs.is_water_tile(cx, cy):
                        return True
                        
                    # 2. à¹€à¸Šà¹‡à¸à¸à¸²à¸£à¸Šà¸™à¸à¸±à¸šà¸«à¸´à¸™à¸«à¸£à¸·à¸­à¹à¸£à¹ˆ (à¸”à¸¶à¸‡à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸ˆà¸²à¸ Grid)
                    # à¹à¸›à¸¥à¸‡à¸žà¸´à¸à¸±à¸” Pixel à¹ƒà¸«à¹‰à¹€à¸›à¹‡à¸™à¸žà¸´à¸à¸±à¸” Grid (à¸«à¸²à¸£à¸”à¹‰à¸§à¸¢à¸‚à¸™à¸²à¸”à¸šà¸¥à¹‡à¸­à¸ 120)
                    grid_x = int(cx / 120)
                    grid_y = int(cy / 120)
                    
                    # à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸§à¹ˆà¸²à¸žà¸´à¸à¸±à¸”à¸¢à¸±à¸‡à¸­à¸¢à¸¹à¹ˆà¹ƒà¸™à¸‚à¸­à¸šà¹€à¸‚à¸•à¹à¸œà¸™à¸—à¸µà¹ˆ
                    if gs.grid_map[grid_y][grid_x] is not None:
                                # ==========================================
                                # à¸­à¸±à¸›à¹€à¸”à¸•à¹ƒà¸«à¸¡à¹ˆ: à¸šà¸µà¸šà¸à¸£à¸­à¸šà¸à¸²à¸£à¸Šà¸™ (Hitbox) à¹ƒà¸«à¹‰à¹€à¸¥à¹‡à¸à¸à¸§à¹ˆà¸²à¸£à¸¹à¸›à¸ à¸²à¸žà¸ˆà¸£à¸´à¸‡
                                # ==========================================
                                visual_size = 45 
                                offset = (120 - visual_size) / 2
                                
                                # --- à¸›à¸£à¸±à¸šà¸£à¸°à¸¢à¸°à¸„à¸§à¸²à¸¡à¸Šà¸´à¸”à¸•à¸£à¸‡à¸™à¸µà¹‰à¸„à¸£à¸±à¸š ---
                                # à¸¢à¸´à¹ˆà¸‡à¹ƒà¸ªà¹ˆà¹€à¸¥à¸‚à¹€à¸¢à¸­à¸° à¸¢à¸´à¹ˆà¸‡à¹€à¸”à¸´à¸™à¸—à¸°à¸¥à¸¸à¹€à¸‚à¹‰à¸²à¹„à¸›à¹ƒà¸à¸¥à¹‰à¹à¸£à¹ˆà¹„à¸”à¹‰à¸¡à¸²à¸à¸‚à¸¶à¹‰à¸™
                                ore_inset_x = 10  # à¸¢à¸­à¸¡à¹ƒà¸«à¹‰à¹€à¸”à¸´à¸™à¸‹à¹‰à¸­à¸™à¸—à¸±à¸šà¸”à¹‰à¸²à¸™à¸‹à¹‰à¸²à¸¢/à¸‚à¸§à¸² à¹„à¸”à¹‰ 10 à¸žà¸´à¸à¹€à¸‹à¸¥
                                ore_inset_y = 15  # à¸¢à¸­à¸¡à¹ƒà¸«à¹‰à¹€à¸”à¸´à¸™à¸‹à¹‰à¸­à¸™à¸—à¸±à¸šà¸”à¹‰à¸²à¸™à¸šà¸™/à¸¥à¹ˆà¸²à¸‡ à¹„à¸”à¹‰ 15 à¸žà¸´à¸à¹€à¸‹à¸¥
                                
                                ore_left = (grid_x * 120) + offset + ore_inset_x
                                ore_right = (grid_x * 120) + offset + visual_size - ore_inset_x
                                ore_bottom = (grid_y * 120) + offset + ore_inset_y
                                ore_top = (grid_y * 120) + offset + visual_size - ore_inset_y
                                
                                # à¹€à¸Šà¹‡à¸à¸§à¹ˆà¸²à¸ˆà¸¸à¸”à¸žà¸´à¸à¸±à¸” à¹€à¸«à¸¢à¸µà¸¢à¸šà¹‚à¸”à¸™ Hitbox à¸—à¸µà¹ˆà¸–à¸¹à¸à¸šà¸µà¸šà¹à¸¥à¹‰à¸§à¸«à¸£à¸·à¸­à¹„à¸¡à¹ˆ
                                if ore_left <= cx <= ore_right and ore_bottom <= cy <= ore_top:
                                    return True
                                
            return False

        # --- à¹ƒà¸Šà¹‰à¹€à¸—à¸„à¸™à¸´à¸„ Wall Sliding (à¹ƒà¸«à¹‰à¹€à¸”à¸´à¸™à¹„à¸–à¸à¸³à¹à¸žà¸‡à¹„à¸”à¹‰) ---
        # à¸—à¸”à¸ªà¸­à¸šà¸à¸²à¸£à¸‚à¸¢à¸±à¸šà¹à¸à¸™ X à¸à¹ˆà¸­à¸™
        if hits_solid(new_x, player.y):
            new_x = player.x  # à¸–à¹‰à¸²à¸Šà¸™à¸ªà¸´à¹ˆà¸‡à¸à¸µà¸”à¸‚à¸§à¸²à¸‡ à¹ƒà¸«à¹‰à¸•à¸³à¹à¸«à¸™à¹ˆà¸‡ X à¸à¸¥à¸±à¸šà¸¡à¸²à¸—à¸µà¹ˆà¹€à¸”à¸´à¸¡

        # à¸—à¸”à¸ªà¸­à¸šà¸à¸²à¸£à¸‚à¸¢à¸±à¸šà¹à¸à¸™ Y
        if hits_solid(new_x, new_y):
            new_y = player.y  # à¸–à¹‰à¸²à¸Šà¸™à¸ªà¸´à¹ˆà¸‡à¸à¸µà¸”à¸‚à¸§à¸²à¸‡ à¹ƒà¸«à¹‰à¸•à¸³à¹à¸«à¸™à¹ˆà¸‡ Y à¸à¸¥à¸±à¸šà¸¡à¸²à¸—à¸µà¹ˆà¹€à¸”à¸´à¸¡

        # à¸­à¸±à¸›à¹€à¸”à¸•à¸•à¸³à¹à¸«à¸™à¹ˆà¸‡à¸ˆà¸£à¸´à¸‡à¸‚à¸­à¸‡à¸•à¸±à¸§à¸¥à¸°à¸„à¸£
        player.x = new_x
        player.y = new_y

        # --- à¸­à¸±à¸›à¹€à¸”à¸•à¸à¸¥à¹‰à¸­à¸‡à¹à¸¥à¸° Minimap (à¸£à¸°à¸šà¸šà¹€à¸”à¸´à¸¡à¸‚à¸­à¸‡à¸„à¸¸à¸“) ---
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
        self.update_fog_overlay()

    def toggle_upgrade_menu(self):
        """à¹€à¸›à¸´à¸”/à¸›à¸´à¸” à¸«à¸™à¹‰à¸²à¸•à¹ˆà¸²à¸‡à¸­à¸±à¸›à¹€à¸à¸£à¸”"""
        overlay = self.ids.upgrade_overlay
        if overlay.disabled:
            overlay.opacity = 1
            overlay.disabled = False
            self.update_upgrade_ui()
        else:
            overlay.opacity = 0
            overlay.disabled = True

    def update_upgrade_ui(self):
        """à¸­à¸±à¸›à¹€à¸”à¸•à¸‚à¹‰à¸­à¸„à¸§à¸²à¸¡à¸£à¸²à¸„à¸²à¹ƒà¸™à¸«à¸™à¹‰à¸²à¸ˆà¸­"""
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
        """à¹€à¸¡à¸·à¹ˆà¸­à¸à¸”à¸›à¸¸à¹ˆà¸¡à¸‹à¸·à¹‰à¸­à¸­à¸±à¸›à¹€à¸à¸£à¸”"""
        next_level = self.pickaxe_level + 1
        if next_level not in self.upgrade_costs:
            return # à¹€à¸¥à¹€à¸§à¸¥à¸•à¸±à¸™à¹à¸¥à¹‰à¸§

        costs = self.upgrade_costs[next_level]
        
        # 1. à¹€à¸Šà¹‡à¸à¸§à¹ˆà¸²à¹à¸£à¹ˆà¹ƒà¸™à¸à¸£à¸°à¹€à¸›à¹‹à¸²à¸¡à¸µà¸žà¸­à¸ˆà¹ˆà¸²à¸¢à¹„à¸«à¸¡?
        can_afford = True
        for ore, req_amount in costs.items():
            if self.game_state.inventory.get(ore, 0) < req_amount:
                can_afford = False
                break
                
        # 2. à¸–à¹‰à¸²à¸¡à¸µà¹à¸£à¹ˆà¸žà¸­ à¹ƒà¸«à¹‰à¸«à¸±à¸à¹à¸£à¹ˆà¹à¸¥à¸°à¸­à¸±à¸›à¹€à¸à¸£à¸”
        if can_afford:
            for ore, req_amount in costs.items():
                self.game_state.inventory[ore] -= req_amount
                self.game_state.current_capacity -= req_amount
                
            self.pickaxe_level += 1
            
            # --- à¸«à¸±à¸§à¹ƒà¸ˆà¸ªà¸³à¸„à¸±à¸: à¸—à¸³à¹ƒà¸«à¹‰à¸‚à¸¸à¸”à¹€à¸£à¹‡à¸§à¸‚à¸¶à¹‰à¸™! ---
            player = self.ids.player_character
            # à¸¥à¸”à¹€à¸§à¸¥à¸²à¸­à¸™à¸´à¹€à¸¡à¸Šà¸±à¸™à¸•à¸­à¸™à¸‚à¸¸à¸”à¸¥à¸‡ (à¸¢à¸´à¹ˆà¸‡à¸„à¹ˆà¸²à¸™à¹‰à¸­à¸¢ à¸¢à¸´à¹ˆà¸‡à¸ªà¸±à¸šà¸ˆà¸­à¸šà¹„à¸§)
            player.mine_speed = max(0.01, player.mine_speed - 0.01) 
            
            print(f"Upgraded to Level {self.pickaxe_level}! New Speed: {player.mine_speed}")
            self.update_upgrade_ui() # à¸£à¸µà¹€à¸Ÿà¸£à¸Šà¸«à¸™à¹‰à¸²à¸ˆà¸­
        else:
            # à¸–à¹‰à¸²à¹à¸£à¹ˆà¹„à¸¡à¹ˆà¸žà¸­ à¹ƒà¸«à¹‰à¸›à¸¸à¹ˆà¸¡à¸šà¸­à¸à¹ƒà¸šà¹‰
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
