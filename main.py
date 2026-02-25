# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Idle Mining Game สร้างด้วย Kivy Framework
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window  # ดึงระบบหน้าต่างมาจับคีย์บอร์ด
from kivy.clock import Clock

# =============================================
# หน้าจอต่างๆ (Screens)
# =============================================

class MenuScreen(Screen):
    """หน้าเมนูหลัก - แสดงชื่อเกมและปุ่มเริ่มเล่น"""
    pass


class MiningScreen(Screen):
    """หน้าขุดแร่ - หน้าเล่นหลักของเกม"""
    pass

class MapScreen(Screen):
    """หน้าจอแผนที่สำหรับเดินสำรวจ"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keys_pressed = set() # เซ็ตสำหรับเก็บปุ่มที่กำลังถูกกดค้างไว้
        self.move_speed = 300     # ความเร็วตัวละคร (พิกเซล ต่อ วินาที)

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

        # เช็ครหัสปุ่ม: 119='w', 273='up'
        if 119 in self.keys_pressed or 273 in self.keys_pressed:
            player.y += step
            
        # 115='s', 274='down'
        if 115 in self.keys_pressed or 274 in self.keys_pressed:
            player.y -= step
            
        # 97='a', 276='left'
        if 97 in self.keys_pressed or 276 in self.keys_pressed:
            player.x -= step
            
        # 100='d', 275='right'
        if 100 in self.keys_pressed or 275 in self.keys_pressed:
            player.x += step
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
