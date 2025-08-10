"""
AI Manager - Handles Ollama integration and AI model management
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, AsyncGenerator
import httpx
import ollama
from loguru import logger


class AIManager:
    """Manages AI models and chat interactions"""
    
    def __init__(self):
        self.ollama_client = None
        self.ollama_host = "http://localhost:11434"
        self.available_models = []
        self.default_models = [
            "gpt-oss:20b",
            "gpt-oss:120b", 
            "llama3.1:8b",
            "llama3.1:70b",
            "codellama:7b",
            "mistral:7b"
        ]
    
    async def initialize(self):
        """Initialize AI manager and check models"""
        try:
            # Initialize Ollama client
            self.ollama_client = ollama.AsyncClient(host=self.ollama_host)
            
            # Check available models
            await self.refresh_models()
            
            logger.info(f"✅ AI Manager initialized with {len(self.available_models)} models")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Manager: {e}")
            raise
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.ollama_client:
            # Close any open connections
            pass
        logger.info("🧹 AI Manager cleanup complete")
    
    async def check_health(self) -> Dict:
        """Check Ollama service health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.ollama_host}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    return {"status": "healthy", "models_count": len(self.available_models)}
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    async def refresh_models(self):
        """Refresh the list of available models"""
        try:
            if not self.ollama_client:
                return
                
            models_response = await self.ollama_client.list()
            
            # Handle different response structures
            if hasattr(models_response, 'models'):
                models_list = models_response.models
            elif isinstance(models_response, dict) and 'models' in models_response:
                models_list = models_response['models']
            else:
                logger.warning(f"Unexpected models response structure: {type(models_response)}")
                models_list = []
            
            # Extract model names safely
            self.available_models = []
            for model in models_list:
                if isinstance(model, dict) and 'name' in model:
                    self.available_models.append(model['name'])
                elif hasattr(model, 'name'):
                    self.available_models.append(model.name)
                else:
                    logger.warning(f"Unexpected model structure: {model}")
            
            logger.info(f"📋 Found {len(self.available_models)} models: {self.available_models}")
            
        except Exception as e:
            logger.warning(f"⚠️ Could not refresh models: {e}")
            # Use default models as fallback
            self.available_models = self.default_models
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models"""
        if not self.available_models:
            await self.refresh_models()
        return self.available_models
    
    async def pull_model(self, model_name: str) -> Dict:
        """Pull/download a model"""
        try:
            logger.info(f"📥 Pulling model: {model_name}")
            
            if not self.ollama_client:
                raise Exception("Ollama client not initialized")
            
            # This will download the model if not available
            await self.ollama_client.pull(model_name)
            
            # Refresh models list
            await self.refresh_models()
            
            return {"success": True, "message": f"Model {model_name} pulled successfully"}
            
        except Exception as e:
            logger.error(f"❌ Failed to pull model {model_name}: {e}")
            return {"success": False, "error": str(e)}
    
    async def chat(
        self, 
        model: str, 
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict:
        """Send chat request to AI model"""
        try:
            start_time = time.time()
            
            if not self.ollama_client:
                raise Exception("Ollama client not initialized")
            
            # Ensure model is available
            if model not in self.available_models:
                # Try to pull the model
                pull_result = await self.pull_model(model)
                if not pull_result["success"]:
                    raise Exception(f"Model {model} not available and pull failed")
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Make the request
            response = await self.ollama_client.chat(
                model=model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": 2048,
                },
                stream=stream
            )
            
            response_time = time.time() - start_time
            
            if stream:
                return response  # Return the stream directly
            else:
                response_text = response['message']['content']
                
                logger.info(f"💬 Chat completed in {response_time:.2f}s")
                
                return {
                    "response": response_text,
                    "response_time": response_time,
                    "tokens": len(response_text.split()),  # Rough token estimate
                    "model": model
                }
                
        except Exception as e:
            logger.error(f"❌ Chat error with {model}: {e}")
            raise Exception(f"Chat failed: {str(e)}")
    
    async def chat_stream(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[Dict, None]:
        """Stream chat response"""
        try:
            if not self.ollama_client:
                raise Exception("Ollama client not initialized")
            
            # Prepare messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            # Stream the response
            async for chunk in await self.ollama_client.chat(
                model=model,
                messages=messages,
                options={"temperature": temperature},
                stream=True
            ):
                if chunk.get('message', {}).get('content'):
                    yield {
                        "content": chunk['message']['content'],
                        "done": chunk.get('done', False),
                        "model": model
                    }
                    
        except Exception as e:
            logger.error(f"❌ Stream chat error: {e}")
            yield {"error": str(e), "done": True}
    
    async def generate_system_prompt(self, task_type: str) -> str:
        """Generate appropriate system prompts for different tasks"""
        prompts = {
            "pc_control": """You are an AI assistant that helps with PC control and automation. 
            You can execute system commands, manage files, monitor processes, and control applications.
            Always prioritize safety and ask for confirmation before executing potentially harmful commands.
            Provide clear explanations of what each command does.""",
            
            "web_browsing": """You are an AI assistant that helps with web browsing automation.
            You can navigate websites, extract information, fill forms, and interact with web elements.
            Always respect website terms of service and be mindful of rate limiting.
            Provide screenshots and detailed descriptions of your actions.""",
            
            "general": """You are a helpful AI assistant running locally on the user's PC.
            You have access to system controls and web browsing capabilities.
            Be helpful, accurate, and safe in your responses."""
        }
        
        return prompts.get(task_type, prompts["general"])
    
    async def analyze_intent(self, prompt: str) -> Dict:
        """Analyze user intent to determine if PC control or web browsing is needed"""
        try:
            # Use a small model for quick intent analysis
            intent_model = "llama3.1:8b" if "llama3.1:8b" in self.available_models else self.available_models[0]
            
            intent_prompt = f"""
            Analyze this user request and determine the intent:
            "{prompt}"
            
            Respond with JSON containing:
            - "type": "chat", "pc_control", or "web_browsing"
            - "confidence": 0.0 to 1.0
            - "reasoning": brief explanation
            - "suggested_action": what action to take
            
            Examples:
            - "open notepad" -> pc_control
            - "search google for python tutorials" -> web_browsing  
            - "explain quantum physics" -> chat
            """
            
            response = await self.chat(
                model=intent_model,
                prompt=intent_prompt,
                system_prompt="You are an intent analyzer. Respond only with valid JSON.",
                temperature=0.1
            )
            
            # Try to parse JSON response
            try:
                intent_data = json.loads(response["response"])
                return intent_data
            except json.JSONDecodeError:
                # Fallback to simple text analysis
                prompt_lower = prompt.lower()
                if any(word in prompt_lower for word in ["open", "close", "run", "execute", "process", "file", "folder"]):
                    return {"type": "pc_control", "confidence": 0.7, "reasoning": "Contains PC control keywords"}
                elif any(word in prompt_lower for word in ["browse", "search", "website", "google", "click", "navigate"]):
                    return {"type": "web_browsing", "confidence": 0.7, "reasoning": "Contains web browsing keywords"}
                else:
                    return {"type": "chat", "confidence": 0.8, "reasoning": "General conversation"}
                    
        except Exception as e:
            logger.warning(f"Intent analysis failed: {e}")
            return {"type": "chat", "confidence": 0.5, "reasoning": "Fallback due to error"}
