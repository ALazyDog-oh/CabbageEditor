import json

from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QGuiApplication
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineWidgets import QWebEngineView
from ui.DockWidget import AddDock, RemoveDock
from utils.Bridge import get_bridge
from utils.CentralManager import CentralManager


class BrowserWidget(QWebEngineView):
    def __init__(self, Main_Window, url:str):
        super(BrowserWidget, self).__init__(Main_Window)
        self.Main_Window = Main_Window
        self.CentralManager = CentralManager()
        self.url = url

        self.setMinimumSize(1, 1)
        self.setStyleSheet("background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.page().setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        self.load(self.url)
        self.setContentsMargins(0, 0, 0, 0)

        self.setup_web_channel()
        self.connect_signals()

    def setup_web_channel(self):
        self.channel = QWebChannel()
        self.bridge = get_bridge(self.CentralManager)
        self.channel.registerObject("pyBridge", self.bridge)
        self.page().setWebChannel(self.channel)

    def connect_signals(self):
        self.bridge.create_route.connect(self.AddDockWidget)
        self.bridge.remove_route.connect(self.RemoveDockWidget)
        self.bridge.command_to_main.connect(self.handle_command_to_main)

    def AddDockWidget(self, routename, routepath, position, floatposition, size):
        if not routename or not routepath:
            print("错误：routename 和 routepath 不能为空")
            return
        browser = QWebEngineView()
        browser.is_main_browser = False
        dock_area, isFloat, pos = self.get_dock_area(position, floatposition)

        if self.CentralManager.docks.get(routename):
            self.RemoveDockWidget(routename)
            del self.CentralManager.docks[routename]
            return
        try:
            dock = AddDock(browser, routename, routepath, self.CentralManager, self.Main_Window, isFloat)
            # With a global singleton bridge, main connections are already set in connect_signals.
            # Avoid duplicating connections here to prevent multiple slot invocations.
            if isFloat:
                if size:
                    dock.resize(size.get("width"),size.get("height"))
                    dock.browser.resize(size.get("width"),size.get("height"))
                dock.setWindowFlags(dock.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
                dock.move(pos)
                dock.show()
            else:
                self.Main_Window.addDockWidget(dock_area, dock)

        except Exception as e:
            print(f"添加停靠窗口失败: {str(e)}")
            browser.deleteLater()

    def RemoveDockWidget(self, routename):
        browser = self.CentralManager.docks.get(routename)
        dock = self.CentralManager.docks.get(routename)
        if dock:
            self.Main_Window.removeDockWidget(dock)
            RemoveDock(browser, routename, self.CentralManager)

    def get_dock_area(self, position, floatposition):
        position_map = {
            "left": (Qt.DockWidgetArea.LeftDockWidgetArea, False, None),
            "right": (Qt.DockWidgetArea.RightDockWidgetArea, False, None),
            "top": (Qt.DockWidgetArea.TopDockWidgetArea, False, None),
            "bottom": (Qt.DockWidgetArea.BottomDockWidgetArea, False, None),
        }

        if position.lower() == "float":
            screen = QGuiApplication.primaryScreen()
            float_position_map = {
                "top_left": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topLeft()),
                "bottom_left": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().bottomLeft()-QPoint(0,200)),
                "top_right": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topRight()-QPoint(150,0)),
                "bottom_right": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().bottomRight()-QPoint(150,200)),
                "center": (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().center()),
            }
            return float_position_map.get(floatposition.lower(), (Qt.DockWidgetArea.AllDockWidgetAreas, True, screen.geometry().topLeft()))

        return position_map.get(
            position.lower(), (Qt.DockWidgetArea.LeftDockWidgetArea, False, None)
        )

    def handle_command_to_main(self, command_name, command_data):
        if command_name == "go_home":
            self.load(self.url)
            return

        if command_name == "input_event":
            # Swallow input_event logs: parse silently, no prints
            try:
                _ = json.loads(command_data) if isinstance(command_data, str) else command_data
            except Exception:
                pass
            return

        # Fallback: retain minimal logging for unknown commands if needed
        # print(f"[Bridge] Unknown command: {command_name} data={command_data}")
        return

    def closeEvent(self, event):
        try:
            # Disconnect signals to this BrowserWidget (auto-disconnect happens on QObject dtor, but we ensure it)
            try:
                self.bridge.create_route.disconnect(self.AddDockWidget)
            except Exception:
                pass
            try:
                self.bridge.remove_route.disconnect(self.RemoveDockWidget)
            except Exception:
                pass
            try:
                self.bridge.command_to_main.disconnect(self.handle_command_to_main)
            except Exception:
                pass
            # Unhook WebChannel and deregister object
            try:
                if hasattr(self, "channel") and self.channel:
                    self.channel.deregisterObject("pyBridge")
            except Exception:
                pass
            try:
                if self.page():
                    self.page().setWebChannel(None)
            except Exception:
                pass
            # Delete channel later to free resources
            if hasattr(self, "channel") and self.channel:
                self.channel.deleteLater()
        finally:
            super().closeEvent(event)
