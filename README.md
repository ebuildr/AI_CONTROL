# 🤖 AI Control System

**Advanced Local AI with Complete PC Control and Web Browsing Automation**

A comprehensive local AI solution featuring **Ollama integration**, **FastAPI web interface**, **PC control capabilities**, and **web browsing automation** with **NordVPN Meshnet support** for secure remote access.

---

## 🚀 Features

### 🧠 **AI Capabilities**
- **Multiple AI Models**: GPT-OSS 20B/120B, Llama 3.1 8B/70B with 4-bit quantization
- **Intelligent Model Management**: Automatic model loading and optimization
- **Streaming Responses**: Real-time AI chat with configurable parameters
- **Intent Analysis**: Automatic classification of user requests (chat, PC control, web browsing)

### 💻 **PC Control**
- **System Monitoring**: Real-time CPU, memory, disk usage tracking
- **Process Management**: List, start, stop, and monitor running processes
- **File Operations**: Create, copy, move, delete files and directories
- **Application Control**: Launch and manage desktop applications
- **Security Layer**: Command filtering and rate limiting for safety

### 🌐 **Web Browsing Automation**
- **Browser Automation**: Playwright and Selenium integration
- **Web Scraping**: Extract text, links, images from websites
- **Form Interaction**: Fill forms, click buttons, navigate pages
- **Screenshot Capture**: Take and analyze webpage screenshots
- **Search Automation**: Automated Google searches and result extraction

### 🌍 **Network & Remote Access**
- **Local Access**: Standard localhost interface
- **LAN Access**: Network-wide access for local devices
- **Meshnet Support**: Secure remote access via NordVPN Meshnet
- **Firewall Integration**: Automated Windows Firewall configuration

### 🛡️ **Security & Safety**
- **Command Filtering**: Blocks dangerous system commands
- **Rate Limiting**: Prevents abuse with request throttling
- **Safe Mode**: Restricted operations for untrusted environments
- **Audit Logging**: Comprehensive logging of all operations

### ⚡ **Performance & Optimization**
- **Memory Management**: Intelligent CPU offloading for large models
- **Concurrent Processing**: Optimized for multiple simultaneous requests
- **Resource Monitoring**: Real-time performance tracking
- **Auto-scaling**: Dynamic resource allocation

---

## 📊 Supported AI Models

| Model | Size | Memory Req. | Speed | Best For | Status |
|-------|------|-------------|-------|----------|---------|
| **GPT-OSS 20B** | 13.8 GB | ~16GB RAM | Fast | General use, quick responses | ✅ Recommended |
| **GPT-OSS 120B** | 65.3 GB | ~68GB RAM | Slower | Complex tasks, highest quality | ✅ Advanced |
| **Llama 3.1 8B** | 4.9 GB | ~8GB RAM | Fastest | Testing, lightweight tasks | ✅ Beginner |
| **Llama 3.1 70B** | 39.2 GB | ~42GB RAM | Medium | Balanced performance | ✅ Professional |
| **Code Llama 7B** | 3.8 GB | ~6GB RAM | Fast | Code generation | ✅ Developer |
| **Mistral 7B** | 4.1 GB | ~6GB RAM | Fast | Multilingual tasks | ✅ Global |

---

## 🎯 Quick Start

### 📋 **Prerequisites**

#### 💻 **System Requirements**
| Component | Minimum | Recommended | For 120B Model |
|-----------|---------|-------------|----------------|
| **OS** | Windows 10 | Windows 11 | Windows 11 Pro |
| **RAM** | 16 GB | 32 GB | **64+ GB** |
| **Storage** | 50 GB free | 100 GB SSD | 200+ GB NVMe |
| **CPU** | 4 cores | 8+ cores | 16+ cores |
| **GPU** | Optional | RTX 4060+ | RTX 4090/A100 |
| **Network** | 100 Mbps | Gigabit | Gigabit+ |

#### 📦 **Software Dependencies**
- **Windows 10/11** with PowerShell 5.1+
- **Python 3.10+** with pip package manager
- **Git** for repository cloning
- **Ollama** (auto-installed by scripts)
- **Visual C++ Redistributable** (for Python packages)

### 🛠️ **Installation**

#### **Option 1: Automated Setup (Recommended)**
```powershell
# Clone the repository
git clone https://github.com/your-username/ai-control-system.git
cd ai-control-system

# Run comprehensive setup (as Administrator)
.\scripts\install_system.ps1

# Test installation
.\scripts\test_system.ps1

# Start the system
.\scripts\start_stack.ps1
```

#### **Option 2: Manual Setup**
```powershell
# 1. Clone and navigate
git clone https://github.com/your-username/ai-control-system.git
cd ai-control-system

# 2. Install Ollama
.\scripts\install_ollama.ps1

# 3. Setup Python environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 4. Install browser automation
playwright install chromium

# 5. Configure firewall (as Administrator)
.\scripts\setup_firewall.ps1

# 6. Start the system
.\scripts\start_stack.ps1
```

---

## 🌐 Access & Usage

### **Local Access**
```
🏠 Web Interface:    http://localhost:8001
📡 API Endpoint:     http://localhost:8001/docs
❤️ Health Check:     http://localhost:8001/health
🧠 Ollama Direct:    http://localhost:11434
```

### **Network Access**
```bash
# Find your local IP
ipconfig | findstr "IPv4"

# Access from any device on your network
http://YOUR_LOCAL_IP:8001
```

### **Remote Access (Meshnet)**
1. Install and configure NordVPN with Meshnet
2. Find your Meshnet IP: `ipconfig | findstr "100."`
3. Access from anywhere: `http://YOUR_MESHNET_IP:8001`

---

## 💬 **AI Chat Interface**

### **Web Interface Features**
- 🎨 **Modern UI**: Glass-morphism design with dark theme
- 💬 **Real-time Chat**: Instant AI responses with typing indicators
- ⚙️ **Model Selection**: Switch between AI models on-the-fly
- 🎛️ **Advanced Settings**: Temperature, system prompts, streaming
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile

### **Chat Examples**
```
User: "Explain quantum computing in simple terms"
AI: [Detailed explanation with examples]

User: "Open notepad and create a new file"
AI: [Executes PC command and provides confirmation]

User: "Search Google for latest AI news and summarize"
AI: [Performs web search and provides summary]
```

---

## 💻 **PC Control Features**

### **System Commands**
```powershell
# System information
dir, ls, pwd, whoami, date, time, hostname

# Network utilities
ping, ipconfig, netstat, tracert

# Process management
tasklist, ps, top, htop
```

### **File Operations**
```json
{
  "command_type": "file",
  "command": "copy",
  "parameters": {
    "source": "C:\\source\\file.txt",
    "destination": "C:\\destination\\file.txt"
  }
}
```

### **Application Control**
```json
{
  "command_type": "application",
  "command": "open",
  "parameters": {
    "application": "notepad"
  }
}
```

### **Process Management**
```json
{
  "command_type": "process",
  "command": "start",
  "parameters": {
    "executable": "calc.exe"
  }
}
```

---

## 🌐 **Web Browsing Automation**

### **Supported Actions**
- **navigate**: Go to a specific URL
- **search**: Perform Google searches
- **click**: Click on page elements
- **type**: Enter text in form fields
- **screenshot**: Capture page screenshots
- **extract_links**: Get all links from a page
- **extract_images**: Get all images from a page
- **get_content**: Extract page HTML/text
- **scroll**: Navigate page content

### **Web Automation Examples**
```json
{
  "action": "search",
  "text": "latest AI developments 2024"
}

{
  "action": "navigate",
  "url": "https://github.com"
}

{
  "action": "screenshot"
}
```

---

## 🔧 **API Documentation**

### **Chat Endpoint**
```http
POST /chat
Content-Type: application/json

{
  "model": "gpt-oss:20b",
  "prompt": "Hello, world!",
  "system_prompt": "You are a helpful assistant",
  "temperature": 0.7,
  "stream": false
}
```

### **PC Control Endpoint**
```http
POST /pc/command
Content-Type: application/json

{
  "command_type": "system",
  "command": "dir",
  "parameters": {}
}
```

### **Web Browsing Endpoint**
```http
POST /web/browse
Content-Type: application/json

{
  "action": "navigate",
  "url": "https://example.com"
}
```

### **Health Check**
```http
GET /health

{
  "status": "healthy",
  "components": {
    "ai_manager": "ready",
    "pc_controller": "ready",
    "web_browser": "ready"
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 🛠️ **Management Scripts**

### **Core Scripts**
| Script | Purpose | Usage |
|--------|---------|-------|
| `start_stack.ps1` | Start all services | `.\scripts\start_stack.ps1` |
| `stop_stack.ps1` | Stop all services | `.\scripts\stop_stack.ps1` |
| `test_system.ps1` | Run comprehensive tests | `.\scripts\test_system.ps1` |
| `setup_firewall.ps1` | Configure Windows Firewall | `.\scripts\setup_firewall.ps1` |
| `install_ollama.ps1` | Install Ollama and models | `.\scripts\install_ollama.ps1` |

### **Advanced Management**
```powershell
# Start with custom settings
.\scripts\start_stack.ps1 -Port 8002 -Host "0.0.0.0"

# Stop but keep Ollama running
.\scripts\stop_stack.ps1 -KeepOllama

# Force stop all processes
.\scripts\stop_stack.ps1 -Force

# Test specific components
.\scripts\test_system.ps1 -SkipModels -Verbose

# Remove firewall rules
.\scripts\setup_firewall.ps1 -Remove
```

---

## 📊 **Performance Optimization**

### **Memory Configuration**
```powershell
# For 64GB RAM systems (optimal for all models)
$env:OLLAMA_NUM_PARALLEL = "1"      # Single request processing
$env:OLLAMA_NUM_GPU = "0"           # CPU-only for stability
$env:OLLAMA_HOST = "0.0.0.0:11434"  # Network access

# For 32GB RAM systems (up to 20B models)
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"

# For 16GB RAM systems (8B models only)
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
```

### **Performance Tips**
1. **SSD Storage**: Use NVMe SSD for 3-5x faster model loading
2. **Memory Management**: Close unnecessary applications before loading large models
3. **CPU vs GPU**: For 120B models, CPU-only often provides better stability
4. **Network Optimization**: Use wired connection for best performance
5. **Browser Settings**: Use headless mode for web automation to save resources

---

## 🔒 **Security Features**

### **Command Safety**
- **Whitelist System**: Only safe commands are allowed by default
- **Pattern Blocking**: Dangerous command patterns are automatically blocked
- **Rate Limiting**: Maximum 20 commands per minute per session
- **Audit Logging**: All commands are logged with timestamps

### **Blocked Commands**
```
format, fdisk, del /f, rm -rf /, shutdown, reboot
reg delete, sc delete, net user delete, taskkill /f
wmic delete, powershell remove-item -force -recurse
```

### **Safe Commands**
```
dir, ls, pwd, whoami, date, time, hostname
ping, ipconfig, netstat, tasklist, systeminfo
copy, move, mkdir, type, cat, find, where
```

### **Security Configuration**
```powershell
# Enable strict security mode
$env:AI_CONTROL_SECURITY_LEVEL = "strict"

# Disable PC control features
$env:ENABLE_PC_CONTROL = "false"

# Disable web browsing features
$env:ENABLE_WEB_BROWSING = "false"

# Set custom rate limits
$env:RATE_LIMIT_PER_MINUTE = "10"
```

---

## 🌍 **Network Configuration**

### **Firewall Rules**
The system automatically configures Windows Firewall with these rules:
- **Port 8001**: AI Control System web interface (inbound/outbound)
- **Port 11434**: Ollama API server (inbound/outbound)
- **HTTP/HTTPS**: Web browsing automation (outbound)
- **DNS**: Domain name resolution (outbound)

### **Finding Your IP Addresses**
```powershell
# Get all IPv4 addresses
ipconfig | findstr "IPv4"

# Typical results:
# IPv4 Address. . . . . . : 192.168.1.100   # LAN IP
# IPv4 Address. . . . . . : 100.77.109.59   # Meshnet IP
# IPv4 Address. . . . . . : 172.22.192.1    # Docker/VM IP
```

### **Testing Network Access**
```powershell
# Test from another computer on your network
curl http://YOUR_LAN_IP:8001/health

# Test Meshnet access
curl http://YOUR_MESHNET_IP:8001/health

# PowerShell alternative
Invoke-RestMethod http://YOUR_IP:8001/health
```

---

## 🧪 **Testing & Troubleshooting**

### **Comprehensive System Test**
```powershell
# Run all tests
.\scripts\test_system.ps1

# Verbose output
.\scripts\test_system.ps1 -Verbose

# Skip model tests (faster)
.\scripts\test_system.ps1 -SkipModels

# Test specific host/port
.\scripts\test_system.ps1 -Host "192.168.1.100" -Port "8002"
```

### **Common Issues & Solutions**

#### **"SSL_RECORD_TOO_LONG" Error**
```
❌ Problem: Browser shows SSL error
✅ Solution: Ensure you're using http:// not https://
```

#### **Port Already in Use**
```powershell
❌ Problem: Port 8001 or 11434 in use
✅ Solution: 
.\scripts\stop_stack.ps1
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

#### **Ollama Connection Failed**
```powershell
❌ Problem: Cannot connect to Ollama
✅ Solution:
ollama serve
# Or restart:
.\scripts\stop_stack.ps1
.\scripts\start_stack.ps1
```

#### **Out of Memory**
```
❌ Problem: System runs out of RAM
✅ Solution: Use smaller model or add more RAM
```

#### **Browser Automation Fails**
```powershell
❌ Problem: Web browsing doesn't work
✅ Solution:
playwright install chromium
# Or reinstall:
pip install playwright
playwright install
```

### **Log Files**
```
📁 logs/
  ├── ai_control_YYYYMMDD_HHMMSS.log    # Main application log
  ├── ollama.log                         # Ollama service log
  ├── security.log                       # Security events log
  └── performance.log                    # Performance metrics
```

---

## 📁 **Project Structure**

```
AI_CONTROL/
├── 📁 app/                              # FastAPI application
│   ├── 📄 main.py                       # Main API server
│   ├── 📁 core/                         # Core modules
│   │   ├── 📄 ai_manager.py             # AI model management
│   │   ├── 📄 pc_controller.py          # PC control operations
│   │   ├── 📄 web_browser.py            # Web automation
│   │   └── 📄 security.py               # Security & safety
│   ├── 📁 models/                       # Pydantic data models
│   │   ├── 📄 requests.py               # API request models
│   │   └── 📄 responses.py              # API response models
│   ├── 📁 utils/                        # Utility modules
│   │   ├── 📄 config.py                 # Configuration management
│   │   └── 📄 logger.py                 # Logging setup
│   └── 📁 static/                       # Web interface
│       └── 📄 index.html                # Main web UI
├── 📁 scripts/                          # Management scripts
│   ├── 📄 start_stack.ps1               # Start all services
│   ├── 📄 stop_stack.ps1                # Stop all services
│   ├── 📄 test_system.ps1               # System testing
│   ├── 📄 setup_firewall.ps1            # Firewall configuration
│   └── 📄 install_ollama.ps1            # Ollama installation
├── 📁 logs/                             # Log files (auto-created)
├── 📁 uploads/                          # File uploads (auto-created)
├── 📁 temp/                             # Temporary files (auto-created)
├── 📄 requirements.txt                  # Python dependencies
├── 📄 README.md                         # This documentation
├── 📄 .env.example                      # Environment variables template
└── 📄 .gitignore                        # Git ignore rules
```

---

## ⚙️ **Configuration**

### **Environment Variables**
Create a `.env` file in the project root:

```bash
# API Settings
API_HOST=0.0.0.0
API_PORT=8001
DEBUG=false

# Ollama Settings
OLLAMA_HOST=http://localhost:11434
OLLAMA_TIMEOUT=300
DEFAULT_MODEL=gpt-oss:20b

# Security Settings
ENABLE_AUTH=false
RATE_LIMIT_PER_MINUTE=20
SECRET_KEY=your-secret-key-here

# Browser Settings
BROWSER_TYPE=playwright
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30

# Features
ENABLE_PC_CONTROL=true
ENABLE_WEB_BROWSING=true
MAX_COMMAND_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ai_control.log
LOG_ROTATION=10 MB
LOG_RETENTION=30 days
```

### **Production Configuration**
```bash
# Set environment
$env:ENVIRONMENT = "production"

# Production settings
DEBUG=false
ENABLE_AUTH=true
CORS_ORIGINS=https://yourdomain.com
BROWSER_HEADLESS=true
LOG_LEVEL=WARNING
```

---

## 🚀 **Advanced Features**

### **Automation Workflows**
Create complex automation sequences:

```json
{
  "name": "Daily Report",
  "steps": [
    {
      "type": "web",
      "action": "search",
      "text": "AI news today"
    },
    {
      "type": "web", 
      "action": "screenshot"
    },
    {
      "type": "pc",
      "command": "open",
      "application": "notepad"
    },
    {
      "type": "ai",
      "prompt": "Summarize the search results"
    }
  ]
}
```

### **Custom Model Integration**
```python
# Add custom models to ai_manager.py
custom_models = [
    "custom-model:latest",
    "specialized-model:v1.0"
]
```

### **Plugin System**
Extend functionality with custom plugins:

```python
# app/plugins/custom_controller.py
class CustomController:
    async def custom_action(self, parameters):
        # Your custom logic here
        return {"success": True, "data": "Custom result"}
```

---

## 🤝 **Contributing**

### **Development Setup**
```powershell
# Fork and clone
git clone https://github.com/your-username/ai-control-system.git
cd ai-control-system

# Create development branch
git checkout -b feature/your-feature

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/

# Format code
black app/
flake8 app/
```

### **Contribution Guidelines**
1. **Code Style**: Follow PEP 8 and use Black formatter
2. **Testing**: Add tests for new features
3. **Documentation**: Update README and docstrings
4. **Security**: Security-first development approach
5. **Performance**: Consider resource usage and optimization

### **Areas for Contribution**
- 🧠 **AI Models**: Add support for new model types
- 🌐 **Web Automation**: Enhance browser capabilities
- 🔒 **Security**: Improve safety and authentication
- 📱 **Mobile**: Mobile-responsive interface
- 🔌 **Integrations**: Third-party service connections
- 🎨 **UI/UX**: Interface improvements
- 📊 **Analytics**: Usage metrics and insights

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### **Third-Party Licenses**
- **Ollama**: Apache 2.0 License
- **FastAPI**: MIT License
- **Playwright**: Apache 2.0 License
- **Selenium**: Apache 2.0 License

---

## 🆘 **Support & Community**

### **Getting Help**
- 📖 **Documentation**: This README and `/docs` endpoint
- 🐛 **Issues**: GitHub Issues for bug reports
- 💬 **Discussions**: GitHub Discussions for questions
- 📧 **Email**: [your-email@domain.com]

### **Useful Links**
- **Ollama Documentation**: https://ollama.com/docs
- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Playwright Documentation**: https://playwright.dev
- **NordVPN Meshnet**: https://meshnet.nordvpn.com

---

## 🚨 **Disclaimer**

This software is provided "as is" without warranty. Use responsibly:

- ⚠️ **PC Control**: Commands can modify your system - use with caution
- 🌐 **Web Automation**: Respect website terms of service and rate limits
- 🔒 **Security**: Keep your system updated and use strong authentication
- 📡 **Network**: Secure your network access appropriately
- 💾 **Data**: Back up important data before using system commands

---

## 🎉 **Acknowledgments**

Special thanks to:
- **Ollama Team** for the excellent local AI platform
- **FastAPI Team** for the amazing web framework
- **Playwright Team** for browser automation tools
- **Open Source Community** for inspiration and contributions

---

**Made with ❤️ for the AI community**

*Run AI locally, control everything! 🌍*
