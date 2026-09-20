from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import wmi
import platform
import pythoncom

app = FastAPI(title="AIDA64 System Spec API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def safe_get(obj, attr, default="N/A"):
    val = getattr(obj, attr, None)
    return str(val).strip() if val is not None and str(val).strip() != "" else default

@app.get("/api/system/spec")
def get_system_spec():
    pythoncom.CoInitialize()
    try:
        c = wmi.WMI()
        
        # CPU
        cpus = c.Win32_Processor()
        cpu_info = {}
        if cpus:
            cpu = cpus[0]
            cpu_info = {
                "name": safe_get(cpu, "Name"),
                "cores": safe_get(cpu, "NumberOfCores"),
                "threads": safe_get(cpu, "NumberOfLogicalProcessors"),
                "max_clock_mhz": safe_get(cpu, "MaxClockSpeed"),
                "socket": safe_get(cpu, "SocketDesignation"),
                "l2_cache": f"{int(safe_get(cpu, 'L2CacheSize', 0))} KB" if safe_get(cpu, 'L2CacheSize') != "N/A" else "N/A",
                "l3_cache": f"{int(safe_get(cpu, 'L3CacheSize', 0)) / 1024:.1f} MB" if safe_get(cpu, 'L3CacheSize') != "N/A" else "N/A",
                "manufacturer": safe_get(cpu, "Manufacturer"),
                "description": safe_get(cpu, "Description")
            }

        # Motherboard
        boards = c.Win32_BaseBoard()
        board_info = {
            "manufacturer": safe_get(boards[0], "Manufacturer") if boards else "N/A",
            "product": safe_get(boards[0], "Product") if boards else "N/A",
            "serial": safe_get(boards[0], "SerialNumber") if boards else "N/A",
            "version": safe_get(boards[0], "Version") if boards else "N/A"
        }

        # GPU
        gpus = c.Win32_VideoController()
        gpu_info = {}
        if gpus:
            gpu = gpus[0]
            ram_bytes = getattr(gpu, "AdapterRAM", 0)
            ram_mb = round(int(ram_bytes) / (1024**2)) if ram_bytes and str(ram_bytes).isdigit() else "N/A"
            gpu_info = {
                "name": safe_get(gpu, "Name"),
                "driver": safe_get(gpu, "DriverVersion"),
                "driver_date": safe_get(gpu, "DriverDate"),
                "video_processor": safe_get(gpu, "VideoProcessor"),
                "adapter_ram": f"{ram_mb} MB" if ram_mb != "N/A" else "N/A",
                "resolution": f"{safe_get(gpu, 'CurrentHorizontalResolution')}x{safe_get(gpu, 'CurrentVerticalResolution')} @ {safe_get(gpu, 'CurrentRefreshRate')}Hz",
                "dac_type": safe_get(gpu, "AdapterDACType")
            }

        # RAM (Подробно)
        ram_modules = []
        for r in c.Win32_PhysicalMemory():
            cap_bytes = getattr(r, "Capacity", 0)
            cap_gb = round(int(cap_bytes) / (1024**3), 2) if cap_bytes and str(cap_bytes).isdigit() else "N/A"
            
            ram_modules.append({
                "manufacturer": safe_get(r, "Manufacturer"),
                "capacity_gb": cap_gb,
                "speed_mhz": safe_get(r, "Speed"),
                "configured_speed": safe_get(r, "ConfiguredClockSpeed"),
                "part_number": safe_get(r, "PartNumber"),
                "serial_number": safe_get(r, "SerialNumber"),
                "bank_label": safe_get(r, "BankLabel"),
                "device_locator": safe_get(r, "DeviceLocator"),
                "form_factor": safe_get(r, "FormFactor"),
                "voltage": f"{int(getattr(r, 'ConfiguredVoltage', 0))/1000} V" if getattr(r, 'ConfiguredVoltage', None) else "N/A"
            })

        # Storage (Подробно)
        disks = []
        for d in c.Win32_DiskDrive():
            size_bytes = getattr(d, "Size", 0)
            size_gb = round(int(size_bytes) / (1024**3), 2) if size_bytes and str(size_bytes).isdigit() else "N/A"
            
            disks.append({
                "model": safe_get(d, "Model"),
                "size_gb": size_gb,
                "interface": safe_get(d, "InterfaceType"),
                "media_type": safe_get(d, "MediaType"),
                "serial_number": safe_get(d, "SerialNumber"),
                "partitions": safe_get(d, "Partitions"),
                "status": safe_get(d, "Status"),
                "firmware": safe_get(d, "FirmwareRevision")
            })

        return {
            "status": "success",
            "os": f"{platform.system()} {platform.release()} (Build {platform.version()})",
            "motherboard": board_info,
            "cpu": cpu_info,
            "gpu": gpu_info,
            "ram": ram_modules,
            "storage": disks
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        pythoncom.CoUninitialize()

@app.get("/")
def read_index():
    return FileResponse("frontend/index.html")
