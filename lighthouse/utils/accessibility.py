"""Accessibility utilities for Lighthouse.ai"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


@dataclass
class AccessibilityNode:
    """Represents an accessibility tree node"""
    role: str
    name: str
    description: Optional[str] = None
    state: Optional[Dict[str, Any]] = None
    bounds: Optional[Dict[str, int]] = None
    children: List['AccessibilityNode'] = None
    element_id: Optional[str] = None
    xpath: Optional[str] = None
    
    def __post_init__(self):
        if self.children is None:
            self.children = []


@dataclass
class PageSummary:
    """Summary of page content and structure"""
    title: str
    url: str
    main_heading: Optional[str] = None
    landmarks: List[Dict[str, Any]] = None
    actionable_elements: List[Dict[str, Any]] = None
    focused_element: Optional[Dict[str, Any]] = None
    notifications: List[Dict[str, Any]] = None
    errors: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.landmarks is None:
            self.landmarks = []
        if self.actionable_elements is None:
            self.actionable_elements = []
        if self.notifications is None:
            self.notifications = []
        if self.errors is None:
            self.errors = []


class AccessibilityExtractor(LoggerMixin):
    """Extract accessibility information from web pages"""
    
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.settings = get_settings()
    
    def get_accessibility_tree(self) -> Optional[AccessibilityNode]:
        """Get the full accessibility tree via CDP"""
        try:
            # Execute CDP command to get accessibility tree
            result = self.driver.execute_cdp_cmd('Accessibility.getFullAXTree', {})
            
            if result and 'nodes' in result:
                return self._parse_accessibility_tree(result['nodes'])
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get accessibility tree", error=str(e))
            return None
    
    def _parse_accessibility_tree(self, nodes: List[Dict]) -> AccessibilityNode:
        """Parse accessibility tree nodes"""
        if not nodes:
            return None
        
        # Find root node
        root_node = None
        for node in nodes:
            if node.get('parentId') is None:
                root_node = node
                break
        
        if not root_node:
            return None
        
        return self._build_node_tree(root_node, nodes)
    
    def _build_node_tree(self, node_data: Dict, all_nodes: List[Dict]) -> AccessibilityNode:
        """Build accessibility node tree"""
        # Extract node properties
        role = node_data.get('role', {}).get('value', 'unknown')
        name = node_data.get('name', {}).get('value', '')
        description = node_data.get('description', {}).get('value')
        
        # Extract state
        state = {}
        if 'state' in node_data:
            for state_item in node_data['state']:
                state[state_item['name']] = state_item['value']
        
        # Extract bounds
        bounds = None
        if 'bounds' in node_data:
            bounds = {
                'x': node_data['bounds'].get('x', 0),
                'y': node_data['bounds'].get('y', 0),
                'width': node_data['bounds'].get('width', 0),
                'height': node_data['bounds'].get('height', 0)
            }
        
        # Create node
        node = AccessibilityNode(
            role=role,
            name=name,
            description=description,
            state=state,
            bounds=bounds,
            element_id=node_data.get('nodeId')
        )
        
        # Find and build children
        children = []
        for child_data in all_nodes:
            if child_data.get('parentId') == node_data.get('nodeId'):
                child_node = self._build_node_tree(child_data, all_nodes)
                if child_node:
                    children.append(child_node)
        
        node.children = children
        return node
    
    def get_page_summary(self) -> PageSummary:
        """Get a summary of the current page"""
        try:
            # Basic page info
            title = self.driver.title
            url = self.driver.current_url
            
            # Get accessibility tree
            ax_tree = self.get_accessibility_tree()
            
            # Extract information
            main_heading = self._find_main_heading(ax_tree)
            landmarks = self._extract_landmarks(ax_tree)
            actionable_elements = self._extract_actionable_elements(ax_tree)
            focused_element = self._find_focused_element(ax_tree)
            notifications = self._extract_notifications(ax_tree)
            errors = self._extract_errors(ax_tree)
            
            return PageSummary(
                title=title,
                url=url,
                main_heading=main_heading,
                landmarks=landmarks,
                actionable_elements=actionable_elements,
                focused_element=focused_element,
                notifications=notifications,
                errors=errors
            )
            
        except Exception as e:
            self.logger.error("Failed to get page summary", error=str(e))
            return PageSummary(title="", url="")
    
    def _find_main_heading(self, ax_tree: AccessibilityNode) -> Optional[str]:
        """Find the main heading (H1) on the page"""
        if not ax_tree:
            return None
        
        def search_heading(node: AccessibilityNode) -> Optional[str]:
            if node.role == 'heading' and node.state and node.state.get('level') == 1:
                return node.name
            for child in node.children:
                result = search_heading(child)
                if result:
                    return result
            return None
        
        return search_heading(ax_tree)
    
    def _extract_landmarks(self, ax_tree: AccessibilityNode) -> List[Dict[str, Any]]:
        """Extract landmark elements (header, nav, main, aside, footer)"""
        landmarks = []
        
        def search_landmarks(node: AccessibilityNode):
            if node.role in ['banner', 'navigation', 'main', 'complementary', 'contentinfo']:
                landmarks.append({
                    'role': node.role,
                    'name': node.name,
                    'description': node.description
                })
            for child in node.children:
                search_landmarks(child)
        
        if ax_tree:
            search_landmarks(ax_tree)
        
        return landmarks
    
    def _extract_actionable_elements(self, ax_tree: AccessibilityNode) -> List[Dict[str, Any]]:
        """Extract actionable elements (buttons, links, form controls)"""
        actionable = []
        
        def search_actionable(node: AccessibilityNode):
            if node.role in ['button', 'link', 'textbox', 'checkbox', 'radio', 'combobox', 'slider']:
                actionable.append({
                    'role': node.role,
                    'name': node.name,
                    'description': node.description,
                    'state': node.state,
                    'bounds': node.bounds
                })
            for child in node.children:
                search_actionable(child)
        
        if ax_tree:
            search_actionable(ax_tree)
        
        # Sort by importance and limit to top 5
        actionable.sort(key=lambda x: self._get_element_importance(x))
        return actionable[:5]
    
    def _get_element_importance(self, element: Dict[str, Any]) -> int:
        """Calculate importance score for element sorting"""
        score = 0
        
        # Role importance
        role_scores = {
            'button': 10,
            'link': 8,
            'textbox': 6,
            'checkbox': 4,
            'radio': 4,
            'combobox': 5,
            'slider': 3
        }
        score += role_scores.get(element['role'], 0)
        
        # Name presence
        if element['name']:
            score += 5
        
        # Description presence
        if element['description']:
            score += 2
        
        return score
    
    def _find_focused_element(self, ax_tree: AccessibilityNode) -> Optional[Dict[str, Any]]:
        """Find the currently focused element"""
        if not ax_tree:
            return None
        
        def search_focused(node: AccessibilityNode) -> Optional[Dict[str, Any]]:
            if node.state and node.state.get('focused'):
                return {
                    'role': node.role,
                    'name': node.name,
                    'description': node.description,
                    'state': node.state
                }
            for child in node.children:
                result = search_focused(child)
                if result:
                    return result
            return None
        
        return search_focused(ax_tree)
    
    def _extract_notifications(self, ax_tree: AccessibilityNode) -> List[Dict[str, Any]]:
        """Extract notification elements (alerts, toasts, etc.)"""
        notifications = []
        
        def search_notifications(node: AccessibilityNode):
            if node.role in ['alert', 'status', 'log', 'marquee']:
                notifications.append({
                    'role': node.role,
                    'name': node.name,
                    'description': node.description
                })
            for child in node.children:
                search_notifications(child)
        
        if ax_tree:
            search_notifications(ax_tree)
        
        return notifications
    
    def _extract_errors(self, ax_tree: AccessibilityNode) -> List[Dict[str, Any]]:
        """Extract error elements"""
        errors = []
        
        def search_errors(node: AccessibilityNode):
            if node.role == 'alert' and 'error' in (node.name or '').lower():
                errors.append({
                    'role': node.role,
                    'name': node.name,
                    'description': node.description
                })
            for child in node.children:
                search_errors(child)
        
        if ax_tree:
            search_errors(ax_tree)
        
        return errors
    
    def find_element_by_accessibility(self, role: str, name: str = None, description: str = None) -> Optional[WebElement]:
        """Find element using accessibility information"""
        try:
            # Try different strategies
            strategies = [
                # By role and name
                lambda: self.driver.find_element(By.XPATH, f"//*[@role='{role}' and contains(text(), '{name}')]") if name else None,
                # By ARIA label
                lambda: self.driver.find_element(By.XPATH, f"//*[@role='{role}' and @aria-label='{name}']") if name else None,
                # By title attribute
                lambda: self.driver.find_element(By.XPATH, f"//*[@role='{role}' and @title='{name}']") if name else None,
                # By role only
                lambda: self.driver.find_element(By.XPATH, f"//*[@role='{role}']"),
            ]
            
            for strategy in strategies:
                try:
                    element = strategy()
                    if element:
                        return element
                except:
                    continue
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to find element by accessibility", error=str(e))
            return None
    
    def get_element_accessibility_info(self, element: WebElement) -> Dict[str, Any]:
        """Get accessibility information for a specific element"""
        try:
            info = {
                'tag': element.tag_name,
                'text': element.text,
                'role': element.get_attribute('role'),
                'aria_label': element.get_attribute('aria-label'),
                'aria_description': element.get_attribute('aria-describedby'),
                'title': element.get_attribute('title'),
                'id': element.get_attribute('id'),
                'class': element.get_attribute('class'),
                'enabled': element.is_enabled(),
                'displayed': element.is_displayed(),
                'selected': element.is_selected() if hasattr(element, 'is_selected') else False
            }
            
            return info
            
        except Exception as e:
            self.logger.error("Failed to get element accessibility info", error=str(e))
            return {}


class PageDiffer(LoggerMixin):
    """Detect changes between page states"""
    
    def __init__(self):
        self.last_summary: Optional[PageSummary] = None
    
    def detect_changes(self, current_summary: PageSummary) -> Dict[str, Any]:
        """Detect changes from last page state"""
        if not self.last_summary:
            self.last_summary = current_summary
            return {'type': 'initial', 'changes': []}
        
        changes = []
        
        # Check for URL changes
        if current_summary.url != self.last_summary.url:
            changes.append({
                'type': 'navigation',
                'from': self.last_summary.url,
                'to': current_summary.url
            })
        
        # Check for title changes
        if current_summary.title != self.last_summary.title:
            changes.append({
                'type': 'title_change',
                'from': self.last_summary.title,
                'to': current_summary.title
            })
        
        # Check for new notifications
        new_notifications = []
        for notification in current_summary.notifications:
            if notification not in self.last_summary.notifications:
                new_notifications.append(notification)
        
        if new_notifications:
            changes.append({
                'type': 'new_notifications',
                'notifications': new_notifications
            })
        
        # Check for new errors
        new_errors = []
        for error in current_summary.errors:
            if error not in self.last_summary.errors:
                new_errors.append(error)
        
        if new_errors:
            changes.append({
                'type': 'new_errors',
                'errors': new_errors
            })
        
        # Check for actionable element changes
        if len(current_summary.actionable_elements) != len(self.last_summary.actionable_elements):
            changes.append({
                'type': 'actionable_elements_changed',
                'count': len(current_summary.actionable_elements)
            })
        
        self.last_summary = current_summary
        
        return {
            'type': 'changes_detected' if changes else 'no_changes',
            'changes': changes
        }
