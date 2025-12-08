import logging
import socket
import json
from datetime import datetime

class LogstashHandler(logging.Handler):
    """Custom handler that sends logs to Logstash via TCP"""
    
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.sock = None
        self._connect()
    
    def _connect(self):
        """Establish TCP connection to Logstash"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            print(f"✓ Connected to Logstash at {self.host}:{self.port}")
        except Exception as e:
            print(f"✗ Failed to connect to Logstash: {e}")
            self.sock = None
    
    def emit(self, record):
        """Send log record to Logstash"""
        if not self.sock:
            self._connect()
        
        if self.sock:
            try:
                # Build JSON log entry
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'service': getattr(record, 'service_name', 'backend'),
                    'message': record.getMessage(),
                    'logger': record.name,
                    'pathname': record.pathname,
                    'lineno': record.lineno
                }
                
                # Add event data if present (for login events)
                if hasattr(record, 'event_data'):
                    log_entry['event_data'] = record.event_data
                    log_entry['event_type'] = 'login_event'
                
                # Send to Logstash
                message = json.dumps(log_entry) + '\n'
                self.sock.sendall(message.encode('utf-8'))
                
            except Exception as e:
                print(f"✗ Failed to send log to Logstash: {e}")
                self.sock = None
                self._connect()

def setup_logging(service_name='backend'):
    """
    Setup logging with both console and Logstash handlers
    
    Args:
        service_name: Name of the service (backend/consumer)
    
    Returns:
        logger: Configured logger instance
    """
    import os
    
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console Handler (so you can see logs in docker logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Logstash Handler (sends to ELK)
    logstash_host = os.getenv('LOGSTASH_HOST', 'logstash')
    logstash_port = int(os.getenv('LOGSTASH_PORT', 5044))
    
    try:
        logstash_handler = LogstashHandler(logstash_host, logstash_port)
        logstash_handler.setLevel(logging.INFO)
        
        # Add service name to all records
        class ServiceFilter(logging.Filter):
            def filter(self, record):
                record.service_name = service_name
                return True
        
        logstash_handler.addFilter(ServiceFilter())
        logger.addHandler(logstash_handler)
        
    except Exception as e:
        print(f"⚠ Could not connect to Logstash: {e}")
    
    return logger