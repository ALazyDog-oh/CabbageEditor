import os
from typing import Any, Dict, Optional

from PyQt6.QtCore import QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QWidget


class RenderWidget(QWidget):
    geometry_changed = pyqtSignal(QRect)

    def __init__(self, Main_Window, scene_dict: Dict[str, Dict[str, Any]]):
        super(RenderWidget, self).__init__()
        self.Main_Window = Main_Window

        self.setGeometry(0, 0, self.Main_Window.width(), self.Main_Window.height())
        self.setStyleSheet("QLabel {background-color: transparent;}")

        try:
            import CoronaEngine
            print("import CoronaEngine")
        except ImportError:
            from corona_engine_fallback import CoronaEngine

        self.mainscene = CoronaEngine.Scene(
            int(self.winId()),False
        )
        self.mainscene.setCamera(
            [10.0, 10.0, 0.0], [-1.0, -1.0, -1.0], [0.0, 1.0, 0.0], 45.0
        )
        print(self.mainscene)
        scene_dict["mainscene"]={
            "scene":self.mainscene,
            "actor_dict":{}
        }

        self.image_path = os.path.join(os.path.dirname(__file__), "background.png")
        self.pixmap: Optional[QPixmap] = None
        if self.image_path and os.path.exists(self.image_path):
            self.pixmap = QPixmap(self.image_path)
            self.update()
        else:
            print(f"警告: 背景图片路径不存在: {self.image_path}")

    def paintEvent(self, event) -> None:
        if self.pixmap:
            painter = QPainter(self)
            painter.drawPixmap(self.rect(), self.pixmap)

    def scene(self):
        return self.winId()