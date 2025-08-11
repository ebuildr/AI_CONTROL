"""
Real-time Hardware Monitoring System
Provides live monitoring of NPU and GPU performance metrics
"""

import asyncio
import time
import psutil
from typing import Dict, List, Optional, Callable
from collections import deque
from datetime import datetime

from loguru import logger

try:
    import nvidia_ml_py3 as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False


class RealtimeMonitor:
    """Real-time monitoring for NPU and GPU hardware"""
    
    def __init__(self):
        self.monitoring_active = False
        self.update_interval = 1.0  # Update every second
        self.history_size = 60  # Keep 60 seconds of history
        
        # Metrics history
        self.cpu_history = deque(maxlen=self.history_size)
        self.gpu_history = deque(maxlen=self.history_size)
        self.npu_history = deque(maxlen=self.history_size)
        self.memory_history = deque(maxlen=self.history_size)
        
        # Current metrics
        self.current_metrics = {
            "timestamp": None,
            "cpu": {},
            "gpu": {},
            "npu": {},
            "memory": {},
            "processes": []
        }
        
        # Callbacks for real-time updates
        self.update_callbacks = []
        
        # NVML initialization for GPU monitoring
        self.nvml_initialized = False
        if NVML_AVAILABLE:
            try:
                nvml.nvmlInit()
                self.nvml_initialized = True
                logger.info("✅ NVML initialized for GPU monitoring")
            except:
                logger.warning("⚠️ NVML initialization failed")
    
    async def start_monitoring(self):
        """Start real-time monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        logger.info("🚀 Starting real-time hardware monitoring")
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        logger.info("🛑 Stopping real-time hardware monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Update history
                self._update_history(metrics)
                
                # Update current metrics
                self.current_metrics = metrics
                
                # Notify callbacks
                for callback in self.update_callbacks:
                    try:
                        await callback(metrics)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def _collect_metrics(self) -> Dict:
        """Collect all hardware metrics"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": await self._get_cpu_metrics(),
            "gpu": await self._get_gpu_metrics(),
            "npu": await self._get_npu_metrics(),
            "memory": await self._get_memory_metrics(),
            "processes": await self._get_ai_processes()
        }
        return metrics
    
    async def _get_cpu_metrics(self) -> Dict:
        """Get CPU metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            return {
                "usage_percent": sum(cpu_percent) / len(cpu_percent),
                "per_core_usage": cpu_percent,
                "frequency_current": cpu_freq.current if cpu_freq else 0,
                "frequency_max": cpu_freq.max if cpu_freq else 0,
                "core_count": psutil.cpu_count(logical=False),
                "thread_count": psutil.cpu_count(logical=True),
                "temperature": self._get_cpu_temperature()
            }
        except Exception as e:
            logger.debug(f"CPU metrics error: {e}")
            return {}
    
    async def _get_gpu_metrics(self) -> Dict:
        """Get GPU metrics"""
        metrics = {
            "devices": [],
            "total_usage": 0,
            "total_memory_used": 0,
            "total_memory_free": 0
        }
        
        if not self.nvml_initialized:
            return metrics
        
        try:
            device_count = nvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                try:
                    handle = nvml.nvmlDeviceGetHandleByIndex(i)
                    
                    # Basic info
                    name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                    
                    # Utilization
                    utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
                    
                    # Memory
                    memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_used_gb = memory_info.used / (1024**3)
                    memory_total_gb = memory_info.total / (1024**3)
                    
                    # Temperature
                    try:
                        temperature = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                    except:
                        temperature = None
                    
                    # Power
                    try:
                        power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Watts
                        power_limit = nvml.nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
                    except:
                        power = None
                        power_limit = None
                    
                    # Clock speeds
                    try:
                        graphics_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_GRAPHICS)
                        memory_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_MEM)
                    except:
                        graphics_clock = None
                        memory_clock = None
                    
                    # Fan speed
                    try:
                        fan_speed = nvml.nvmlDeviceGetFanSpeed(handle)
                    except:
                        fan_speed = None
                    
                    device_metrics = {
                        "id": i,
                        "name": name,
                        "gpu_usage": utilization.gpu,
                        "memory_usage": utilization.memory,
                        "memory_used_gb": round(memory_used_gb, 2),
                        "memory_total_gb": round(memory_total_gb, 2),
                        "memory_free_gb": round(memory_total_gb - memory_used_gb, 2),
                        "temperature": temperature,
                        "power_watts": round(power, 1) if power else None,
                        "power_limit_watts": round(power_limit, 1) if power_limit else None,
                        "graphics_clock_mhz": graphics_clock,
                        "memory_clock_mhz": memory_clock,
                        "fan_speed_percent": fan_speed
                    }
                    
                    metrics["devices"].append(device_metrics)
                    metrics["total_usage"] += utilization.gpu
                    metrics["total_memory_used"] += memory_used_gb
                    metrics["total_memory_free"] += (memory_total_gb - memory_used_gb)
                    
                except Exception as e:
                    logger.debug(f"GPU {i} metrics error: {e}")
            
            # Calculate averages
            if metrics["devices"]:
                metrics["average_usage"] = metrics["total_usage"] / len(metrics["devices"])
            
        except Exception as e:
            logger.debug(f"GPU metrics error: {e}")
        
        return metrics
    
    async def _get_npu_metrics(self) -> Dict:
        """Get NPU metrics (simulated for now)"""
        # TODO: Implement real NPU metrics when APIs become available
        # For now, we'll simulate based on AI workload
        
        ai_processes = await self._get_ai_processes()
        npu_usage = min(len(ai_processes) * 15, 100)  # Simulate usage based on AI processes
        
        return {
            "available": True,
            "usage_percent": npu_usage,
            "memory_used_mb": npu_usage * 10,  # Simulate memory usage
            "temperature": 45 + (npu_usage * 0.2),  # Simulate temperature
            "power_watts": 2 + (npu_usage * 0.08),  # NPUs are power efficient
            "inference_throughput": npu_usage * 100,  # Inferences per second
            "active_models": len(ai_processes)
        }
    
    async def _get_memory_metrics(self) -> Dict:
        """Get system memory metrics"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                "total_gb": round(mem.total / (1024**3), 2),
                "used_gb": round(mem.used / (1024**3), 2),
                "free_gb": round(mem.free / (1024**3), 2),
                "available_gb": round(mem.available / (1024**3), 2),
                "percent": mem.percent,
                "swap_total_gb": round(swap.total / (1024**3), 2),
                "swap_used_gb": round(swap.used / (1024**3), 2),
                "swap_percent": swap.percent
            }
        except Exception as e:
            logger.debug(f"Memory metrics error: {e}")
            return {}
    
    async def _get_ai_processes(self) -> List[Dict]:
        """Get AI-related processes"""
        ai_processes = []
        ai_keywords = ['python', 'ollama', 'cuda', 'tensor', 'onnx', 'openvino']
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if any(keyword in pinfo['name'].lower() for keyword in ai_keywords):
                        ai_processes.append({
                            "pid": pinfo['pid'],
                            "name": pinfo['name'],
                            "cpu_percent": pinfo['cpu_percent'],
                            "memory_percent": pinfo['memory_percent']
                        })
                except:
                    continue
        except:
            pass
        
        return ai_processes
    
    def _get_cpu_temperature(self) -> Optional[float]:
        """Get CPU temperature if available"""
        try:
            # Try to get temperature from sensors
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    for entry in entries:
                        if entry.label in ['Core 0', 'CPU', 'Package id 0']:
                            return entry.current
        except:
            pass
        return None
    
    def _update_history(self, metrics: Dict):
        """Update metrics history"""
        timestamp = time.time()
        
        # CPU history
        cpu_usage = metrics.get("cpu", {}).get("usage_percent", 0)
        self.cpu_history.append((timestamp, cpu_usage))
        
        # GPU history
        gpu_usage = metrics.get("gpu", {}).get("average_usage", 0)
        self.gpu_history.append((timestamp, gpu_usage))
        
        # NPU history
        npu_usage = metrics.get("npu", {}).get("usage_percent", 0)
        self.npu_history.append((timestamp, npu_usage))
        
        # Memory history
        memory_percent = metrics.get("memory", {}).get("percent", 0)
        self.memory_history.append((timestamp, memory_percent))
    
    def add_update_callback(self, callback: Callable):
        """Add a callback for real-time updates"""
        self.update_callbacks.append(callback)
    
    def remove_update_callback(self, callback: Callable):
        """Remove a callback"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def get_current_metrics(self) -> Dict:
        """Get current metrics"""
        return self.current_metrics
    
    def get_history(self) -> Dict:
        """Get metrics history"""
        return {
            "cpu": list(self.cpu_history),
            "gpu": list(self.gpu_history),
            "npu": list(self.npu_history),
            "memory": list(self.memory_history)
        }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_monitoring()
        if self.nvml_initialized:
            try:
                nvml.nvmlShutdown()
            except:
                pass


# Global monitor instance
realtime_monitor = RealtimeMonitor()
