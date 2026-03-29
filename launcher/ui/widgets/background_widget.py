from __future__ import annotations

import random
from pathlib import Path

from PySide6.QtCore import QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QCursor, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


class BackgroundWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._background = QPixmap()
        self._particles: list[dict[str, float | int | QColor]] = []
        self._particle_sprites: list[QPixmap] = []
        self._particle_colors = [
            QColor(157, 78, 221),
            QColor(192, 132, 252),
            QColor(216, 180, 254),
        ]
        self._max_particles = 22
        self._bg_shift_x = 0.0
        self._bg_shift_y = 0.0
        self._bg_target_x = 0.0
        self._bg_target_y = 0.0
        self._bg_max_shift = 16.0
        self._bg_margin = 34
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_particles)
        self._timer.start(33)

    def set_background(self, image_path: Path) -> None:
        self._background = QPixmap(str(image_path))
        self._load_particle_sprites(image_path.parent)
        self._rebuild_particles()
        self.update()

    def _load_particle_sprites(self, assets_dir: Path) -> None:
        sprites: list[QPixmap] = []
        excluded = {"background.png", "ico.png", "logo.png", "logo1.png", "logo2.png", "dust.png"}
        for png_file in sorted(assets_dir.glob("*.png")):
            name = png_file.name.lower()
            if name in excluded or name.startswith("logo") or name.startswith("dust"):
                continue
            sprite = QPixmap(str(png_file))
            if not sprite.isNull():
                sprites.append(sprite)
        self._particle_sprites = sprites

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._rebuild_particles()
        super().resizeEvent(event)

    def _rebuild_particles(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        self._particles = [self._spawn_particle(initial=True) for _ in range(self._max_particles)]

    def _spawn_particle(self, initial: bool = False) -> dict[str, float | int | QColor]:
        width = max(1, self.width())
        height = max(1, self.height())
        start_y = random.uniform(0, height)
        return {
            "x": random.uniform(0, width),
            "y": start_y,
            "vx": random.uniform(-0.08, 0.08),
            "vy": random.uniform(-0.35, -0.12),
            "size": random.uniform(2.2, 5.8),
            "age": random.uniform(0.0, 0.5) if initial else 0.0,
            "life": random.uniform(1.2, 2.0),
            "color": random.choice(self._particle_colors),
            "twinkle": random.uniform(0.6, 1.2),
            "scale": random.uniform(0.45, 1.1),
            "sprite": random.randrange(len(self._particle_sprites)) if self._particle_sprites else -1,
        }

    def _tick_particles(self) -> None:
        if self.width() <= 0 or self.height() <= 0:
            return
        self._update_parallax_target()
        self._bg_shift_x += (self._bg_target_x - self._bg_shift_x) * 0.06
        self._bg_shift_y += (self._bg_target_y - self._bg_shift_y) * 0.06
        if len(self._particles) != self._max_particles:
            self._rebuild_particles()
        if not self._particles:
            return

        for index, particle in enumerate(self._particles):
            particle["age"] = float(particle["age"]) + 0.033
            particle["x"] = float(particle["x"]) + float(particle["vx"])
            particle["y"] = float(particle["y"]) + float(particle["vy"])
            particle["vx"] = max(-0.12, min(0.12, float(particle["vx"]) + random.uniform(-0.01, 0.01)))
            particle["vy"] = max(-0.45, min(-0.08, float(particle["vy"]) + random.uniform(-0.008, 0.008)))

            dead = float(particle["age"]) > float(particle["life"])
            out = float(particle["y"]) < -20 or float(particle["x"]) < -20 or float(particle["x"]) > self.width() + 20
            if dead or out:
                self._particles[index] = self._spawn_particle()

        self.update()

    def _update_parallax_target(self) -> None:
        cursor_local = self.mapFromGlobal(QCursor.pos())
        if self.width() <= 1 or self.height() <= 1:
            self._bg_target_x = 0.0
            self._bg_target_y = 0.0
            return

        if not self.rect().contains(cursor_local):
            self._bg_target_x = 0.0
            self._bg_target_y = 0.0
            return

        cx = self.width() / 2.0
        cy = self.height() / 2.0
        nx = max(-1.0, min(1.0, (cursor_local.x() - cx) / cx))
        ny = max(-1.0, min(1.0, (cursor_local.y() - cy) / cy))

        self._bg_target_x = -nx * self._bg_max_shift
        self._bg_target_y = -ny * self._bg_max_shift

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        if self._background.isNull():
            painter.fillRect(self.rect(), Qt.black)
        else:
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            target_rect = QRectF(
                -self._bg_margin + self._bg_shift_x,
                -self._bg_margin + self._bg_shift_y,
                self.width() + self._bg_margin * 2,
                self.height() + self._bg_margin * 2,
            )
            source_rect = QRectF(0.0, 0.0, float(self._background.width()), float(self._background.height()))
            painter.drawPixmap(target_rect, self._background, source_rect)

        painter.setRenderHint(QPainter.Antialiasing, True)
        for particle in self._particles:
            progress = float(particle["age"]) / float(particle["life"])
            if progress < 0.12:
                fade = progress / 0.12
            elif progress > 0.55:
                fade = (1.0 - progress) / 0.45
            else:
                fade = 1.0
            fade = max(0.0, min(1.0, fade))
            twinkle = float(particle["twinkle"])
            alpha_core = int(170 * fade * twinkle)
            alpha_glow = int(90 * fade * twinkle)

            color = QColor(particle["color"])
            glow = QColor(color)
            glow.setAlpha(max(0, min(255, alpha_glow)))
            color.setAlpha(max(0, min(255, alpha_core)))

            size = float(particle["size"])
            x = float(particle["x"])
            y = float(particle["y"])
            sprite_index = int(particle["sprite"])

            painter.setPen(Qt.NoPen)
            if self._particle_sprites and 0 <= sprite_index < len(self._particle_sprites):
                sprite = self._particle_sprites[sprite_index]
                scale = float(particle["scale"])
                width = max(4, int(sprite.width() * scale))
                height = max(4, int(sprite.height() * scale))
                painter.setOpacity(max(0.0, min(1.0, alpha_glow / 255.0)))
                painter.drawPixmap(int(x - width // 2), int(y - height // 2), width, height, sprite)
                painter.setOpacity(max(0.0, min(1.0, alpha_core / 255.0)))
                painter.drawPixmap(int(x - width // 2), int(y - height // 2), width, height, sprite)
                painter.setOpacity(1.0)
            else:
                painter.setBrush(glow)
                painter.drawEllipse(int(x - size * 1.25), int(y - size * 1.25), int(size * 3.0), int(size * 3.0))
                painter.setBrush(color)
                painter.drawEllipse(int(x), int(y), int(size), int(size))
        super().paintEvent(event)
