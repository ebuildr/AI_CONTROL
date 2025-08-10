"""
Hardware Detection Utility
Robust detection of NPU and GPU hardware on Windows
"""

import os
import subprocess
import json
import platform
from typing import Dict, List, Optional
from pathlib import Path

from loguru import logger


class HardwareDetector:
    """Unified hardware detection for NPU and GPU"""
    
    @staticmethod
    def run_powershell_command(command: str) -> Optional[str]:
        """Run PowerShell command with better error handling"""
        try:
            # Create a temporary PowerShell script file
            script_path = Path("temp_hw_detect.ps1")
            script_path.write_text(command, encoding='utf-8')
            
            # Run PowerShell script
            result = subprocess.run(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", str(script_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Clean up
            script_path.unlink(missing_ok=True)
            
            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            else:
                logger.debug(f"PowerShell command failed: {result.stderr}")
                return None
                
        except Exception as e:
            logger.debug(f"PowerShell execution error: {e}")
            return None
    
    @staticmethod
    def detect_processor_info() -> Dict:
        """Get processor information using multiple methods"""
        info = {
            "name": "Unknown",
            "vendor": "Unknown",
            "cores": 0,
            "has_npu": False
        }
        
        # Method 1: Use platform module (most reliable)
        try:
            processor = platform.processor()
            if processor:
                info["name"] = processor
                if "Intel" in processor:
                    info["vendor"] = "Intel"
                    # Check for Intel Core Ultra or AI features
                    if any(x in processor.upper() for x in ["ULTRA", "CORE ULTRA", "METEOR LAKE", "ARROW LAKE"]):
                        info["has_npu"] = True
                elif "AMD" in processor:
                    info["vendor"] = "AMD"
                    # Check for AMD processors with AI engine
                    if any(x in processor.upper() for x in ["7040", "7045", "8040", "8045", "PHOENIX", "HAWK"]):
                        info["has_npu"] = True
        except:
            pass
        
        # Method 2: Try WMI via PowerShell
        ps_script = """
$processor = Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors
@{
    Name = $processor.Name
    Cores = $processor.NumberOfCores
    LogicalProcessors = $processor.NumberOfLogicalProcessors
} | ConvertTo-Json
"""
        
        result = HardwareDetector.run_powershell_command(ps_script)
        if result:
            try:
                data = json.loads(result)
                if data.get("Name"):
                    info["name"] = data["Name"]
                    info["cores"] = data.get("Cores", 0)
            except:
                pass
        
        # Method 3: Direct WMI query for NPU
        npu_script = """
# Check for Intel NPU
$intelNPU = Get-WmiObject -Namespace root\cimv2 -Query "SELECT * FROM Win32_PnPEntity WHERE Name LIKE '%Intel%AI%' OR Name LIKE '%Neural%' OR Name LIKE '%NPU%'"
if ($intelNPU) {
    "INTEL_NPU_DETECTED"
}

# Check processor features
$proc = Get-WmiObject Win32_Processor
if ($proc.Name -match "Core.*Ultra|Meteor Lake|Arrow Lake") {
    "INTEL_NPU_CAPABLE"
}
"""
        
        npu_result = HardwareDetector.run_powershell_command(npu_script)
        if npu_result and ("NPU_DETECTED" in npu_result or "NPU_CAPABLE" in npu_result):
            info["has_npu"] = True
            
        return info
    
    @staticmethod
    def detect_gpu_info() -> List[Dict]:
        """Detect GPU information"""
        gpus = []
        
        # PowerShell script to get GPU info
        gpu_script = """
$gpus = Get-WmiObject Win32_VideoController | Where-Object {$_.Name -ne $null}
$gpuList = @()
foreach ($gpu in $gpus) {
    $gpuInfo = @{
        Name = $gpu.Name
        AdapterRAM = [math]::Round($gpu.AdapterRAM / 1GB, 2)
        DriverVersion = $gpu.DriverVersion
        Status = $gpu.Status
    }
    $gpuList += $gpuInfo
}
$gpuList | ConvertTo-Json
"""
        
        result = HardwareDetector.run_powershell_command(gpu_script)
        if result:
            try:
                data = json.loads(result)
                if isinstance(data, dict):  # Single GPU
                    data = [data]
                
                for gpu_data in data:
                    gpu_info = {
                        "name": gpu_data.get("Name", "Unknown"),
                        "memory_gb": gpu_data.get("AdapterRAM", 0),
                        "driver_version": gpu_data.get("DriverVersion", "Unknown"),
                        "vendor": "Unknown",
                        "type": "integrated"
                    }
                    
                    # Determine vendor and type
                    name = gpu_info["name"].upper()
                    if "NVIDIA" in name:
                        gpu_info["vendor"] = "NVIDIA"
                        gpu_info["type"] = "discrete"
                        # Check for specific models
                        if "RTX" in name:
                            gpu_info["architecture"] = "RTX"
                            if "5090" in name or "5080" in name:
                                gpu_info["generation"] = "Blackwell"
                            elif "4090" in name or "4080" in name:
                                gpu_info["generation"] = "Ada Lovelace"
                    elif "AMD" in name or "RADEON" in name:
                        gpu_info["vendor"] = "AMD"
                        gpu_info["type"] = "discrete" if "RX" in name else "integrated"
                    elif "INTEL" in name:
                        gpu_info["vendor"] = "Intel"
                        gpu_info["type"] = "integrated"
                        if "ARC" in name:
                            gpu_info["type"] = "discrete"
                    
                    gpus.append(gpu_info)
                    
            except Exception as e:
                logger.debug(f"GPU parsing error: {e}")
        
        # Fallback: Try NVIDIA-specific detection
        try:
            nvidia_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if nvidia_result.returncode == 0 and nvidia_result.stdout:
                lines = nvidia_result.stdout.strip().split('\n')
                for line in lines:
                    parts = line.split(', ')
                    if len(parts) >= 3:
                        gpu_info = {
                            "name": parts[0],
                            "memory_gb": float(parts[1].replace(' MiB', '')) / 1024,
                            "driver_version": parts[2],
                            "vendor": "NVIDIA",
                            "type": "discrete"
                        }
                        
                        # Avoid duplicates
                        if not any(g["name"] == gpu_info["name"] for g in gpus):
                            gpus.append(gpu_info)
                            
        except:
            pass
        
        return gpus
    
    @staticmethod
    def detect_all_hardware() -> Dict:
        """Detect all hardware (CPU, NPU, GPU)"""
        logger.info("🔍 Starting hardware detection...")
        
        # Detect processor and NPU
        processor_info = HardwareDetector.detect_processor_info()
        
        # Detect GPUs
        gpu_list = HardwareDetector.detect_gpu_info()
        
        # Compile results
        result = {
            "processor": processor_info,
            "npu": {
                "available": processor_info.get("has_npu", False),
                "devices": []
            },
            "gpu": {
                "available": len(gpu_list) > 0,
                "devices": gpu_list,
                "count": len(gpu_list)
            }
        }
        
        # Add NPU device info if available
        if processor_info.get("has_npu"):
            result["npu"]["devices"].append({
                "name": "Intel AI Boost" if processor_info["vendor"] == "Intel" else "AMD AI Engine",
                "vendor": processor_info["vendor"],
                "type": "integrated"
            })
            result["npu"]["count"] = 1
        
        logger.info(f"✅ Hardware detection complete: NPU={result['npu']['available']}, GPUs={result['gpu']['count']}")
        
        return result


# Test the detector if run directly
if __name__ == "__main__":
    detector = HardwareDetector()
    hardware = detector.detect_all_hardware()
    print(json.dumps(hardware, indent=2))
