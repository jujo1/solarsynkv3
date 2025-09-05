"""Main entry point for SolarSynkV3 application."""

import gettoken
import getapi
import postapi
import settingsmanager
import os
import threading
import logging
import traceback
from datetime import datetime
from typing import Callable, List, Tuple

from utils import ConsoleColor, load_settings, print_colored

# Configure logging
logging.basicConfig(
    filename="solar_script.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load settings from JSON file
json_settings = load_settings()
api_server = json_settings['API_Server']

# Retrieve inverter serials
inverter_serials = str(json_settings['sunsynk_serial']).split(";")


def fetch_data(
    api_function: Callable[[str, str], None],
    bearer_token: str,
    serial_item: str,
    description: str
) -> None:
    """
    Safely fetch data using threading.

    Args:
        api_function: The API function to call
        bearer_token: Authentication token
        serial_item: Inverter serial number
        description: Description for logging
    """
    try:
        print_colored(f"Fetching {description}...", ConsoleColor.WARNING)
        api_function(bearer_token, str(serial_item))
    except Exception as e:
        logging.error(f"Error fetching {description}: {e}")
        print_colored(f"Error fetching {description}: {e}", ConsoleColor.FAIL)
        print(traceback.format_exc())


def main() -> None:
    """Main execution function."""
    current_date = datetime.now()

    # Start the Loop
    print("-" * 78)
    print_colored("Running Script SolarSynkV3", ConsoleColor.MAGENTA)
    print(f"Using API Endpoint: {ConsoleColor.MAGENTA}"
          f"{json_settings['API_Server']}{ConsoleColor.ENDC}")
    print("https://github.com/martinville/solarsynkv3")
    print("-" * 78)

    # Get Bearer Token
    bearer_token = ""
    try:
        bearer_token = gettoken.gettoken()
        if not bearer_token:
            print("Failed to retrieve Bearer Token. "
                  "Check credentials or server status.")
    except Exception as e:
        logging.error(f"Token retrieval error: {e}")
        print_colored("Error retrieving Bearer Token.", ConsoleColor.FAIL)
        print(traceback.format_exc())
        return

    # Iterate through all inverters (Only if bearer exists)
    if bearer_token:
        for serial_item in inverter_serials:
            process_inverter(bearer_token, serial_item, current_date)

    print_colored("Script execution completed.", ConsoleColor.OKBLUE)


def process_inverter(bearer_token: str, serial_item: str,
                     current_date: datetime) -> None:
    """
    Process a single inverter.

    Args:
        bearer_token: Authentication token
        serial_item: Inverter serial number
        current_date: Current datetime
    """
    print_colored(f"Getting {serial_item} @ {current_date}", ConsoleColor.OKCYAN)

    refresh_rate = json_settings['Refresh_rate']
    print(f"Script refresh rate set to: {ConsoleColor.OKCYAN}"
          f"{refresh_rate}{ConsoleColor.ENDC} milliseconds")

    # Clean cache
    print("Cleaning cache...")
    settings_file = "settings.json"
    if os.path.exists(settings_file):
        os.remove(settings_file)
        print("Old settings.json file removed.")

    # Test API connection
    print_colored("Testing HA API", ConsoleColor.WARNING)
    connection_result = postapi.ConnectionTest(
        "TEST", "A", "current", "connection_test", "connection_test_current", "100"
    )

    if connection_result == "Connection Success":
        print(connection_result)
        execute_api_calls(bearer_token, serial_item)
        execute_settings_management(bearer_token, serial_item)
    else:
        print_colored(connection_result, ConsoleColor.FAIL)
        print_colored("Ensure correct IP, port, and Home Assistant accessibility.",
                      ConsoleColor.MAGENTA)

    # Script completion time
    completion_time = datetime.now()
    print(f"Script completion time: {ConsoleColor.OKBLUE}"
          f" {completion_time} {ConsoleColor.ENDC}")


def execute_api_calls(bearer_token: str, serial_item: str) -> None:
    """
    Execute all API calls in parallel.

    Args:
        bearer_token: Authentication token
        serial_item: Inverter serial number
    """
    api_calls: List[Tuple[Callable[[str, str], None], str]] = [
        (getapi.GetInverterInfo, "Inverter Information"),
        (getapi.GetPvData, "PV Data"),
        (getapi.GetGridData, "Grid Data"),
        (getapi.GetBatteryData, "Battery Data"),
        (getapi.GetLoadData, "Load Data"),
        (getapi.GetOutputData, "Output Data"),
        (getapi.GetDCACTemp, "DC & AC Temperature Data"),
        (getapi.GetInverterSettingsData, "Inverter Settings")
    ]

    # Start threaded API calls
    threads = []
    for api_function, description in api_calls:
        thread = threading.Thread(
            target=fetch_data,
            args=(api_function, bearer_token, serial_item, description)
        )
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    print_colored("All API calls completed successfully!", ConsoleColor.OKGREEN)


def execute_settings_management(bearer_token: str, serial_item: str) -> None:
    """
    Execute settings download and management.

    Args:
        bearer_token: Authentication token
        serial_item: Inverter serial number
    """
    # Download and process inverter settings
    settingsmanager.DownloadProviderSettings(bearer_token, str(serial_item))
    settingsmanager.GetNewSettingsFromHAEntity(bearer_token, str(serial_item))

    # Clear old settings to prevent re-sending
    print("Cleaning out previous settings...")
    settingsmanager.ResetSettingsEntity(serial_item)


if __name__ == "__main__":
    main()
