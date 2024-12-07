import requests
import base64
import logging
import re
import socket

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

def validate_config(config):
    """Validate a Shadowsocks config by checking format and testing connection."""
    try:
        # Extract the host and port from the config
        match = re.match(r"ss://[a-zA-Z0-9+/=]+@([^:]+):(\d+)", config)
        if not match:
            logger.warning(f"Invalid config format: {config}")
            return False

        host, port = match.groups()

        # Test if the port is open
        with socket.create_connection((host, int(port)), timeout=5):
            logger.info(f"Config is valid: {config}")
            return True
    except Exception as e:
        logger.warning(f"Failed to validate config: {config} - {e}")
        return False

def filter_valid_configs(content):
    """Extract and validate Shadowsocks configs."""
    lines = content.splitlines()
    valid_configs = []
    for line in lines:
        if line.startswith("ss://"):
            config = line.strip()
            if validate_config(config):
                valid_configs.append(config)
    logger.info(f"Extracted {len(valid_configs)} valid configs.")
    return valid_configs

def save_to_file(header, configs, file_name):
    """Save the header and content to the output file."""
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(header)
            f.write("\n\n")
            for config in configs:
                f.write(config + "\n")
        logger.info(f"Configs saved to {file_name}.")
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

    # Save valid configs with header to the output file
    save_to_file(valid_configs, OUTPUT_FILE)
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()
