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

# Se añade la importación de WMI para las temperaturas en Windows.
# Es opcional, por lo que se encapsula en un try-except.
try:
    import wmi
except ImportError:
    wmi = None

class SystemInfoGUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        Window.clearcolor = get_color_from_hex('#2E3440')

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
        Clock.schedule_interval(lambda dt: self.refresh_labels(), 5)

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
                height=self.get_label_height(data, 14),
                line_height=1.2 # Mejora la legibilidad en textos multilínea
            ))

            self.content.add_widget(Widget(size_hint_y=None, height=10))

    def get_label_height(self, text, font_size):
        lines = text.count('\n') + 1
        return lines * (font_size + 12) # Ajustado para el line_height

    def get_system_info(self):
        # La 'Temperatura' se elimina de aquí porque ahora está dentro de 'CPU'
        return {
            'Sistema Operativo': self.get_os_info(),
            'CPU': self.get_cpu_info(),
            'GPU': self.get_gpu_info(),
            'Memoria': self.get_memory_info(),
            'Disco': self.get_disk_info(),
            'Red': self.get_network_info(),
            'Batería': self.get_battery_info(),
            'Tiempo de Actividad': self.get_uptime_info()
        }

    def get_windows_info(self):
        version_info = platform.version()
        release_info = platform.release()
        edition = "Unknown"
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
                edition = winreg.QueryValueEx(key, "ProductName")[0]
        except:
            pass
        return f"{edition} (Versión: {version_info}, Release: {release_info})"

    def get_linux_info(self):
        try:
            with open('/etc/os-release') as f:
                lines = f.readlines()
            os_info = {}
            for line in lines:
                if '=' in line:
                    key, value = line.split('=', 1)
                    os_info[key] = value.strip().strip('"')
            name = os_info.get('PRETTY_NAME', 'Linux (distribución desconocida)')
            version = os_info.get('VERSION_ID', 'versión no disponible')
            return f"{name} (Versión: {version})"
        except FileNotFoundError:
            return "Linux (información detallada no disponible)"

    def get_os_info(self):
        system = platform.system()
        if system == "Windows":
            os_details = self.get_windows_info()
        elif system == "Linux":
            os_details = self.get_linux_info()
        else:
            os_details = f"Sistema operativo no soportado: {system}"
        architecture = f"Arquitectura: {platform.machine()}"
        return f"{os_details}\n{architecture}"

    ### --- MÉTODO 'get_cpu_info' MODIFICADO --- ###
    def get_cpu_info(self):
        try:
            # --- Información principal de la CPU ---
            name = "Información no disponible"
            if platform.system() == 'Windows':
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                    name = winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
            elif platform.system() == 'Linux':
                with open('/proc/cpuinfo') as f:
                    for line in f:
                        if "model name" in line:
                            name = line.split(':')[1].strip()
                            break
            
            physical = psutil.cpu_count(logical=False)
            logical = psutil.cpu_count(logical=True)
            total_usage = psutil.cpu_percent()
            per_core_usage = psutil.cpu_percent(percpu=True)
            
            cpu_info_str = (f"{name}\n"
                            f"Núcleos: {physical} físicos, {logical} lógicos\n"
                            f"Uso total: {total_usage}%\n")
            
            core_usage_str = "\n".join([f"  · Uso Núcleo {i}: {usage}%" for i, usage in enumerate(per_core_usage)])
            cpu_info_str += core_usage_str

            # --- Información de Temperatura ---
            temp_str = "\nTemperaturas:"
            temps_found = False
            
            if platform.system() == 'Linux':
                if hasattr(psutil, "sensors_temperatures"):
                    temps = psutil.sensors_temperatures()
                    if 'coretemp' in temps:
                        for i, core in enumerate(temps['coretemp']):
                            temp_str += f"\n  · {core.label}: {core.current}°C"
                        temps_found = True

            elif platform.system() == 'Windows':
                if wmi:
                    try:
                        wmi_instance = wmi.WMI(namespace="root\\OpenHardwareMonitor")
                        sensors = wmi_instance.Sensor()
                        cpu_temps = [s for s in sensors if s.SensorType == 'Temperature' and 'CPU' in s.Name]
                        if cpu_temps:
                            for sensor in cpu_temps:
                                temp_str += f"\n  · {sensor.Name}: {sensor.Value}°C"
                            temps_found = True
                    except Exception:
                        pass # Falla si OHM no está corriendo

            if temps_found:
                cpu_info_str += temp_str
            else:
                cpu_info_str += "\nTemperaturas: No disponibles"

            return cpu_info_str

        except Exception:
            return "Información de CPU no disponible"

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
    
    # El método get_temperature_info() ha sido eliminado.

    def get_memory_info(self):
        mem = psutil.virtual_memory()
        total = round(mem.total / (1024**3), 2)
        used = round(mem.used / (1024**3), 2)
        available = round(mem.available / (1024**3), 2)
        return (f"Total: {total} GB\n"
                f"Usado: {used} GB ({mem.percent}%)\n"
                f"Disponible: {available} GB")

    def get_disk_info(self):
        disks = []
        for partition in psutil.disk_partitions():
            if partition.fstype:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disks.append(
                        f"{partition.device} ({partition.mountpoint}): {round(usage.used / (1024 ** 3), 2)} / "
                        f"{round(usage.total / (1024 ** 3), 2)} GB ({usage.percent}%)"
                    )
                except PermissionError:
                    continue
        return "\n".join(disks)

    def get_network_info(self):
        nets = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == 2:
                    nets.append(f"{name}: {addr.address}")
        return "\n".join(nets)

    def get_battery_info(self):
        try:
            battery = psutil.sensors_battery()
            if battery:
                tiempo = ("Conectado" if battery.power_plugged and battery.secsleft == psutil.POWER_TIME_UNLIMITED
                          else "Calculando..." if battery.power_plugged else f"{round(battery.secsleft / 60)} min restantes")
                estado = "Cargando" if battery.power_plugged else "Descargando"
                
                return (f"Porcentaje: {battery.percent}%\n"
                        f"Estado: {estado}\n"
                        f"Tiempo: {tiempo}")
        except Exception:
            pass
        return "No disponible o no detectada"

    def get_uptime_info(self):
        uptime_seconds = time.time() - psutil.boot_time()
        return str(timedelta(seconds=int(uptime_seconds)))

class SystemInfoApp(App):
    def build(self):
        self.title = 'Sysfo v1.3' # Versión actualizada
        return SystemInfoGUI()

if __name__ == '__main__':
    SystemInfoApp().run()