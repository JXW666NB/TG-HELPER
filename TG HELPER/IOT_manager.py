import json
import os
import socket
import threading
import time
from typing import Dict, List, Optional, Any

# 尝试导入MQTT库，若失败则标记并后续自动安装
MQTT_AVAILABLE = False
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    pass

class IOTDevice:
    """单个设备的数据结构"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data['name']
        self.device_type = data['device_type']  # 'bool' or 'complex'
        self.protocol = data['protocol']        # 'udp', 'tcp', 'mqtt'
        self.params = data.get('params', {})
        self.icon = data.get('icon', '')
        self.on_msg = data.get('on_msg', 'ON')
        self.off_msg = data.get('off_msg', 'OFF')
        self.presets = data.get('presets', [])
        self.notes = data.get('notes', '')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'protocol': self.protocol,
            'params': self.params,
            'icon': self.icon,
            'on_msg': self.on_msg,
            'off_msg': self.off_msg,
            'presets': self.presets,
            'notes': self.notes
        }

class IOTSensor:
    """传感器设备"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data['name']
        self.protocol = data['protocol']
        self.params = data.get('params', {})
        self.icon = data.get('icon', '')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'protocol': self.protocol,
            'params': self.params,
            'icon': self.icon
        }

class IOTTrigger:
    """触发器：当传感器收到指定消息时执行一系列任务"""
    def __init__(self, data: dict):
        self.id = data.get('id')
        self.name = data['name']
        self.sensor_name = data['sensor_name']
        self.match_pattern = data.get('match_pattern', '')
        self.tasks = data.get('tasks', [])   # 任务列表
        self.enabled = data.get('enabled', True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sensor_name': self.sensor_name,
            'match_pattern': self.match_pattern,
            'tasks': self.tasks,
            'enabled': self.enabled
        }

class IOTManager:
    """物联网设备管理器（单例模式）"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_dir="./device_configs"):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
        self.devices_file = os.path.join(config_dir, "devices.json")
        self.sensors_file = os.path.join(config_dir, "sensors.json")
        self.triggers_file = os.path.join(config_dir, "triggers.json")

        self.devices: Dict[str, IOTDevice] = {}
        self.sensors: Dict[str, IOTSensor] = {}
        self.triggers: Dict[str, IOTTrigger] = {}

        # MQTT客户端管理
        self.mqtt_clients: Dict[str, mqtt.Client] = {}
        self.mqtt_threads: Dict[str, threading.Thread] = {}
        self.mqtt_running: Dict[str, bool] = {}

        # TCP服务器管理
        self.tcp_servers: Dict[str, socket.socket] = {}
        self.tcp_threads: Dict[str, threading.Thread] = {}
        self.tcp_running: Dict[str, bool] = {}

        self.ai_callback = None

        self._load_all()
        self._start_sensor_listeners()

    # -------------------- 库自动安装 --------------------
    @staticmethod
    def _ensure_mqtt_library():
        """确保 paho-mqtt 已安装，否则自动安装"""
        global MQTT_AVAILABLE, mqtt
        if MQTT_AVAILABLE:
            return True
        try:
            import subprocess
            import sys
            print("[IOT] 正在自动安装 paho-mqtt 库...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "paho-mqtt", "-q"])
            import paho.mqtt.client as mqtt
            MQTT_AVAILABLE = True
            print("[IOT] paho-mqtt 安装成功")
            return True
        except Exception as e:
            print(f"[IOT] 自动安装 paho-mqtt 失败: {e}")
            return False

    # -------------------- 持久化 --------------------
    def _load_all(self):
        self._load_devices()
        self._load_sensors()
        self._load_triggers()

    def _load_devices(self):
        self.devices.clear()
        if os.path.exists(self.devices_file):
            with open(self.devices_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('devices', []):
                    dev = IOTDevice(item)
                    self.devices[dev.name] = dev

    def _save_devices(self):
        data = {'devices': [dev.to_dict() for dev in self.devices.values()]}
        with open(self.devices_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_sensors(self):
        self.sensors.clear()
        if os.path.exists(self.sensors_file):
            with open(self.sensors_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('sensors', []):
                    sen = IOTSensor(item)
                    self.sensors[sen.name] = sen

    def _save_sensors(self):
        data = {'sensors': [s.to_dict() for s in self.sensors.values()]}
        with open(self.sensors_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_triggers(self):
        self.triggers.clear()
        if os.path.exists(self.triggers_file):
            with open(self.triggers_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get('triggers', []):
                    trig = IOTTrigger(item)
                    self.triggers[trig.name] = trig

    def _save_triggers(self):
        data = {'triggers': [t.to_dict() for t in self.triggers.values()]}
        with open(self.triggers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # -------------------- 设备管理 API --------------------
    def add_device(self, device_data: dict) -> bool:
        import time
        device_data['id'] = str(int(time.time() * 1000))
        dev = IOTDevice(device_data)
        if dev.name in self.devices:
            return False
        self.devices[dev.name] = dev
        self._save_devices()
        return True

    def remove_device(self, name: str) -> bool:
        if name in self.devices:
            del self.devices[name]
            self._save_devices()
            return True
        return False

    def get_device(self, name: str) -> Optional[IOTDevice]:
        return self.devices.get(name)

    def list_devices(self) -> List[Dict]:
        result = []
        for dev in self.devices.values():
            info = {
                "name": dev.name,
                "type": dev.device_type,
                "protocol": dev.protocol,
                "notes": dev.notes
            }
            if dev.device_type == 'complex':
                presets = [{"index": i+1, "name": p['name']} for i, p in enumerate(dev.presets)]
                info["presets"] = presets
            result.append(info)
        return result

    # -------------------- 传感器管理 API --------------------
    def add_sensor(self, sensor_data: dict) -> bool:
        import time
        sensor_data['id'] = str(int(time.time() * 1000))
        sen = IOTSensor(sensor_data)
        if sen.name in self.sensors:
            return False
        self.sensors[sen.name] = sen
        self._save_sensors()
        self._start_sensor_listener(sen)
        return True

    def remove_sensor(self, name: str) -> bool:
        if name in self.sensors:
            self._stop_sensor_listener(name)
            del self.sensors[name]
            self._save_sensors()
            return True
        return False

    # -------------------- 触发器管理 API --------------------
    def add_trigger(self, trigger_data: dict) -> bool:
        import time
        trigger_data['id'] = str(int(time.time() * 1000))
        trig = IOTTrigger(trigger_data)
        if trig.name in self.triggers:
            return False
        self.triggers[trig.name] = trig
        self._save_triggers()
        return True

    def remove_trigger(self, name: str) -> bool:
        if name in self.triggers:
            del self.triggers[name]
            self._save_triggers()
            return True
        return False

    def get_triggers(self) -> List[Dict]:
        return [t.to_dict() for t in self.triggers.values()]

    # -------------------- 设备控制核心 --------------------
    def send_to_device(self, device_name: str, command: str) -> str:
        dev = self.get_device(device_name)
        if not dev:
            return f"错误：设备 '{device_name}' 不存在"

        raw_msg = None
        if dev.device_type == 'bool':
            if command.lower() == 'on':
                raw_msg = dev.on_msg
            elif command.lower() == 'off':
                raw_msg = dev.off_msg
            else:
                return f"错误：布尔设备只接受 on/off，收到 '{command}'"
        else:
            matched = False
            for preset in dev.presets:
                if preset['name'] == command or str(preset.get('index', '')) == command:
                    raw_msg = preset['msg']
                    matched = True
                    break
            if not matched:
                raw_msg = command

        if not raw_msg:
            return f"错误：无法生成指令（设备 '{device_name}'）"

        try:
            if dev.protocol == 'udp':
                result = self._send_udp(dev.params.get('ip'), dev.params.get('port'), raw_msg)
            elif dev.protocol == 'tcp':
                result = self._send_tcp(dev.params.get('ip'), dev.params.get('port'), raw_msg)
            elif dev.protocol == 'mqtt':
                result = self._send_mqtt(dev.params.get('topic'), raw_msg, dev.params)
            else:
                result = f"错误：不支持的协议 '{dev.protocol}'"
            # 记录日志
            from iot_logger import iot_logger
            iot_logger.log_device_command(device_name, command, result, dev.protocol)
            return result
        except Exception as e:
            error_msg = f"发送失败：{str(e)}"
            from iot_logger import iot_logger
            iot_logger.log_device_command(device_name, command, error_msg, dev.protocol)
            return error_msg

    def _send_udp(self, ip, port, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(msg.encode('utf-8'), (ip, int(port)))
        sock.close()
        return f"UDP 已发送到 {ip}:{port} -> {msg}"

    def _send_tcp(self, ip, port, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, int(port)))
        sock.sendall(msg.encode('utf-8'))
        sock.close()
        return f"TCP 已发送到 {ip}:{port} -> {msg}"

    def _send_mqtt(self, topic, msg, params):
        if not self._ensure_mqtt_library():
            return "错误：MQTT 库未安装且自动安装失败"
        client_id = params.get('client_id', f'tghelper_sender_{int(time.time())}')
        client = mqtt.Client(client_id=client_id)
        if params.get('username') and params.get('password'):
            client.username_pw_set(params['username'], params['password'])
        broker = params.get('broker', 'localhost')
        port = int(params.get('port', 1883))
        try:
            client.connect(broker, port, 60)
            client.publish(topic, msg)
            client.disconnect()
            return f"MQTT 已发布到 {topic} -> {msg}"
        except Exception as e:
            return f"MQTT 发送失败：{str(e)}"

    # -------------------- 传感器监听核心 --------------------
    def _start_sensor_listeners(self):
        for sensor in self.sensors.values():
            self._start_sensor_listener(sensor)

    def _start_sensor_listener(self, sensor: IOTSensor):
        name = sensor.name
        if name in self.mqtt_running or name in self.tcp_running:
            return
        if sensor.protocol == 'udp':
            threading.Thread(target=self._udp_sensor_listener, args=(sensor,), daemon=True).start()
        elif sensor.protocol == 'tcp':
            threading.Thread(target=self._tcp_sensor_listener, args=(sensor,), daemon=True).start()
        elif sensor.protocol == 'mqtt':
            if self._ensure_mqtt_library():
                threading.Thread(target=self._mqtt_sensor_listener, args=(sensor,), daemon=True).start()
            else:
                print(f"[传感器 {name}] MQTT 库不可用，跳过监听")

    def _stop_sensor_listener(self, sensor_name: str):
        if sensor_name in self.mqtt_running:
            self.mqtt_running[sensor_name] = False
            if sensor_name in self.mqtt_clients:
                try:
                    self.mqtt_clients[sensor_name].loop_stop()
                    self.mqtt_clients[sensor_name].disconnect()
                except:
                    pass
            if sensor_name in self.mqtt_threads:
                self.mqtt_threads[sensor_name].join(timeout=2)
            self.mqtt_clients.pop(sensor_name, None)
            self.mqtt_threads.pop(sensor_name, None)
            self.mqtt_running.pop(sensor_name, None)
        if sensor_name in self.tcp_running:
            self.tcp_running[sensor_name] = False
            if sensor_name in self.tcp_servers:
                try:
                    self.tcp_servers[sensor_name].close()
                except:
                    pass
            if sensor_name in self.tcp_threads:
                self.tcp_threads[sensor_name].join(timeout=2)
            self.tcp_servers.pop(sensor_name, None)
            self.tcp_threads.pop(sensor_name, None)
            self.tcp_running.pop(sensor_name, None)

    def _stop_all_listeners(self):
        """停止所有传感器监听器"""
        for name in list(self.mqtt_running.keys()):
            self._stop_sensor_listener(name)
        for name in list(self.tcp_running.keys()):
            self._stop_sensor_listener(name)
        # 注：UDP 监听器没有独立标志，但通过 _stop_sensor_listener 也会停止
        for name in list(self.sensors.keys()):
            self._stop_sensor_listener(name)

    # ---------- UDP ----------
    def _udp_sensor_listener(self, sensor: IOTSensor):
        ip = sensor.params.get('ip', '0.0.0.0')
        port = int(sensor.params.get('port', 0))
        if port == 0:
            print(f"[传感器 {sensor.name}] 端口为0，跳过监听")
            return
        if ip == '255.255.255.255' or ip == '':
            ip = '0.0.0.0'
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((ip, port))
            print(f"[传感器 {sensor.name}] UDP 监听 {ip}:{port}")
        except Exception as e:
            print(f"[传感器 {sensor.name}] UDP 绑定失败: {e}")
            return
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                msg = data.decode('utf-8')
                print(f"[传感器 {sensor.name}] 收到: {msg}")
                self._on_sensor_message(sensor.name, msg, source_addr=addr)
            except Exception as e:
                print(f"[传感器 {sensor.name}] UDP 错误: {e}")
                break

    # ---------- TCP ----------
    def _tcp_sensor_listener(self, sensor: IOTSensor):
        ip = sensor.params.get('ip', '0.0.0.0')
        port = int(sensor.params.get('port', 0))
        if port == 0:
            print(f"[传感器 {sensor.name}] 端口为0，跳过监听")
            return
        if ip == '255.255.255.255':
            ip = '0.0.0.0'
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((ip, port))
            server.listen(5)
            self.tcp_servers[sensor.name] = server
            self.tcp_running[sensor.name] = True
            print(f"[传感器 {sensor.name}] TCP 监听 {ip}:{port}")
        except Exception as e:
            print(f"[传感器 {sensor.name}] TCP 绑定失败: {e}")
            return
        while self.tcp_running.get(sensor.name, False):
            try:
                server.settimeout(1.0)
                conn, addr = server.accept()
                threading.Thread(target=self._handle_tcp_connection, args=(sensor.name, conn), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[传感器 {sensor.name}] TCP 错误: {e}")
                break

    def _handle_tcp_connection(self, sensor_name: str, conn: socket.socket):
        try:
            data = conn.recv(1024)
            if data:
                msg = data.decode('utf-8')
                print(f"[传感器 {sensor_name}] 收到: {msg}")
                self._on_sensor_message(sensor_name, msg, source_conn=conn)
        except Exception as e:
            print(f"[传感器 {sensor_name}] TCP 接收错误: {e}")
        finally:
            conn.close()

    # ---------- MQTT ----------
    def _mqtt_sensor_listener(self, sensor: IOTSensor):
        if not MQTT_AVAILABLE:
            print(f"[传感器 {sensor.name}] MQTT 库未安装，跳过")
            return
        name = sensor.name
        params = sensor.params
        broker = params.get('broker', 'localhost')
        port = int(params.get('port', 1883))
        topic = params.get('topic', '')
        username = params.get('username', '')
        password = params.get('password', '')
        client_id = params.get('client_id', f'tghelper_sensor_{name}_{int(time.time())}')

        if not topic:
            print(f"[传感器 {name}] 未配置 Topic，跳过")
            return

        client = mqtt.Client(client_id=client_id)
        client.on_connect = lambda c, u, f, rc: self._on_mqtt_connect(name, rc)
        client.on_message = lambda c, u, m: self._on_mqtt_message(name, m.payload, m.topic)
        client.on_subscribe = lambda c, u, mid, granted_qos: print(f"[传感器 {name}] 订阅主题 {topic} 成功")
        
        if username:
            client.username_pw_set(username, password)

        try:
            client.connect(broker, port, 60)
            client.subscribe(topic, qos=1)
            client.loop_start()
            self.mqtt_clients[name] = client
            self.mqtt_running[name] = True
            print(f"[传感器 {name}] MQTT 已连接 {broker}:{port} (ClientID={client_id})，订阅 {topic}")
        except Exception as e:
            print(f"[传感器 {name}] MQTT 连接失败: {e}")
            return

        while self.mqtt_running.get(name, False):
            time.sleep(1)
        client.loop_stop()
        client.disconnect()
    def _on_mqtt_connect(self, sensor_name, rc):
        if rc == 0:
            print(f"[传感器 {sensor_name}] MQTT 连接成功")
        else:
            print(f"[传感器 {sensor_name}] MQTT 连接失败，错误码: {rc}")
            
    def _on_mqtt_message(self, sensor_name: str, payload, topic: str):
        try:
            if isinstance(payload, bytes):
                msg = payload.decode('utf-8')
            else:
                msg = str(payload)
            print(f"[传感器 {sensor_name}] 收到: {msg} (主题: {topic})")
            self._on_sensor_message(sensor_name, msg, source_topic=topic)
        except Exception as e:
            print(f"[传感器 {sensor_name}] 消息处理失败: {e}, 原始数据: {payload}")

    # ---------- 消息处理与触发器 ----------
    def set_ai_trigger_callback(self, callback):
        """设置传感器触发 AI 的回调，callback 接受一个字符串参数（触发消息）"""
        self.ai_trigger_callback = callback

    def _on_sensor_message(self, sensor_name: str, message: str, source_addr=None, source_conn=None, source_topic=None):
        """
        处理传感器消息
        source_addr: UDP 来源地址 (ip, port)
        source_conn: TCP 连接对象（用于回复）
        source_topic: MQTT 来源主题（用于回复）
        """
        sensor = self.sensors.get(sensor_name)
        if not sensor:
            return
        try:
            from iot_logger import iot_logger
            iot_logger.log_sensor_message(sensor_name, message, sensor.protocol, source_topic or "")
        except Exception as e:
            print(f"[日志] 记录传感器消息失败: {e}")
        protocol = sensor.protocol

        for trigger in self.triggers.values():
            if not trigger.enabled:
                continue
            if trigger.sensor_name != sensor_name:
                continue
            if trigger.match_pattern and trigger.match_pattern not in message:
                continue

            self._current_source = {
                'sensor_name': sensor_name,
                'message': message,
                'addr': source_addr,
                'conn': source_conn,
                'topic': source_topic
            }
            try:
                from iot_logger import iot_logger
                iot_logger.log_trigger_triggered(trigger.name, sensor_name, message)
            except Exception as e:
                print(f"[日志] 记录触发器触发失败: {e}")
            for task in trigger.tasks:
                task_type = task.get('type')
                if task_type == 'ai_notify':
                    custom_prompt = task.get('prompt', '').strip()
                    source_info = f"[传感器: {sensor_name}][触发器: {trigger.name}]"
                    if custom_prompt:
                        ai_prompt = f"{source_info} {custom_prompt}"
                    else:
                        ai_prompt = f"{source_info} 收到消息: {message}"
                    if hasattr(self, 'ai_trigger_callback') and self.ai_trigger_callback:
                        send_reply = task.get('send_reply', False)
                        if send_reply:
                            if protocol == 'udp':
                                def reply_callback(reply_text):
                                    self._send_reply_to_source(sensor_name, reply_text, source_addr=source_addr)
                            elif protocol == 'tcp':
                                def reply_callback(reply_text):
                                    self._send_reply_to_source(sensor_name, reply_text, source_conn=source_conn)
                            elif protocol == 'mqtt':
                                def reply_callback(reply_text):
                                    self._send_reply_to_source(sensor_name, reply_text, source_topic=source_topic)
                            else:
                                reply_callback = None
                            self.ai_trigger_callback(ai_prompt, reply_callback)
                        else:
                            self.ai_trigger_callback(ai_prompt, None)
                elif task_type == 'control_device':
                    device_name = task.get('device_name')
                    command = task.get('command')
                    if device_name and command:
                        self.send_to_device(device_name, command)
                elif task_type == 'qq_notify':
                    target_type = task.get('target_type')
                    target_id = task.get('target_id')
                    content = task.get('content', '').replace('{message}', message)
                    if target_type and target_id:
                        if hasattr(self, 'qq_send_callback'):
                            self.qq_send_callback(target_type, target_id, content)

            # 触发器所有任务执行完毕后，延迟触发巡检（随机 10~30 分钟）
            import random
            from smart_inspector import inspector
            delay_seconds = random.randint(600, 1800)
            inspector.schedule_inspection_after(delay_seconds, reason="post_trigger")
            print(f"[触发器 {trigger.name}] 已触发，将在 {delay_seconds} 秒后执行巡检")

            self._current_source = None

    def _send_reply_to_source(self, sensor_name: str, reply_text: str, source_addr=None, source_conn=None, source_topic=None):
        """将 AI 回复发送回原始传感器（设备）"""
        sensor = self.sensors.get(sensor_name)
        if not sensor:
            print(f"[回传] 找不到传感器 {sensor_name}")
            return
        protocol = sensor.protocol
        params = sensor.params
        try:
            if protocol == 'udp' and source_addr:
                ip, port = source_addr
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(reply_text.encode('utf-8'), (ip, port))
                sock.close()
                print(f"[回传] UDP 已回复 {ip}:{port} -> {reply_text}")
            elif protocol == 'tcp' and source_conn:
                source_conn.sendall(reply_text.encode('utf-8'))
                source_conn.close()
                print(f"[回传] TCP 已回复 -> {reply_text}")
            elif protocol == 'mqtt' and source_topic:
                if self._ensure_mqtt_library():
                    client_id = f'tghelper_reply_{int(time.time())}'
                    client = mqtt.Client(client_id=client_id)
                    if params.get('username') and params.get('password'):
                        client.username_pw_set(params['username'], params['password'])
                    broker = params.get('broker', 'localhost')
                    port = int(params.get('port', 1883))
                    client.connect(broker, port, 60)
                    client.publish(source_topic, reply_text)
                    client.disconnect()
                    print(f"[回传] MQTT 已回复到主题 {source_topic} -> {reply_text}")
                else:
                    print(f"[回传] MQTT 库不可用")
            else:
                print(f"[回传] 无法回复：协议 {protocol} 缺少来源信息")
        except Exception as e:
            print(f"[回传] 发送失败: {e}")

    def set_qq_send_callback(self, callback):
        """设置 QQ 发送回调，callback(target_type, target_id, content)"""
        self.qq_send_callback = callback
        
    def set_ai_callback(self, callback):
        self.ai_callback = callback

iot_manager = IOTManager()
