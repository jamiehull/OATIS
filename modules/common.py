import json
import logging
import netifaces
import ipaddress
from PIL import ImageFile
from PIL import ImageColor

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
    "Writes a python dictionary to JSON file."
    #Convert Dictionary to JSON and save to file
    logger.debug(f"Commiting dict to file...")
    file = open(file_path, "w")
    json.dump(dict, file, indent=4)
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
    """Converts a binary to image file"""
    image_file = open(path_to_save_file, "wb")
    image_file.write(blob_image)

#Converts an image to binary
def convert_to_blob(image_path:str):
    """Converts an image file to binary"""
    #Open the image file and convert to binary data
    blob_image = open(image_path, "rb")
    blob_image = blob_image.read()
    return blob_image

#Function to check for a valid ip address in the correct format
def validate_ip(ip_string):
    try:
        ip_object = ipaddress.ip_address(ip_string) #Throws ValueError exception if not valid
        valid = True

    except ValueError:
        valid = False

    return valid

def combine_lists(list1, list2) -> list:
    """Combines 2 equal length lists together into another list in the format:
    [[list1_item1, list2_item1],[list1_item2, list2_item2],...]"""

    combined_list = []

    if len(list1) == len(list2):
        for i in range(len(list1)):
            combined_list.append([list1[i], list2[i]])

    return combined_list

def resize_image_keep_aspect(image : ImageFile.ImageFile, target_width : int, target_height : int):
    """Resizes an image to a target size whilst keeping the aspect ratio."""
    
    print(f"Target Dimensions Width:{target_width}, Height:{target_height}")
    print(f"Input Image Dimensions Width:{image.width}, Height:{image.height}")

    #Find which dimension needs resizing the most
    width_resize_multiplier = target_width / image.width
    height_resize_multiplier = target_height / image.height

    if width_resize_multiplier <= height_resize_multiplier:
        #Calculate the multplier needed to scale the image's biggest dimension to the preview window size
        multiplier = width_resize_multiplier
        #Resize the image
        resized_image = image.resize(size=(int(image.width*multiplier), int(image.height*multiplier)))

    else:
        #Calculate the multplier needed to scale the image's biggest dimension to the preview window size
        multiplier = height_resize_multiplier
        #Resize the image
        resized_image = image.resize(size=(int(image.width*multiplier), int(image.height*multiplier)))

    print(f"Output Image Dimensions Width:{resized_image.width}, Height:{resized_image.height}")

    return resized_image

def make_dict(list_of_keys:list, list_of_values:list) -> dict:
    """Combines 2 equal lenght lists to make a key value dictionary. Returns an empty dict if the lists are not of equal length"""
    dict_to_return = {}
    if len(list_of_keys) == len(list_of_values):
        length = len(list_of_keys)

        for i in range(length):
            dict_to_return[list_of_keys[i]] = list_of_values[i]
    else:
        print("Lists not equal lengths!")
        print(f"Keys List: {list_of_keys}")
        print(f"Values List: {list_of_values}")

    return dict_to_return

def hex_to_rgb(hex_colour:str) -> tuple:
    """Converts a hex colour string to RGB tuple."""
    rgb_colour = ImageColor.getcolor(hex_colour, "RGB")

    return rgb_colour

def validate_hex_str(hex_str:str) -> bool:
    """Checks if a string is a valid hexadecimal colour string."""
    #Check if the first character is #
    if hex_str[0] != "#":
        return False
    
    #Check length
    if (len(hex_str) != 4) and len(hex_str) != 7:
        return False

    #Check Characters
    for i in range(1, len(hex_str)):
        character = hex_str[i]
        if (not((character >= "0" and character <= "9") or (character >= "a" and character <= "f") or (character >= "A" and character <= "F"))):
            return False
    
    return True


"""
    #Find biggest dimension
    if image.width >= image.height:
        #Calculate the multplier needed to scale the image's biggest dimension to the preview window size
        multiplier = target_width / image.width
        #Resize the image
        resized_image = image.resize(size=(int(image.width*multiplier), int(image.height*multiplier)))
    else:
        #Calculate the multplier needed to scale the image's biggest dimension to the preview window size
        multiplier = target_height / image.height
        #Resize the image
        resized_image = image.resize(size=(int(image.width*multiplier), int(image.height*multiplier)))
"""
    
