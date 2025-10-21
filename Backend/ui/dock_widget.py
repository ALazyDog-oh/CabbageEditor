import json

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWidgets import QDockWidget, QWidget
from utils.bridge import get_bridge
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage


class AddDock(QDockWidget):
    def __init__(self, browser, name: str, path: str, CentralManager, Main_Window, isFloat: bool):
        super(AddDock, self).__init__(name, Main_Window)
        self.Main_Window = Main_Window
        self.max_width = int(Main_Window.width() * 0.3)
        self.min_height = int(Main_Window.height() * 0.5)
        self.browser = browser
        self.isFloat = isFloat
        self.centralmanager = CentralManager
        self.name = name
        self.worker_threads = []

        from PyQt6.QtCore import QUrl
        from utils.static_components import url as base_url
        self.url = QUrl(base_url.toString())
        self.url.setFragment(path)

        self.setup_ui()
        self.setup_web_channel()
        self.connect_signals()

        if isFloat:
            self.setFloating(True)
            self.show()

    def setup_ui(self) -> None:
        self.setMinimumSize(1, 1)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.update_stylesheet()
        self.setMaximumWidth(self.max_width)
        self.setMinimumHeight(self.min_height)
        self.setTitleBarWidget(QWidget())
        self.setContentsMargins(0, 0, 0, 0)

        self.browser.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.browser.setStyleSheet("background: transparent;")
        self.browser.page().setBackgroundColor(QColor(Qt.GlobalColor.transparent))
        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        # Create off-the-record profile for this dock to isolate memory/cache
        try:
            self.profile = QWebEngineProfile(self)
            # use ephemeral storage and no cache to minimize accumulation
            self.profile.setOffTheRecord(True)
            try:
                self.profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
                self.profile.setHttpCacheMaximumSize(0)
                self.profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
            except Exception:
                pass
            page = QWebEnginePage(self.profile, self.browser)
            self.browser.setPage(page)
        except Exception:
            self.profile = None
        self.browser.load(self.url)
        # 向页面注入当前 dock 的 routename，供前端事件携带
        try:
            self.browser.loadFinished.connect(lambda ok, name=self.name: self.browser.page().runJavaScript(
                f"window.__dockRouteName = {json.dumps(name)};"))
        except Exception:
            pass

        self.setWidget(self.browser)

    def update_stylesheet(self) ->None:
        self.round_corner_stylesheet = """
            QDockWidget {
                background: rgba(0, 0, 0, 0); 
                border: 8px solid rgba(100, 100, 100, 150);
                border-radius: 5px;
                padding: 4px;
            }
            QDockWidget[floating="true"] {
                border: 8px solid rgba(120, 120, 120, 200);
                padding: 4px;
            }
            QDockWidget::title {
                height: 0px;
            }
        """
        self.setStyleSheet(self.round_corner_stylesheet)

    def setup_web_channel(self) -> None:
        self.channel = QWebChannel()
        self.bridge = get_bridge(self.centralmanager)
        self.channel.registerObject("pybridge", self.bridge)
        # Set on the current page (may be a custom page)
        try:
            self.browser.page().setWebChannel(self.channel)
        except Exception:
            pass
        self.centralmanager.register_dock(self.name, self)

    def connect_signals(self) -> None:
        self.bridge.ai_response.connect(self.send_ai_message_to_js)
        self.bridge.dock_event.connect(self.dock_event)
        self.topLevelChanged.connect(self.handle_top_level_change)
        self.destroyed.connect(self.cleanup_resources)

    def dock_event(self, event_type: str, event_data: str) -> None:
        # 仅处理发给当前 dock 的事件（通过 routename 过滤）
        target_ok = True
        try:
            data_obj = json.loads(event_data) if isinstance(event_data, str) else (event_data or {})
            target = data_obj.get("routename")
            if target is not None and target != self.name:
                return
        except Exception:
            # 解析失败则保守忽略（避免误操作所有 dock）
            return

        if event_type == "drag" and self.isFloating():
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                current_pos = self.pos()
                new_x = current_pos.x() + int(data.get("deltaX", 0))
                new_y = current_pos.y() + int(data.get("deltaY", 0))
                self.move(new_x, new_y)
            except Exception as e:
                print(f"处理拖拽事件失败: {str(e)}")
        elif event_type == "close":
            self.close()
        elif event_type == "float":
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                self.setFloating(bool(data.get("isFloating", False)))
                self.raise_()
            except Exception as e:
                print(f"处理float事件失败: {str(e)}")
        elif event_type == "resize":
            try:
                data = data_obj if isinstance(data_obj, dict) else {}
                x = int(data.get("x", self.pos().x()))
                y = int(data.get("y", self.pos().y()))
                width = int(data.get("width", self.width()))
                height = int(data.get("height", self.height()))
                self.move(x, y)
                self.resize(width, height)
                self.update()
            except Exception as e:
                print(f"处理resize事件失败: {str(e)}")

    def handle_top_level_change(self) -> None:
        if self.isFloating():
            self.setStyleSheet(self.round_corner_stylesheet)
            self.setFeatures(
                QDockWidget.DockWidgetFeature.DockWidgetFloatable
                | QDockWidget.DockWidgetFeature.DockWidgetMovable
                | QDockWidget.DockWidgetFeature.DockWidgetClosable
            )
            self.setMaximumWidth(16777215)
            self.setMinimumHeight(1)
        else:
            self.setStyleSheet(self.round_corner_stylesheet)
            self.setMaximumWidth(self.max_width)
            self.setMinimumHeight(self.min_height)
            if hasattr(self, "browser"):
                self.browser.update()

    def send_message_to_dock(self, json_data: str) -> None:
        self.bridge.dock_event.emit("dockData", json_data)

    def send_message_to_main(self, json_data: str) -> None:
        self.bridge.dock_event.emit("mainData", json_data)

    def send_ai_message_to_js(self, message: str) -> None:
        try:
            if not isinstance(message, str):
                message = str(message)
            try:
                json.loads(message)
                js_code = f"window.receiveAIMessage({message})"
            except:
                js_code = f"window.receiveAIMessage({json.dumps({'content': message})})"

            QTimer.singleShot(0, lambda: self.browser.page().runJavaScript(js_code))
        except Exception as e:
            print(f"发送消息到JS失败: {str(e)}")

    def cleanup_resources(self) -> None:
        try:
            # Disconnect from bridge signals to avoid sending to dead dock
            try:
                self.bridge.ai_response.disconnect(self.send_ai_message_to_js)
            except Exception:
                pass
            try:
                self.bridge.dock_event.disconnect(self.dock_event)
            except Exception:
                pass
            # Unregister and release webchannel resources
            try:
                if hasattr(self, "channel") and self.channel:
                    self.channel.deregisterObject("pybridge")
            except Exception:
                pass
            try:
                if hasattr(self, "browser") and self.browser and self.browser.page():
                    self.browser.page().setWebChannel(None)
            except Exception:
                pass
            if hasattr(self, "channel") and self.channel:
                self.channel.deleteLater()
            # Remove from central manager safely
            try:
                self.centralmanager.delete_dock(self.name)
            except Exception:
                pass
            # Clear and delete profile to free Chromium resources
            try:
                if getattr(self, "profile", None) is not None:
                    try:
                        self.profile.clearHttpCache()
                    except Exception:
                        pass
                    self.profile.deleteLater()
                    self.profile = None
            except Exception:
                pass
            # Schedule browser deletion
            if hasattr(self, "browser"):
                self.browser.deleteLater()
                print(f"清理浏览器资源: {self.name}")
        except Exception as e:
            print(f"资源清理异常: {str(e)}")

    def closeEvent(self, event) -> None:
        try:
            for thread in self.worker_threads:
                thread.quit()
                thread.wait()
            self.worker_threads.clear()
        except Exception as e:
            print(f"关闭事件处理异常: {str(e)}")
        super().closeEvent(event)

class RemoveDock(QWidget):
    def __init__(self, browser, name, central_manager):
        super(RemoveDock, self).__init__()
        self.centralmanager = central_manager
        self.browser = browser
        dock = self.centralmanager.docks.get(name)

        if dock:
            print(f"[DEBUG] 开始删除 {name}")
            dock.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

            def step1() -> None:
                if dock and dock.isWidgetType():
                    content = dock.widget()
                    if content:
                        print(f"[DEBUG] Step1 清理内容 {name}")
                        content.hide()
                        try:
                            if content.page():
                                content.page().setWebChannel(None)
                        except RuntimeError:
                            pass
                        content.setParent(None)
                QTimer.singleShot(50, step2)

            def step2() -> None:
                try:
                    if dock and dock.isWidgetType() and dock.isVisible():
                        print(f"[DEBUG] Step2 删除dock {name}")
                        dock.hide()
                        dock.setParent(None)
                        dock.deleteLater()
                except RuntimeError as e:
                    print(f"[WARN] 对象已提前删除: {str(e)}")

                if name in self.centralmanager.docks:
                    del self.centralmanager.docks[name]

                QTimer.singleShot(50, step3)

            def step3() -> None:
                print(f"[DEBUG] Step3 最终确认 {name}")

            QTimer.singleShot(0, step1)