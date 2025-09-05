import json
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ConsoleColor:    
    OKBLUE = "\033[34m"
    OKCYAN = "\033[36m"
    OKGREEN = "\033[32m"        
    MAGENTA = "\033[35m"
    WARNING = "\033[33m"
    FAIL = "\033[31m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

def load_ha_settings(config_path='/data/options.json'):
    """Load Home Assistant settings from the options file"""
    try:
        with open(config_path) as options_file:
            return json.load(options_file)
    except Exception as e:
        print(ConsoleColor.FAIL + f"Error loading settings from {config_path}: {e}" + ConsoleColor.ENDC)
        raise

def get_ha_url_and_headers(config_path='/data/options.json'):
    """Get the Home Assistant URL and headers for API calls"""
    json_settings = load_ha_settings(config_path)
    
    if json_settings['Enable_HTTPS']:
        httpurl_proto = "https"
    else:
        httpurl_proto = "http"
    
    base_url = f"{httpurl_proto}://{json_settings['Home_Assistant_IP']}:{json_settings['Home_Assistant_PORT']}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {json_settings['HA_LongLiveToken']}"
    }
    
    return base_url, headers

def check_entity_exists(entity_id, config_path='/data/options.json'):
    """Check if a Home Assistant entity exists"""
    try:
        base_url, headers = get_ha_url_and_headers(config_path)
        url = f"{base_url}/api/states/{entity_id}"
        
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        
        # If we get a 200 response, entity exists
        if response.status_code == 200:
            return True
        # If we get a 404, entity doesn't exist
        elif response.status_code == 404:
            return False
        else:
            response.raise_for_status()
            
    except requests.exceptions.RequestException as e:
        print(ConsoleColor.WARNING + f"Error checking entity {entity_id}: {e}" + ConsoleColor.ENDC)
        return False
    
    return False

def create_input_text_helper(entity_id, friendly_name, max_length=255, initial_value="", config_path='/data/options.json'):
    """Create an input_text helper entity in Home Assistant"""
    try:
        base_url, headers = get_ha_url_and_headers(config_path)
        
        # For input_text helpers, we use the config/input_text API endpoint
        url = f"{base_url}/api/config/input_text"
        
        # Extract the helper name from the entity_id (remove 'input_text.' prefix)
        helper_name = entity_id.replace('input_text.', '')
        
        payload = {
            helper_name: {
                "name": friendly_name,
                "max": max_length,
                "initial": initial_value
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        print(ConsoleColor.OKGREEN + f"Created input_text helper: {entity_id}" + ConsoleColor.ENDC)
        return True
        
    except requests.exceptions.RequestException as e:
        print(ConsoleColor.FAIL + f"Error creating input_text helper {entity_id}: {e}" + ConsoleColor.ENDC)
        
        # Fallback: try creating via states API (this might work in some HA versions)
        try:
            print(ConsoleColor.WARNING + f"Trying fallback method for {entity_id}" + ConsoleColor.ENDC)
            url = f"{base_url}/api/states/{entity_id}"
            payload = {
                "state": initial_value,
                "attributes": {
                    "friendly_name": friendly_name,
                    "max": max_length
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10, verify=False)
            response.raise_for_status()
            
            print(ConsoleColor.OKGREEN + f"Created input_text helper via fallback: {entity_id}" + ConsoleColor.ENDC)
            return True
            
        except requests.exceptions.RequestException as e2:
            print(ConsoleColor.FAIL + f"Fallback also failed for {entity_id}: {e2}" + ConsoleColor.ENDC)
            return False

def validate_and_create_required_entities(inverter_serials, config_path='/data/options.json'):
    """Validate that all required entities exist and create missing ones"""
    print(ConsoleColor.OKBLUE + "=== Validating Required Home Assistant Entities ===" + ConsoleColor.ENDC)
    
    missing_entities = []
    created_entities = []
    
    for serial in inverter_serials:
        # Check required input_text helper for settings
        settings_entity = f"input_text.solarsynkv3_{serial}_settings"
        
        print(f"Checking entity: {settings_entity}")
        
        if not check_entity_exists(settings_entity, config_path):
            print(ConsoleColor.WARNING + f"Entity {settings_entity} does not exist" + ConsoleColor.ENDC)
            missing_entities.append(settings_entity)
            
            # Try to create the missing input_text helper
            friendly_name = f"SolarSynkV3 {serial} Settings"
            if create_input_text_helper(settings_entity, friendly_name, config_path=config_path):
                created_entities.append(settings_entity)
            else:
                print(ConsoleColor.FAIL + f"Failed to create required entity: {settings_entity}" + ConsoleColor.ENDC)
                print(ConsoleColor.MAGENTA + f"Manual creation required: Go to HA GUI -> Settings -> Devices & Services -> Helpers -> Create Helper -> Text" + ConsoleColor.ENDC)
                print(ConsoleColor.MAGENTA + f"Name: {friendly_name}" + ConsoleColor.ENDC)
                print(ConsoleColor.MAGENTA + f"Entity ID: {settings_entity}" + ConsoleColor.ENDC)
        else:
            print(ConsoleColor.OKGREEN + f"Entity {settings_entity} exists" + ConsoleColor.ENDC)
    
    # Report results
    if missing_entities:
        print(ConsoleColor.WARNING + f"Found {len(missing_entities)} missing entities" + ConsoleColor.ENDC)
        if created_entities:
            print(ConsoleColor.OKGREEN + f"Successfully created {len(created_entities)} entities automatically" + ConsoleColor.ENDC)
            for entity in created_entities:
                print(f"  - {entity}")
        
        failed_entities = [e for e in missing_entities if e not in created_entities]
        if failed_entities:
            print(ConsoleColor.FAIL + f"Failed to create {len(failed_entities)} entities (manual creation required)" + ConsoleColor.ENDC)
            for entity in failed_entities:
                print(f"  - {entity}")
            return False
    else:
        print(ConsoleColor.OKGREEN + "All required entities exist" + ConsoleColor.ENDC)
    
    print(ConsoleColor.OKBLUE + "=== Entity Validation Complete ===" + ConsoleColor.ENDC)
    return True