"""Browser automation module using Selenium + CDP for Lighthouse.ai"""

import time
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    ElementNotInteractableException, WebDriverException
)
import undetected_chromedriver as uc

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.utils.accessibility import AccessibilityExtractor, PageSummary, PageDiffer
from lighthouse.config.settings import get_settings


@dataclass
class BrowserConfig:
    """Browser configuration parameters"""
    headless: bool = False
    window_width: int = 1280
    window_height: int = 720
    timeout: int = 10
    user_agent: str = "Lighthouse.ai/1.0"
    disable_images: bool = False
    disable_javascript: bool = False


@dataclass
class ElementInfo:
    """Information about a web element"""
    tag: str
    text: str
    role: Optional[str] = None
    aria_label: Optional[str] = None
    title: Optional[str] = None
    id: Optional[str] = None
    class_name: Optional[str] = None
    xpath: Optional[str] = None
    bounds: Optional[Dict[str, int]] = None
    enabled: bool = True
    displayed: bool = True


class BrowserAutomation(LoggerMixin):
    """Browser automation using Selenium with Chrome DevTools Protocol"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.settings = get_settings()
        self.config = config or BrowserConfig(
            headless=self.settings.headless_mode,
            window_width=self.settings.browser_width,
            window_height=self.settings.browser_height,
            timeout=self.settings.browser_timeout,
            user_agent=self.settings.user_agent
        )
        
        self.driver: Optional[WebDriver] = None
        self.wait: Optional[WebDriverWait] = None
        self.accessibility_extractor: Optional[AccessibilityExtractor] = None
        self.page_differ = PageDiffer()
        
        self._initialize_driver()
    
    def _initialize_driver(self) -> None:
        """Initialize Chrome driver with CDP support"""
        try:
            self.logger.info("Initializing Chrome driver")
            
            # Chrome options
            options = uc.ChromeOptions()
            
            if self.config.headless:
                options.add_argument("--headless")
            
            options.add_argument(f"--window-size={self.config.window_width},{self.config.window_height}")
            options.add_argument(f"--user-agent={self.config.user_agent}")
            
            # Performance optimizations
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            if self.config.disable_images:
                options.add_argument("--disable-images")
            
            # Enable CDP
            options.add_argument("--enable-logging")
            options.add_argument("--log-level=0")
            
            # Create driver
            try:
                self.driver = uc.Chrome(options=options)
            except Exception as e:
                self.logger.error("Failed to create Chrome driver", error=str(e))
                # Try with regular selenium Chrome as fallback
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from selenium.webdriver.chrome.options import Options as ChromeOptions
                
                # Convert undetected options to regular Chrome options
                chrome_options = ChromeOptions()
                for arg in options.arguments:
                    chrome_options.add_argument(arg)
                
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.config.timeout)
            self.driver.implicitly_wait(self.config.timeout)
            
            # Initialize wait
            self.wait = WebDriverWait(self.driver, self.config.timeout)
            
            # Initialize accessibility extractor
            self.accessibility_extractor = AccessibilityExtractor(self.driver)
            
            self.logger.info("Chrome driver initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize Chrome driver", error=str(e))
            raise
    
    def navigate_to(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            self.logger.info("Navigating to URL", url=url)
            
            # Validate URL
            parsed_url = urlparse(url)
            if not parsed_url.scheme:
                url = f"https://{url}"
            
            # Navigate
            self.driver.get(url)
            
            # Wait for page load
            self.wait_for_page_load()
            
            self.logger.info("Navigation completed", url=url)
            return True
            
        except Exception as e:
            self.logger.error("Navigation failed", url=url, error=str(e))
            return False
    
    def wait_for_page_load(self, timeout: Optional[int] = None) -> bool:
        """Wait for page to finish loading"""
        try:
            timeout = timeout or self.config.timeout
            
            # Wait for document ready state
            self.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for network idle (basic implementation)
            time.sleep(1)
            
            return True
            
        except TimeoutException:
            self.logger.warning("Page load timeout")
            return False
        except Exception as e:
            self.logger.error("Page load wait failed", error=str(e))
            return False
    
    def find_element(self, selector: str, by: By = By.XPATH) -> Optional[WebElement]:
        """Find element using various strategies"""
        try:
            # Try primary selector
            element = self.driver.find_element(by, selector)
            if element and element.is_displayed():
                return element
            
            # Fallback strategies
            fallback_strategies = [
                (By.ID, selector),
                (By.CLASS_NAME, selector),
                (By.CSS_SELECTOR, selector),
                (By.PARTIAL_LINK_TEXT, selector),
                (By.TAG_NAME, selector)
            ]
            
            for fallback_by, fallback_selector in fallback_strategies:
                try:
                    element = self.driver.find_element(fallback_by, fallback_selector)
                    if element and element.is_displayed():
                        return element
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error("Element not found", selector=selector, error=str(e))
            return None
    
    def find_elements(self, selector: str, by: By = By.XPATH) -> List[WebElement]:
        """Find multiple elements"""
        try:
            elements = self.driver.find_elements(by, selector)
            return [elem for elem in elements if elem.is_displayed()]
        except Exception as e:
            self.logger.error("Elements not found", selector=selector, error=str(e))
            return []
    
    def click_element(self, element: WebElement) -> bool:
        """Click an element with retry logic"""
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # Try different click methods
            click_methods = [
                lambda: element.click(),
                lambda: self.driver.execute_script("arguments[0].click();", element),
                lambda: ActionChains(self.driver).move_to_element(element).click().perform()
            ]
            
            for method in click_methods:
                try:
                    method()
                    time.sleep(1)  # Wait for action to complete
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.logger.error("Click failed", error=str(e))
            return False
    
    def type_text(self, element: WebElement, text: str) -> bool:
        """Type text into an element"""
        try:
            # Clear existing text
            element.clear()
            
            # Type text
            element.send_keys(text)
            
            return True
            
        except Exception as e:
            self.logger.error("Type text failed", error=str(e))
            return False
    
    def submit_form(self, element: Optional[WebElement] = None) -> bool:
        """Submit a form"""
        try:
            if element:
                # Submit specific element
                element.submit()
            else:
                # Submit current form
                self.driver.execute_script("document.forms[0].submit();")
            
            # Wait for submission
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error("Form submission failed", error=str(e))
            return False
    
    def get_page_summary(self) -> PageSummary:
        """Get current page summary"""
        if not self.accessibility_extractor:
            return PageSummary(title="", url="")
        
        return self.accessibility_extractor.get_page_summary()
    
    def detect_page_changes(self) -> Dict[str, Any]:
        """Detect changes since last page state"""
        current_summary = self.get_page_summary()
        return self.page_differ.detect_changes(current_summary)
    
    def get_element_info(self, element: WebElement) -> ElementInfo:
        """Get detailed information about an element"""
        try:
            bounds = element.rect
            bounds_dict = {
                'x': int(bounds['x']),
                'y': int(bounds['y']),
                'width': int(bounds['width']),
                'height': int(bounds['height'])
            }
            
            return ElementInfo(
                tag=element.tag_name,
                text=element.text,
                role=element.get_attribute('role'),
                aria_label=element.get_attribute('aria-label'),
                title=element.get_attribute('title'),
                id=element.get_attribute('id'),
                class_name=element.get_attribute('class'),
                bounds=bounds_dict,
                enabled=element.is_enabled(),
                displayed=element.is_displayed()
            )
            
        except Exception as e:
            self.logger.error("Failed to get element info", error=str(e))
            return ElementInfo(tag="unknown", text="")
    
    def list_actionable_elements(self) -> List[ElementInfo]:
        """List all actionable elements on the page"""
        try:
            page_summary = self.get_page_summary()
            elements = []
            
            for action_item in page_summary.actionable_elements:
                # Try to find the actual element
                element = self.find_element_by_accessibility(
                    action_item['role'], 
                    action_item['name']
                )
                
                if element:
                    element_info = self.get_element_info(element)
                    elements.append(element_info)
            
            return elements
            
        except Exception as e:
            self.logger.error("Failed to list actionable elements", error=str(e))
            return []
    
    def find_element_by_accessibility(self, role: str, name: str = None) -> Optional[WebElement]:
        """Find element using accessibility information"""
        if not self.accessibility_extractor:
            return None
        
        return self.accessibility_extractor.find_element_by_accessibility(role, name)
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            self.driver.save_screenshot(filename)
            self.logger.info("Screenshot saved", filename=filename)
            return filename
            
        except Exception as e:
            self.logger.error("Screenshot failed", error=str(e))
            return ""
    
    def execute_javascript(self, script: str, *args) -> Any:
        """Execute JavaScript in the browser"""
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            self.logger.error("JavaScript execution failed", error=str(e))
            return None
    
    def get_current_url(self) -> str:
        """Get current URL"""
        try:
            return self.driver.current_url
        except:
            return ""
    
    def get_page_title(self) -> str:
        """Get page title"""
        try:
            return self.driver.title
        except:
            return ""
    
    def go_back(self) -> bool:
        """Go back in browser history"""
        try:
            self.driver.back()
            self.wait_for_page_load()
            return True
        except Exception as e:
            self.logger.error("Go back failed", error=str(e))
            return False
    
    def go_forward(self) -> bool:
        """Go forward in browser history"""
        try:
            self.driver.forward()
            self.wait_for_page_load()
            return True
        except Exception as e:
            self.logger.error("Go forward failed", error=str(e))
            return False
    
    def refresh_page(self) -> bool:
        """Refresh the current page"""
        try:
            self.driver.refresh()
            self.wait_for_page_load()
            return True
        except Exception as e:
            self.logger.error("Page refresh failed", error=str(e))
            return False
    
    def close(self) -> None:
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.logger.info("Browser closed")
        except Exception as e:
            self.logger.error("Browser close failed", error=str(e))
    
    def cleanup(self) -> None:
        """Clean up browser resources"""
        self.close()


class BrowserManager:
    """Manager for browser automation with session handling"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.browser: Optional[BrowserAutomation] = None
        self._initialize_browser()
    
    def _initialize_browser(self) -> None:
        """Initialize browser automation"""
        try:
            self.browser = BrowserAutomation()
            self.logger.info("Browser manager initialized")
        except Exception as e:
            self.logger.error("Failed to initialize browser", error=str(e))
            raise
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        return self.browser.navigate_to(url)
    
    def get_page_info(self) -> PageSummary:
        """Get current page information"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
        
        return self.browser.get_page_summary()
    
    def cleanup(self) -> None:
        """Clean up browser manager"""
        if self.browser:
            self.browser.cleanup()
        self.logger.info("Browser manager cleaned up")


# Global browser manager instance
browser_manager = BrowserManager()
