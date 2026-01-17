from client.pygame_window import *
from modules.common import *
import logging
from time import sleep
from client.settings_window import Settings

class Launcher:
    """Provides an interface to set IP settings on first run or if the settings file is missing. Launches app as normal if settings file is present and not first run."""
    def __init__(self):
    
        #Setup Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        self.client_ip = ""
        self.server_ip = ""
        self.settings_dict = {}
        self.settings_path = "client/data/settings.json"


        settings_dict : dict = open_json_file(self.settings_path)
        if settings_dict == False:
            logger.warning("No settings file, entering setup script...")
            self.ip_config()
            self.start_app()

        #If its the first run, setup the ip settings
        elif settings_dict["first_run"] == True:
            logger.info("First run, entering setup script...")
            self.ip_config()
            self.start_app()
                
        #If a valid settings file exists and it's not first run, boot as normal
        elif settings_dict["first_run"] == False:
            logger.info("Starting app normally...")
            self.start_app()

        else:
            self.ip_config()
            self.start_app()

    def ip_config(self):
        """Creates the settings file."""
        settings_window = Settings(self.settings_path)

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


       