from client.window import *
from client.settings import *
from modules.common import *
import logging


class Launcher:
    def __init__(self):
    
        #Setup Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        self.client_ip = ""
        self.server_ip = ""
        self.settings_dict = {}
        self.settings_path = "client/data/settings.json"

        #Try and read the settings file
        try:
            settings_dict : dict = open_json_file(self.settings_path)
            if settings_dict["first_run"] == True:
                self.ip_config()

            else:
                #Create an instance of the GUI
                gui = Window()
                gui.on_execute()

        except Exception as e:
            logger.error(f"Unable to open settings file: {e}")
            self.ip_config()

    def ip_config(self):
        interface_ip_list = get_machine_ip()
        interface_list_length = len(interface_ip_list)
        print(f"Available Interface Ip Addresses:")
        i=0
        for ip in interface_ip_list:
            print(f"{i} - {ip}")
            i+=1

        print("Please select an interface ip by inputting the number associated with it:")
        selection = input()
        selection_int = int(selection)

        if selection_int in range (0, interface_list_length):
            self.client_ip = interface_ip_list[selection_int]

        print("Please enter a server IP:")
        valid = False
        while valid == False:
            self.server_ip = input()
            valid = validate_ip(self.server_ip)
            print(f"Server IP Invalid, please re-enter:")

        self.settings_dict["client_ip"] = self.client_ip
        self.settings_dict["server_ip"] = self.server_ip
        self.settings_dict["fist_run"] = False

        write_dict_to_file(self.settings_dict, self.settings_path)