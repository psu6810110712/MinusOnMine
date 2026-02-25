# ข้อมูลแร่ 12 ชนิด (เรียงตามความหายาก)
ORES = {
    "stone": {"name": "Stone", "value": 1, "weight": 100},
    "coal": {"name": "Coal", "value": 5, "weight": 80},
    "copper": {"name": "Copper", "value": 15, "weight": 60},
    "iron": {"name": "Iron", "value": 30, "weight": 40},
    "gold": {"name": "Gold", "value": 100, "weight": 20},
    "diamond": {"name": "Diamond", "value": 500, "weight": 5},
    "emerald": {"name": "Emerald", "value": 1000, "weight": 3},
    "ruby": {"name": "Ruby", "value": 2500, "weight": 2},
    "sapphire": {"name": "Sapphire", "value": 5000, "weight": 1},
    "amethyst": {"name": "Amethyst", "value": 10000, "weight": 0.5},
    "obsidian": {"name": "Obsidian", "value": 50000, "weight": 0.1},
    "mithril": {"name": "Mithril", "value": 100000, "weight": 0.01},
}

# ข้อมูลอัปเกรด 8 ชนิด
UPGRADES = {
    "pickaxe_tier_1": {"name": "Iron Pickaxe", "cost": 100, "multiplier": 2},
    "pickaxe_tier_2": {"name": "Gold Pickaxe", "cost": 1000, "multiplier": 5},
    "pickaxe_tier_3": {"name": "Diamond Pickaxe", "cost": 10000, "multiplier": 15},
    "miner_bot_1": {"name": "Basic Auto-Miner", "cost": 500, "auto_mine_rate": 1},
    "miner_bot_2": {"name": "Advanced Auto-Miner", "cost": 5000, "auto_mine_rate": 5},
    "luck_potion": {"name": "Luck Potion", "cost": 2000, "luck_bonus": 1.5},
    "backpack_expansion": {"name": "Bigger Backpack", "cost": 3000, "capacity": 50},
    "dynamite": {"name": "Dynamite", "cost": 15000, "mine_burst": 10},
}

# สีของแร่แต่ละชนิด (RGBA) สำหรับแสดงผลบน Map
ORE_COLORS = {
    "stone":    (0.50, 0.50, 0.50, 1),  # เทา
    "coal":     (0.20, 0.20, 0.20, 1),  # ดำ
    "copper":   (0.80, 0.50, 0.20, 1),  # ส้มทองแดง
    "iron":     (0.60, 0.60, 0.70, 1),  # เทาเงิน
    "gold":     (1.00, 0.84, 0.00, 1),  # ทอง
    "diamond":  (0.50, 0.90, 1.00, 1),  # ฟ้าอ่อน
    "emerald":  (0.18, 0.80, 0.44, 1),  # เขียวมรกต
    "ruby":     (0.90, 0.11, 0.14, 1),  # แดงทับทิม
    "sapphire": (0.15, 0.30, 0.85, 1),  # น้ำเงินไพลิน
    "amethyst": (0.60, 0.30, 0.80, 1),  # ม่วงอเมทิสต์
    "obsidian": (0.10, 0.05, 0.15, 1),  # ดำม่วง
    "mithril":  (0.75, 0.90, 1.00, 1),  # ฟ้าเรืองแสง
}

# สีพื้น (ทางเดิน) บน map
GROUND_COLOR = (0.25, 0.20, 0.15, 1)

# ค่าคงที่อื่นๆ
STARTING_MONEY = 0
MAX_LEVEL = 99
MAP_WIDTH = 96
MAP_HEIGHT = 96