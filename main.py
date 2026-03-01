from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.widget import Widget

from game_logic import GameState
from game_data import ORES


class PlayerWidget(Widget):
    image_source = StringProperty("assets/sprites/player/movement/down/1.png")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.frames = {
            "up": [f"assets/sprites/player/movement/up/{i}.png" for i in range(1, 10)],
            "down": [f"assets/sprites/player/movement/down/{i}.png" for i in range(1, 10)],
            "left": [f"assets/sprites/player/movement/left/{i}.png" for i in range(1, 10)],
            "right": [f"assets/sprites/player/movement/right/{i}.png" for i in range(1, 10)],
        }
        self.current_frame = 0
        self.is_moving = False
        self.direction = "down"
        self.anim_timer = 0.0
        self.anim_speed = 0.08

    def update_animation(self, dt):
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
        
        # Determine color from game_data
        ore_data = ORES.get(self.ore_type)
        self.color = ore_data.color if ore_data else (1, 1, 1, 1)

        self.size_hint = (None, None)
        self.size = (120, 120)  # Fixed size matching grid
        self.pos = (self.grid_x * 120, self.grid_y * 120)

        with self.canvas:
            Color(*self.color)
            # Make it slightly smaller than 120 so there's a visible grid gap
            self.rect = Rectangle(pos=(self.pos[0] + 5, self.pos[1] + 5), size=(110, 110))

    def mine(self):
        """Called when the block is mined. Removes itself from the parent."""
        if self.parent:
            self.parent.remove_widget(self)


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

    def on_leave(self):
        Window.unbind(on_key_down=self.on_keyboard_down)
        Window.unbind(on_key_up=self.on_keyboard_up)
        if hasattr(self, "game_loop"):
            self.game_loop.cancel()
        self.keys_pressed.clear()

    def on_camera_zoom(self, _instance, value):
        self.camera.zoom = max(1.0, float(value))

    def on_keyboard_down(self, _window, key, _scancode, _codepoint, _modifiers):
        self.keys_pressed.add(key)
        
        # Handle 'E' key for mining (key code 101 or the actual character 'e')
        if key == 101 or _codepoint == 'e':
            self.mine_action()

    def mine_action(self):
        player = self.ids.player_character
        
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
                if ore_type in self.game_state.inventory:
                    self.game_state.inventory[ore_type] += 1
                else:
                    self.game_state.inventory[ore_type] = 1
                    
                print(f"Mined {ore_type} at ({grid_x}, {grid_y})! Inventory: {self.game_state.inventory}")

    def on_keyboard_up(self, _window, key, _scancode):
        self.keys_pressed.discard(key)

    def update(self, dt):
        step = self.move_speed * dt
        player = self.ids.player_character
        world = self.ids.world_layer

        new_x = player.x
        new_y = player.y
        is_moving_now = False

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

        if new_x < 0:
            new_x = 0
        elif new_x > world.width - player.width:
            new_x = world.width - player.width

        if new_y < 0:
            new_y = 0
        elif new_y > world.height - player.height:
            new_y = world.height - player.height

        player.x = new_x
        player.y = new_y

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


class MinusOnMineApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(MiningScreen(name="mining"))
        sm.add_widget(MapScreen(name="map"))
        return sm


if __name__ == "__main__":
    MinusOnMineApp().run()
