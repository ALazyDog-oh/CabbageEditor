import os
import sys

from PyQt6.QtCore import Qt, QPoint, QEvent
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QMainWindow, QApplication, QDockWidget
from ui.browser_widget import browser_widget
from ui.custom_window import custom_window
from ui.render_widget import render_widget
from utils.static_components import scene_dict, url


class main_window(QMainWindow):
    def __init__(self):
        self.osd = None
        super(main_window, self).__init__()
        screen = QApplication.primaryScreen().availableGeometry()
        self.setGeometry(0, 0, screen.width(), screen.height())
        self.setWindowTitle("CoronaEngine")
        self.configure_web_engine()

        self.render_widget = render_widget(self, scene_dict)
        self.setCentralWidget(self.render_widget)

        self.osd = custom_window(self)
        self.osd.resize(self.size())
        self.osd.move(self.geometry().x(), self.geometry().y())

        self.browser_widget = browser_widget(self.osd, url)
        self.osd.setCentralWidget(self.browser_widget)

        self.osd.show()

    def changeEvent(self, event) -> None:
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized:
                if self.osd:
                    self.osd.hide()
            elif (self.windowState() in (Qt.WindowState.WindowNoState, Qt.WindowState.WindowMaximized) and
                  event.oldState() == Qt.WindowState.WindowMinimized):
                if self.osd:
                    p = self.mapToGlobal(QPoint(0, 0))
                    self.osd.move(p.x(), p.y())
                    self.osd.show()
        super().changeEvent(event)

    def moveEvent(self, event) -> None:
        x = int(event.pos().x() - event.oldPos().x())
        y = int(event.pos().y() - event.oldPos().y())
        if self.osd:
            self.osd.move(self.osd.pos().x() + x, self.osd.pos().y() + y)
        super().moveEvent(event)

    def reloadWidget(self) -> None:
        # 保持渲染窗口为主窗口中心部件，仅重建 OSD 的 browser_widget
        for dock in self.findChildren(QDockWidget):
            dock.setParent(None)

        for child in self.children():
            if isinstance(child, QWebEngineView):
                child.setParent(None)

        if self.browser_widget:
            self.browser_widget.setParent(None)
        # 重新创建并挂载到 OSD 窗口
        self.browser_widget = browser_widget(self.osd, url)
        self.osd.setCentralWidget(self.browser_widget)

    def closeEvent(self, event) -> None:
        QApplication.instance().quit()
        event.accept()
        os._exit(0)
    
    def resizeEvent(self,event) -> None:
        self.osd.resize(self.size())
        super().resizeEvent(event)

    def configure_web_engine(self) -> None:
        profile = QWebEngineProfile.defaultProfile()
        settings = profile.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.ShowScrollBars, False)
        # Reduce cache/cookies persistence to mitigate memory accumulation
        try:
            profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            profile.setHttpCacheMaximumSize(0)
            profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        except Exception:
            pass

app = QApplication(sys.argv)
window = main_window()
window.show()