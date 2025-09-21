"""Natural Language Understanding module for Lighthouse.ai"""

import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from lighthouse.utils.logging import get_logger, LoggerMixin
from lighthouse.config.settings import get_settings


class Intent(Enum):
    """Supported voice command intents"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SUBMIT = "submit"
    DESCRIBE = "describe"
    LIST = "list"
    STOP = "stop"
    HELP = "help"
    UNKNOWN = "unknown"


@dataclass
class Entity:
    """Extracted entity from user input"""
    type: str
    value: str
    confidence: float
    start: int
    end: int


@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: Intent
    confidence: float
    entities: List[Entity]
    original_text: str
    processed_text: str


class NLUEngine(LoggerMixin):
    """Natural Language Understanding engine for voice commands"""
    
    def __init__(self):
        self.settings = get_settings()
        self.confidence_threshold = self.settings.nlu_confidence_threshold
        
        # Intent patterns
        self.intent_patterns = self._build_intent_patterns()
        
        # Entity patterns
        self.entity_patterns = self._build_entity_patterns()
        
        self.logger.info("NLU engine initialized")
    
    def _build_intent_patterns(self) -> Dict[Intent, List[str]]:
        """Build regex patterns for intent recognition"""
        return {
            Intent.NAVIGATE: [
                r'\b(?:go to|navigate to|visit|open|browse to)\b',
                r'\b(?:take me to|show me|load)\b',
                r'^(?:go|navigate|visit|open|browse)\s+',
            ],
            Intent.CLICK: [
                r'\b(?:click|press|tap|select|choose)\b',
                r'\b(?:hit|push|activate)\b',
                r'^(?:click|press|tap|select|choose|hit|push|activate)\s+',
            ],
            Intent.TYPE: [
                r'\b(?:type|enter|input|write|fill)\b',
                r'\b(?:put|insert|add)\s+(?:in|into)\b',
                r'^(?:type|enter|input|write|fill|put|insert|add)\s+',
            ],
            Intent.SUBMIT: [
                r'\b(?:submit|send|post|confirm)\b',
                r'\b(?:go|proceed|continue|finish)\b',
                r'^(?:submit|send|post|confirm|go|proceed|continue|finish)',
            ],
            Intent.DESCRIBE: [
                r'\b(?:describe|tell me about|what is|what\'s on)\b',
                r'\b(?:summarize|explain|read)\b',
                r'^(?:describe|tell|what|summarize|explain|read)\s+',
            ],
            Intent.LIST: [
                r'\b(?:list|show|find|search for)\b',
                r'\b(?:what are|what\'s available)\b',
                r'^(?:list|show|find|search|what)\s+',
            ],
            Intent.STOP: [
                r'\b(?:stop|cancel|quit|exit|abort)\b',
                r'\b(?:end|terminate|halt)\b',
                r'^(?:stop|cancel|quit|exit|abort|end|terminate|halt)',
            ],
            Intent.HELP: [
                r'\b(?:help|assist|guide|support)\b',
                r'\b(?:what can|how do|how to)\b',
                r'^(?:help|assist|guide|support|what|how)',
            ]
        }
    
    def _build_entity_patterns(self) -> Dict[str, List[str]]:
        """Build regex patterns for entity extraction"""
        return {
            'url': [
                r'\b(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
                r'\b(?:www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}\b',
            ],
            'number': [
                r'\b(?:first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)\b',
                r'\b(?:one|two|three|four|five|1|2|3|4|5)\b',
                r'\b(?:number|item|option|choice)\s+(\d+)\b',
            ],
            'text': [
                r'"(?:[^"\\]|\\.)*"',  # Quoted text
                r"'(?:[^'\\]|\\.)*'",  # Single quoted text
            ],
            'button': [
                r'\b(?:button|link|option|choice|item)\b',
                r'\b(?:submit|search|login|sign in|sign up|register|buy|add to cart)\b',
            ],
            'field': [
                r'\b(?:field|input|box|area)\b',
                r'\b(?:email|password|username|name|address|phone|message|comment)\b',
            ]
        }
    
    def classify_intent(self, text: str) -> IntentResult:
        """Classify intent from user input"""
        try:
            # Clean and normalize text
            processed_text = self._preprocess_text(text)
            
            # Find best matching intent
            best_intent = Intent.UNKNOWN
            best_confidence = 0.0
            matched_pattern = ""
            
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, processed_text, re.IGNORECASE)
                    if match:
                        # Calculate confidence based on pattern match quality
                        confidence = self._calculate_confidence(match, pattern, processed_text)
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_intent = intent
                            matched_pattern = pattern
            
            # Extract entities
            entities = self._extract_entities(processed_text)
            
            # Apply confidence threshold
            if best_confidence < self.confidence_threshold:
                best_intent = Intent.UNKNOWN
                best_confidence = 0.0
            
            result = IntentResult(
                intent=best_intent,
                confidence=best_confidence,
                entities=entities,
                original_text=text,
                processed_text=processed_text
            )
            
            self.logger.debug(
                "Intent classified",
                intent=best_intent.value,
                confidence=best_confidence,
                entities_count=len(entities),
                matched_pattern=matched_pattern
            )
            
            return result
            
        except Exception as e:
            self.logger.error("Intent classification failed", error=str(e))
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.0,
                entities=[],
                original_text=text,
                processed_text=text
            )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for better matching"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle common contractions
        contractions = {
            "what's": "what is",
            "what're": "what are",
            "where's": "where is",
            "where're": "where are",
            "how's": "how is",
            "how're": "how are",
            "i'm": "i am",
            "you're": "you are",
            "he's": "he is",
            "she's": "she is",
            "it's": "it is",
            "we're": "we are",
            "they're": "they are",
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "won't": "will not",
            "can't": "cannot",
            "couldn't": "could not",
            "shouldn't": "should not",
            "wouldn't": "would not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    def _calculate_confidence(self, match: re.Match, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match"""
        try:
            # Base confidence from pattern match
            match_length = len(match.group())
            text_length = len(text)
            base_confidence = match_length / text_length
            
            # Boost confidence for exact matches
            if match.group().lower() == text.lower():
                base_confidence = 1.0
            
            # Boost confidence for patterns at the beginning
            if match.start() == 0:
                base_confidence += 0.2
            
            # Boost confidence for complete words
            if match.start() == 0 or text[match.start()-1] == ' ':
                if match.end() == len(text) or text[match.end()] == ' ':
                    base_confidence += 0.1
            
            return min(1.0, base_confidence)
            
        except Exception as e:
            self.logger.error("Confidence calculation failed", error=str(e))
            return 0.5
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text"""
        entities = []
        
        try:
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        entity = Entity(
                            type=entity_type,
                            value=match.group(),
                            confidence=0.8,  # Default confidence
                            start=match.start(),
                            end=match.end()
                        )
                        entities.append(entity)
            
            # Remove overlapping entities (keep the longest)
            entities = self._remove_overlapping_entities(entities)
            
            return entities
            
        except Exception as e:
            self.logger.error("Entity extraction failed", error=str(e))
            return []
    
    def _remove_overlapping_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove overlapping entities, keeping the longest ones"""
        if not entities:
            return []
        
        # Sort by start position
        entities.sort(key=lambda e: e.start)
        
        filtered_entities = []
        for entity in entities:
            # Check if this entity overlaps with any already added
            overlaps = False
            for existing in filtered_entities:
                if (entity.start < existing.end and entity.end > existing.start):
                    overlaps = True
                    # Keep the longer entity
                    if len(entity.value) > len(existing.value):
                        filtered_entities.remove(existing)
                        filtered_entities.append(entity)
                    break
            
            if not overlaps:
                filtered_entities.append(entity)
        
        return filtered_entities
    
    def get_entity_value(self, entities: List[Entity], entity_type: str) -> Optional[str]:
        """Get the value of a specific entity type"""
        for entity in entities:
            if entity.type == entity_type:
                return entity.value
        return None
    
    def get_entity_values(self, entities: List[Entity], entity_type: str) -> List[str]:
        """Get all values of a specific entity type"""
        return [entity.value for entity in entities if entity.type == entity_type]
    
    def parse_navigation_command(self, result: IntentResult) -> Dict[str, Any]:
        """Parse navigation command and extract URL"""
        url_entities = self.get_entity_values(result.entities, 'url')
        
        if url_entities:
            url = url_entities[0]
            # Clean URL
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            return {'url': url}
        
        # Try to extract URL from text
        text = result.processed_text
        url_match = re.search(r'\b(?:go to|navigate to|visit|open)\s+([^\s]+)', text)
        if url_match:
            url = url_match.group(1)
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"
            return {'url': url}
        
        return {}
    
    def parse_click_command(self, result: IntentResult) -> Dict[str, Any]:
        """Parse click command and extract target"""
        button_entities = self.get_entity_values(result.entities, 'button')
        number_entities = self.get_entity_values(result.entities, 'number')
        
        target = {}
        
        if button_entities:
            target['button'] = button_entities[0]
        
        if number_entities:
            target['number'] = number_entities[0]
        
        # Try to extract target from text
        text = result.processed_text
        
        # Look for "click [target]" pattern
        click_match = re.search(r'\b(?:click|press|tap)\s+(.+)', text)
        if click_match:
            target_text = click_match.group(1).strip()
            target['text'] = target_text
        
        return target
    
    def parse_type_command(self, result: IntentResult) -> Dict[str, Any]:
        """Parse type command and extract text and field"""
        text_entities = self.get_entity_values(result.entities, 'text')
        field_entities = self.get_entity_values(result.entities, 'field')
        
        command = {}
        
        if text_entities:
            # Remove quotes from text
            text = text_entities[0].strip('"\'')
            command['text'] = text
        
        if field_entities:
            command['field'] = field_entities[0]
        
        # Try to extract from "type [text] in [field]" pattern
        text = result.processed_text
        type_match = re.search(r'\b(?:type|enter|input)\s+(.+?)(?:\s+in\s+(.+))?$', text)
        if type_match:
            if not command.get('text'):
                command['text'] = type_match.group(1).strip('"\'')
            if type_match.group(2) and not command.get('field'):
                command['field'] = type_match.group(2).strip()
        
        return command
    
    def get_supported_commands(self) -> List[str]:
        """Get list of supported voice commands"""
        return [
            "Navigate: 'go to google.com', 'visit amazon.com'",
            "Click: 'click search button', 'click the first link'",
            "Type: 'type hello world', 'enter my email'",
            "Submit: 'submit form', 'send message'",
            "Describe: 'describe this page', 'what's on screen'",
            "List: 'list all buttons', 'show me links'",
            "Stop: 'stop', 'cancel', 'quit'",
            "Help: 'help', 'what can you do'"
        ]


class NLUManager:
    """Manager for NLU operations"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self.nlu_engine = NLUEngine()
        self.logger.info("NLU manager initialized")
    
    def process_command(self, text: str) -> IntentResult:
        """Process a voice command"""
        return self.nlu_engine.classify_intent(text)
    
    def get_command_help(self) -> List[str]:
        """Get help information for supported commands"""
        return self.nlu_engine.get_supported_commands()


# Global NLU manager instance
nlu_manager = NLUManager()
