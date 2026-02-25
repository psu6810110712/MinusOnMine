# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Top-Down Mining RPG สร้างด้วย Kivy Framework

import os
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from game_logic import GameState
from game_data import ORE_COLORS, GROUND_COLOR, ORES
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window

# =============================================
# หน้าจอต่างๆ (Screens)
# =============================================

class MenuScreen(Screen):
    """หน้าเมนูหลัก - แสดงชื่อเกมและปุ่มเริ่มเล่น"""
    pass


class MiningScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = None
        self.textures = {} 
        
        # 1. พิกัดตัวละคร (เปลี่ยนเป็นทศนิยมเพื่อความลื่นไหล)
        self.player_x = 0.0
        self.player_y = 0.0
        self.player_speed = 4.0 # ความเร็วในการเดิน (ช่องต่อวินาที)
        
        # 2. เก็บสถานะปุ่มที่ถูกกดค้างไว้
        self.pressed_keys = set()
        # 3. เก็บอ็อบเจกต์รูปตัวละครบนจอเพื่อเอาไว้อัปเดตแค่พิกัด
        self.player_rect = None 
        self.update_event = None

    def on_enter(self):
        self.game_state = GameState()
        
        map_widget = self.ids.get('map_widget')
        if map_widget:
            map_widget.bind(size=self._trigger_redraw, pos=self._trigger_redraw)

        # ผูก Event ปุ่มคีย์บอร์ด (ทั้งตอนกด และ ตอนปล่อยปุ่ม)
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)
        
        # 4. สร้าง Loop ให้เกมอัปเดต 60 ครั้งต่อวินาที (60 FPS)
        self.update_event = Clock.schedule_interval(self.update_player_pos, 1.0 / 60.0)

        Clock.schedule_once(lambda dt: self.draw_map(), 0.1)

    def on_leave(self):
        map_widget = self.ids.get('map_widget')
        if map_widget:
            map_widget.unbind(size=self._trigger_redraw, pos=self._trigger_redraw)
            
        Window.unbind(on_key_down=self._on_key_down)
        Window.unbind(on_key_up=self._on_key_up)
        
        if self.update_event:
            self.update_event.cancel()

    def _trigger_redraw(self, instance, value):
        """ตัวรับ Event เมื่อหน้าต่างถูกย่อ/ขยาย"""
        if self.game_state:
            self.draw_map()

    # --- ระบบตรวจสอบปุ่มกดค้าง ---
    def _on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if text in ['w', 'a', 's', 'd']:
            self.pressed_keys.add(text)

    def _on_key_up(self, instance, keyboard, keycode):
        # แปลงรหัสตัวเลข (keyboard) ให้กลับเป็นตัวอักษรภาษาอังกฤษ
        try:
            text = chr(keyboard)
            if text in self.pressed_keys:
                self.pressed_keys.remove(text)
        except ValueError:
            pass
        
    # --- ระบบอัปเดตพิกัดแบบอิสระ (60 FPS) ---
    def update_player_pos(self, dt):
        if not self.game_state or not self.player_rect:
            return

        moved = False
        move_distance = self.player_speed * dt
        
        max_x = self.game_state.grid_width - 1
        max_y = self.game_state.grid_height - 1

        if 'w' in self.pressed_keys and self.player_y > 0:
            self.player_y -= move_distance
            moved = True
        if 's' in self.pressed_keys and self.player_y < max_y:
            self.player_y += move_distance
            moved = True
        if 'a' in self.pressed_keys and self.player_x > 0:
            self.player_x -= move_distance
            moved = True
        if 'd' in self.pressed_keys and self.player_x < max_x:
            self.player_x += move_distance
            moved = True

        if moved:
            self.update_player_graphics()

    def update_player_graphics(self):
        """คำนวณและอัปเดตพิกัดของรูปตัวละครบนหน้าจอ โดยไม่ต้องวาดแผนที่ใหม่ทั้งหมด"""
        map_widget = self.ids.get('map_widget')
        gs = self.game_state
        tile_size = min(map_widget.width / gs.grid_width, map_widget.height / gs.grid_height)
        total_map_w = tile_size * gs.grid_width
        total_map_h = tile_size * gs.grid_height
        
        offset_x = map_widget.x + (map_widget.width - total_map_w) / 2
        offset_y = map_widget.y + (map_widget.height - total_map_h) / 2

        player_draw_x = offset_x + self.player_x * tile_size
        player_draw_y = offset_y + (gs.grid_height - 1 - self.player_y) * tile_size
        
        self.player_rect.pos = (player_draw_x, player_draw_y)

    # --- ระบบโหลดภาพ ---
    def get_texture(self, source_file):
        """โหลดภาพทั้งไฟล์ให้พิกเซลคมชัด"""
        if source_file in self.textures:
            return self.textures[source_file] 
            
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, source_file)
        
        if not os.path.exists(path):
            print(f"Error: ไม่พบไฟล์ที่ {path}")
            return None
        try:
            core_img = CoreImage(path)
            if core_img and core_img.texture:
                texture = core_img.texture
                texture.mag_filter = 'nearest'
                texture.min_filter = 'nearest'
                self.textures[source_file] = texture 
                return texture
        except Exception as e:
            print(f"Error Loading Image: {e}")
        return None

    def get_sprite_from_sheet(self, source_file, x, y, width, height):
        """ดึงภาพย่อย (Sprite) จาก Sprite Sheet"""
        main_texture = self.get_texture(source_file)
        if main_texture:
            return main_texture.get_region(x, y, width, height)
        return None

    # --- ระบบวาดแผนที่และตัวละคร ---
    def draw_map(self):
        map_widget = self.ids.get('map_widget')
        if not map_widget or not self.game_state:
            return

        map_widget.canvas.after.clear()
        
        ground_tex = self.get_texture('ground.png')
        gs = self.game_state
        
        tile_size = min(map_widget.width / gs.grid_width, map_widget.height / gs.grid_height)
        total_map_w = tile_size * gs.grid_width
        total_map_h = tile_size * gs.grid_height
        
        offset_x = map_widget.x + (map_widget.width - total_map_w) / 2
        offset_y = map_widget.y + (map_widget.height - total_map_h) / 2

        with map_widget.canvas.after:
            # 1. วาดฉากหลัง
            if ground_tex:
                Color(1, 1, 1, 1) 
                Rectangle(texture=ground_tex, pos=(offset_x, offset_y), size=(total_map_w, total_map_h))

            # 2. วนลูปวาดกล่องแร่ / ไอเทม
            for y in range(gs.grid_height):
                for x in range(gs.grid_width):
                    tile = gs.get_tile(x, y)
                    draw_x = offset_x + x * tile_size
                    draw_y = offset_y + (gs.grid_height - 1 - y) * tile_size

                    if tile:
                        sprite_coords = {
                            "stone": (16, 0), "coal": (32, 0), "copper": (48, 0), "iron": (64, 0), 
                        }
                        
                        Color(1, 1, 1, 1)
                        if tile in sprite_coords:
                            sx, sy = sprite_coords[tile]
                            ore_tex = self.get_sprite_from_sheet('details.png', sx, sy, 16, 16)
                            if ore_tex:
                                Rectangle(texture=ore_tex, pos=(draw_x + 4, draw_y + 4), size=(tile_size - 8, tile_size - 8))
                            else:
                                Color(*ORE_COLORS.get(tile, (1, 1, 1, 1)))
                                Rectangle(pos=(draw_x + 4, draw_y + 4), size=(tile_size - 8, tile_size - 8))
                        else:
                            Color(*ORE_COLORS.get(tile, (1, 1, 1, 1)))
                            Rectangle(pos=(draw_x + 4, draw_y + 4), size=(tile_size - 8, tile_size - 8))

            # 3. วาดตัวละคร (Player) ทับชั้นบนสุด และเก็บไว้ขยับ
            player_draw_x = offset_x + self.player_x * tile_size
            player_draw_y = offset_y + (gs.grid_height - 1 - self.player_y) * tile_size
            
            # ทดลองดึงรูปตัวละครจาก Floor.png (แก้พิกัดตรงนี้ได้เลย)
            player_tex = self.get_sprite_from_sheet('Floor.png', 288, 128, 32, 32)
            
            Color(1, 1, 1, 1) 
            if player_tex:
                self.player_rect = Rectangle(texture=player_tex, pos=(player_draw_x, player_draw_y), size=(tile_size, tile_size))
            else:
                Color(1, 0, 0, 1) # ถ้าหาภาพไม่เจอเป็นกล่องสีแดง
                self.player_rect = Rectangle(pos=(player_draw_x + 4, player_draw_y + 4), size=(tile_size - 8, tile_size - 8))

    def new_map(self):
        """สร้าง map ใหม่ (กดปุ่ม New Map)"""
        if self.game_state:
            self.game_state.generate_map()
            self.draw_map()
                
# =============================================
# แอปหลัก (Main App)
# =============================================

class MinusOnMineApp(App):
    """แอปพลิเคชันหลักของเกม MinusOnMine"""

    def build(self):
        """สร้าง ScreenManager และเพิ่มหน้าจอทั้งหมด"""
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(MiningScreen(name='mining'))
        return sm


# รันแอป
if __name__ == '__main__':
    MinusOnMineApp().run()
