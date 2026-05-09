import os
import platform
import subprocess
import sys

class HardwareDetector:
    @staticmethod
    def get_cpu_info():
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                cpu = c.Win32_Processor()[0]
                return {
                    "name": cpu.Name.strip(),
                    "cores": int(cpu.NumberOfCores),
                    "threads": int(cpu.NumberOfLogicalProcessors)
                }
            except:
                pass
        else:
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    lines = f.readlines()
                name = [l for l in lines if 'model name' in l][0].split(':')[1].strip()
                cores = len([l for l in lines if 'processor' in l])
                return {"name": name, "cores": cores, "threads": cores}
            except:
                pass
        return {"name": "Unknown", "cores": 2, "threads": 2}

    @staticmethod
    def get_memory_gb():
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                total_mem = int(c.Win32_ComputerSystem()[0].TotalPhysicalMemory) / (1024**3)
                return total_mem
            except:
                pass
        else:
            try:
                total_mem = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / (1024**3)
                return total_mem
            except:
                pass
        return 8.0

    @staticmethod
    def get_gpu_info():
        gpu_name = ""
        gpu_memory_mb = 0
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for gpu in c.Win32_VideoController():
                    if gpu.AdapterRAM:
                        gpu_memory_mb = int(gpu.AdapterRAM) / (1024**2)
                        gpu_name = gpu.Name
                        break
            except:
                pass
        else:
            try:
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True, text=True
                )
                if result.returncode == 0:
                    line = result.stdout.strip()
                    if line:
                        gpu_name, mem_str = line.split(',')
                        gpu_memory_mb = int(mem_str.split()[0])
            except:
                pass
        return {"name": gpu_name, "memory_mb": gpu_memory_mb}

    @staticmethod
    def get_grade():
        cpu = HardwareDetector.get_cpu_info()
        memory = HardwareDetector.get_memory_gb()
        gpu = HardwareDetector.get_gpu_info()

        score = 0
        if cpu['cores'] >= 16:
            score += 30
        elif cpu['cores'] >= 8:
            score += 20
        elif cpu['cores'] >= 4:
            score += 10

        if memory >= 32:
            score += 30
        elif memory >= 16:
            score += 20
        elif memory >= 8:
            score += 10

        if gpu['memory_mb'] >= 24000:
            score += 40
        elif gpu['memory_mb'] >= 12000:
            score += 30
        elif gpu['memory_mb'] >= 8000:
            score += 20
        elif gpu['memory_mb'] >= 4000:
            score += 10

        if score >= 80:
            return "ultra"
        elif score >= 50:
            return "high"
        elif score >= 25:
            return "mid"
        else:
            return "low"