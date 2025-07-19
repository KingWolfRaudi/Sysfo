import platform
import sys
import os
import subprocess
import re
from datetime import datetime
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
                processor_name = processor_name.strip()
                return processor_name
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

def get_gpu_info():
    system = platform.system()
    gpu_info = []
    
    if system == "Windows":
        # Método 1: Usar dxdiag (el más confiable)
        try:
            import winreg
            try:
                # Verificar GPUs activas en el registro
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}") as key:
                    for i in range(100):
                        try:
                            subkey_name = f"000{i}"
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    driver_desc = winreg.QueryValueEx(subkey, "DriverDesc")[0]
                                    # Filtrar adaptadores básicos
                                    if "Microsoft" not in driver_desc and "Basic" not in driver_desc:
                                        gpu_info.append(driver_desc)
                                except:
                                    pass
                        except:
                            break
            except:
                pass
            
            # Método 2: Usar WMI como alternativa
            try:
                output = subprocess.check_output(["wmic", "path", "win32_VideoController", "get", "name"]).decode('utf-8').strip()
                gpus = [line.strip() for line in output.split('\n') if line.strip() and not line.strip() == 'Name']
                for gpu in gpus:
                    if gpu not in gpu_info:
                        gpu_info.append(gpu)
            except:
                pass
            
            # Si no se encontró nada, usar el método simple
            if not gpu_info:
                try:
                    output = subprocess.check_output(["wmic", "cpu", "get", "name"]).decode('utf-8').strip()
                    if "Name" in output:
                        gpu_info.append(output.replace("Name", "").strip())
                except:
                    pass
                
        except Exception as e:
            print(f"  Error al detectar GPU: {str(e)}")
    
    elif system == "Linux":
        # Método 1: Usar nvidia-smi (para NVIDIA)
        try:
            if os.path.exists("/usr/bin/nvidia-smi"):
                output = subprocess.check_output(["nvidia-smi", "--query-gpu=gpu_name", "--format=csv,noheader"]).decode('utf-8').strip()
                if output:
                    gpu_info.append(f"NVIDIA {output}")
        except:
            pass
        
        # Método 2: Usar lspci
        try:
            output = subprocess.check_output(["lspci", "-nnk"]).decode('utf-8')
            gpu_lines = [line.strip() for line in output.split('\n') if 'VGA' in line or '3D' in line or 'Display' in line]
            
            for line in gpu_lines:
                # Extraer el nombre después de los dos puntos
                gpu_name = line.split(':')[2].strip()
                # Filtrar controladores básicos
                if "llvmpipe" not in gpu_name.lower() and "swrast" not in gpu_name.lower():
                    gpu_info.append(gpu_name)
        except:
            pass
        
        # Método 3: Verificar GPUs activas en uso
        try:
            # Verificar si hay procesos usando GPU
            if os.path.exists("/usr/bin/nvidia-smi"):
                output = subprocess.check_output(["nvidia-smi", "--query-compute-apps=pid,name", "--format=csv,noheader"]).decode('utf-8').strip()
                if output:
                    gpu_info.append("GPU en uso por procesos activos")
        except:
            pass
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_gpus = []
    for gpu in gpu_info:
        clean_gpu = gpu.split('(')[0].strip()  # Eliminar información adicional entre paréntesis
        if clean_gpu not in seen:
            seen.add(clean_gpu)
            unique_gpus.append(gpu)
    
    return "\n  ".join(unique_gpus) if unique_gpus else "No se pudo detectar la GPU (pero puede estar presente)"
    system = platform.system()
    gpu_info = []
    
    if system == "Windows":
        try:
            # Método mejorado para detectar GPUs activas
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}") as key:
                for i in range(100):
                    try:
                        subkey_name = f"000{i}"
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            try:
                                # Verificar si la GPU está activa
                                status = winreg.QueryValueEx(subkey, "EnableStatus")[0]
                                if status == 1:  # 1 significa activa
                                    driver_desc = winreg.QueryValueEx(subkey, "DriverDesc")[0]
                                    # Filtrar adaptadores básicos de Microsoft
                                    if "Microsoft" not in driver_desc and "Basic" not in driver_desc:
                                        gpu_info.append(driver_desc)
                            except:
                                pass
                    except:
                        break
            
            # Verificación adicional con DirectX
            try:
                import comtypes.client
                from ctypes import POINTER
                from comtypes import CLSCTX_ALL
                from pywintypes import IID
                
                # Definir interfaces necesarias
                dx = comtypes.client.GetModule("dxgi.dll")
                factory = comtypes.client.CreateObject(
                    "{770aaf78-26a4-4398-815c-2a60a820a77b}",
                    interface=POINTER(dx.IDXGIFactory),
                    clsctx=CLSCTX_ALL
                )
                
                adapter = POINTER(dx.IDXGIAdapter)()
                if factory.EnumAdapters(0, adapter) == 0:
                    desc = dx.DXGI_ADAPTER_DESC()
                    adapter.GetDesc(desc)
                    gpu_name = desc.Description.strip()
                    if gpu_name not in gpu_info:
                        gpu_info.append(gpu_name)
            except:
                pass
            
        except Exception as e:
            print(f"  Error al detectar GPU: {str(e)}")
    
    elif system == "Linux":
        try:
            # Método mejorado para Linux
            if os.path.exists("/usr/bin/nvidia-smi"):
                output = subprocess.check_output(["nvidia-smi", "-L"]).decode('utf-8')
                for line in output.split('\n'):
                    if "GPU" in line:
                        gpu_name = line.split(":")[1].split("(")[0].strip()
                        gpu_info.append(f"NVIDIA {gpu_name}")
            else:
                # Usar lspci y filtrar solo las activas
                output = subprocess.check_output(["lspci", "-vnnn"]).decode('utf-8')
                vga_sections = output.split("\n\n")
                
                for section in vga_sections:
                    if "VGA" in section or "3D" in section or "Display" in section:
                        # Verificar si el kernel está usando el dispositivo
                        if "Kernel driver in use:" in section:
                            driver_line = [line for line in section.split('\n') if "Kernel driver in use:" in line][0]
                            driver = driver_line.split(":")[1].strip()
                            name_line = [line for line in section.split('\n') if "VGA" in line or "3D" in line][0]
                            gpu_name = name_line.split(":")[2].strip()
                            gpu_info.append(f"{gpu_name} ({driver})")
        except:
            pass
    
    # Eliminar duplicados manteniendo el orden
    seen = set()
    unique_gpus = []
    for gpu in gpu_info:
        if gpu not in seen:
            seen.add(gpu)
            unique_gpus.append(gpu)
    
    return "\n  ".join(unique_gpus) if unique_gpus else "No se detectaron GPUs activas"

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
            if addr.family == 2:  # AF_INET
                net_info.append(f"Interfaz: {interface}, IPv4: {addr.address}")
            elif addr.family == 17:  # AF_PACKET
                net_info.append(f"Interfaz: {interface}, MAC: {addr.address}")
    
    return "\n  ".join(net_info) if net_info else "Información no disponible"

def get_uptime():
    if platform.system() == "Linux":
        try:
            with open('/proc/uptime') as f:
                uptime_seconds = float(f.readline().split()[0])
                uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
                return uptime_str.split('.')[0]
        except:
            pass
    elif platform.system() == "Windows":
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
            return uptime_str.split('.')[0]
        except:
            pass
    return "No disponible"

def get_system_temperature():
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
        try:
            import wmi
            w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            temperatures = w.Sensor()
            cpu_temps = [f"{s.Value}°C" for s in temperatures if s.SensorType=='Temperature' and 'CPU' in s.Name]
            gpu_temps = [f"GPU: {s.Value}°C" for s in temperatures if s.SensorType=='Temperature' and 'GPU' in s.Name]
            all_temps = cpu_temps + gpu_temps
            return ", ".join(all_temps) if all_temps else "No disponible"
        except:
            return "No disponible (instala OpenHardwareMonitor)"
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
    if "No se pudo detectar" in gpu_info:
        print("  " + gpu_info)
        print("  Sugerencias:")
        print("  1. En Windows, ejecuta 'dxdiag' en la terminal para ver tu GPU")
        print("  2. En Linux, prueba 'lspci | grep VGA' o 'nvidia-smi'")
        print("  3. Asegúrate de tener los drivers de gráficos instalados")
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

if __name__ == "__main__":
    main()