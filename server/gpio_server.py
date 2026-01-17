from server.controller import Controller
from database.database_connection import DB
from threading import Thread
from threading import Lock
import logging
from server.router import Router
import time
from modules.exceptions import Unable_To_Start_Exception
 
class GPIO_Server:
    """GPIO Server for handling events from multiple arduinos."""
    def __init__(self):

        #Controller Table indexes
        self.CONTROLLER_ID = 0
        self.SERIAL_PORT = 4

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create a database connection object and router
        self.db = DB()
        self.router = Router(self.change_gpo_state)

        #DB lock for keeping access to the router module thread-safe
        self.db_lock = Lock()
    
    def start_gpio_server(self):
        """Starts the GPIO server."""

        #Get all configured controller configs
        config = self.db.get_current_table_data("controllers")
        
        self.controller_thread_list = []
        self.controller_server_dict = {}
        self.controller_port_list = []
        controller_status_list = []

        #Setup each controller

        for controller_config in config:
            controller_id = controller_config[self.CONTROLLER_ID]
            if controller_id != 0:
                controller_port = controller_config[self.SERIAL_PORT]
                
                #Get the pin configuratioon for the controller
                pin_config_list = self.db.get_current_row_data("pin_modes", "controller_id", controller_id)
                
                #Create an instance of controller passing in the controlers config from the database and a handler for dealing with input changes
                controller_server :Controller  = Controller(self.handle_gpi, controller_id, controller_port, pin_config_list) 

                #Setup the serial connection and return the status
                controller_status = controller_server.setup_controller_connection()
                controller_status_list.append(controller_status)

                #If connection successfull start the loop in a seperate blocking thread
                if controller_status == True:
                    self.controller_server_dict[controller_id] = controller_server
                    self.controller_port_list.append(controller_port)

        if all(controller_status_list) == True:
            self.logger.debug("Starting GPIO Threads...")
            self.__start_controller_server_threads()

        else:
            self.stop_gpio_server()
            raise Unable_To_Start_Exception("Serial Port not found.")
            
    def stop_gpio_server(self):
        """Stops the GPIO Server."""
        for controller_id in self.controller_server_dict:
            controller_server : Controller = self.controller_server_dict.get(controller_id)
            controller_server.stop_loop()

        self.logger.debug("Clearing Controller Instances")
        self.controller_server_dict.clear()

    def __start_controller_server_threads(self):
        """Starts a thread for each microcontroller."""
        for controller_id in self.controller_server_dict:
            controller_server : Controller = self.controller_server_dict.get(controller_id)
            self.__start_controller_server_thread(controller_server.start_loop)

    def __start_controller_server_thread(self, target_function):
        """Starts an single thread for handling a single microcontroller."""
        #Start the GPI controller in a seperate thread
        controller_thread : Thread = Thread(target=target_function, daemon=True)
        controller_thread.start()
        self.logger.debug(f"Controller Server loop running in thread: {controller_thread.name}")
        self.controller_thread_list.append(controller_thread)

    def get_controller_statuses(self):
        """Returns the status of each controller."""
        controller_status_list = []
        for controller_id in self.controller_server_dict:
            controller : Controller = self.controller_server_dict.get(controller_id)
            status = controller.get_controller_status()
            controller_status_list.append(f"Controller:{controller_id} Status:{status}")
        
        return controller_status_list
    
    def get_controller_ports(self):
        """Returns the serial ports in use by each controller."""
        return self.controller_port_list

    def handle_gpi(self, *args):
        """Forwards GPI event data to the router module utelising a lock for keeping access thread-safe."""
        with self.db_lock:
            self.router.handle_gpi(*args)

    def change_gpo_state(self, controller_id:int, pin_address:int, state:bool):
        """Sets a controllers GPO pin high or low."""
        controller : Controller = self.controller_server_dict.get(controller_id)
        controller.set_output_pin_state(pin_address, state)
        