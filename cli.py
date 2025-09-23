#!/usr/bin/env python3
"""CLI interface for Lighthouse.ai voice-driven web navigator"""

import sys
import time
import signal
import threading
from typing import Optional
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.live import Live
from rich.table import Table

from lighthouse.utils.logging import get_logger, setup_logging
from lighthouse.core.asr import asr_manager
from lighthouse.core.tts import tts_manager
from lighthouse.core.browser import browser_manager
from lighthouse.core.nlu import nlu_manager, Intent
from lighthouse.core.safety import safety_manager, ActionType
from lighthouse.core.state import session_manager
from lighthouse.config.settings import get_settings


class LighthouseCLI:
    """Main CLI interface for Lighthouse.ai"""
    
    def __init__(self):
        self.console = Console()
        self.settings = get_settings()
        self.logger = get_logger(self.__class__.__name__)
        
        # State
        self.is_running = False
        self.is_listening = False
        self.current_command = ""
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info("Received shutdown signal", signal=signum)
        self.stop()
        sys.exit(0)
    
    def _speak(self, text: str) -> None:
        """Speak text with error handling"""
        try:
            self._speak(text)
        except Exception:
            # TTS not available, just continue silently
            pass
    
    def start(self) -> None:
        """Start the Lighthouse CLI"""
        try:
            self.console.print(Panel.fit(
                "[bold blue]Lighthouse.ai[/bold blue]\n"
                "Voice-driven web navigator for blind and low-vision users",
                title="Welcome"
            ))
            
            # Initialize components
            self._initialize_components()
            
            # Start main loop
            self.is_running = True
            self._main_loop()
            
        except Exception as e:
            self.logger.error("Failed to start CLI", error=str(e))
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    def _initialize_components(self) -> None:
        """Initialize all components"""
        self.console.print("[yellow]Initializing components...[/yellow]")
        
        # Create session
        session_manager.create_session()
        
        # Test TTS
        try:
            self._speak("Lighthouse is ready. Press spacebar to start listening.")
            self.console.print("[green]✓ TTS initialized[/green]")
        except Exception as e:
            self.console.print(f"[yellow]⚠ TTS not available: {e}[/yellow]")
            self.console.print("[yellow]Voice feedback disabled, but speech recognition still works.[/yellow]")
        
        self.console.print("[green]All components initialized successfully![/green]")
    
    def _main_loop(self) -> None:
        """Main command loop"""
        self.console.print("\n[bold]Commands:[/bold]")
        self.console.print("• Press [bold]SPACEBAR[/bold] to start/stop listening")
        self.console.print("• Type [bold]'help'[/bold] for available commands")
        self.console.print("• Type [bold]'quit'[/bold] to exit")
        self.console.print("\n[dim]Waiting for input...[/dim]")
        
        while self.is_running:
            try:
                # Check for keyboard input
                user_input = self._get_user_input()
                
                if user_input:
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        break
                    elif user_input.lower() == 'help':
                        self._show_help()
                    elif user_input.lower() == 'listen':
                        self._start_listening()
                    elif user_input.lower() == 'stop':
                        self._stop_listening()
                    else:
                        # Process as voice command
                        self._process_command(user_input)
                
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error("Main loop error", error=str(e))
                self.console.print(f"[red]Error: {e}[/red]")
    
    def _get_user_input(self) -> Optional[str]:
        """Get user input (simplified for demo)"""
        import select
        import tty
        import termios
        
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            return input().strip()
        return None
    
    def _start_listening(self) -> None:
        """Start voice listening"""
        if self.is_listening:
            self.console.print("[yellow]Already listening...[/yellow]")
            return
        
        try:
            self.is_listening = True
            self.console.print("[green]🎤 Listening... (speak now)[/green]")
            
            # Listen for speech
            result = asr_manager.listen(max_duration=10.0)
            
            if result.text:
                self.current_command = result.text
                self.console.print(f"[blue]Heard: {result.text}[/blue]")
                self._process_command(result.text)
            else:
                self.console.print("[yellow]No speech detected[/yellow]")
                self._speak("No speech detected. Please try again.")
            
        except Exception as e:
            self.logger.error("Listening failed", error=str(e))
            self.console.print(f"[red]Listening error: {e}[/red]")
            self._speak("Sorry, I couldn't hear you. Please try again.")
        finally:
            self.is_listening = False
    
    def _stop_listening(self) -> None:
        """Stop voice listening"""
        self.is_listening = False
        self.console.print("[yellow]Stopped listening[/yellow]")
    
    def _process_command(self, command: str) -> None:
        """Process a voice command"""
        try:
            self.console.print(f"\n[bold]Processing: {command}[/bold]")
            
            # Classify intent
            intent_result = nlu_manager.process_command(command)
            
            if intent_result.intent == Intent.UNKNOWN:
                self.console.print("[red]Unknown command[/red]")
                self._speak("I didn't understand that command. Please try again.")
                return
            
            # Execute command
            self._execute_intent(intent_result)
            
        except Exception as e:
            self.logger.error("Command processing failed", error=str(e))
            self.console.print(f"[red]Error: {e}[/red]")
            self._speak("Sorry, there was an error processing your command.")
    
    def _execute_intent(self, intent_result) -> None:
        """Execute the classified intent"""
        start_time = time.time()
        
        try:
            if intent_result.intent == Intent.NAVIGATE:
                self._handle_navigate(intent_result)
            elif intent_result.intent == Intent.CLICK:
                self._handle_click(intent_result)
            elif intent_result.intent == Intent.TYPE:
                self._handle_type(intent_result)
            elif intent_result.intent == Intent.SUBMIT:
                self._handle_submit(intent_result)
            elif intent_result.intent == Intent.DESCRIBE:
                self._handle_describe(intent_result)
            elif intent_result.intent == Intent.LIST:
                self._handle_list(intent_result)
            elif intent_result.intent == Intent.STOP:
                self._handle_stop(intent_result)
            elif intent_result.intent == Intent.HELP:
                self._handle_help(intent_result)
            
            # Log action
            duration = time.time() - start_time
            session_manager.add_action(
                action_type=intent_result.intent.value,
                target=intent_result.processed_text,
                result="Success",
                success=True,
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            session_manager.add_action(
                action_type=intent_result.intent.value,
                target=intent_result.processed_text,
                result="Failed",
                success=False,
                duration=duration,
                error=str(e)
            )
            raise
    
    def _handle_navigate(self, intent_result) -> None:
        """Handle navigation command"""
        parsed = nlu_manager.nlu_engine.parse_navigation_command(intent_result)
        
        if 'url' in parsed:
            url = parsed['url']
            
            # Check safety
            if not safety_manager.is_domain_allowed(url):
                self.console.print(f"[red]Domain not allowed: {url}[/red]")
                self._speak(f"Sorry, {url} is not in the allowed domains list.")
                return
            
            # Navigate
            self.console.print(f"[blue]Navigating to: {url}[/blue]")
            self._speak(f"Navigating to {url}")
            
            success = browser_manager.navigate(url)
            if success:
                session_manager.update_current_url(url)
                page_info = browser_manager.get_page_info()
                self._announce_page_info(page_info)
            else:
                self._speak("Navigation failed. Please try again.")
        else:
            self._speak("I didn't understand the URL. Please specify a website to visit.")
    
    def _handle_click(self, intent_result) -> None:
        """Handle click command"""
        parsed = nlu_manager.nlu_engine.parse_click_command(intent_result)
        
        # Check safety
        if safety_manager.requires_confirmation(ActionType.CLICK):
            if not Confirm.ask("Confirm click action?"):
                self._speak("Click action cancelled.")
                return
        
        self.console.print("[blue]Looking for clickable element...[/blue]")
        self._speak("Looking for clickable element")
        
        # Find and click element
        elements = browser_manager.browser.list_actionable_elements()
        if elements:
            # For demo, click the first element
            element = browser_manager.browser.find_element("button")
            if element:
                success = browser_manager.browser.click_element(element)
                if success:
                    self._speak("Element clicked successfully")
                    self._announce_page_changes()
                else:
                    self._speak("Click failed")
            else:
                self._speak("No clickable elements found")
        else:
            self._speak("No clickable elements found on this page")
    
    def _handle_type(self, intent_result) -> None:
        """Handle type command"""
        parsed = nlu_manager.nlu_engine.parse_type_command(intent_result)
        
        if 'text' in parsed:
            text = parsed['text']
            self.console.print(f"[blue]Typing: {text}[/blue]")
            self._speak(f"Typing {text}")
            
            # Find input field and type
            element = browser_manager.browser.find_element("input")
            if element:
                success = browser_manager.browser.type_text(element, text)
                if success:
                    self._speak("Text entered successfully")
                else:
                    self._speak("Failed to enter text")
            else:
                self._speak("No input field found")
        else:
            self._speak("I didn't understand what to type. Please specify the text.")
    
    def _handle_submit(self, intent_result) -> None:
        """Handle submit command"""
        # Check safety
        if safety_manager.requires_confirmation(ActionType.SUBMIT):
            if not Confirm.ask("Confirm form submission?"):
                self._speak("Form submission cancelled.")
                return
        
        self.console.print("[blue]Submitting form...[/blue]")
        self._speak("Submitting form")
        
        success = browser_manager.browser.submit_form()
        if success:
            self._speak("Form submitted successfully")
            self._announce_page_changes()
        else:
            self._speak("Form submission failed")
    
    def _handle_describe(self, intent_result) -> None:
        """Handle describe command"""
        self.console.print("[blue]Describing page...[/blue]")
        
        page_info = browser_manager.get_page_info()
        self._announce_page_info(page_info)
    
    def _handle_list(self, intent_result) -> None:
        """Handle list command"""
        self.console.print("[blue]Listing elements...[/blue]")
        
        elements = browser_manager.browser.list_actionable_elements()
        if elements:
            self._speak(f"Found {len(elements)} actionable elements")
            for i, element in enumerate(elements[:5], 1):
                description = f"{i}. {element.role}: {element.text or element.aria_label or 'No label'}"
                self.console.print(f"[green]{description}[/green]")
                self._speak(description)
        else:
            self._speak("No actionable elements found on this page")
    
    def _handle_stop(self, intent_result) -> None:
        """Handle stop command"""
        self.console.print("[yellow]Stopping current action...[/yellow]")
        self._speak("Stopping current action")
        self._stop_listening()
    
    def _handle_help(self, intent_result) -> None:
        """Handle help command"""
        self._show_help()
    
    def _announce_page_info(self, page_info) -> None:
        """Announce page information"""
        announcement = f"Page: {page_info.title}"
        if page_info.main_heading:
            announcement += f". Main heading: {page_info.main_heading}"
        
        announcement += f". Found {len(page_info.actionable_elements)} actionable elements."
        
        self.console.print(f"[green]{announcement}[/green]")
        self._speak(announcement)
    
    def _announce_page_changes(self) -> None:
        """Announce page changes"""
        changes = browser_manager.browser.detect_page_changes()
        
        if changes['type'] == 'changes_detected':
            self._speak("Page has changed")
        elif changes['type'] == 'navigation':
            self._speak("Navigated to new page")
        else:
            self._speak("No significant changes detected")
    
    def _show_help(self) -> None:
        """Show help information"""
        help_text = Text("Available Commands:", style="bold blue")
        help_text.append("\n\n")
        
        commands = nlu_manager.get_command_help()
        for command in commands:
            help_text.append(f"• {command}\n")
        
        help_text.append("\nKeyboard Shortcuts:")
        help_text.append("\n• SPACEBAR: Start/stop listening")
        help_text.append("\n• 'help': Show this help")
        help_text.append("\n• 'quit': Exit Lighthouse")
        
        self.console.print(Panel(help_text, title="Help"))
        self._speak("Help information displayed. You can say navigate, click, type, submit, describe, list, stop, or help.")
    
    def stop(self) -> None:
        """Stop the CLI"""
        self.is_running = False
        self.is_listening = False
        
        # Cleanup components
        try:
            session_manager.cleanup()
            browser_manager.cleanup()
            tts_manager.cleanup()
            asr_manager.cleanup()
        except Exception as e:
            self.logger.error("Cleanup error", error=str(e))
        
        self.console.print("\n[yellow]Lighthouse stopped. Goodbye![/yellow]")


@click.command()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--headless', is_flag=True, help='Run browser in headless mode')
@click.option('--url', help='Start by navigating to a specific URL')
def main(debug: bool, headless: bool, url: Optional[str]):
    """Lighthouse.ai - Voice-driven web navigator"""
    
    # Setup logging
    setup_logging()
    
    # Update settings
    settings = get_settings()
    if debug:
        settings.debug = True
        settings.log_level = "DEBUG"
    if headless:
        settings.headless_mode = True
    
    # Create and start CLI
    cli = LighthouseCLI()
    
    try:
        if url:
            # Navigate to initial URL
            cli.console.print(f"[blue]Starting with URL: {url}[/blue]")
            browser_manager.navigate(url)
            session_manager.update_current_url(url)
        
        cli.start()
    except KeyboardInterrupt:
        cli.console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        cli.console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)
    finally:
        cli.stop()


if __name__ == "__main__":
    main()
