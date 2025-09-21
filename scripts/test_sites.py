#!/usr/bin/env python3
"""Test script for Lighthouse.ai on target websites"""

import sys
import time
import asyncio
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, '..')

from lighthouse.utils.logging import get_logger, setup_logging
from lighthouse.core.browser import browser_manager
from lighthouse.core.nlu import nlu_manager
from lighthouse.core.safety import safety_manager
from lighthouse.config.settings import get_settings


class SiteTester:
    """Test Lighthouse.ai functionality on target websites"""
    
    def __init__(self):
        setup_logging()
        self.logger = get_logger(self.__class__.__name__)
        self.settings = get_settings()
        
        # Test sites
        self.test_sites = [
            {
                "name": "Google",
                "url": "https://www.google.com",
                "tests": ["navigation", "search", "describe"]
            },
            {
                "name": "Wikipedia",
                "url": "https://en.wikipedia.org",
                "tests": ["navigation", "describe", "list"]
            },
            {
                "name": "GitHub",
                "url": "https://github.com",
                "tests": ["navigation", "describe", "list"]
            },
            {
                "name": "Example Form",
                "url": "https://httpbin.org/forms/post",
                "tests": ["navigation", "form_filling", "submit"]
            }
        ]
        
        self.results = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run tests on all target sites"""
        self.logger.info("Starting site tests")
        
        for site in self.test_sites:
            self.logger.info(f"Testing {site['name']}: {site['url']}")
            
            try:
                result = self._test_site(site)
                self.results.append(result)
                
                if result["success"]:
                    self.logger.info(f"✓ {site['name']} tests passed")
                else:
                    self.logger.error(f"✗ {site['name']} tests failed: {result['error']}")
                    
            except Exception as e:
                self.logger.error(f"✗ {site['name']} test error: {e}")
                self.results.append({
                    "site": site["name"],
                    "url": site["url"],
                    "success": False,
                    "error": str(e),
                    "tests": {}
                })
        
        return self._generate_report()
    
    def _test_site(self, site: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific site"""
        result = {
            "site": site["name"],
            "url": site["url"],
            "success": True,
            "error": None,
            "tests": {}
        }
        
        try:
            # Test navigation
            if "navigation" in site["tests"]:
                nav_result = self._test_navigation(site["url"])
                result["tests"]["navigation"] = nav_result
                if not nav_result["success"]:
                    result["success"] = False
                    result["error"] = "Navigation failed"
            
            # Test page description
            if "describe" in site["tests"]:
                desc_result = self._test_describe()
                result["tests"]["describe"] = desc_result
                if not desc_result["success"]:
                    result["success"] = False
                    if not result["error"]:
                        result["error"] = "Description failed"
            
            # Test element listing
            if "list" in site["tests"]:
                list_result = self._test_list_elements()
                result["tests"]["list"] = list_result
                if not list_result["success"]:
                    result["success"] = False
                    if not result["error"]:
                        result["error"] = "Element listing failed"
            
            # Test search functionality
            if "search" in site["tests"]:
                search_result = self._test_search()
                result["tests"]["search"] = search_result
                if not search_result["success"]:
                    result["success"] = False
                    if not result["error"]:
                        result["error"] = "Search failed"
            
            # Test form filling
            if "form_filling" in site["tests"]:
                form_result = self._test_form_filling()
                result["tests"]["form_filling"] = form_result
                if not form_result["success"]:
                    result["success"] = False
                    if not result["error"]:
                        result["error"] = "Form filling failed"
            
            # Test form submission
            if "submit" in site["tests"]:
                submit_result = self._test_form_submission()
                result["tests"]["submit"] = submit_result
                if not submit_result["success"]:
                    result["success"] = False
                    if not result["error"]:
                        result["error"] = "Form submission failed"
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _test_navigation(self, url: str) -> Dict[str, Any]:
        """Test navigation to a URL"""
        try:
            # Check if domain is allowed
            if not safety_manager.is_domain_allowed(url):
                return {
                    "success": False,
                    "error": "Domain not in allowlist",
                    "details": f"URL: {url}"
                }
            
            # Navigate to URL
            success = browser_manager.navigate(url)
            
            if success:
                # Get page info
                page_info = browser_manager.get_page_info()
                
                return {
                    "success": True,
                    "details": {
                        "title": page_info.title,
                        "url": page_info.url,
                        "main_heading": page_info.main_heading,
                        "actionable_elements": len(page_info.actionable_elements)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Navigation failed",
                    "details": f"URL: {url}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": f"URL: {url}"
            }
    
    def _test_describe(self) -> Dict[str, Any]:
        """Test page description functionality"""
        try:
            page_info = browser_manager.get_page_info()
            
            if page_info.title:
                return {
                    "success": True,
                    "details": {
                        "title": page_info.title,
                        "main_heading": page_info.main_heading,
                        "landmarks": len(page_info.landmarks),
                        "actionable_elements": len(page_info.actionable_elements)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No page title found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_list_elements(self) -> Dict[str, Any]:
        """Test element listing functionality"""
        try:
            elements = browser_manager.browser.list_actionable_elements()
            
            if elements:
                element_types = {}
                for element in elements:
                    role = element.role or "unknown"
                    element_types[role] = element_types.get(role, 0) + 1
                
                return {
                    "success": True,
                    "details": {
                        "total_elements": len(elements),
                        "element_types": element_types
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "No actionable elements found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_search(self) -> Dict[str, Any]:
        """Test search functionality"""
        try:
            # Look for search input
            search_input = browser_manager.browser.find_element("input[type='search']")
            if not search_input:
                search_input = browser_manager.browser.find_element("input[name*='search']")
            if not search_input:
                search_input = browser_manager.browser.find_element("input[placeholder*='search']")
            
            if search_input:
                # Try to type in search box
                success = browser_manager.browser.type_text(search_input, "test search")
                
                if success:
                    return {
                        "success": True,
                        "details": "Search input found and text entered"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to type in search input"
                    }
            else:
                return {
                    "success": False,
                    "error": "No search input found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_form_filling(self) -> Dict[str, Any]:
        """Test form filling functionality"""
        try:
            # Find form inputs
            inputs = browser_manager.browser.find_elements("input")
            textareas = browser_manager.browser.find_elements("textarea")
            
            filled_fields = 0
            
            # Fill text inputs
            for input_elem in inputs:
                input_type = input_elem.get_attribute("type") or "text"
                if input_type in ["text", "email", "password"]:
                    field_name = input_elem.get_attribute("name") or "field"
                    test_value = f"test_{field_name}"
                    
                    if browser_manager.browser.type_text(input_elem, test_value):
                        filled_fields += 1
            
            # Fill textareas
            for textarea in textareas:
                if browser_manager.browser.type_text(textarea, "Test comment"):
                    filled_fields += 1
            
            if filled_fields > 0:
                return {
                    "success": True,
                    "details": f"Filled {filled_fields} form fields"
                }
            else:
                return {
                    "success": False,
                    "error": "No form fields could be filled"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _test_form_submission(self) -> Dict[str, Any]:
        """Test form submission functionality"""
        try:
            # Check if submission requires confirmation
            if safety_manager.requires_confirmation(ActionType.SUBMIT):
                # In a real test, we'd handle confirmation
                pass
            
            # Find submit button
            submit_button = browser_manager.browser.find_element("input[type='submit']")
            if not submit_button:
                submit_button = browser_manager.browser.find_element("button[type='submit']")
            if not submit_button:
                submit_button = browser_manager.browser.find_element("button")
            
            if submit_button:
                # Take screenshot before submission
                screenshot_before = browser_manager.browser.take_screenshot("before_submit.png")
                
                # Submit form
                success = browser_manager.browser.click_element(submit_button)
                
                if success:
                    # Wait for submission
                    time.sleep(2)
                    
                    # Take screenshot after submission
                    screenshot_after = browser_manager.browser.take_screenshot("after_submit.png")
                    
                    return {
                        "success": True,
                        "details": "Form submitted successfully",
                        "screenshots": {
                            "before": screenshot_before,
                            "after": screenshot_after
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": "Failed to click submit button"
                    }
            else:
                return {
                    "success": False,
                    "error": "No submit button found"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate test report"""
        total_sites = len(self.results)
        successful_sites = sum(1 for result in self.results if result["success"])
        failed_sites = total_sites - successful_sites
        
        # Calculate test statistics
        total_tests = 0
        successful_tests = 0
        
        for result in self.results:
            for test_name, test_result in result["tests"].items():
                total_tests += 1
                if test_result["success"]:
                    successful_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_sites": total_sites,
                "successful_sites": successful_sites,
                "failed_sites": failed_sites,
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": success_rate
            },
            "results": self.results
        }
        
        return report
    
    def print_report(self, report: Dict[str, Any]) -> None:
        """Print test report"""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("LIGHTHOUSE.AI SITE TEST REPORT")
        print("="*60)
        
        print(f"\nSUMMARY:")
        print(f"  Sites tested: {summary['total_sites']}")
        print(f"  Successful sites: {summary['successful_sites']}")
        print(f"  Failed sites: {summary['failed_sites']}")
        print(f"  Total tests: {summary['total_tests']}")
        print(f"  Successful tests: {summary['successful_tests']}")
        print(f"  Success rate: {summary['success_rate']:.1f}%")
        
        print(f"\nDETAILED RESULTS:")
        for result in report["results"]:
            status = "✓ PASS" if result["success"] else "✗ FAIL"
            print(f"\n  {status} {result['site']} ({result['url']})")
            
            if result["error"]:
                print(f"    Error: {result['error']}")
            
            for test_name, test_result in result["tests"].items():
                test_status = "✓" if test_result["success"] else "✗"
                print(f"    {test_status} {test_name}")
                
                if not test_result["success"] and "error" in test_result:
                    print(f"      Error: {test_result['error']}")
        
        print("\n" + "="*60)
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        try:
            browser_manager.cleanup()
        except Exception as e:
            self.logger.error("Cleanup error", error=str(e))


def main():
    """Main test function"""
    tester = SiteTester()
    
    try:
        # Run tests
        report = tester.run_all_tests()
        
        # Print report
        tester.print_report(report)
        
        # Return exit code based on results
        if report["summary"]["success_rate"] >= 80:
            print("\n🎉 Tests passed! Lighthouse.ai is working well.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the report above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())
