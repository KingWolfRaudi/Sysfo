import platform
import sys
import os
import subprocess
import re
from datetime import datetime, timedelta
import psutil
import time

def get_os_info():
    system = platform.system()
    
    if system == "Windows":
        return get_windows_info()
    elif system == "Linux":
        return get_linux_info()
    else:
        return f"Sistema operativo no soportado: {system}"

def get_windows_info():
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

def get_linux_info():
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

def get_cpu_info():
    system = platform.system()
    
    if system == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as key:
                processor_name = winreg.QueryValueEx(key, "ProcessorNameString")[0]
                return processor_name.strip()
        except:
            try:
                output = subprocess.check_output(["wmic", "cpu", "get", "name"]).decode('utf-8').strip()
                if "Name" in output:
                    return output.replace("Name", "").strip()
            except:
                return platform.processor()
    
    elif system == "Linux":
        try:
            with open('/proc/cpuinfo') as f:
                for line in f:
                    if "model name" in line:
                        return re.sub(r".*model name.*:", "", line, 1).strip()
                f.seek(0)
                for line in f:
                    if "Hardware" in line:
                        return re.sub(r".*Hardware.*:", "", line, 1).strip()
                f.seek(0)
                for line in f:
                    if "Processor" in line:
                        return re.sub(r".*Processor.*:", "", line, 1).strip()
        except:
            pass
    
    return platform.processor() if platform.processor() else "Información no disponible"

# --- FUNCIÓN MODIFICADA ---
# Se ha reemplazado la lógica de esta función por la del script con GUI.
def get_gpu_info():
    """
    Detecta la GPU usando los métodos del script con interfaz gráfica (Kivy).
    """
    gpus = []
    try:
        if platform.system() == 'Windows':
            # Usa el comando WMIC para obtener los nombres de las controladoras de video
            output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"], text=True, stderr=subprocess.DEVNULL)
            # Limpia la salida para obtener solo los nombres, excluyendo el encabezado "Name"
            gpus = [line.strip() for line in output.split('\n') if line.strip() and "Name" not in line]
        
        elif platform.system() == 'Linux':
            # Usa el comando lspci y filtra las líneas que contienen 'VGA' o '3D'
            output = subprocess.check_output(["lspci"], text=True, stderr=subprocess.DEVNULL)
            gpus = [line.split(':', 2)[2].strip() for line in output.split('\n') if 'VGA' in line or '3D' in line]
            
    except Exception as e:
        # Si ocurre un error (ej. comando no encontrado), no hace nada y deja la lista de GPUs vacía.
        # El mensaje de error se manejará en el bloque 'main'.
        pass

    # Une la lista de GPUs con el formato de indentación esperado o devuelve un mensaje de error.
    return "\n  ".join(gpus) if gpus else "No se pudo detectar la GPU"
# --- FIN DE LA FUNCIÓN MODIFICADA ---

def get_memory_info():
    mem = psutil.virtual_memory()
    total_gb = round(mem.total / (1024 ** 3), 2)
    available_gb = round(mem.available / (1024 ** 3), 2)
    used_percent = mem.percent
    return f"{total_gb} GB totales, {available_gb} GB disponibles ({used_percent}% usado)"

def get_disk_info():
    partitions = psutil.disk_partitions()
    info = []
    for partition in partitions:
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            info.append(f"{partition.device} ({partition.mountpoint}): {round(usage.total / (1024**3), 2)} GB totales, {round(usage.free / (1024**3), 2)} GB libres ({usage.percent}% usado)")
        except:
            continue
    return "\n  ".join(info) if info else "Información no disponible"

def get_network_info():
    if_addrs = psutil.net_if_addrs()
    net_info = []
    
    for interface, addresses in if_addrs.items():
        for addr in addresses:
            if addr.family == 2:  # AF_INET (IPv4)
                net_info.append(f"Interfaz: {interface}, IPv4: {addr.address}")
            # Se omite AF_PACKET para no mostrar direcciones MAC y simplificar la salida
    
    return "\n  ".join(net_info) if net_info else "Información no disponible"

def get_uptime():
    boot_time_seconds = psutil.boot_time()
    uptime_seconds = time.time() - boot_time_seconds
    uptime_str = str(timedelta(seconds=uptime_seconds))
    return uptime_str.split('.')[0] # Eliminar microsegundos

def get_system_temperature():
    # Esta función depende de dependencias externas (OpenHardwareMonitor en Windows)
    # o de archivos específicos del sistema en Linux. Se mantiene la lógica original.
    if platform.system() == "Linux":
        try:
            temps = []
            for sensor in os.listdir('/sys/class/thermal'):
                if sensor.startswith('thermal_zone'):
                    try:
                        with open(f'/sys/class/thermal/{sensor}/temp') as f:
                            temp = int(f.read()) / 1000
                            temps.append(f"{temp}°C")
                    except:
                        continue
            return ", ".join(temps) if temps else "No disponible"
        except:
            return "No disponible"
    elif platform.system() == "Windows":
        # La obtención de temperatura en Windows es compleja sin librerías de terceros.
        # Se deja un mensaje informativo.
        return "No disponible (requiere OpenHardwareMonitor y la librería WMI)"
    return "No disponible"

def main():
    print("\n" + "="*50)
    print("INFORMACIÓN COMPLETA DEL SISTEMA".center(50))
    print("="*50)
    
    print("\n[+] Sistema Operativo:")
    print("  " + get_os_info())
    print(f"  Arquitectura: {platform.machine()}")
    print(f"  Versión de Python: {sys.version.split()[0]}")
    
    print("\n[+] CPU:")
    print("  Procesador: " + get_cpu_info())
    print(f"  Núcleos físicos: {psutil.cpu_count(logical=False)}")
    print(f"  Núcleos lógicos: {psutil.cpu_count(logical=True)}")
    print("  Temperatura: " + get_system_temperature())
    
    print("\n[+] GPU:")
    gpu_info = get_gpu_info()
    # Este bloque se mantiene para ofrecer sugerencias si la detección falla
    if "No se pudo detectar" in gpu_info:
        print("  " + gpu_info)
        print("  Sugerencias:")
        print("  1. En Windows, ejecuta 'dxdiag' o revisa el Administrador de Dispositivos.")
        print("  2. En Linux, prueba 'lspci | grep VGA' o 'nvidia-smi'.")
        print("  3. Asegúrate de tener los drivers de gráficos instalados.")
    else:
        print("  " + gpu_info)
    
    print("\n[+] Memoria RAM:")
    print("  " + get_memory_info())
    
    print("\n[+] Almacenamiento:")
    print("  " + get_disk_info())
    
    print("\n[+] Red:")
    print("  " + get_network_info())
    
    print("\n[+] Tiempo de actividad:")
    print("  " + get_uptime())
    
    print("\n" + "="*50)
    print(f"Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*50)

    if platform.system() == "Windows":
        os.system("pause")
    else:
        input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()