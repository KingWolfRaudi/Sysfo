import platform
import psutil
import os
import subprocess
import time
from datetime import timedelta
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

class SystemInfoGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        Window.clearcolor = get_color_from_hex('#2E3440')  # Fondo oscuro

        self.add_widget(Label(
            text='[b]SYSTEM INFORMATION[/b]',
            markup=True,
            font_size=24,
            color=get_color_from_hex('#88C0D0'),
            size_hint_y=None,
            height=40
        ))

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=10)
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.add_widget(self.scroll)

        self.refresh_labels()
        Clock.schedule_interval(lambda dt: self.refresh_labels(), 5)  # Actualiza cada 5 segundos

    def refresh_labels(self):
        self.content.clear_widgets()
        sys_info = self.get_system_info()
        for section, data in sys_info.items():
            self.content.add_widget(Label(
                text=f"[b]{section.upper()}[/b]",
                markup=True,
                font_size=18,
                color=get_color_from_hex('#A3BE8C'),
                size_hint_y=None,
                height=30
            ))

            self.content.add_widget(Label(
                text=data,
                font_size=14,
                color=get_color_from_hex('#E5E9F0'),
                size_hint_y=None,
                height=self.get_label_height(data, 14)
            ))

            self.content.add_widget(Widget(size_hint_y=None, height=10))  # Separador

    def get_label_height(self, text, font_size):
        lines = text.count('\n') + 1
        return lines * (font_size + 8)

    def get_system_info(self):
        return {
            'Sistema Operativo': self.get_os_info(),
            'CPU': self.get_cpu_info(),
            'GPU': self.get_gpu_info(),
            'Temperatura': self.get_temperature_info(),
            'Memoria': self.get_memory_info(),
            'Disco': self.get_disk_info(),
            'Red': self.get_network_info(),
            'Batería': self.get_battery_info(),
            'Tiempo de Actividad': self.get_uptime_info()
        }

    def get_os_info(self):
        return f"{platform.system()} {platform.release()}\n{platform.version()}"

    def get_cpu_info(self):
        try:
            if platform.system() == 'Windows':
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                    r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                    name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                    physical = psutil.cpu_count(logical=False)
                    logical = psutil.cpu_count(logical=True)
                    percent = psutil.cpu_percent()
                    per_core = psutil.cpu_percent(percpu=True)
                    core_info = "\n".join([f"Núcleo {i}: {p}%" for i, p in enumerate(per_core)])
                    return f"{name}\nNúcleos: {physical} físicos, {logical} lógicos\nUso total: {percent}%\n{core_info}"
            elif platform.system() == 'Linux':
                with open('/proc/cpuinfo') as f:
                    for line in f:
                        if "model name" in line:
                            return line.split(':')[1].strip()
        except:
            return platform.processor()
        return "Información no disponible"

    def get_gpu_info(self):
        gpus = []
        try:
            if platform.system() == 'Windows':
                output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"])
                gpus = [line.strip() for line in output.decode().split('\n') if line.strip() and line.strip() != "Name"]
            elif platform.system() == 'Linux':
                output = subprocess.check_output(["lspci"]).decode()
                gpus = [line.split(':')[2].strip() for line in output.split('\n') if 'VGA' in line or '3D' in line]
        except:
            gpus = ["No se detectó GPU"]
        return "\n".join(gpus) if gpus else "No se detectó GPU"

    def get_temperature_info(self):
        temps = []
        try:
            if platform.system() == 'Linux':
                for sensor in os.listdir('/sys/class/thermal'):
                    if sensor.startswith('thermal_zone'):
                        with open(f'/sys/class/thermal/{sensor}/temp') as f:
                            temp = int(f.read()) / 1000
                            temps.append(f"{sensor}: {temp:.1f} °C")
            else:
                temps.append("Temperatura no disponible en Windows sin OpenHardwareMonitor")
        except:
            temps.append("No disponible")
        return "\n".join(temps)

    def get_memory_info(self):
        mem = psutil.virtual_memory()
        total = round(mem.total / (1024**3), 2)
        used = round(mem.used / (1024**3), 2)
        available = round(mem.available / (1024**3), 2)
        return (f"Total: {total} GB\nUsado: {used} GB\nDisponible: {available} GB\n"
                f"Porcentaje usado: {mem.percent}%")

    def get_disk_info(self):
        disks = []
        for partition in psutil.disk_partitions():
            if partition.fstype:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append(
                        f"{partition.device}: {round(usage.used / (1024 ** 3), 2)} / "
                        f"{round(usage.total / (1024 ** 3), 2)} GB ({usage.percent}%)"
                    )
                except PermissionError:
                    continue
        return "\n".join(disks)

    def get_network_info(self):
        nets = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:  # AF_INET
                    nets.append(f"{name}: {addr.address}")
        return "\n".join(nets)

    def get_battery_info(self):
        battery = psutil.sensors_battery()
        if battery:
            tiempo = ("Ilimitado" if battery.secsleft == psutil.POWER_TIME_UNLIMITED
                      else f"{round(battery.secsleft / 60)} minutos")
            return (f"Porcentaje: {battery.percent}%\n"
                    f"En carga: {'Sí' if battery.power_plugged else 'No'}\n"
                    f"Tiempo restante: {tiempo}")
        return "No disponible o no detectada"

    def get_uptime_info(self):
        uptime_seconds = time.time() - psutil.boot_time()
        return str(timedelta(seconds=int(uptime_seconds)))

class SystemInfoApp(App):
    def build(self):
        self.title = 'Sysfo v1.1'
        return SystemInfoGUI()

if __name__ == '__main__':
    SystemInfoApp().run()
