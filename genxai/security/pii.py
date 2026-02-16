"""PII detection and redaction for GenXAI."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, UTC


# PII patterns
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    "ip_address": r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
    "api_key": r'\b[A-Za-z0-9]{32,}\b',
    "passport": r'\b[A-Z]{1,2}\d{6,9}\b',
    "driver_license": r'\b[A-Z]{1,2}\d{5,8}\b',
}


@dataclass
class PIIMatch:
    """PII match result."""
    pii_type: str
    value: str
    start: int
    end: int


class PIIDetector:
    """Detect PII in text."""
    
    def __init__(self, patterns: Optional[Dict[str, str]] = None):
        """Initialize PII detector.
        
        Args:
            patterns: Custom PII patterns (default: use built-in patterns)
        """
        self.patterns = patterns or PII_PATTERNS
    
    def detect(self, text: str) -> List[PIIMatch]:
        """Detect all PII in text.
        
        Args:
            text: Text to scan
            
        Returns:
            List of PII matches
        """
        matches = []
        
        for pii_type, pattern in self.patterns.items():
            for match in re.finditer(pattern, text):
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    value=match.group(),
                    start=match.start(),
                    end=match.end()
                ))
        
        # Sort by position
        matches.sort(key=lambda x: x.start)
        
        return matches
    
    def detect_type(self, text: str, pii_type: str) -> List[PIIMatch]:
        """Detect specific PII type.
        
        Args:
            text: Text to scan
            pii_type: PII type to detect
            
        Returns:
            List of PII matches
        """
        if pii_type not in self.patterns:
            return []
        
        pattern = self.patterns[pii_type]
        matches = []
        
        for match in re.finditer(pattern, text):
            matches.append(PIIMatch(
                pii_type=pii_type,
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))
        
        return matches
    
    def has_pii(self, text: str) -> bool:
        """Check if text contains PII.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII detected
        """
        for pattern in self.patterns.values():
            if re.search(pattern, text):
                return True
        
        return False


class PIIRedactor:
    """Redact PII from text."""
    
    def __init__(self, detector: Optional[PIIDetector] = None):
        """Initialize PII redactor.
        
        Args:
            detector: PII detector (default: create new detector)
        """
        self.detector = detector or PIIDetector()
    
    def redact(
        self,
        text: str,
        replacement: str = "***REDACTED***",
        pii_types: Optional[List[str]] = None
    ) -> str:
        """Redact all PII.
        
        Args:
            text: Text to redact
            replacement: Replacement string
            pii_types: Specific PII types to redact (default: all)
            
        Returns:
            Redacted text
        """
        matches = self.detector.detect(text)
        
        # Filter by PII types if specified
        if pii_types:
            matches = [m for m in matches if m.pii_type in pii_types]
        
        # Redact from end to start to preserve positions
        for match in reversed(matches):
            text = text[:match.start] + replacement + text[match.end:]
        
        return text
    
    def mask(self, text: str, pii_types: Optional[List[str]] = None) -> str:
        """Mask PII (show last 4 characters).
        
        Args:
            text: Text to mask
            pii_types: Specific PII types to mask (default: all)
            
        Returns:
            Masked text
        """
        matches = self.detector.detect(text)
        
        # Filter by PII types if specified
        if pii_types:
            matches = [m for m in matches if m.pii_type in pii_types]
        
        # Mask from end to start to preserve positions
        for match in reversed(matches):
            value = match.value
            
            if match.pii_type == "email":
                # email@example.com -> e***@example.com
                parts = value.split('@')
                if len(parts) == 2:
                    masked = parts[0][0] + '***@' + parts[1]
                else:
                    masked = '***'
            
            elif match.pii_type in ["phone", "ssn", "credit_card"]:
                # Show last 4 digits
                masked = '***-***-' + value[-4:]
            
            elif match.pii_type == "ip_address":
                # Show first octet
                parts = value.split('.')
                masked = parts[0] + '.***.***.***'
            
            else:
                # Default: show last 4 characters
                if len(value) > 4:
                    masked = '***' + value[-4:]
                else:
                    masked = '***'
            
            text = text[:match.start] + masked + text[match.end:]
        
        return text
    
    def redact_dict(
        self,
        data: Dict[str, Any],
        replacement: str = "***REDACTED***"
    ) -> Dict[str, Any]:
        """Redact PII from dictionary recursively.
        
        Args:
            data: Dictionary to redact
            replacement: Replacement string
            
        Returns:
            Redacted dictionary
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.redact(value, replacement)
            elif isinstance(value, dict):
                result[key] = self.redact_dict(value, replacement)
            elif isinstance(value, list):
                result[key] = [
                    self.redact(item, replacement) if isinstance(item, str)
                    else self.redact_dict(item, replacement) if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result


class PIIAuditLogger:
    """Log PII access for compliance."""
    
    def __init__(self, log_file: str = "pii_audit.log"):
        """Initialize PII audit logger.
        
        Args:
            log_file: Path to audit log file
        """
        self.log_file = log_file
    
    def log_access(
        self,
        user_id: str,
        pii_type: str,
        action: str,
        context: Dict[str, Any]
    ):
        """Log PII access.
        
        Args:
            user_id: User ID
            pii_type: PII type accessed
            action: Action performed (read, write, delete)
            context: Additional context
        """
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "pii_type": pii_type,
            "action": action,
            "context": context
        }
        
        with open(self.log_file, 'a') as f:
            import json
            f.write(json.dumps(log_entry) + '\n')
    
    def get_logs(
        self,
        user_id: Optional[str] = None,
        pii_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get audit logs with filters.
        
        Args:
            user_id: Filter by user ID
            pii_type: Filter by PII type
            start_time: Filter by start time
            end_time: Filter by end time
            
        Returns:
            List of log entries
        """
        import json
        logs = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        
                        # Apply filters
                        if user_id and entry.get("user_id") != user_id:
                            continue
                        
                        if pii_type and entry.get("pii_type") != pii_type:
                            continue
                        
                        timestamp = datetime.fromisoformat(entry["timestamp"])
                        
                        if start_time and timestamp < start_time:
                            continue
                        
                        if end_time and timestamp > end_time:
                            continue
                        
                        logs.append(entry)
                    
                    except json.JSONDecodeError:
                        continue
        
        except FileNotFoundError:
            pass
        
        return logs


# Global instances
_pii_detector = None
_pii_redactor = None
_pii_audit_logger = None


def get_pii_detector() -> PIIDetector:
    """Get global PII detector.
    
    Returns:
        PIIDetector instance
    """
    global _pii_detector
    
    if _pii_detector is None:
        _pii_detector = PIIDetector()
    
    return _pii_detector


def get_pii_redactor() -> PIIRedactor:
    """Get global PII redactor.
    
    Returns:
        PIIRedactor instance
    """
    global _pii_redactor
    
    if _pii_redactor is None:
        _pii_redactor = PIIRedactor()
    
    return _pii_redactor


def get_pii_audit_logger() -> PIIAuditLogger:
    """Get global PII audit logger.
    
    Returns:
        PIIAuditLogger instance
    """
    global _pii_audit_logger
    
    if _pii_audit_logger is None:
        _pii_audit_logger = PIIAuditLogger()
    
    return _pii_audit_logger
