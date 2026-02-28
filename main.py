# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Idle Mining Game สร้างด้วย Kivy Framework
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window  # ดึงระบบหน้าต่างมาจับคีย์บอร์ด
from kivy.clock import Clock
import random
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.uix.widget import Widget
from kivy.properties import StringProperty
from game_data import ORES  # ดึงมาจากไฟล์ game_data.py

# =============================================
# คลาสตัวละคร (Player) และระบบแอนิเมชัน
# =============================================

class PlayerWidget(Widget):
    # ตั้งค่าภาพเริ่มต้นเป็นท่ายืนหันลงหน้าจอ (ไฟล์ 1.png ของโฟลเดอร์ down)
    image_source = StringProperty('assets/sprites/player/movement/down/1.png')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # ใช้ Dictionary เก็บ path ของภาพทั้ง 4 ทิศทาง ทิศละ 9 เฟรม
        self.frames = {
            'up': [f'assets/sprites/player/movement/up/{i}.png' for i in range(1, 10)],
            'down': [f'assets/sprites/player/movement/down/{i}.png' for i in range(1, 10)],
            'left': [f'assets/sprites/player/movement/left/{i}.png' for i in range(1, 10)],
            'right': [f'assets/sprites/player/movement/right/{i}.png' for i in range(1, 10)]
        }
        
        self.current_frame = 0
        self.is_moving = False
        self.direction = 'down'  # เริ่มต้นหันหน้าลง
        
        self.anim_timer = 0
        self.anim_speed = 0.08  # ปรับให้เร็วขึ้นนิดนึงเพราะมีตั้ง 9 เฟรม (ลองปรับลด/เพิ่มความเร็วตรงนี้ได้ครับ)

    def update_animation(self, dt):
        """อัปเดตภาพตัวละครตามสถานะการเดินทั้ง 4 ทิศทาง"""
        if not self.is_moving:
            # ถ้ายืนเฉยๆ ให้กลับไปภาพแรก (ท่ายืน) ของทิศทางที่กำลังหันอยู่
            self.current_frame = 0
            self.image_source = self.frames[self.direction][0]
            return

        # ถ้ากำลังเดิน ให้นับเวลาเพื่อเปลี่ยนเฟรม
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0
            # วนลูปเฟรม 0 ถึง 8 (เพราะมี 9 ภาพ)
            self.current_frame = (self.current_frame + 1) % 9
            
            # อัปเดตภาพตามทิศทางปัจจุบัน
            self.image_source = self.frames[self.direction][self.current_frame]

# =============================================
# หน้าจอต่างๆ (Screens)
# =============================================

class MenuScreen(Screen):
    """หน้าเมนูหลัก - แสดงชื่อเกมและปุ่มเริ่มเล่น"""
    pass

class MiningScreen(Screen):
    """หน้าขุดแร่ (Mining) - แสดง Grid Map"""
    def new_map(self):
        """สร้าง Map ใหม่"""
        pass

class MapScreen(Screen):
    """หน้าจอแผนที่สำหรับเดินสำรวจ"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set()
        self.move_speed = 300
        
        # --- ตัวแปรสำหรับแผนที่ ---
        self.map_data = []      # เก็บข้อมูลแผนที่เป็น 2D Array
        self.tile_size = 50     # ขนาดของบล็อกแต่ละช่อง (ให้พอๆ กับตัวละคร)
        self.grid_w = 16        # จำนวนช่องแนวนอน
        self.grid_h = 12        # จำนวนช่องแนวตั้ง

    def on_enter(self):
        """ฟังก์ชันนี้จะทำงานอัตโนมัติเมื่อเข้ามาที่หน้านี้"""
        Window.bind(on_key_down=self.on_keyboard_down)
        Window.bind(on_key_up=self.on_keyboard_up)
        self.game_loop = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_leave(self):
        """ฟังก์ชันนี้จะทำงานอัตโนมัติเมื่อออกจากหน้านี้"""
        Window.unbind(on_key_down=self.on_keyboard_down)
        Window.unbind(on_key_up=self.on_keyboard_up)
        self.game_loop.cancel()
        self.keys_pressed.clear()

    def on_keyboard_down(self, window, key, scancode, codepoint, modifiers):
        """บันทึกรหัสปุ่ม (เป็นตัวเลข) ที่ถูกกด"""
        self.keys_pressed.add(key)

    def on_keyboard_up(self, window, key, scancode):
        """ลบรหัสปุ่มออกเมื่อปล่อยนิ้ว"""
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)

    def update(self, dt):
        step = self.move_speed * dt
        player = self.ids.player_character
        world = self.ids.world_layer

        new_x = player.x
        new_y = player.y

        # ตัวแปรเช็คว่ารอบนี้มีการเดินหรือไม่
        is_moving_now = False

        # คำนวณทิศทางการเดินตามปุ่มที่กด พร้อมกำหนดทิศทางให้ตัวละคร
        if 119 in self.keys_pressed or 273 in self.keys_pressed:  # W หรือ Up
            new_y += step
            player.direction = 'up'
            is_moving_now = True
        elif 115 in self.keys_pressed or 274 in self.keys_pressed:  # S หรือ Down
            new_y -= step
            player.direction = 'down'
            is_moving_now = True
            
        if 97 in self.keys_pressed or 276 in self.keys_pressed:   # A หรือ Left
            new_x -= step
            player.direction = 'left'
            is_moving_now = True
        elif 100 in self.keys_pressed or 275 in self.keys_pressed:  # D หรือ Right
            new_x += step
            player.direction = 'right'
            is_moving_now = True

        # อัปเดตสถานะแอนิเมชันให้ตัวละคร
        player.is_moving = is_moving_now
        player.update_animation(dt)

        # ... (โค้ดด้านล่างเรื่องขอบโลกและกล้อง เหมือนเดิมเลยครับ) ...

        # อัปเดตสถานะแอนิเมชันให้ตัวละคร
        player.is_moving = is_moving_now
        player.update_animation(dt)

        # ==========================================
        # ระบบกำแพงกั้นขอบโลก (Boundary Collision)
        # ==========================================
        if new_x < 0:
            new_x = 0
        elif new_x > world.width - player.width:
            new_x = world.width - player.width

        if new_y < 0:
            new_y = 0
        elif new_y > world.height - player.height:
            new_y = world.height - player.height

        # สั่งให้ตัวละครขยับ
        player.x = new_x
        player.y = new_y

        # ==========================================
        # ระบบกล้อง (Camera Follow)
        # ==========================================
        world.x = (self.width / 2) - player.x - (player.width / 2)
        world.y = (self.height / 2) - player.y - (player.height / 2)

        # วาด minimap ทุกเฟรม
        self.draw_minimap()

    def draw_minimap(self):
        """วาด minimap แสดงภาพแผนที่ย่อส่วน + ตำแหน่งผู้เล่น"""
        # โค้ดส่วนนี้เหมือนเดิมที่คุณเพิ่งเขียนมาครับ
        minimap = self.ids.minimap_widget
        player = self.ids.player_character
        world = self.ids.world_layer

        padding = 4
        map_draw_w = minimap.width - padding * 2
        map_draw_h = minimap.height - padding * 2

        scale_x = map_draw_w / world.width
        scale_y = map_draw_h / world.height

        base_x = minimap.x + padding
        base_y = minimap.y + padding

        minimap.canvas.after.clear()
        with minimap.canvas.after:
            Color(1, 1, 1, 1)
            Rectangle(pos=(base_x, base_y), size=(map_draw_w, map_draw_h),
                      source='ground.png')

            cam_x = base_x + (-world.x) * scale_x
            cam_y = base_y + (-world.y) * scale_y
            cam_w = self.width * scale_x
            cam_h = self.height * scale_y

            Color(1, 1, 1, 0.8)
            Line(rectangle=(cam_x, cam_y, cam_w, cam_h), width=1.2)

            player_mx = base_x + player.x * scale_x
            player_my = base_y + player.y * scale_y
            dot_size = 6

            Color(1, 0.2, 0.2, 1)
            Ellipse(pos=(player_mx - dot_size / 2, player_my - dot_size / 2),
                    size=(dot_size, dot_size))

# =============================================
# แอปหลัก (Main App)
# =============================================

class MinusOnMineApp(App):
    """แอปพลิเคชันหลักของเกม MinusOnMine"""

    def build(self):
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(MiningScreen(name='mining'))
        sm.add_widget(MapScreen(name='map'))
        return sm

# รันแอป
if __name__ == '__main__':
    MinusOnMineApp().run()