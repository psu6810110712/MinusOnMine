from dataclasses import dataclass
from typing import Dict

# =============================================
# ระบบ Design (UI Theme)
# =============================================
@dataclass
class UITheme:
    """เก็บสี, ขนาดฟอนต์, และค่า UI ทั่วแอป"""
    # ขนาดฟอนต์
    TITLE_SIZE: int = 32
    HEADING_SIZE: int = 24
    BODY_SIZE: int = 18
    SMALL_SIZE: int = 14
    
    # สี layout
    BACKGROUND_DARK: tuple = (0.12, 0.12, 0.18, 1)
    BACKGROUND_LIGHT: tuple = (0.25, 0.20, 0.15, 1)
    TEXT_PRIMARY: tuple = (1, 1, 1, 1)
    TEXT_SECONDARY: tuple = (0.7, 0.7, 0.8, 1)
    GROUND_COLOR: tuple = (0.25, 0.20, 0.15, 1)

# =============================================
# คลาสแร่ (Ore Class)
# =============================================
@dataclass
class Ore:
    """เก็บข้อมูลแร่: ชื่อ, ค่าขาย, ความหนาแน่น, สี"""
    ore_id: str         # ชื่อระบุตัวตน เช่น "stone", "gold"
    name: str           # ชื่อแสดง เช่น "Stone", "Gold"
    value: int          # มูลค่าเมื่อขายแร่นี้
    weight: float       # ความหนาแน่น (weight สูง = ได้บ่อย)
    color: tuple        # สี RGBA สำหรับแสดงผลบน Map

# =============================================
# คลาสอัปเกรด (Upgrade Class)
# =============================================
@dataclass
class Upgrade:
    """เก็บข้อมูลอัปเกรด: ชื่อ, ราคา, คุณสมบัติพิเศษ"""
    upgrade_id: str     # ชื่อระบุตัวตน เช่น "pickaxe_tier_1"
    name: str           # ชื่อแสดง เช่น "Iron Pickaxe"
    cost: int           # ราคาการอัปเกรด
    attributes: Dict    # คุณสมบัติพิเศษ เช่น {"multiplier": 2}

# =============================================
# คลาสเซตติ้งเกม (GameConfig Class)
# =============================================
@dataclass
class GameConfig:
    """เก็บค่าคงที่ของเกม"""
    STARTING_MONEY: int = 0     # เงินเริ่มต้น
    MAX_LEVEL: int = 99         # ระดับสูงสุด
    MAP_WIDTH: int = 20         # ความกว้างแผนที่
    MAP_HEIGHT: int = 20        # ความสูงแผนที่

# =============================================
# ข้อมูลแร่ 12 ชนิด (เรียงตามความหายาก)
# =============================================
ORES: Dict[str, Ore] = {
    "stone": Ore("stone", "Stone", 1, 100, (0.50, 0.50, 0.50, 1)),  # เทา
    "coal": Ore("coal", "Coal", 5, 80, (0.20, 0.20, 0.20, 1)),  # ดำ
    "copper": Ore("copper", "Copper", 15, 60, (0.80, 0.50, 0.20, 1)),  # ส้มทองแดง
    "iron": Ore("iron", "Iron", 30, 40, (0.60, 0.60, 0.70, 1)),  # เทาเงิน
    "gold": Ore("gold", "Gold", 100, 20, (1.00, 0.84, 0.00, 1)),  # ทอง
    "diamond": Ore("diamond", "Diamond", 500, 5, (0.50, 0.90, 1.00, 1)),  # ฟ้าอ่อน
    "emerald": Ore("emerald", "Emerald", 1000, 3, (0.18, 0.80, 0.44, 1)),  # เขียวมรกต
    "ruby": Ore("ruby", "Ruby", 2500, 2, (0.90, 0.11, 0.14, 1)),  # แดงทับทิม
    "sapphire": Ore("sapphire", "Sapphire", 5000, 1, (0.15, 0.30, 0.85, 1)),  # น้ำเงินไพลิน
    "amethyst": Ore("amethyst", "Amethyst", 10000, 0.5, (0.60, 0.30, 0.80, 1)),  # ม่วงอเมทิสต์
    "obsidian": Ore("obsidian", "Obsidian", 50000, 0.1, (0.10, 0.05, 0.15, 1)),  # ดำม่วง
    "mithril": Ore("mithril", "Mithril", 100000, 0.01, (0.75, 0.90, 1.00, 1)),  # ฟ้าเรืองแสง
}

# =============================================
# ข้อมูลอัปเกรด 8 ชนิด
# =============================================
UPGRADES: Dict[str, Upgrade] = {
    "pickaxe_tier_1": Upgrade("pickaxe_tier_1", "Iron Pickaxe", 100, {"multiplier": 2}),
    "pickaxe_tier_2": Upgrade("pickaxe_tier_2", "Gold Pickaxe", 1000, {"multiplier": 5}),
    "pickaxe_tier_3": Upgrade("pickaxe_tier_3", "Diamond Pickaxe", 10000, {"multiplier": 15}),
    "miner_bot_1": Upgrade("miner_bot_1", "Basic Auto-Miner", 500, {"auto_mine_rate": 1}),
    "miner_bot_2": Upgrade("miner_bot_2", "Advanced Auto-Miner", 5000, {"auto_mine_rate": 5}),
    "luck_potion": Upgrade("luck_potion", "Luck Potion", 2000, {"luck_bonus": 1.5}),
    "backpack_expansion": Upgrade("backpack_expansion", "Bigger Backpack", 3000, {"capacity": 50}),
    "dynamite": Upgrade("dynamite", "Dynamite", 15000, {"mine_burst": 10}),
}

# =============================================
# ค่าคงที่เกม
# =============================================
STARTING_MONEY = 0
MAX_LEVEL = 99
MAP_WIDTH = 20
MAP_HEIGHT = 20

# สีพื้น (ทางเดิน) บน map - ใช้จาก UITheme
GROUND_COLOR = UITheme().GROUND_COLOR