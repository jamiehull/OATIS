import json
import logging
import netifaces
import ipaddress

#Setup Logging
logger = logging.getLogger(__name__)

#Network helper functions
def get_machine_ip() -> list:
    interfaces = netifaces.interfaces()
    logger.debug(f"Available network interfaces:{interfaces}")
    ip_list = []
    for interface in interfaces:
        try:
            interface_addresses = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]
            interface_ip = interface_addresses['addr']
            print(interface_ip)
            ip_list.append(interface_ip)

        except:
            logger.debug(f"Interface: {interface} does not have a valid ipv4 address")

    logger.info(f"Available IP Addresses:{ip_list}")
    return ip_list

#JSON Functions
def write_dict_to_file(dict, file_path):
    #Convert Dictionary to JSON and save to file
    logger.debug(f"Commiting dict to file...")
    file = open(file_path, "w")
    json.dump(dict, file)
    file.close()
    logger.debug(f"JSON File Saved")

def open_json_file(path) -> dict:
    """Returns Dictionary if the JSON File exists, Returns False if no JSON file Found."""
    try:
        file = open(path, "r")
        json_dict : dict = json.load(file)
        logger.info(f"JSON file opened")
        return json_dict
    
    except Exception as e:
        logger.error(f"Unable to open json file, reason: {e}")
        return False
    
#Converts a binary image to a jpg file
def convert_from_blob(blob_image:bytes, path_to_save_file:str):
    blob_logo = open(path_to_save_file, "wb")
    blob_logo.write(blob_image)

#Function to check for a valid ip address in the correct format
def validate_ip(ip_string):
    try:
        ip_object = ipaddress.ip_address(ip_string) #Throws ValueError exception if not valid
        valid = True

    except ValueError:
        valid = False

    return valid
