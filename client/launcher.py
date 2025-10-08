from client.window import *
from modules.common import *
import logging


class Launcher:
    """Provides a terminal interface to set IP settings on first run or if the settings file is missing. Launches app as normal if settings file is present and not first run."""
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
            if settings_dict == False:
                logger.warning("No settings file, entering setup script...")
                self.ip_config()
                self.start_app()

            #If its the first run, setup the ip settings
            elif settings_dict["first_run"] == True:
                self.ip_config()
                self.start_app()
                    
            #If a valid settings file exists and it's not first run, boot as normal
            elif settings_dict["first_run"] == False:
                self.start_app()

            else:
                self.ip_config()
                self.start_app()

        #If the settings file does not exist make a new one and start app
        except Exception as e:
            logger.error(f"Unable to open settings file: {e}")
            self.ip_config()

    def ip_config(self):
        """Creates the settings file."""
        #Get a list of IP's associated wit this machines network interfaces
        self.interface_ip_list = get_machine_ip()
        self.interface_list_length = len(self.interface_ip_list)

        #Print to terminal
        print(f"Available Interface Ip Addresses:")
        i=0
        for ip in self.interface_ip_list:
            print(f"{i} - {ip}")
            i+=1

        self.get_client_ip_input()

        #Ask user for server ip, validate and set
        print("Please enter a server IP:")
        valid = False
        while valid == False:
            self.server_ip = input()
            valid = validate_ip(self.server_ip)
            if valid == False:
                print(f"Server IP Invalid, please re-enter:")

        #Add all values to the dict
        self.settings_dict["client_ip"] = self.client_ip
        self.settings_dict["server_ip"] = self.server_ip
        self.settings_dict["first_run"] = False

        #Write to settings file
        write_dict_to_file(self.settings_dict, self.settings_path)

    def get_client_ip_input(self):
        self.valid = False
        while self.valid == False:
            #Ask user to select an IP
            print("Please select an interface ip by inputting the number associated with it:")
            selection = input()
            try:
                selection_int = int(selection)
                #Set client IP based on selection
                if selection_int in range (0, self.interface_list_length):
                    self.client_ip = self.interface_ip_list[selection_int]
                    self.valid = True
                else:
                    print("IP address invalid, please select again:")
            except:
                print("IP address invalid, please select again:")

                
                    


    def start_app(self):
        #Create an instance of the GUI
        gui = Window()
        gui.on_execute()