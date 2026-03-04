# camera.py
from kivy.graphics import Color, Ellipse, Line, Rectangle

class CameraController:
    def __init__(self, zoom=1.0):
        self.zoom = max(1.0, float(zoom))
        self.offset_x = 0.0
        self.offset_y = 0.0

    def update(self, player_pos, player_size, viewport_size, world_size):
        player_x, player_y = player_pos
        player_w, player_h = player_size
        view_w, view_h = viewport_size
        world_w, world_h = world_size

        player_cx = player_x + (player_w / 2.0)
        player_cy = player_y + (player_h / 2.0)
        target_x = (view_w / 2.0) - (player_cx * self.zoom)
        target_y = (view_h / 2.0) - (player_cy * self.zoom)

        scaled_world_w = world_w * self.zoom
        scaled_world_h = world_h * self.zoom

        if scaled_world_w <= view_w:
            self.offset_x = (view_w - scaled_world_w) / 2.0
        else:
            min_x = view_w - scaled_world_w
            self.offset_x = min(0.0, max(min_x, target_x))

        if scaled_world_h <= view_h:
            self.offset_y = (view_h - scaled_world_h) / 2.0
        else:
            min_y = view_h - scaled_world_h
            self.offset_y = min(0.0, max(min_y, target_y))

        return self.offset_x, self.offset_y

    def visible_world_rect(self, viewport_size, world_size):
        view_w, view_h = viewport_size
        world_w, world_h = world_size

        visible_w = view_w / self.zoom
        visible_h = view_h / self.zoom

        if world_w <= visible_w:
            cam_x = 0.0
            cam_w = world_w
        else:
            cam_x = -self.offset_x / self.zoom
            cam_x = min(world_w - visible_w, max(0.0, cam_x))
            cam_w = visible_w

        if world_h <= visible_h:
            cam_y = 0.0
            cam_h = world_h
        else:
            cam_y = -self.offset_y / self.zoom
            cam_y = min(world_h - visible_h, max(0.0, cam_y))
            cam_h = visible_h

        return cam_x, cam_y, cam_w, cam_h


class MinimapRenderer:
    def __init__(self, padding=4, line_width=1.2, min_dot=6, max_dot=12):
        self.padding = padding
        self.line_width = line_width
        self.min_dot = min_dot
        self.max_dot = max_dot

    def draw(self, widget, world_size, camera_rect, player_pos, background_source):
        world_w, world_h = world_size
        cam_x, cam_y, cam_w, cam_h = camera_rect
        player_x, player_y = player_pos

        map_draw_w = max(1, widget.width - self.padding * 2)
        map_draw_h = max(1, widget.height - self.padding * 2)
        base_x = widget.x + self.padding
        base_y = widget.y + self.padding

        scale_x = map_draw_w / world_w
        scale_y = map_draw_h / world_h

        widget.canvas.after.clear()
        with widget.canvas.after:
            Color(1, 1, 1, 1)
            Rectangle(pos=(base_x, base_y), size=(map_draw_w, map_draw_h), source=background_source)

            cam_mx = base_x + (cam_x * scale_x)
            cam_my = base_y + (cam_y * scale_y)
            cam_mw = min(map_draw_w, cam_w * scale_x)
            cam_mh = min(map_draw_h, cam_h * scale_y)

            cam_mx = min(base_x + map_draw_w - cam_mw, max(base_x, cam_mx))
            cam_my = min(base_y + map_draw_h - cam_mh, max(base_y, cam_my))

            Color(1, 1, 1, 0.8)
            Line(rectangle=(cam_mx, cam_my, cam_mw, cam_mh), width=self.line_width)

            player_mx = base_x + (player_x * scale_x)
            player_my = base_y + (player_y * scale_y)
            dot_size = max(self.min_dot, min(self.max_dot, map_draw_w * 0.03))

            Color(1, 0.2, 0.2, 1)
            Ellipse(
                pos=(player_mx - dot_size / 2, player_my - dot_size / 2),
                size=(dot_size, dot_size),
            )
