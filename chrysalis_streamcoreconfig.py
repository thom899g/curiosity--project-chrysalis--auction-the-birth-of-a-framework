"""
Configuration management for Project CHRYSALIS.
Centralizes all environment variables and settings with validation.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


class Tier(Enum):
    """Subscription tier definitions."""
    OBSERVER = "observer"
    ARCHITECT = "architect"
    EMBEDDED = "embedded"
    
    def get_permissions(self) -> Dict[str, bool]:
        """Return permissions for each tier."""
        return {
            "view_logs": True,
            "view_code": self in [self.ARCHITECT, self.EMBEDDED],
            "view_telemetry": self in [self.ARCHITECT, self.EMBEDDED],
            "ask_questions": self == self.EMBEDDED,
            "access_realtime": True
        }


@dataclass
class FirebaseConfig:
    """Firebase configuration with validation."""
    project_id: str
    private_key_id: str
    private_key: str
    client_email: str
    client_id: str
    auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    token_uri: str = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url: str = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url: str = ""
    
    @classmethod
    def from_env(cls) -> Optional['FirebaseConfig']:
        """Load Firebase config from environment variables or file."""
        try:
            # Try JSON string first
            firebase_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
            if firebase_json:
                config_data = json.loads(firebase_json)
            else:
                # Try file path
                config_path = os.getenv('FIREBASE_CONFIG_PATH', './firebase-config.json')
                if not os.path.exists(config_path):
                    logger.warning(f"Firebase config file not found at {config_path}")
                    return None
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
            
            return cls(
                project_id=config_data.get('project_id', ''),
                private_key_id=config_data.get('private_key_id', ''),
                private_key=config_data.get('private_key', '').replace('\\n', '\n'),
                client_email=config_data.get('client_email', ''),
                client_id=config_data.get('client_id', ''),
                client_x509_cert_url=config_data.get('client_x509_cert_url', '')
            )
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.error(f"Failed to load Firebase config: {e}")
            return None


@dataclass
class StripeConfig:
    """Stripe API configuration."""
    secret_key: str
    publishable_key: str
    webhook_secret: str
    
    @classmethod
    def from_env(cls) -> Optional['StripeConfig']:
        """Load Stripe config from environment."""
        secret_key = os.getenv('STRIPE_SECRET_KEY')
        if not secret_key:
            logger.warning("STRIPE_SECRET_KEY not found in environment")
            return None
            
        return cls(
            secret_key=secret_key,
            publishable_key=os.getenv('STRIPE_PUBLISHABLE_KEY', ''),
            webhook_secret=os.getenv('STRIPE_WEBHOOK_SECRET', '')
        )


class AppConfig:
    """Main application configuration."""
    
    _instance: Optional['AppConfig'] = None
    
    def __init__(self):
        if AppConfig._instance is not None:
            raise Exception("AppConfig is a singleton")
        
        # Core settings
        self.project_name = os.getenv('PROJECT_NAME', 'Project CHRYSALIS')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # AWS Lightsail settings
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Firebase config
        self.firebase = FirebaseConfig.from_env()
        
        # Stripe config
        self.stripe = StripeConfig.from_env()
        
        # Pricing tiers (in cents)
        self.pricing = {
            Tier.OBSERVER: 999,  # $