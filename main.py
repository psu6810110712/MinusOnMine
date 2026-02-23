# main.py - ไฟล์หลักสำหรับรันแอป MinusOnMine
# Idle Mining Game สร้างด้วย Kivy Framework

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen


# =============================================
# หน้าจอต่างๆ (Screens)
# =============================================

class MenuScreen(Screen):
    """หน้าเมนูหลัก - แสดงชื่อเกมและปุ่มเริ่มเล่น"""
    pass


class MiningScreen(Screen):
    """หน้าขุดแร่ - หน้าเล่นหลักของเกม"""
    pass


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
