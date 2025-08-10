"""
AI Control System - Main FastAPI Application
Advanced local AI with PC control and web browsing capabilities
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx
import ollama
from loguru import logger

# Import our custom modules
from app.core.ai_manager import AIManager
from app.core.pc_controller import PCController
from app.core.web_browser import WebBrowserController
from app.core.security import SecurityManager
from app.core.npu_manager import NPUManager
from app.core.gpu_manager import GPUManager
from app.models.requests import ChatRequest, PCCommandRequest, WebBrowseRequest
from app.models.responses import ChatResponse, PCCommandResponse, WebBrowseResponse
from app.utils.config import get_settings
from app.utils.logger import setup_logging
from app.utils.monitoring import system_monitor, monitor_endpoint, log_error_context

# Initialize logging
setup_logging()

# Get configuration
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title="AI Control System",
    description="Advanced Local AI with PC Control and Web Browsing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
ai_manager = AIManager()
pc_controller = PCController()
web_browser = WebBrowserController()
security_manager = SecurityManager()
npu_manager = NPUManager()
gpu_manager = GPUManager()

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    logger.info("🚀 Starting AI Control System...")
    
    # Initialize hardware acceleration managers first
    await npu_manager.initialize()
    await gpu_manager.initialize()
    
    # Initialize AI models (with hardware acceleration if available)
    await ai_manager.initialize()
    
    # Initialize PC controller
    await pc_controller.initialize()
    
    # Initialize web browser
    await web_browser.initialize()
    
    logger.info("✅ AI Control System ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down AI Control System...")
    
    await npu_manager.cleanup()
    await gpu_manager.cleanup()
    await ai_manager.cleanup()
    await pc_controller.cleanup()
    await web_browser.cleanup()
    
    logger.info("✅ Shutdown complete")


@app.get("/", response_class=HTMLResponse)
async def get_web_interface():
    """Serve the main web interface"""
    try:
        html_file = static_path / "index.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding='utf-8'), status_code=200)
        else:
            return HTMLResponse(
                content="<h1>AI Control System</h1><p>Web interface not found. Please check static files.</p>",
                status_code=200
            )
    except Exception as e:
        logger.error(f"Error serving web interface: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>{str(e)}</p>",
            status_code=500
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connection
        ollama_status = await ai_manager.check_health()
        
        # Check system resources
        system_status = await pc_controller.get_system_status()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ollama": ollama_status,
            "system": system_status,
            "components": {
                "ai_manager": "ready",
                "pc_controller": "ready",
                "web_browser": "ready"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/models")
async def get_available_models():
    """Get list of available AI models"""
    try:
        models = await ai_manager.get_available_models()
        return {"models": models}
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
async def chat_with_ai(request: ChatRequest):
    """Main chat endpoint for AI interaction"""
    try:
        logger.info(f"Chat request: {request.model} - {request.prompt[:100]}...")
        
        # Process the chat request
        response = await ai_manager.chat(
            model=request.model,
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            stream=request.stream
        )
        
        return ChatResponse(
            response=response["response"],
            model=request.model,
            tokens_used=response.get("tokens", 0),
            response_time=response.get("response_time", 0),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    try:
        if not request.stream:
            request.stream = True
            
        async def generate():
            async for chunk in ai_manager.chat_stream(
                model=request.model,
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature
            ):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pc/command", response_model=PCCommandResponse)
async def execute_pc_command(request: PCCommandRequest):
    """Execute PC control commands"""
    try:
        logger.info(f"PC command: {request.command_type} - {request.command}")
        
        # Security check
        if not security_manager.is_command_safe(request.command, request.command_type):
            raise HTTPException(
                status_code=403, 
                detail="Command not allowed for security reasons"
            )
        
        result = await pc_controller.execute_command(
            command_type=request.command_type,
            command=request.command,
            parameters=request.parameters
        )
        
        return PCCommandResponse(
            success=result["success"],
            output=result["output"],
            error=result.get("error"),
            command_type=request.command_type,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"PC command error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/web/browse", response_model=WebBrowseResponse)
async def browse_web(request: WebBrowseRequest):
    """Web browsing automation"""
    try:
        logger.info(f"Web browse: {request.action} - {request.url}")
        
        result = await web_browser.execute_action(
            action=request.action,
            url=request.url,
            selector=request.selector,
            text=request.text,
            options=request.options
        )
        
        return WebBrowseResponse(
            success=result["success"],
            data=result["data"],
            screenshot=result.get("screenshot"),
            error=result.get("error"),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Web browsing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pc/status")
async def get_pc_status():
    """Get comprehensive PC status"""
    try:
        status = await pc_controller.get_comprehensive_status()
        return status
    except Exception as e:
        logger.error(f"Error getting PC status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pc/processes")
async def get_running_processes():
    """Get list of running processes"""
    try:
        processes = await pc_controller.get_processes()
        return {"processes": processes}
    except Exception as e:
        logger.error(f"Error getting processes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pc/files")
async def list_files(path: str = "C:\\"):
    """List files in directory"""
    try:
        files = await pc_controller.list_files(path)
        return {"path": path, "files": files}
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pc/file/upload")
async def upload_file(file: UploadFile = File(...), path: str = ""):
    """Upload file to PC"""
    try:
        result = await pc_controller.upload_file(file, path)
        return result
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/web/screenshot")
async def take_screenshot():
    """Take a screenshot of current screen"""
    try:
        screenshot = await web_browser.take_screenshot()
        return {"screenshot": screenshot, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Diagnostics endpoints
@app.get("/diagnostics")
@monitor_endpoint("diagnostics")
async def get_diagnostics():
    """Get comprehensive system diagnostics"""
    try:
        diagnostics = system_monitor.export_diagnostics()
        return diagnostics
    except Exception as e:
        log_error_context(e, "Diagnostics export failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/diagnostics/errors")
@monitor_endpoint("diagnostics_errors")
async def get_error_history(hours: int = 24):
    """Get error history for the last N hours"""
    try:
        return system_monitor.get_error_summary(hours)
    except Exception as e:
        log_error_context(e, "Error history retrieval failed")
        raise HTTPException(status_code=500, detail=str(e))


# NPU Management Endpoints
@app.get("/npu/status")
@monitor_endpoint("npu_status")
async def get_npu_status():
    """Get NPU hardware status and capabilities"""
    try:
        status = await npu_manager.get_npu_status()
        return status
    except Exception as e:
        log_error_context(e, "NPU status retrieval failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/npu/performance")
@monitor_endpoint("npu_performance")
async def get_npu_performance():
    """Get NPU performance metrics"""
    try:
        metrics = await npu_manager.get_npu_performance_metrics()
        return metrics
    except Exception as e:
        log_error_context(e, "NPU performance metrics failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/npu/benchmark")
@monitor_endpoint("npu_benchmark")
async def run_npu_benchmark():
    """Run NPU benchmark tests"""
    try:
        results = await npu_manager.benchmark_npu()
        return results
    except Exception as e:
        log_error_context(e, "NPU benchmark failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/npu/optimize/{model_name}")
@monitor_endpoint("npu_optimize_model")
async def optimize_model_for_npu(model_name: str):
    """Optimize a specific model for NPU inference"""
    try:
        result = await npu_manager.optimize_model_for_npu(model_name)
        return result
    except Exception as e:
        log_error_context(e, f"NPU model optimization failed for {model_name}")
        raise HTTPException(status_code=500, detail=str(e))


# GPU Management Endpoints
@app.get("/gpu/status")
@monitor_endpoint("gpu_status")
async def get_gpu_status():
    """Get GPU hardware status and capabilities"""
    try:
        status = await gpu_manager.get_gpu_status()
        return status
    except Exception as e:
        log_error_context(e, "GPU status retrieval failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gpu/performance")
@monitor_endpoint("gpu_performance")
async def get_gpu_performance():
    """Get GPU performance metrics"""
    try:
        metrics = await gpu_manager.get_gpu_performance_metrics()
        return metrics
    except Exception as e:
        log_error_context(e, "GPU performance metrics failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gpu/benchmark")
@monitor_endpoint("gpu_benchmark")
async def run_gpu_benchmark():
    """Run GPU benchmark tests"""
    try:
        results = await gpu_manager.benchmark_gpu()
        return results
    except Exception as e:
        log_error_context(e, "GPU benchmark failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/gpu/optimize/{model_name}")
@monitor_endpoint("gpu_optimize_model")
async def optimize_model_for_gpu(model_name: str, gpu_type: str = "auto"):
    """Optimize a specific model for GPU inference"""
    try:
        result = await gpu_manager.optimize_model_for_gpu(model_name, gpu_type)
        return result
    except Exception as e:
        log_error_context(e, f"GPU model optimization failed for {model_name}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Development server
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
