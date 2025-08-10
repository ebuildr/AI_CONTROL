"""
Security Manager - Handles authentication and command safety
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import jwt
from passlib.context import CryptContext
from loguru import logger


class SecurityManager:
    """Manages security aspects of the AI control system"""
    
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Define dangerous command patterns
        self.dangerous_patterns = [
            r"format\s+[a-z]:",
            r"del\s+/[sfrq]",
            r"rm\s+-rf\s+/",
            r"shutdown\s+[/-]",
            r"reboot",
            r"fdisk",
            r"reg\s+delete",
            r"sc\s+delete",
            r"net\s+user.*delete",
            r"taskkill\s+/f",
            r"wmic\s+.*delete",
            r"powershell.*remove-item.*-force.*-recurse",
            r"cmd.*rd\s+/s\s+/q",
            r"cipher\s+/w",
            r"sdelete",
            r"bcdedit",
            r"diskpart\s+(?!list)",
            r"attrib\s+.*\+s\s+.*\+h",
            r"icacls.*deny",
            r"takeown",
            r"cacls.*deny"
        ]
        
        # Safe command whitelist
        self.safe_commands = {
            "system": [
                "dir", "ls", "pwd", "whoami", "date", "time", "hostname",
                "ipconfig", "ifconfig", "ping", "tracert", "nslookup",
                "systeminfo", "ver", "uname", "ps", "top", "htop",
                "netstat", "tasklist", "diskpart list"
            ],
            "file": [
                "copy", "cp", "move", "mv", "mkdir", "md", "type", "cat",
                "more", "less", "head", "tail", "find", "where", "which"
            ],
            "safe_apps": [
                "notepad", "calc", "mspaint", "wordpad", "explorer",
                "chrome", "firefox", "code", "notepad++"
            ]
        }
        
        # Rate limiting
        self.command_history = {}
        self.max_commands_per_minute = 20
        
    def is_command_safe(self, command: str, command_type: str) -> bool:
        """Check if a command is safe to execute"""
        try:
            command_lower = command.lower().strip()
            
            # Check against dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, command_lower, re.IGNORECASE):
                    logger.warning(f"🚨 Blocked dangerous command: {command}")
                    return False
            
            # Check if it's in safe commands
            if command_type in self.safe_commands:
                safe_list = self.safe_commands[command_type]
                command_base = command_lower.split()[0] if command_lower.split() else ""
                if command_base in safe_list:
                    return True
            
            # Additional safety checks
            if any(danger in command_lower for danger in [
                "format", "fdisk", "delete system", "remove-item", "rm -rf /",
                "del /f /s /q", "shutdown", "reboot", "restart", "logoff"
            ]):
                logger.warning(f"🚨 Blocked dangerous command: {command}")
                return False
            
            # Check for file system root operations
            if any(root in command_lower for root in [
                "c:\\windows", "/etc", "/bin", "/usr", "/sys", "/proc"
            ]):
                if any(action in command_lower for action in ["delete", "remove", "rm", "del"]):
                    logger.warning(f"🚨 Blocked system directory operation: {command}")
                    return False
            
            # Check for path traversal attempts
            if self._has_path_traversal(command):
                logger.warning(f"🚨 Blocked path traversal attempt: {command}")
                return False
            
            # Rate limiting check
            if not self._check_rate_limit():
                logger.warning("🚨 Rate limit exceeded")
                return False
            
            # Default to safe for simple commands
            logger.info(f"✅ Command approved: {command}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking command safety: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit is exceeded"""
        try:
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)
            
            # Clean old entries
            self.command_history = {
                timestamp: count for timestamp, count in self.command_history.items()
                if timestamp > minute_ago
            }
            
            # Count commands in last minute
            total_commands = sum(self.command_history.values())
            
            if total_commands >= self.max_commands_per_minute:
                return False
            
            # Add current command
            current_minute = now.replace(second=0, microsecond=0)
            self.command_history[current_minute] = self.command_history.get(current_minute, 0) + 1
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Default to allow if check fails
    
    def create_access_token(self, data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        try:
            to_encode = data.copy()
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(hours=24)
            
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm="HS256")
            return encoded_jwt
            
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise
    
    def verify_token(self, token: str) -> Dict:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.JWTError:
            raise Exception("Invalid token")
    
    def hash_password(self, password: str) -> str:
        """Hash password"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input"""
        try:
            # Remove potentially dangerous characters
            sanitized = re.sub(r'[<>"\';\\]', '', user_input)
            
            # Limit length
            if len(sanitized) > 1000:
                sanitized = sanitized[:1000]
            
            return sanitized.strip()
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {e}")
            return ""
    
    def get_security_report(self) -> Dict:
        """Get security status report"""
        try:
            now = datetime.now()
            hour_ago = now - timedelta(hours=1)
            
            # Count recent commands
            recent_commands = sum(
                count for timestamp, count in self.command_history.items()
                if timestamp > hour_ago
            )
            
            return {
                "timestamp": now.isoformat(),
                "rate_limit_status": "normal" if recent_commands < self.max_commands_per_minute else "elevated",
                "commands_last_hour": recent_commands,
                "dangerous_patterns_count": len(self.dangerous_patterns),
                "safe_commands_count": sum(len(cmds) for cmds in self.safe_commands.values()),
                "security_level": "high"
            }
            
        except Exception as e:
            logger.error(f"Security report failed: {e}")
            return {"error": str(e)}
    
    def log_security_event(self, event_type: str, details: str, severity: str = "info"):
        """Log security events"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "details": details,
                "severity": severity
            }
            
            if severity == "critical":
                logger.critical(f"🚨 SECURITY: {event_type} - {details}")
            elif severity == "warning":
                logger.warning(f"⚠️ SECURITY: {event_type} - {details}")
            else:
                logger.info(f"🔒 SECURITY: {event_type} - {details}")
                
        except Exception as e:
            logger.error(f"Security logging failed: {e}")
    
    def check_file_safety(self, file_path: str, operation: str) -> bool:
        """Check if file operation is safe"""
        try:
            path_lower = file_path.lower()
            
            # Protected system directories
            protected_paths = [
                "c:\\windows", "c:\\program files", "c:\\system32",
                "/etc", "/bin", "/usr/bin", "/sbin", "/usr/sbin",
                "/sys", "/proc", "/dev"
            ]
            
            # Check if trying to modify protected paths
            if operation in ["delete", "modify", "write"]:
                for protected in protected_paths:
                    if path_lower.startswith(protected.lower()):
                        logger.warning(f"🚨 Blocked {operation} on protected path: {file_path}")
                        return False
            
            # Check file extensions for executables
            dangerous_extensions = [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar"]
            if operation == "execute":
                file_ext = file_path.lower().split('.')[-1] if '.' in file_path else ""
                if f".{file_ext}" in dangerous_extensions:
                    logger.warning(f"🚨 Blocked execution of: {file_path}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"File safety check failed: {e}")
            return False
    
    def _has_path_traversal(self, command: str) -> bool:
        """Check for path traversal patterns"""
        traversal_patterns = [
            r"\.\.[\\/]",
            r"[\\/]\.\.[\\/]",
            r"\.\.[\\/]\.\.[\\/]",
            r"%2e%2e[\\/]",
            r"\.\.%2f",
            r"\.\.%5c"
        ]
        
        for pattern in traversal_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False
