import json
import os
import time
import traceback

from PyQt6.QtCore import QThread, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtWidgets import QApplication
from mcp_client import qa_one_sync
from utils.file_handle import FileHandler
from utils.static_components import root_dir, scene_dict

try:
    import CoronaEngine

    print("import CoronaEngine")
except ImportError:
    from corona_engine_fallback import CoronaEngine

_bridge_singleton = None


def get_bridge(central_manager=None):
    global _bridge_singleton
    if _bridge_singleton is None:
        instance = Bridge(central_manager)
        _bridge_singleton = instance
    else:
        if central_manager is not None and getattr(_bridge_singleton, "central_manager", None) is None:
            _bridge_singleton.central_manager = central_manager
    return _bridge_singleton


class WorkerThread(QThread):
    work_finished = pyqtSignal()
    result_ready = pyqtSignal(object)

    def __init__(self, func, *args, parent: QObject | None = None, **kwargs):
        super().__init__(parent)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.result_ready.emit(result)
        except Exception as e:
            print(f"Worker thread error: {str(e)}")
        finally:
            self.work_finished.emit()


class Bridge(QObject):
    create_route = pyqtSignal(str, str, str, str, object)
    ai_message = pyqtSignal(str)
    remove_route = pyqtSignal(str)
    ai_response = pyqtSignal(str)
    dock_event = pyqtSignal(str, str)
    command_to_main = pyqtSignal(str, str)
    key_event = pyqtSignal(str)
    script_dir = os.path.join(root_dir, "CabbageEditor", "Backend", "script")
    saves_dir = os.path.join(root_dir, "CabbageEditor", "saves")
    os.makedirs(script_dir, exist_ok=True)
    os.makedirs(saves_dir, exist_ok=True)
    obj_dir = ""

    def __init__(self, central_manager=None):
        super().__init__()
        self.camera_position = [0.0, 5.0, 10.0]
        self.camera_forward = [0.0, 1.5, 0.0]
        self.central_manager = central_manager
        self._workers: set[WorkerThread] = set()

    @pyqtSlot(str, str, str, str, str)
    def add_dock_widget(self, routename, routepath, position="left", floatposition="None", size=None):
        try:
            if isinstance(size, str):
                size = json.loads(size)
        except json.JSONDecodeError:
            size = None
        self.create_route.emit(routename, routepath, position, floatposition, size)

    @pyqtSlot(str)
    def remove_dock_widget(self, routename):
        self.remove_route.emit(routename)

    @pyqtSlot(str, str)
    def create_actor(self, scene_name, obj_path):
        name = os.path.basename(obj_path)
        object = CoronaEngine.Actor(obj_path)
        scene_dict[scene_name]["actor_dict"][name] = {
            "actor": object,
            "path": obj_path
        }

    @pyqtSlot()
    def remove_actor(self):
        scene_dict["mainscene"] = {
            "scene": None,
            "actor_dict": {}
        }

    @pyqtSlot(str)
    def create_scene(self, data):
        scene_name = json.loads(data).get("sceneName")
        if scene_name not in scene_dict:
            scene_dict[scene_name] = {
                "scene": CoronaEngine.Scene(),
                "actor_dict": {}
            }
        else:
            print(f"场景已存在: {scene_name}")


    @pyqtSlot(str, str)
    def send_message_to_dock(self, routename, json_data):
        try:
            self.central_manager.send_json_to_dock(routename, json_data)
        except json.JSONDecodeError:
            print("发送消息失败：无效的JSON字符串")
        except Exception as e:
            print(f"发送消息失败: {str(e)}")

    @pyqtSlot(str)
    def send_message_to_ai(self, ai_message: str):
        def ai_work() -> str:
            try:
                msg_data = json.loads(ai_message)
                query = msg_data.get("message", "")
                response_text = qa_one_sync(query=query)
                final_response = {
                    "type": "ai_response",
                    "content": response_text,
                    "status": "success",
                    "timestamp": int(time.time()),
                }
                return json.dumps(final_response)
            except Exception as e:
                error_response = {
                    "type": "error",
                    "content": str(e),
                    "status": "error",
                    "timestamp": int(time.time()),
                }
                return json.dumps(error_response)

        worker = WorkerThread(ai_work, parent=self)
        worker.result_ready.connect(self.ai_response.emit)
        worker.finished.connect(worker.deleteLater)
        worker.finished.connect(lambda: self._workers.discard(worker))
        self._workers.add(worker)
        worker.start()

    @pyqtSlot(str, str)
    def open_file_dialog(self, sceneName, file_type="model"):
        file_handler = FileHandler()
        if file_type == "model":
            _, file_path = file_handler.open_file("选择模型文件", "3D模型文件 (*.obj *.fbx *.dae)")
            if file_path:
                try:
                    print(f"选择的模型文件路径: {file_path}")
                    name = os.path.basename(file_path)
                    object = CoronaEngine.Actor(file_path)
                    scene_dict[sceneName]["actor_dict"][name] = {
                        "actor": object,
                        "path": file_path
                    }
                    response = {
                        "name": name,
                        "path": file_path,
                    }
                    self.dock_event.emit("actorCreated", json.dumps(response))
                except Exception as e:
                    print(f"创建角色失败: {str(e)}")
        elif file_type == "scene":
            content, file_path = file_handler.open_file("选择场景文件", "场景文件 (*.json)")
            if file_path:
                try:
                    scene_dict[sceneName]["actor_dict"] = {}
                    scene_data = json.loads(content)
                    actors = []
                    for actor in scene_data.get("actors", []):
                        path = actor.get("path")
                        if path:
                            actor_obj = CoronaEngine.Actor(path)
                            name = os.path.basename(path)
                            scene_dict[sceneName]["actor_dict"][name] = {
                                "name": name,
                                "actor": actor_obj,
                                "path": path
                            }
                            actors.append({
                                "name": name,
                                "path": path
                            })
                    self.dock_event.emit("sceneLoaded", json.dumps({"actors": actors}))
                except Exception as e:
                    print(f"加载场景失败: {str(e)}")
                    error_response = {"type": "error", "message": str(e)}
                    self.dock_event.emit("sceneError", json.dumps(error_response))

    @pyqtSlot(str, str)
    def send_message_to_main(self, command_name, command_data):
        try:
            try:
                self.command_to_main.emit(command_name, command_data)
            except Exception:
                pass
            key_text = self._extract_key_text(command_name, command_data)
            if key_text:
                try:
                    self.key_event.emit(key_text)
                except Exception:
                    pass
        except Exception as e:
            print(f"send_message_to_main failed: {str(e)}")

    def _extract_key_text(self, command_name, command_data):
        try:
            if not command_data:
                return None
            payload = None
            if not isinstance(command_data, str):
                payload = command_data
            else:
                s = command_data.strip()
                if not s:
                    return None
                try:
                    payload = json.loads(s)
                except Exception:
                    return s
            if isinstance(payload, dict):
                for k in ('key', 'code', 'combo', 'text', 'name', 'key_text'):
                    v = payload.get(k)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, list) and v:
                        try:
                            return '+'.join(map(str, v))
                        except Exception:
                            pass
                if isinstance(payload.get('keys'), list) and payload.get('keys'):
                    try:
                        return '+'.join(map(str, payload.get('keys')))
                    except Exception:
                        pass
                if isinstance(payload.get('comboKeys'), list) and payload.get('comboKeys'):
                    try:
                        return '+'.join(map(str, payload.get('comboKeys')))
                    except Exception:
                        pass
                for container in ('event', 'data', 'payload', 'value', 'detail'):
                    sub = payload.get(container)
                    if isinstance(sub, dict):
                        for k in ('key', 'code', 'combo', 'keys', 'comboKeys', 'text', 'name', 'key_text'):
                            v = sub.get(k)
                            if isinstance(v, str) and v.strip():
                                return v.strip()
                            if isinstance(v, list) and v:
                                try:
                                    return '+'.join(map(str, v))
                                except Exception:
                                    pass
            if command_name and isinstance(command_name, str) and command_name.lower().startswith('key'):
                return command_name
        except Exception:
            return None
        return None

    @pyqtSlot(str, str)
    def actor_delete(self, sceneName, actorName):
        try:
            if actorName not in scene_dict[sceneName]["actor_dict"]:
                print(f"当前场景中的角色列表: {list(scene_dict[sceneName]['actor_dict'].keys())}")
                raise ValueError(f"角色 '{actorName}' 不在场景 '{sceneName}' 中")
            del scene_dict[sceneName]["actor_dict"][actorName]
            print(f"成功移除角色: {actorName}")
        except Exception as e:
            print(f"Actor delete failed: {str(e)}")
            return str(e)

    @pyqtSlot(str)
    def actor_operation(self, data):
        try:
            Actor_data = json.loads(data)
            sceneName = Actor_data.get("sceneName")
            actorName = Actor_data.get("actorName")
            Operation = Actor_data.get("Operation")
            x = float(Actor_data.get("x", 0.0))
            y = float(Actor_data.get("y", 0.0))
            z = float(Actor_data.get("z", 0.0))
            match Operation:
                case "Scale":
                    CoronaEngine.Actor.scale(scene_dict[sceneName]["actor_dict"][actorName]["actor"], [x, y, z])
                case "Move":
                    CoronaEngine.Actor.move(scene_dict[sceneName]["actor_dict"][actorName]["actor"], [x, y, z])
                case "Rotate":
                    CoronaEngine.Actor.rotate(scene_dict[sceneName]["actor_dict"][actorName]["actor"], [x, y, z])
        except Exception as e:
            print(f"Actor transform error: {str(e)}")
            return

    @pyqtSlot(str)
    def camera_move(self, data):
        try:
            move_data = json.loads(data)
            sceneName = move_data.get("sceneName", "scene1")
            position = move_data.get("position", [0.0, 5.0, 10.0])
            forward = move_data.get("forward", [0.0, 1.5, 0.0])
            up = move_data.get("up", [0.0, -1.0, 0.0])
            fov = float(move_data.get("fov", 45.0))
            CoronaEngine.Scene.setCamera(scene_dict[sceneName]["scene"], position, forward, up, fov)
        except Exception as e:
            print(f"摄像头移动错误: {str(e)}")

    @pyqtSlot(str)
    def sun_direction(self, data):
        try:
            sun_data = json.loads(data)
            sceneName = sun_data.get("sceneName", "scene1")
            px = float(sun_data.get("px", 1.0))
            py = float(sun_data.get("py", 1.0))
            pz = float(sun_data.get("pz", 1.0))
            direction = [px, py, pz]
            CoronaEngine.Scene.setSunDirection(scene_dict[sceneName]["scene"], direction)
        except Exception as e:
            error_response = {"type": "error", "message": str(e)}
            self.dock_event.emit("sunDirectionError", json.dumps(error_response))

    @pyqtSlot(str, int)
    def execute_python_code(self, code, index):
        try:
            filename = f"blockly_code.py"
            filepath = os.path.join(self.script_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            run_script_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "runScript.py"
            )
            script_files = []
            for f in os.listdir(self.script_dir):
                if f.startswith("blockly_code") and f.endswith(".py"):
                    script_files.append(f.replace(".py", ""))
            run_script_content = ""
            for script in script_files:
                run_script_content += f"import script.{script}\n"

            run_script_content += "\ndef run():\n"
            for script in script_files:
                run_script_content += f"    script.{script}.run()\n"

            with open(run_script_path, "w", encoding="utf-8") as f:
                f.write(run_script_content)
            print(f"[DEBUG] 脚本文件创建成功: {filepath}")
            print(f"[DEBUG] runScript.py创建/覆盖成功: {run_script_path}")
        except Exception as e:
            print(f"[ERROR] 执行Python代码时出错: {str(e)}")
            error_response = {
                "status": "error",
                "message": str(e),
                "stacktrace": traceback.format_exc(),
            }
            self.dock_event.emit("scriptError", json.dumps(error_response))

    @pyqtSlot(str)
    def scene_save(self, data):
        try:
            scene_data = json.loads(data)
            file_handler = FileHandler()

            content = json.dumps(scene_data, indent=4)
            save_path = file_handler.save_file(content, "保存场景文件", "场景文件 (*.json)")
            if save_path:
                print(f"[DEBUG] 场景保存成功: {save_path}")
                self.dock_event.emit(
                    "sceneSaved", json.dumps({"status": "success", "filepath": save_path})
                )
            else:
                print("[DEBUG] 场景保存失败")
                self.dock_event.emit(
                    "sceneSaved", json.dumps({"status": "error", "filepath": save_path})
                )
        except Exception as e:
            print(f"[ERROR] 保存场景失败: {str(e)}")
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.dock_event.emit("sceneError", json.dumps(error_response))

    @pyqtSlot()
    def close_process(self):
        QApplication.quit()
        os._exit(0)

    @pyqtSlot(str, str)
    def forward_dock_event(self, event_type, event_data):
        self.dock_event.emit(event_type, event_data)
