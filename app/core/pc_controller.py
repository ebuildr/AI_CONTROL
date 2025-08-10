"""
PC Controller - Handles system control, file management, and process monitoring
"""

import asyncio
import os
import sys
import subprocess
import json
import platform
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import psutil
from loguru import logger

# Windows-specific imports
if platform.system() == "Windows":
    try:
        import win32api
        import win32con
        import win32gui
        import win32process
        import wmi
    except ImportError:
        logger.warning("Windows-specific libraries not available")


class PCController:
    """Handles PC control operations"""
    
    def __init__(self):
        self.safe_commands = {
            "system": ["dir", "ls", "pwd", "whoami", "date", "time", "hostname"],
            "file": ["copy", "move", "rename", "mkdir", "rmdir"],
            "process": ["tasklist", "ps", "top", "htop"],
            "network": ["ping", "ipconfig", "netstat"]
        }
        self.forbidden_commands = [
            "format", "fdisk", "del /f", "rm -rf", "shutdown", "reboot",
            "reg delete", "sc delete", "net user", "passwd"
        ]
        
    async def initialize(self):
        """Initialize PC controller"""
        try:
            # Check system permissions
            self.is_admin = self._check_admin_privileges()
            
            # Initialize WMI for Windows
            if platform.system() == "Windows":
                try:
                    self.wmi = wmi.WMI()
                except:
                    self.wmi = None
                    logger.warning("WMI not available")
            
            logger.info(f"✅ PC Controller initialized (Admin: {self.is_admin})")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PC Controller: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 PC Controller cleanup complete")
    
    def _check_admin_privileges(self) -> bool:
        """Check if running with admin privileges"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:
                return os.geteuid() == 0
        except:
            return False
    
    async def get_system_status(self) -> Dict:
        """Get basic system status"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "disk_percent": disk.percent,
                "disk_free": disk.free,
                "platform": platform.system(),
                "is_admin": self.is_admin
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {"error": str(e)}
    
    async def get_comprehensive_status(self) -> Dict:
        """Get comprehensive system information"""
        try:
            # Basic system info
            cpu_info = {
                "percent": psutil.cpu_percent(interval=1),
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            }
            
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
            
            disk_info = []
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": (usage.used / usage.total) * 100
                    })
                except PermissionError:
                    continue
            
            # Network info
            network_info = {}
            try:
                network_stats = psutil.net_io_counters()
                network_info = {
                    "bytes_sent": network_stats.bytes_sent,
                    "bytes_recv": network_stats.bytes_recv,
                    "packets_sent": network_stats.packets_sent,
                    "packets_recv": network_stats.packets_recv
                }
            except:
                pass
            
            # Boot time
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "system": {
                    "platform": platform.system(),
                    "platform_release": platform.release(),
                    "platform_version": platform.version(),
                    "architecture": platform.machine(),
                    "processor": platform.processor(),
                    "boot_time": boot_time.isoformat(),
                    "is_admin": self.is_admin
                },
                "cpu": cpu_info,
                "memory": memory_info,
                "disk": disk_info,
                "network": network_info
            }
            
        except Exception as e:
            logger.error(f"Error getting comprehensive status: {e}")
            return {"error": str(e)}
    
    async def get_processes(self) -> List[Dict]:
        """Get list of running processes"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            return processes[:50]  # Return top 50 processes
            
        except Exception as e:
            logger.error(f"Error getting processes: {e}")
            return []
    
    async def list_files(self, path: str) -> List[Dict]:
        """List files in directory"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Path does not exist: {path}")
            
            files = []
            for item in path_obj.iterdir():
                try:
                    stat = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": stat.st_size if not item.is_dir() else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
                    })
                except (PermissionError, OSError):
                    continue
            
            # Sort: directories first, then by name
            files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
            return files
            
        except Exception as e:
            logger.error(f"Error listing files in {path}: {e}")
            raise
    
    async def execute_command(
        self, 
        command_type: str, 
        command: str, 
        parameters: Optional[Dict] = None
    ) -> Dict:
        """Execute various PC commands"""
        try:
            logger.info(f"Executing {command_type} command: {command}")
            
            result = {
                "success": False,
                "output": "",
                "error": None,
                "command_type": command_type
            }
            
            if command_type == "system":
                result = await self._execute_system_command(command, parameters)
            elif command_type == "file":
                result = await self._execute_file_command(command, parameters)
            elif command_type == "process":
                result = await self._execute_process_command(command, parameters)
            elif command_type == "application":
                result = await self._execute_application_command(command, parameters)
            else:
                result["error"] = f"Unknown command type: {command_type}"
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "command_type": command_type
            }
    
    async def _execute_system_command(self, command: str, parameters: Optional[Dict]) -> Dict:
        """Execute system commands"""
        try:
            # Security check
            if any(forbidden in command.lower() for forbidden in self.forbidden_commands):
                return {
                    "success": False,
                    "output": "",
                    "error": "Command not allowed for security reasons"
                }
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "output": stdout.decode('utf-8', errors='ignore'),
                "error": stderr.decode('utf-8', errors='ignore') if stderr else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e)
            }
    
    async def _execute_file_command(self, command: str, parameters: Optional[Dict]) -> Dict:
        """Execute file operations"""
        try:
            if not parameters:
                return {"success": False, "error": "Parameters required for file operations"}
            
            if command == "copy":
                source = parameters.get("source")
                destination = parameters.get("destination")
                if source and destination:
                    shutil.copy2(source, destination)
                    return {"success": True, "output": f"Copied {source} to {destination}"}
            
            elif command == "move":
                source = parameters.get("source")
                destination = parameters.get("destination")
                if source and destination:
                    shutil.move(source, destination)
                    return {"success": True, "output": f"Moved {source} to {destination}"}
            
            elif command == "delete":
                target = parameters.get("target")
                if target:
                    path_obj = Path(target)
                    if path_obj.is_file():
                        path_obj.unlink()
                    elif path_obj.is_dir():
                        shutil.rmtree(target)
                    return {"success": True, "output": f"Deleted {target}"}
            
            elif command == "mkdir":
                directory = parameters.get("directory")
                if directory:
                    Path(directory).mkdir(parents=True, exist_ok=True)
                    return {"success": True, "output": f"Created directory {directory}"}
            
            return {"success": False, "error": f"Unknown file command: {command}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_process_command(self, command: str, parameters: Optional[Dict]) -> Dict:
        """Execute process-related commands"""
        try:
            if command == "kill":
                pid = parameters.get("pid")
                if pid:
                    try:
                        process = psutil.Process(pid)
                        process.terminate()
                        return {"success": True, "output": f"Terminated process {pid}"}
                    except psutil.NoSuchProcess:
                        return {"success": False, "error": f"Process {pid} not found"}
            
            elif command == "start":
                executable = parameters.get("executable")
                if executable:
                    if platform.system() == "Windows":
                        subprocess.Popen(executable, shell=True)
                    else:
                        subprocess.Popen(executable.split())
                    return {"success": True, "output": f"Started {executable}"}
            
            return {"success": False, "error": f"Unknown process command: {command}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_application_command(self, command: str, parameters: Optional[Dict]) -> Dict:
        """Execute application-specific commands"""
        try:
            if command == "open":
                app_name = parameters.get("application")
                if not app_name:
                    return {"success": False, "error": "Application name required"}
                
                # Common applications mapping
                app_mapping = {
                    "notepad": "notepad.exe",
                    "calculator": "calc.exe",
                    "explorer": "explorer.exe",
                    "cmd": "cmd.exe",
                    "powershell": "powershell.exe",
                    "browser": "start chrome",
                    "chrome": "start chrome",
                    "firefox": "start firefox"
                }
                
                executable = app_mapping.get(app_name.lower(), app_name)
                
                if platform.system() == "Windows":
                    subprocess.Popen(executable, shell=True)
                else:
                    subprocess.Popen(executable.split())
                
                return {"success": True, "output": f"Opened {app_name}"}
            
            return {"success": False, "error": f"Unknown application command: {command}"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def upload_file(self, file, destination_path: str = "") -> Dict:
        """Handle file upload"""
        try:
            if not destination_path:
                destination_path = Path.home() / "Downloads"
            else:
                destination_path = Path(destination_path)
            
            destination_path.mkdir(parents=True, exist_ok=True)
            
            file_path = destination_path / file.filename
            
            # Write file
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return {
                "success": True,
                "message": f"File uploaded to {file_path}",
                "path": str(file_path),
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_installed_applications(self) -> List[Dict]:
        """Get list of installed applications (Windows only)"""
        try:
            if platform.system() != "Windows" or not self.wmi:
                return []
            
            apps = []
            for product in self.wmi.Win32_Product():
                if product.Name:
                    apps.append({
                        "name": product.Name,
                        "version": product.Version or "Unknown",
                        "vendor": product.Vendor or "Unknown",
                        "install_date": product.InstallDate or "Unknown"
                    })
            
            return sorted(apps, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Error getting installed applications: {e}")
            return []
