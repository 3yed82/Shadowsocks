import requests
import base64
import re
import logging

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,  # Set level to DEBUG to get more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL for fetching configurations
URL = "https://raw.githubusercontent.com/3yed-61/Shadowsocks/refs/heads/main/Export/clean-configs.txt"

# Output file name
OUTPUT_FILE = "configs.txt"

# Header to include in the output file
HEADER = """//profile-title: base64:4pyU77iPM867zp7EkPCflLgoU2hhZG93c29ja3Mp
//profile-update-interval: 24
//subscription-userinfo: upload=5368709120; download=445097156608; total=955630223360; expire=1762677732
//support-url: https://t.me/talk_to_3yed_bot
//profile-web-page-url: https://github.com/3yed-61
"""

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

def clean_config(config_line):
    """Clean and extract the Shadowsocks configuration along with the flag."""
    # Match valid ss:// configurations
    match = re.match(r"(ss://[a-zA-Z0-9+/=]+@[^#\s]+)(#.*)?", config_line)
    if not match:
        return None
    base_config = match.group(1)  # Base ss:// config
    flag_section = match.group(2)  # Extract the part after #
    
    if flag_section:
        # Extract country flag from the flag section (e.g., 🇺🇸)
        country_flag = re.search(r"[\U0001F1E6-\U0001F1FF]{1,2}", flag_section)
        country_flag = country_flag.group(0) if country_flag else ""
    else:
        country_flag = ""
    
    # Create new config with the required format
    return f"{base_config}#♨️3λΞĐ |{country_flag}"

def extract_ss_configs(decoded_content):
    """Extract and clean Shadowsocks configurations."""
    lines = decoded_content.splitlines()
    cleaned_configs = []
    for line in lines:
        if line.startswith("ss://"):
            cleaned_config = clean_config(line.strip())
            if cleaned_config:
                cleaned_configs.append(cleaned_config)
    logger.info(f"Extracted {len(cleaned_configs)} valid ss:// configs.")
    return cleaned_configs

def save_to_file(header, configs, file_name):
    """Save the header and configurations to the output file."""
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(header)  # Write header first
            f.write("\n\n")   # Add a blank line before configs
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

    # Extract and clean configurations
    ss_configs = extract_ss_configs(decoded_content)
    if not ss_configs:
        logger.warning("No valid ss:// configs found.")
        return

    # Save configurations with header to the output file
    save_to_file(HEADER, ss_configs, OUTPUT_FILE)
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()
