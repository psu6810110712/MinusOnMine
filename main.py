# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Top-Down Mining RPG สร้างด้วย Kivy Framework

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from game_logic import GameState
from game_data import ORE_COLORS, GROUND_COLOR, ORES


# =============================================
# หน้าจอต่างๆ (Screens)
# =============================================

class MenuScreen(Screen):
    """หน้าเมนูหลัก - แสดงชื่อเกมและปุ่มเริ่มเล่น"""
    pass


class MiningScreen(Screen):
    """หน้าขุดแร่ - แสดง Grid Map ที่สุ่มแร่"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_state = None

    def on_enter(self):
        """เรียกตอนเข้าหน้านี้ - สร้าง map ใหม่แล้ววาด"""
        self.game_state = GameState()
        # รอ 1 frame ให้ layout จัดเสร็จก่อนวาด
        Clock.schedule_once(lambda dt: self.draw_map(), 0.1)

    def draw_map(self):
        """วาด Grid Map บน Canvas ของ map_widget"""
        map_widget = self.ids.get('map_widget')
        if not map_widget or not self.game_state:
            return

        map_widget.canvas.after.clear()

        gs = self.game_state
        widget_width = map_widget.width
        widget_height = map_widget.height

        # คำนวณขนาด tile ให้พอดีกับ widget
        tile_w = widget_width / gs.grid_width
        tile_h = widget_height / gs.grid_height
        tile_size = min(tile_w, tile_h)

        # จัดกึ่งกลาง map ใน widget
        total_map_w = tile_size * gs.grid_width
        total_map_h = tile_size * gs.grid_height
        offset_x = map_widget.x + (widget_width - total_map_w) / 2
        offset_y = map_widget.y + (widget_height - total_map_h) / 2

        with map_widget.canvas.after:
            for y in range(gs.grid_height):
                for x in range(gs.grid_width):
                    tile = gs.get_tile(x, y)

                    if tile and tile in ORE_COLORS:
                        Color(*ORE_COLORS[tile])
                    else:
                        Color(*GROUND_COLOR)

                    # y กลับด้าน (Kivy วาดจากล่างขึ้นบน)
                    draw_x = offset_x + x * tile_size
                    draw_y = offset_y + (gs.grid_height - 1 - y) * tile_size

                    Rectangle(
                        pos=(draw_x + 1, draw_y + 1),
                        size=(tile_size - 2, tile_size - 2)
                    )

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
