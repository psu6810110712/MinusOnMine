from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty, ListProperty, BooleanProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from kivy.animation import Animation
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior

from game_data import ORES, UPGRADES

class UpgradeItemWidget(BoxLayout):
    """Widget representing a single upgrade item in the shop."""
    upgrade_name = StringProperty("")
    upgrade_desc = StringProperty("")
    button_text = StringProperty("BUY")
    is_owned = BooleanProperty(False)
    can_afford = BooleanProperty(False)

    def __init__(self, upgrade_id, game_state, parent_screen, **kwargs):
        super().__init__(**kwargs)
        self.upgrade_id = upgrade_id
        self.game_state = game_state
        self.parent_screen = parent_screen
        
        upgrade = UPGRADES[self.upgrade_id]
        self.upgrade_name = upgrade.name
        self.cost = upgrade.cost
        
        # Format description based on attributes
        attrs = []
        for k, v in upgrade.attributes.items():
            if k == "multiplier": attrs.append(f"x{v} Speed")
            elif k == "auto_mine_rate": attrs.append(f"+{v} Ore/s")
            elif k == "luck_bonus": attrs.append(f"x{v} Luck")
            elif k == "capacity": attrs.append(f"+{v} Capacity")
            elif k == "mine_burst": attrs.append(f"{v}x Burst")
        self.upgrade_desc = ", ".join(attrs)
        
        self.update_state()
        
    def update_state(self):
        self.is_owned = self.upgrade_id in self.game_state.owned_upgrades
        self.can_afford = self.game_state.money >= self.cost
        
        if self.is_owned:
            self.button_text = "OWNED"
        else:
            self.button_text = f"${self.cost}"

    def buy_upgrade(self):
        if self.game_state.buy_upgrade(self.upgrade_id):
            print(f"Bought upgrade {self.upgrade_id}!")
            self.parent_screen.update_shop_ui()
            self.parent_screen.update_hud(0)
            
            # Recalculate player stats if needed
            self.parent_screen.ids.player_character.recalculate_stats(self.game_state)
            
            # Show floating text
            ft = FloatText(text=f"-${self.cost}", color=(1, 0.2, 0.2, 1), pos=self.parent_screen.ids.shop_money_label.pos)
            self.parent_screen.add_widget(ft)


class FloatText(Label):
    """Floating text for polished UI feedback (+1 Gold, -$500, etc)"""
    def __init__(self, text, color=(1, 1, 1, 1), **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = color
        self.font_name = 'assets/fonts/PixelifySans-Bold.ttf'
        self.font_size = '20sp'
        self.size_hint = (None, None)
        self.size = (150, 40)
        self.opacity = 1.0

    def on_parent(self, widget, parent):
        if parent:
            # Animate moving up and fading out
            anim = Animation(y=self.y + 100, opacity=0.0, duration=1.0, t='out_quad')
            anim.bind(on_complete=self.remove_self)
            anim.start(self)

    def remove_self(self, *args):
        if self.parent:
            self.parent.remove_widget(self)


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
        
        self.current_frame = 0
        self.is_moving = False
        self.is_mining = False
        self.direction = "down"
        
        # Timers
        self.anim_timer = 0.0
        self.anim_speed = 0.08
        self.mine_timer = 0.0
        self.mine_speed = 0.05
        self.mine_speed_multiplier = 1.0

    def recalculate_stats(self, game_state):
        from game_data import UPGRADES
        highest_mult = 1.0
        for upg_id in game_state.owned_upgrades:
            attrs = UPGRADES[upg_id].attributes
            if "multiplier" in attrs:
                if attrs["multiplier"] > highest_mult:
                    highest_mult = attrs["multiplier"]
        self.mine_speed_multiplier = highest_mult

    def update_animation(self, dt):
        # 1. Handle Mining Animation first (Priority)
        if self.is_mining:
            orig_w, orig_h = self.attack_frame_sizes[self.direction][self.current_frame]
            scaled_w = orig_w * 1.5625
            scaled_h = orig_h * 1.538
            
            self.render_size = [scaled_w, scaled_h]
            offset_x = (100 - scaled_w) / 2.0
            offset_y = 0.0
            
            self.render_offset = [offset_x, offset_y]
            
            # Apply multiplier to mine speed
            actual_mine_speed = self.mine_speed / self.mine_speed_multiplier
            
            self.mine_timer += dt
            if self.mine_timer >= actual_mine_speed:
                self.mine_timer = 0.0
                self.current_frame += 1
                
                if self.current_frame > 5:
                    self.is_mining = False
                    self.current_frame = 0
                    self.image_source = self.frames[self.direction][0]
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
        
        # Determine color and image from game_data
        ore_data = ORES.get(self.ore_type)
        self.color = (1, 1, 1, 1) # Reset to white to let image pass through
        self.image_source = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""

        self.size_hint = (None, None)
        self.size = (120, 120)  # Fixed size matching grid
        self.pos = (self.grid_x * 120, self.grid_y * 120)

        with self.canvas:
            Color(*self.color)
            if self.image_source:
                # Use image sprite
                self.rect = Rectangle(pos=(self.pos[0] + 5, self.pos[1] + 5), size=(110, 110), source=self.image_source)
            else:
                # Fallback to color tinted box
                fallback_color = ore_data.color if ore_data else (1, 1, 1, 1)
                Color(*fallback_color)
                self.rect = Rectangle(pos=(self.pos[0] + 5, self.pos[1] + 5), size=(110, 110))

    def mine(self):
        """Called when the block is mined. Removes itself from the parent."""
        if self.parent:
            self.parent.remove_widget(self)


class ItemDrop(Widget):
    """Widget representing a dropped item flying towards the player"""
    def __init__(self, start_pos, target_player, game_state, ore_type, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (40, 40) # Smaller than a block
        self.pos = start_pos
        self.ore_type = ore_type
        self.game_state = game_state
        self.target_player = target_player

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
            print(f"Collected {self.ore_type}! Inventory: {self.game_state.current_capacity}/{self.game_state.max_capacity}")
            
            # Floating text
            if self.target_player and self.target_player.parent:
                world = self.target_player.parent
                ft = FloatText(text=f"+1 {self.ore_type.capitalize()}", color=(1, 0.9, 0.5, 1), pos=self.pos)
                world.add_widget(ft)
                
            # 2. Delete itself
            if self.parent:
                self.parent.remove_widget(self)
        else:
            # Backpack full! Drop the item back on the ground.
            print("Backpack is full! Ore dropped on the floor.")
            anim = Animation(x=self.pos[0] + 50, y=self.pos[1] - 50, duration=0.3) # Fake bounce
            anim.start(self)


class NPCWidget(Widget):
    """NPC merchant using assets/Pawn_Blue.png with a spritesheet idle animation."""
    image_source = StringProperty("assets/Pawn_Blue.png")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (128, 128) # Visual size on screen
        
        # Spritesheet info: 1152x1152 total, 6x6 grid -> 192x192 per sprite
        self.sprite_row = 0 # Row 1 (Idle)
        self.current_frame = 0
        self.max_frames = 6
        
        # Load texture and set it up
        from kivy.core.image import Image as CoreImage
        self.sprite_texture = CoreImage(self.image_source).texture
        
        with self.canvas:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(
                pos=self.pos,
                size=self.size,
                texture=self.sprite_texture
            )
        
        self.update_tex_coords()
        self.bind(pos=self.update_canvas)
        
        # Add Name Tag label
        from kivy.uix.label import Label
        self.name_tag = Label(
            text="[b]MERCHANT[/b]",
            markup=True,
            font_name='assets/fonts/PixelifySans-Bold.ttf',
            font_size='18sp',
            color=(1, 1, 1, 1),
            size_hint=(None, None),
            size=(200, 30)
        )
        self.add_widget(self.name_tag)
        self.update_canvas() # Initial positioning of label
        
        # Schedule the animation at a typical idle pace
        from kivy.clock import Clock
        Clock.schedule_interval(self.animate_sprite, 0.15)

    def update_tex_coords(self):
        """Map the current frame to the texture coordinates."""
        # Calculate u,v coordinates (0.0 to 1.0)
        # grid is 6x6
        col = self.current_frame % self.max_frames
        row = self.sprite_row
        
        # TinySwords sheet usually has (0,0) at top-left visually
        # Kivy texture (0,0) is bottom-left
        # Width/height of one frame is 1/6
        w = 1.0 / 6.0
        h = 1.0 / 6.0
        
        u0 = col * w
        v1 = 1.0 - (row * h)
        u1 = u0 + w
        v0 = v1 - h
        
        # Swapping v1 and v0 to flip the sprite right-side up
        self.rect.tex_coords = (u0, v1, u1, v1, u1, v0, u0, v0)

    def animate_sprite(self, dt):
        """Cycle through the frames of the idle row."""
        self.current_frame = (self.current_frame + 1) % self.max_frames
        self.update_tex_coords()

    def update_canvas(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        # Position name tag above the head
        if hasattr(self, 'name_tag'):
            self.name_tag.center_x = self.center_x
            self.name_tag.y = self.top - 20 # Anchor slightly inside/above the 128px box


class InventorySlot(Widget):
    """A visual slot in the inventory holding an item icon and its count."""
    item_image = StringProperty("")
    item_count = StringProperty("0")
    parent_screen = ObjectProperty(None)

    def __init__(self, ore_type, count, parent_screen=None, **kwargs):
        super().__init__(**kwargs)
        self.ore_type = ore_type
        self.item_count = str(count)
        self.parent_screen = parent_screen
        
        ore_data = ORES.get(self.ore_type)
        self.item_image = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""


class SellOverlay(BoxLayout):
    """Overlay for selling items that blocks touch from passing through to the map."""
    def on_touch_down(self, touch):
        # If disabled (invisible/inactive), don't block or handle touch
        if self.disabled:
            return False
            
        # If the touch is inside this overlay, handle it and don't let it pass to the map
        if self.collide_point(*touch.pos):
            super().on_touch_down(touch)
            return True # Consume touch
        return False


class SellItemRow(BoxLayout):
    """A row in the NPC sell menu to select how many of an ore to sell."""
    ore_name = StringProperty("")
    item_image = StringProperty("")
    max_amount = NumericProperty(0)
    current_selected_amount = NumericProperty(0)
    subtotal = NumericProperty(0)

    def __init__(self, ore_type, max_amount, price_per_unit, parent_menu, **kwargs):
        super().__init__(**kwargs)
        self.ore_type = ore_type
        self.max_amount = max_amount
        self.price_per_unit = price_per_unit
        self.parent_menu = parent_menu
        
        ore_data = ORES.get(self.ore_type)
        self.ore_name = ore_data.name if ore_data else ore_type
        self.item_image = ore_data.image_path if ore_data and getattr(ore_data, 'image_path', "") else ""

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print(f"Debug: SellItemRow ({self.ore_name}) touched at {touch.pos}")
            # Ensure we call children's on_touch_down (for buttons/sliders)
            return super().on_touch_down(touch)
        return False

    def on_slider_change(self, value):
        self.current_selected_amount = int(value)
        self.subtotal = self.current_selected_amount * self.price_per_unit
        
        if self.parent_menu:
            self.parent_menu.recalculate_total_sell()

    def adjust_quantity(self, amount):
        """Increase or decrease quantity within bounds"""
        new_val = self.current_selected_amount + amount
        if 0 <= new_val <= self.max_amount:
            self.current_selected_amount = new_val
            self.ids.sell_slider.value = self.current_selected_amount # Sync back to slider
            # Recalculate subtotal (handled by on_slider_change or manually set)
            self.subtotal = self.current_selected_amount * self.price_per_unit
            if self.parent_menu:
                self.parent_menu.recalculate_total_sell()

    def set_max(self):
        """Set to full owned amount"""
        self.current_selected_amount = self.max_amount
        self.ids.sell_slider.value = self.max_amount
        self.subtotal = self.current_selected_amount * self.price_per_unit
        if self.parent_menu:
            self.parent_menu.recalculate_total_sell()
