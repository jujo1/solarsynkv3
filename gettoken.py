"""Module for handling Sunsynk API authentication tokens."""

import time
import base64
import json
import requests
from io import StringIO
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from utils import ConsoleColor, load_settings, print_colored


def gettoken() -> Optional[str]:
    """
    Get authentication token from Sunsynk API.

    Returns:
        Bearer token string if successful, empty string if failed
    """
    bearer_token = ""

    json_settings = load_settings()

    try:
        # Get public key for encryption
        public_key = _get_public_key()

        # Encrypt password
        encrypted_password = _encrypt_password(
            json_settings['sunsynk_pass'], public_key)

        # Authenticate and get token
        bearer_token = _authenticate(json_settings, encrypted_password)

    except requests.exceptions.Timeout:
        print_colored("Error: Request timed out while connecting to Sunsynk API.",
                      ConsoleColor.FAIL)
    except requests.exceptions.RequestException as e:
        print_colored(f"Error: Failed to connect to Sunsynk API. {e}",
                      ConsoleColor.FAIL)
    except json.JSONDecodeError:
        print_colored("Error: Failed to parse Sunsynk API response.",
                      ConsoleColor.FAIL)
    except Exception as e:
        print_colored(f"Unexpected error during authentication: {e}",
                      ConsoleColor.FAIL)

    return bearer_token


def _get_public_key():
    """
    Retrieve public key from Sunsynk API.

    Returns:
        Public key object for encryption

    Raises:
        requests.RequestException: If API request fails
    """
    response = requests.get(
        'https://api.sunsynk.net/anonymous/publicKey',
        params={
            'source': 'sunsynk',
            'nonce': int(time.time() * 1000)
        },
        timeout=10
    )
    response.raise_for_status()

    # Write public key file
    public_key_file = StringIO()
    public_key_file.writelines([
        '-----BEGIN PUBLIC KEY-----',
        response.json()['data'],
        '-----END PUBLIC KEY-----'
    ])
    public_key_file.seek(0)

    # Load public key
    return load_pem_public_key(
        bytes(public_key_file.read(), encoding='utf-8'),
    )


def _encrypt_password(password: str, public_key) -> str:
    """
    Encrypt password using public key.

    Args:
        password: Plain text password
        public_key: Public key for encryption

    Returns:
        Base64 encoded encrypted password
    """
    encrypted_password = base64.b64encode(public_key.encrypt(
        password.encode('utf-8'),
        padding=PKCS1v15()
    )).decode('utf-8')

    return encrypted_password


def _authenticate(json_settings: dict, encrypted_password: str) -> str:
    """
    Authenticate with Sunsynk API and get bearer token.

    Args:
        json_settings: Configuration settings
        encrypted_password: Encrypted password

    Returns:
        Bearer token if successful, empty string if failed

    Raises:
        requests.RequestException: If API request fails
        json.JSONDecodeError: If response parsing fails
    """
    # API URL
    url = f'https://{json_settings["API_Server"]}/oauth/token/new'

    # Prepare request payload
    payload = {
        "areaCode": "sunsynk",
        "client_id": "csp-web",
        "grant_type": "password",
        "password": encrypted_password,
        "source": "sunsynk",
        "username": json_settings['sunsynk_user']
    }

    # Headers
    headers = {"Content-Type": "application/json"}

    # Send POST request with timeout (10s)
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()

    # Parse response
    parsed_login_json = response.json()

    # Check login status
    if parsed_login_json.get('msg') == "Success":
        print_colored(f"Sunsynk Login: {parsed_login_json['msg']}",
                      ConsoleColor.OKGREEN)
        return parsed_login_json['data']['access_token']
    else:
        print_colored(f"Sunsynk Login: {parsed_login_json['msg']}",
                      ConsoleColor.FAIL)
        return ""
