import requests
import base64
import logging
import re
import socket
import os

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
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        logger.info("Content fetched successfully.")
        return response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch content: {e}")
        return None

def decode_base64(content):
    """Decode Base64 content."""
    try:
        decoded_content = base64.b64decode(content).decode("utf-8")
        logger.info("Base64 content decoded successfully.")
        return decoded_content
    except Exception as e:
        logger.error(f"Failed to decode Base64 content: {e}")
        return None

def extract_config_details(config):
    """Extract and parse details from a Shadowsocks config."""
    try:
        match = re.match(r"ss://([a-zA-Z0-9+/=]+)@([^:]+):(\d+)", config)
        if not match:
            logger.warning(f"Invalid config format: {config}")
            return None

        base64_part, host, port = match.groups()

        # Decode Base64 to extract method and password
        decoded_part = base64.b64decode(base64_part).decode("utf-8")
        method, password = decoded_part.split(":", 1)
        return {"method": method, "password": password, "host": host, "port": port}
    except Exception as e:
        logger.error(f"Failed to extract details from config: {config} - {e}")
        return None

def validate_and_reencode_config(config):
    """Validate and re-encode a Shadowsocks config."""
    details = extract_config_details(config)
    if not details:
        return None

    try:
        # Test if the port is open
        with socket.create_connection((details["host"], int(details["port"])), timeout=5):
            logger.info(f"Config is valid: {config}")
            return config  # Return the original config if valid
    except Exception as e:
        logger.warning(f"Failed to validate config: {config} - {e}")
        return None

def filter_valid_configs(content):
    """Extract and validate Shadowsocks configs."""
    lines = content.splitlines()
    valid_configs = []
    for line in lines:
        if line.startswith("ss://"):
            config = line.strip()
            validated_config = validate_and_reencode_config(config)
            if validated_config:
                valid_configs.append(validated_config)
    logger.info(f"Extracted {len(valid_configs)} valid configs.")
    return valid_configs

def save_to_file_as_base64(configs, file_name):
    """Save all valid configs as a single Base64-encoded string."""
    try:
        # Combine all configs into one string, then encode to Base64
        combined_configs = "\n".join(configs)
        base64_encoded_configs = base64.b64encode(combined_configs.encode("utf-8")).decode("utf-8")

        # Ensure the output directory exists
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(base64_encoded_configs)

        logger.info(f"Configs saved to {file_name} as a single Base64-encoded string.")
    except Exception as e:
        logger.error(f"Failed to save configs to file: {e}")

def main():
    """Main execution flow."""
    logger.info("Fetching Shadowsocks configs...")

    # Fetch raw content
    raw_content = fetch_content(URL)
    if not raw_content:
        logger.error("Failed to fetch content. Exiting...")
        return

    # Decode Base64 content
    decoded_content = decode_base64(raw_content)
    if not decoded_content:
        logger.error("Failed to decode content. Exiting...")
        return

    # Validate and filter configs
    valid_configs = filter_valid_configs(decoded_content)
    if not valid_configs:
        logger.warning("No valid configs found.")
        return

    # Save valid configs as a single Base64-encoded string
    save_to_file_as_base64(valid_configs, OUTPUT_FILE)
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()
