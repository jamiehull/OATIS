from modules.osc import OSC_Server
from server.router import Router
from server.controller import Controller
from server.tcp_server import *
from database.database_connection import DB
from modules.common import *
import threading
import time
import logging
from sys import exit

class Main_Server:
    def __init__(self):
        #Setup Logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        #Server listen Socket - Defaults
        self.ip = "127.0.0.1"
        self.osc_port = 1337 #UDP and TCP Triggering
        self.tcp_port = 1339 #TCP File Transfers Only
        self.settings_path = "server/settings.json"
        self.serial_port_index = 4

        #Read stored ip settings and set them
        self.__read_and_set_settings()

        #Thread List
        self.controller_thread_list = []

        #Create an instance of the database connection and router
        self.db = DB() 
        self.router = Router()

        #Verify the database
        db_status = self.db.verify_database_setup()
        if db_status != True:
            self.logger.error("Database invalid or missing, please rebuild the database in config tool and re-launch the server.")
            quit()

        #Create an instance of the OSC_Server
        self.osc_server = OSC_Server(self.ip, self.osc_port)

        #Map OSC addresses to handler callback functions in router
        self.__map_osc_handlers()

        #Start the OSC_Server on a seperate thread
        self.__start_osc_server_threads()
        if (self.osc_server.tcp_server_running != True) and (self.osc_server.udp_server_running != True):
            self.logger.error("Unable to start the OSC server, Shutting Down...")
            exit(0)

        #Create an instance of the threaded TCP Server
        try:
            self.tcp_server = ThreadedTCPServer((self.ip, self.tcp_port), ThreadedTCPRequestHandler)
        except Exception as e:
            self.logger.error(f"Unable to start TCP Server, reason:{e}")
            self.logger.error("Shutting down...")
            exit(0)

        #Start the TCP_Server on a seperate thread
        self.__start_tcp_server_thread()

        #Setup Configured GPIO Controllers
        #Query the database to return configured controllers
        config = self.db.get_current_table_data("controllers")
        self.controller_server_list = []
        self.controller_port_list = []
        for controller_config in config:
            controller_port = controller_config[self.serial_port_index] 

            #Create an instance of controller passing in the controlers config from the database and a handler for dealing with input changes
            controller_server :Controller  = Controller(controller_config, self.router.handle_gpi) 

            controller_status = controller_server.setup_controller_connection()

            if controller_status == True:
                self.__start_controller_server_thread(controller_server.start_loop)
                self.controller_server_list.append(controller_server)
                self.controller_port_list.append(controller_port)

        #Shows server heartbeat message - keeps main thread alive
        while True:
            self.__show_server_status()

    def __map_osc_handlers(self):
        self.osc_server.map_osc_handler('/*/signal-lights/*', self.router.handle_signal_light_osc_message)
        self.osc_server.map_osc_handler('/messaging/send_to_multiple', self.router.handle_ticker_on_osc_message)
        self.osc_server.map_osc_handler('/messaging/stop_message', self.router.handle_ticker_off_osc_message)

    def __start_tcp_server_thread(self):
        #Start the TCP_Server on a seperate thread
        self.tcp_server_thread :threading.Thread = threading.Thread(target=self.tcp_server.serve_forever, daemon=True)
        self.tcp_server_thread.start()
        self.logger.debug(f"TCP Server loop running in thread: {self.tcp_server_thread.name}")

    def __start_osc_server_threads(self):
        #Start the UDP OSC_Server on a seperate thread
        self.udp_osc_server_thread :threading.Thread = threading.Thread(target=self.osc_server.start_udp_osc_server, daemon=True)
        self.udp_osc_server_thread.start()
        self.logger.debug(f"UDP OSC Server loop running in thread: {self.udp_osc_server_thread.name}")
        #Start the TCP OSC_Server on a seperate thread
        self.tcp_osc_server_thread :threading.Thread = threading.Thread(target=self.osc_server.start_tcp_osc_server, daemon=True)
        self.tcp_osc_server_thread.start()
        self.logger.debug(f"TCP OSC Server loop running in thread: {self.tcp_osc_server_thread.name}")

    def __start_controller_server_thread(self, target_function):
        #Start the GPI controller in a seperate thread
        controller_thread :threading.Thread = threading.Thread(target=target_function, daemon=True)
        controller_thread.start()
        self.logger.debug(f"Controller Server loop running in thread: {controller_thread.name}")
        self.controller_thread_list.append(controller_thread)

    def __read_and_set_settings(self):
        #Read IP Settings file
        settings_dict = open_json_file(self.settings_path)

        #Only set ip's if settings file exists 
        if settings_dict != False:
            self.ip = settings_dict["server_ip"]

    def __show_server_status(self):
        controller_status_list = []
        for thread in self.controller_thread_list:
            status = thread.is_alive()
            controller_status_list.append(status)

        self.logger.debug("Server Heartbeat...")
        self.logger.debug(f"TCP Server              Status:{self.tcp_server_thread.is_alive()},  Listening on {self.ip}:{self.tcp_port}")
        self.logger.debug(f"UDP OSC Server          Status:{self.udp_osc_server_thread.is_alive()},  Listening on {self.ip}:{self.osc_port} UDP")
        self.logger.debug(f"TCP OSC Server          Status:{self.tcp_osc_server_thread.is_alive()},  Listening on {self.ip}:{self.osc_port} TCP")
        self.logger.debug(f"Controller Server       Status:{controller_status_list},  Listening on {self.controller_port_list}")
        self.logger.debug(f"Number of Active Threads:{threading.active_count()}")
        time.sleep(10)

    def __stop_server(self):
        if self.controller_thread.is_alive() == True:
            self.controller_server.stop_loop()
            self.logger.info("Controller Server Shutdown")
        if self.udp_osc_server_thread.is_alive() == True:
            self.osc_server.stop_udp_osc_server()
            self.logger.info("UDP OSC Server Shutdown")
        if self.tcp_osc_server_thread.is_alive() == True:
            self.osc_server.stop_tcp_osc_server()
            self.logger.info("TCP OSC Server Shutdown")
        if self.tcp_server_thread.is_alive() == True:
            self.tcp_server.shutdown()
            self.logger.info("TCP Server Shutdown")

    def __start_server(self):
        if self.controller_thread.is_alive() == False:
            self.__start_controller_server_thread()
        if (self.udp_osc_server_thread.is_alive() == False) and (self.tcp_osc_server_thread.is_alive() == False):
            self.__start_osc_server_threads()
        if self.tcp_server_thread.is_alive() == False:
            self.__start_tcp_server_thread()

server = Main_Server()
