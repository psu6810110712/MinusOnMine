# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Idle Mining Game สร้างด้วย Kivy Framework
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window  # ดึงระบบหน้าต่างมาจับคีย์บอร์ด
from kivy.clock import Clock
import random
from kivy.graphics import Color, Rectangle
from game_data import ORES, UITheme

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
        # สร้างและวาดแมพทันทีที่เข้ามาในหน้านี้
        self.generate_map()
        self.draw_map()
        
        Window.bind(on_key_down=self.on_keyboard_down)
        Window.bind(on_key_up=self.on_keyboard_up)
        self.game_loop = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_enter(self):
        """ฟังก์ชันนี้จะทำงานอัตโนมัติเมื่อเข้ามาที่หน้านี้"""
        # 1. ผูกคีย์บอร์ดเข้ากับฟังก์ชัน
        Window.bind(on_key_down=self.on_keyboard_down)
        Window.bind(on_key_up=self.on_keyboard_up)
        # 2. สั่งให้ฟังก์ชัน update ทำงาน 60 ครั้งต่อวินาที (60 FPS)
        self.game_loop = Clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_leave(self):
        """ฟังก์ชันนี้จะทำงานอัตโนมัติเมื่อออกจากหน้านี้"""
        # ยกเลิกการผูกคีย์บอร์ดและหยุด Game Loop เพื่อไม่ให้กินเครื่องตอนอยู่หน้าเมนู
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
        """Game Loop: จะถูกเรียก 60 ครั้งต่อวินาทีเพื่อขยับตัวละคร"""
        step = self.move_speed * dt
        player = self.ids.player_character
        world = self.ids.world_layer  # ดึงตัวแปร "โลก" มาใช้

        # 1. จำลองพิกัดตำแหน่งใหม่ขึ้นมาก่อน (ยังไม่ขยับจริง)
        new_x = player.x
        new_y = player.y

        # 2. คำนวณทิศทางการเดินตามปุ่มที่กด
        if 119 in self.keys_pressed or 273 in self.keys_pressed:  # W หรือ Up
            new_y += step
        if 115 in self.keys_pressed or 274 in self.keys_pressed:  # S หรือ Down
            new_y -= step
        if 97 in self.keys_pressed or 276 in self.keys_pressed:   # A หรือ Left
            new_x -= step
        if 100 in self.keys_pressed or 275 in self.keys_pressed:  # D หรือ Right
            new_x += step

        # ==========================================
        # ระบบกำแพงกั้นขอบโลก (Boundary Collision)
        # เปลี่ยนจากชนขอบจอ (self.width) มาชนขอบโลก (world.width) แทน
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
        # เลื่อนตำแหน่งของ "โลก" เพื่อให้ตัวละครอยู่ตรงกลางจอเสมอ
        # ==========================================
        world.x = (self.width / 2) - player.x - (player.width / 2)
        world.y = (self.height / 2) - player.y - (player.height / 2)

    # ==========================================
    # ระบบแผนที่อย่างง่าย (Simple Map System)
    # ==========================================
    def generate_map(self):
        """สุ่มสร้างข้อมูลแผนที่ (0 = ดิน, 1 = หินแร่)"""
        self.map_data = []
        for y in range(self.grid_h):
            row = []
            for x in range(self.grid_w):
                # สุ่มโอกาส 20% ที่จะเป็นก้อนหิน (1) นอกนั้นเป็นดิน (0)
                if random.random() < 0.2:
                    row.append(1)
                else:
                    row.append(0)
            self.map_data.append(row)

    def draw_map(self):
        """วาดแผนที่ลงบน map_layer"""
        map_layer = self.ids.map_layer
        map_layer.canvas.clear() # ล้างภาพเก่าทิ้งก่อนวาดใหม่
        
        with map_layer.canvas:
            for y in range(self.grid_h):
                for x in range(self.grid_w):
                    tile = self.map_data[y][x]
                    
                    # กำหนดสีตามประเภทของช่อง
                    if tile == 1:
                        Color(*ORES["stone"].color)  # ใช้สีแร่จาก object
                    else:
                        Color(*UITheme().GROUND_COLOR)  # ใช้สีพื้นจาก UITheme
                        
                    # คำนวณพิกัด x, y แล้ววาดกล่อง
                    draw_x = x * self.tile_size
                    draw_y = y * self.tile_size
                    
                    # วาดขนาดเล็กลง 2 พิกเซล เพื่อให้เห็นเส้นขอบตารางชัดๆ
                    Rectangle(pos=(draw_x, draw_y), size=(self.tile_size - 2, self.tile_size - 2))

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
        sm.add_widget(MapScreen(name='map'))
        return sm


# รันแอป
if __name__ == '__main__':
    MinusOnMineApp().run()
