import requests
import base64
import logging
import re
import socket
import os
import dns.resolver

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL for fetching configurations
URL = "https://raw.githubusercontent.com/3yed82/telegram-configs-collector/refs/heads/main/protocols/shadowsocks"

# Output file name
OUTPUT_FILE = "Export/clean-configs.txt"

def fetch_content(url):
    """Download content from the given URL."""
    logger.info(f"Attempting to fetch content from URL: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info(f"Content fetched successfully from {url}. Length: {len(response.text)} characters.")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch content from {url}: {e}")
        return None

def decode_base64(content):
    """Decode Base64 content."""
    logger.info("Attempting to decode Base64 content.")
    try:
        decoded_content = base64.b64decode(content).decode("utf-8")
        logger.info(f"Base64 content decoded successfully. Decoded length: {len(decoded_content)} characters.")
        return decoded_content
    except Exception as e:
        logger.error(f"Failed to decode Base64 content: {e}")
        return None

def extract_config_details(config):
    """Extract and parse details from a Shadowsocks config."""
    logger.info(f"Attempting to extract details from config: {config}")
    try:
        match = re.match(r"ss://([a-zA-Z0-9+/=]+)@([^:]+):(\d+)", config)
        if not match:
            logger.warning(f"Invalid config format: {config}")
            return None

        base64_part, host, port = match.groups()
        logger.info(f"Config parsed successfully. Host: {host}, Port: {port}, Base64 Part: {base64_part[:10]}...")
        decoded_part = base64.b64decode(base64_part).decode("utf-8")
        method, password = decoded_part.split(":", 1)
        logger.info(f"Decoded method: {method}, password: [hidden].")
        return {"method": method, "password": password, "host": host, "port": port}
    except Exception as e:
        logger.error(f"Failed to extract details from config: {config} - {e}")
        return None

def validate_host(host):
    """Validate if the host (IP or domain) is reachable."""
    logger.info(f"Validating host: {host}")
    try:
        dns.resolver.resolve(host, "A")
        logger.info(f"Host {host} is valid.")
        return True
    except Exception as e:
        logger.warning(f"Host {host} is invalid: {e}")
        return False

def validate_encryption_method(method):
    """Validate if the encryption method is supported."""
    logger.info(f"Validating encryption method: {method}")
    valid_methods = [
        "aes-256-gcm", "aes-128-gcm", "chacha20-ietf-poly1305",
        "xchacha20-ietf-poly1305", "aes-256-cfb", "aes-128-cfb"
    ]
    if method.lower() in valid_methods:
        logger.info(f"Encryption method {method} is valid.")
        return True
    else:
        logger.warning(f"Invalid encryption method: {method}")
        return False

def validate_and_reencode_config(config):
    """Validate and re-encode a Shadowsocks config."""
    logger.info(f"Validating config: {config}")
    details = extract_config_details(config)
    if not details:
        logger.warning(f"Config extraction failed: {config}")
        return None

    if not validate_encryption_method(details["method"]):
        logger.warning(f"Config rejected due to invalid encryption method: {config}")
        return None

    if not validate_host(details["host"]):
        logger.warning(f"Config rejected due to invalid host: {config}")
        return None

    try:
        with socket.create_connection((details["host"], int(details["port"])), timeout=5):
            logger.info(f"Port validation successful for config: {config}")
            return config
    except Exception as e:
        logger.warning(f"Port validation failed for config: {config} - {e}")
        return None

def filter_valid_configs(content):
    """Extract and validate Shadowsocks configs."""
    logger.info("Starting to filter valid configs.")
    lines = content.splitlines()
    valid_configs = []
    for line in lines:
        if line.startswith("ss://"):
            config = line.strip()
            logger.info(f"Processing config: {config}")
            validated_config = validate_and_reencode_config(config)
            if validated_config:
                valid_configs.append(validated_config)
    logger.info(f"Filtering complete. Valid configs extracted: {len(valid_configs)}")
    return valid_configs

def save_to_file_as_base64(configs, file_name):
    """Save all valid configs as a single Base64-encoded string."""
    logger.info(f"Saving configs to file: {file_name}")
    try:
        combined_configs = "\n".join(configs)
        base64_encoded_configs = base64.b64encode(combined_configs.encode("utf-8")).decode("utf-8")
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(base64_encoded_configs)
        logger.info(f"Configs saved successfully to {file_name}.")
    except Exception as e:
        logger.error(f"Failed to save configs to file: {e}")

def main():
    """Main execution flow."""
    logger.info("Fetching Shadowsocks configs...")
    raw_content = fetch_content(URL)
    if not raw_content:
        logger.error("Failed to fetch content. Exiting...")
        return

    decoded_content = decode_base64(raw_content)
    if not decoded_content:
        logger.error("Failed to decode content. Exiting...")
        return

    valid_configs = filter_valid_configs(decoded_content)
    if not valid_configs:
        logger.warning("No valid configs found.")
        return

    save_to_file_as_base64(valid_configs, OUTPUT_FILE)
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()
