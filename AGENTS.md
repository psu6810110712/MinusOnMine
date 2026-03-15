# AGENTS.md - Development Guide for MinusOnMine

This file provides guidance for agentic coding agents working on the MinusOnMine project.

---

## 1. Project Overview

MinusOnMine is a top-down mining RPG game built with Python and Kivy framework. Players plan mining routes, collect resources, and upgrade their abilities across rounds.

- **Language**: Python 3.13
- **Framework**: Kivy
- **Entry Point**: `python main.py`
- **No formal test suite exists** - tests should be added using pytest

---

## 2. Build & Run Commands

### Running the Game
```bash
python main.py
```

### Running Tests (No tests currently exist)
```bash
pytest                           # Run all tests
pytest tests/test_game_logic.py  # Run single test file
pytest -k "ore"                  # Run tests matching pattern
pytest -v                        # Verbose output
```

### Linting & Type Checking (Not configured)
```bash
ruff check .   # If ruff is added
mypy .         # If mypy is added
```

---

## 3. Code Style Guidelines

### 3.1 File Structure
```
MinusOnMine/
├── main.py              # Entry point, ScreenManager, PlayerWidget
├── game_logic.py        # GameState, core mechanics
├── game_data.py         # Data models, constants, ore/upgrade definitions
├── widgets.py           # Custom Kivy widgets
├── minusonmine.kv       # Kivy layout definitions
├── assets/              # Sprites, fonts, images
└── save_data.json       # Save file (gitignored)
```

### 3.2 Import Order
Follow this order, separated by blank lines:
1. Standard library (`random`, `json`, etc.)
2. Third-party libraries (`kivy`, `pytest`)
3. Local imports (`from game_logic import ...`)

```python
import random
from typing import Dict

from kivy.app import App
from kivy.properties import StringProperty

from game_logic import GameState
from game_data import ORES
```

### 3.3 Naming Conventions
- **Classes**: `PascalCase` (e.g., `GameState`, `PlayerWidget`)
- **Functions/Methods**: `snake_case` (e.g., `generate_map`, `buy_torch`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAP_WIDTH`, `STARTING_MONEY`)
- **Private methods**: `_leading_underscore` (e.g., `_weighted_random_ore`)

### 3.4 Type Hints
Use type hints for function parameters and return types. Use `typing` module for complex types.

```python
def get_tile(self, x: int, y: int) -> str | None:
    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
        return self.grid_map[y][x]
    return None
```

### 3.5 Dataclasses for Data Models
Use `@dataclass` for structured data (ores, upgrades, config):

```python
from dataclasses import dataclass
from typing import Dict

@dataclass
class Ore:
    ore_id: str
    name: str
    value: int
    weight: float
    color: tuple
    image_path: str = ""

ORES: Dict[str, Ore] = {
    "stone": Ore("stone", "Stone", 1, 100, (0.5, 0.5, 0.5, 1), ""),
}
```

### 3.6 Kivy Widget Patterns
- Define Kivy properties at class level using `StringProperty`, `NumericProperty`, etc.
- Initialize properties in `__init__` via `super().__init__(**kwargs)`
- Register custom widgets with `Factory` for use in `.kv` files:

```python
from kivy.factory import Factory
Factory.register('SellOverlay', cls=SellOverlay)

class MyWidget(Widget):
    text = StringProperty("")
```

### 3.7 Error Handling
- Use explicit error messages for game logic failures
- Return `False`/`None` for failed operations rather than raising exceptions:

```python
def buy_torch(self):
    if self.money >= self.torch_price:
        self.money -= self.torch_price
        self.torch_count += 1
        return True
    return False
```

### 3.8 Comments & Documentation
- Use comments for game-specific logic (Thai explanations common in this repo)
- Add docstrings for complex functions and classes

```python
def generate_map(self):
    """สุ่มวางแร่ลงในตาราง โดยเช็กระยะห่างจากน้ำ"""
    ...
```

### 3.9 Formatting
- Line length: ~100 characters (flexible for readability)
- Use 4 spaces for indentation (Kivy and Python standard)
- One blank line between top-level definitions

---

## 4. Git Workflow

- **Main branch**: `main` - stable releases
- **Develop branch**: `develop` - integration branch
- **Feature branches**: `feature/<topic>` - new features

**Commit guidelines**: Commit small, commit often, write clear commit messages.

---

## 5. Adding New Features

### Adding New Ores (edit `game_data.py`)
```python
ORES: Dict[str, Ore] = {
    "new_ore": Ore("new_ore", "New Ore", value, weight, color, ""),
}
```

### Adding New Upgrades (edit `game_data.py`)
```python
UPGRADES: Dict[str, Upgrade] = {
    "new_upgrade": Upgrade("new_upgrade", "Name", cost, {"attribute": value}),
}
```

### Adding New Widgets
1. Create widget class in `widgets.py`
2. Register with `Factory` in `main.py`
3. Add to `minusonmine.kv` for layout

---

## 6. Known Issues & TODOs

- No test coverage - prioritize adding tests for new features
- Save system uses JSON (see `save_data.json`)
- Camera system in `camera.py` handles viewport
- Map uses grid-based collision detection via `WATER_MAP`

---

## 7. Quick Reference

| Task | Command |
|------|---------|
| Run game | `python main.py` |
| Run tests | `pytest` |

**Key Files**:
- `main.py:18` - GameState import
- `game_data.py:61` - Ore definitions
- `game_logic.py:11` - GameState class
- `widgets.py` - UI components
