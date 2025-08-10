"""
Web Browser Controller - Handles web browsing automation and scraping
"""

import asyncio
import base64
import json
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
import requests
from bs4 import BeautifulSoup
from loguru import logger


class WebBrowserController:
    """Handles web browsing automation"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.selenium_driver = None
        self.browser_type = "playwright"  # or "selenium"
        
    async def initialize(self):
        """Initialize web browser controller"""
        try:
            # Try to initialize Playwright first
            await self._init_playwright()
            
            logger.info(f"✅ Web Browser Controller initialized ({self.browser_type})")
            
        except Exception as e:
            logger.warning(f"Playwright initialization failed: {e}")
            try:
                # Fallback to Selenium
                await self._init_selenium()
                self.browser_type = "selenium"
                logger.info("✅ Web Browser Controller initialized (selenium)")
            except Exception as e2:
                logger.error(f"❌ Failed to initialize any browser: {e2}")
                raise
    
    async def cleanup(self):
        """Cleanup browser resources"""
        try:
            if self.browser_type == "playwright":
                if self.page:
                    await self.page.close()
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
            elif self.browser_type == "selenium":
                if self.selenium_driver:
                    self.selenium_driver.quit()
                    
            logger.info("🧹 Web Browser Controller cleanup complete")
            
        except Exception as e:
            logger.warning(f"Browser cleanup warning: {e}")
    
    async def _init_playwright(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        
        # Launch browser (headless by default)
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Create page
        self.page = await self.context.new_page()
    
    async def _init_selenium(self):
        """Initialize Selenium browser"""
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--window-size=1920,1080')
        
        self.selenium_driver = webdriver.Chrome(options=chrome_options)
    
    async def execute_action(
        self,
        action: str,
        url: Optional[str] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> Dict:
        """Execute web browsing action"""
        try:
            logger.info(f"Executing web action: {action}")
            
            if self.browser_type == "playwright":
                return await self._execute_playwright_action(action, url, selector, text, options)
            else:
                return await self._execute_selenium_action(action, url, selector, text, options)
                
        except Exception as e:
            logger.error(f"Web action failed: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    async def _execute_playwright_action(
        self, action: str, url: Optional[str], selector: Optional[str], 
        text: Optional[str], options: Optional[Dict]
    ) -> Dict:
        """Execute action using Playwright"""
        try:
            if not self.page:
                raise Exception("Playwright page not initialized")
            
            result = {"success": True, "data": None}
            
            if action == "navigate":
                if not url:
                    raise ValueError("URL required for navigate action")
                await self.page.goto(url, wait_until="networkidle")
                result["data"] = {"url": self.page.url, "title": await self.page.title()}
            
            elif action == "get_content":
                content = await self.page.content()
                result["data"] = {"content": content, "url": self.page.url}
            
            elif action == "get_text":
                if selector:
                    element = await self.page.wait_for_selector(selector, timeout=10000)
                    text_content = await element.inner_text()
                else:
                    text_content = await self.page.inner_text("body")
                result["data"] = {"text": text_content}
            
            elif action == "click":
                if not selector:
                    raise ValueError("Selector required for click action")
                await self.page.click(selector)
                result["data"] = {"clicked": selector}
            
            elif action == "type":
                if not selector or not text:
                    raise ValueError("Selector and text required for type action")
                await self.page.fill(selector, text)
                result["data"] = {"typed": text, "selector": selector}
            
            elif action == "search":
                if not text:
                    raise ValueError("Search text required")
                # Navigate to Google if not already there
                if "google.com" not in self.page.url:
                    await self.page.goto("https://www.google.com")
                
                # Search
                await self.page.fill('input[name="q"]', text)
                await self.page.press('input[name="q"]', 'Enter')
                await self.page.wait_for_load_state("networkidle")
                
                # Get search results
                results = await self.page.evaluate("""
                    () => {
                        const results = [];
                        document.querySelectorAll('div[data-header-feature] h3').forEach((h3, index) => {
                            if (index < 10) {
                                const link = h3.closest('a');
                                results.push({
                                    title: h3.innerText,
                                    url: link ? link.href : '',
                                    snippet: ''
                                });
                            }
                        });
                        return results;
                    }
                """)
                
                result["data"] = {"query": text, "results": results}
            
            elif action == "screenshot":
                screenshot_bytes = await self.page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                result["screenshot"] = screenshot_b64
                result["data"] = {"screenshot_taken": True}
            
            elif action == "extract_links":
                links = await self.page.evaluate("""
                    () => {
                        const links = [];
                        document.querySelectorAll('a[href]').forEach(link => {
                            links.push({
                                text: link.innerText.trim(),
                                url: link.href,
                                title: link.title || ''
                            });
                        });
                        return links;
                    }
                """)
                result["data"] = {"links": links}
            
            elif action == "extract_images":
                images = await self.page.evaluate("""
                    () => {
                        const images = [];
                        document.querySelectorAll('img[src]').forEach(img => {
                            images.push({
                                src: img.src,
                                alt: img.alt || '',
                                width: img.width,
                                height: img.height
                            });
                        });
                        return images;
                    }
                """)
                result["data"] = {"images": images}
            
            elif action == "scroll":
                direction = options.get("direction", "down") if options else "down"
                if direction == "down":
                    await self.page.keyboard.press("PageDown")
                elif direction == "up":
                    await self.page.keyboard.press("PageUp")
                elif direction == "bottom":
                    await self.page.keyboard.press("End")
                elif direction == "top":
                    await self.page.keyboard.press("Home")
                result["data"] = {"scrolled": direction}
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return result
            
        except Exception as e:
            logger.error(f"Playwright action failed: {e}")
            return {"success": False, "data": None, "error": str(e)}
    
    async def _execute_selenium_action(
        self, action: str, url: Optional[str], selector: Optional[str], 
        text: Optional[str], options: Optional[Dict]
    ) -> Dict:
        """Execute action using Selenium"""
        try:
            if not self.selenium_driver:
                raise Exception("Selenium driver not initialized")
            
            result = {"success": True, "data": None}
            
            if action == "navigate":
                if not url:
                    raise ValueError("URL required for navigate action")
                self.selenium_driver.get(url)
                result["data"] = {"url": self.selenium_driver.current_url, "title": self.selenium_driver.title}
            
            elif action == "get_content":
                content = self.selenium_driver.page_source
                result["data"] = {"content": content, "url": self.selenium_driver.current_url}
            
            elif action == "get_text":
                if selector:
                    element = WebDriverWait(self.selenium_driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    text_content = element.text
                else:
                    text_content = self.selenium_driver.find_element(By.TAG_NAME, "body").text
                result["data"] = {"text": text_content}
            
            elif action == "click":
                if not selector:
                    raise ValueError("Selector required for click action")
                element = WebDriverWait(self.selenium_driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                element.click()
                result["data"] = {"clicked": selector}
            
            elif action == "type":
                if not selector or not text:
                    raise ValueError("Selector and text required for type action")
                element = WebDriverWait(self.selenium_driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                element.clear()
                element.send_keys(text)
                result["data"] = {"typed": text, "selector": selector}
            
            elif action == "search":
                if not text:
                    raise ValueError("Search text required")
                # Navigate to Google if not already there
                if "google.com" not in self.selenium_driver.current_url:
                    self.selenium_driver.get("https://www.google.com")
                
                # Search
                search_box = self.selenium_driver.find_element(By.NAME, "q")
                search_box.clear()
                search_box.send_keys(text)
                search_box.send_keys(Keys.RETURN)
                
                # Wait for results
                WebDriverWait(self.selenium_driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-header-feature] h3"))
                )
                
                # Extract results
                results = []
                result_elements = self.selenium_driver.find_elements(By.CSS_SELECTOR, "div[data-header-feature] h3")[:10]
                for element in result_elements:
                    try:
                        link = element.find_element(By.XPATH, "./ancestor::a")
                        results.append({
                            "title": element.text,
                            "url": link.get_attribute("href"),
                            "snippet": ""
                        })
                    except:
                        continue
                
                result["data"] = {"query": text, "results": results}
            
            elif action == "screenshot":
                screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                result["screenshot"] = screenshot_b64
                result["data"] = {"screenshot_taken": True}
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
            return result
            
        except Exception as e:
            logger.error(f"Selenium action failed: {e}")
            return {"success": False, "data": None, "error": str(e)}
    
    async def take_screenshot(self) -> str:
        """Take a screenshot and return as base64"""
        try:
            if self.browser_type == "playwright" and self.page:
                screenshot_bytes = await self.page.screenshot(full_page=True)
                return base64.b64encode(screenshot_bytes).decode()
            elif self.browser_type == "selenium" and self.selenium_driver:
                screenshot_bytes = self.selenium_driver.get_screenshot_as_png()
                return base64.b64encode(screenshot_bytes).decode()
            else:
                raise Exception("No browser available for screenshot")
                
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            raise
    
    async def scrape_website(self, url: str, extract_type: str = "text") -> Dict:
        """Scrape website content using requests + BeautifulSoup (faster for simple scraping)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            result = {
                "url": url,
                "title": soup.title.string if soup.title else "",
                "status_code": response.status_code
            }
            
            if extract_type == "text":
                # Extract clean text
                for script in soup(["script", "style"]):
                    script.decompose()
                result["text"] = soup.get_text()
            
            elif extract_type == "links":
                # Extract all links
                links = []
                for link in soup.find_all('a', href=True):
                    links.append({
                        "text": link.get_text().strip(),
                        "url": link['href'],
                        "title": link.get('title', '')
                    })
                result["links"] = links
            
            elif extract_type == "images":
                # Extract all images
                images = []
                for img in soup.find_all('img', src=True):
                    images.append({
                        "src": img['src'],
                        "alt": img.get('alt', ''),
                        "title": img.get('title', '')
                    })
                result["images"] = images
            
            elif extract_type == "all":
                # Extract everything
                for script in soup(["script", "style"]):
                    script.decompose()
                result["text"] = soup.get_text()
                result["links"] = [{"text": link.get_text().strip(), "url": link['href']} 
                                 for link in soup.find_all('a', href=True)]
                result["images"] = [{"src": img['src'], "alt": img.get('alt', '')} 
                                  for img in soup.find_all('img', src=True)]
            
            return {"success": True, "data": result}
            
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_current_page_info(self) -> Dict:
        """Get information about current page"""
        try:
            if self.browser_type == "playwright" and self.page:
                return {
                    "url": self.page.url,
                    "title": await self.page.title(),
                    "browser": "playwright"
                }
            elif self.browser_type == "selenium" and self.selenium_driver:
                return {
                    "url": self.selenium_driver.current_url,
                    "title": self.selenium_driver.title,
                    "browser": "selenium"
                }
            else:
                return {"error": "No active browser session"}
                
        except Exception as e:
            logger.error(f"Error getting page info: {e}")
            return {"error": str(e)}
