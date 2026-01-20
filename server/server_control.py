from modules.osc import OSC_Server
from server.router import Router
from server.controller import Controller
from server.tcp_server import ThreadedTCPServer, ThreadedTCPRequestHandler
from database.database_connection import DB
from modules.common import *
import threading
import time
import logging
from server.gpio_server import GPIO_Server
from modules.exceptions import Unable_To_Start_Exception
from tkinter import StringVar

class Server_Control:
    """This is the Main OATIS Server Control Class. This class orchestrates the entire OATIS Server."""
    def __init__(self, status_var):
        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Server listen Socket - Defaults
        self.ip = "127.0.0.1"
        self.osc_port = 1337 #UDP and TCP
        self.tcp_port = 1339 #TCP File Transfers Only
        self.settings_path = "server/settings.json"

        #Variables to keep track of what is running
        self.controller_thread_list = []
        self.osc_server_running = False
        self.tcp_server_running  = False
        self.gpio_server_running = False

        #Create an instance of the GPIO_Server
        self.gpio_server = GPIO_Server()

        #Create an instance of the router, passing in the GPO Output Function
        self.router = Router(self.gpio_server.change_gpo_state)

        #Server Status GUI Var - Used to show status of server on GUI
        self.status_var : StringVar = status_var

    def get_ip_address(self) -> str:
        """Returns currently set IP address."""
        return self.ip

    def __map_osc_handlers(self):
        #System OSC Handlers
        self.osc_server.map_osc_handler('/messaging/send_message', self.router.handle_ticker_on_osc_message)
        self.osc_server.map_osc_handler('/messaging/stop_message', self.router.handle_ticker_off_osc_message)
        self.osc_server.map_osc_handler('/client/control/stacked_image', self.router.handle_stacked_image_change_message)

        #Handles user Configured OSC Input
        self.osc_server.set_default_handler(self.router.handle_custom_osc_input_message)

    def __unmap_osc_handlers(self):
        self.osc_server.unmap_osc_handler('/messaging/send_message', self.router.handle_ticker_on_osc_message)
        self.osc_server.unmap_osc_handler('/messaging/stop_message', self.router.handle_ticker_off_osc_message)
        self.osc_server.map_osc_handler('/client/control/stacked_image', self.router.handle_stacked_image_change_message)

    def __read_and_set_settings(self):
        """Reads the ip settings and sets these in memory."""
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
        self.logger.debug(f"Controller Server       Status:{self.gpio_server.get_controller_statuses()},  Listening on {self.gpio_server.get_controller_ports()}")
        self.logger.debug(f"Number of Active Threads:{threading.active_count()}")
        time.sleep(10)

    #--------------------------------Server Control-------------------------------------------------------------------------------
    def start_server(self) -> str:
        """Starts all server components."""
        if (self.osc_server_running == False) and (self.tcp_server_running == False) and (self.gpio_server_running == False):
            try:
                #Read stored ip settings and set them
                self.__read_and_set_settings()

                #Start each component - a Unable_To_Start_Exception is raised if it fails to start
                self.start_osc_server()
                self.start_tcp_server()
                self.start_gpio_server()
                
                status = "Running"
               
            except Unable_To_Start_Exception as e:
                #If a component fails to start, shutdown the server
                self.logger.error("One or more components failed to start, shutting server down...")
                self.logger.error(e)
                
                #Show the error in the server status window
                self.status_var.set(e)

                self.logger.debug(f"OSC Server Status: {self.osc_server_running}")
                self.logger.debug(f"TCP Server Status: {self.tcp_server_running}")
                self.logger.debug(f"GPIO Server Status: {self.gpio_server_running}")

                if self.osc_server_running == True:
                    self.stop_osc_server()
                    self.logger.debug("Stopped OSC Server")
                if self.tcp_server_running == True:
                    self.stop_tcp_server()
                    self.logger.debug("Stopped TCP Server")
                if self.gpio_server_running == True:
                    self.stop_gpio_server()
                    self.logger.debug("Stopped GPIO Server")

                self.logger.info("Server Shutdown Successfully.")
                status = "Stopped"

            return status
        
    def stop_server(self):
        """Stops all server components."""
        if (self.osc_server_running == True):
            self.stop_osc_server()
            self.logger.debug("Stopped OSC Server")

        if (self.tcp_server_running == True):
            self.stop_tcp_server()
            self.logger.debug("Stopped TCP Server")

        if (self.gpio_server_running == True):
            self.stop_gpio_server()
            self.logger.debug("Stopped GPIO Server")

        self.logger.info("Server Shutdown Successfully.")
    #--------------------------------OSC------------------------------------------------------------------------------------------
    def start_osc_server(self):
        """Starts the OSC Server"""
        try:
            #Create an instance of the OSC_Server
            self.osc_server = OSC_Server(self.ip, self.osc_port)

            #Map OSC addresses to handler callback functions in router
            self.__map_osc_handlers()

            #Start the UDP OSC_Server on a seperate thread
            self.udp_osc_server_thread :threading.Thread = threading.Thread(target=self.osc_server.start_udp_osc_server, daemon=True)
            self.udp_osc_server_thread.start()
            self.logger.debug(f"UDP OSC Server loop started in thread: {self.udp_osc_server_thread.name}")

            #Start the TCP OSC_Server on a seperate thread
            self.tcp_osc_server_thread :threading.Thread = threading.Thread(target=self.osc_server.start_tcp_osc_server, daemon=True)
            self.tcp_osc_server_thread.start()
            self.logger.debug(f"TCP OSC Server loop started in thread: {self.tcp_osc_server_thread.name}")

            self.osc_server_running = True

        except Exception as e:
            #If we run into any issues shutdown the OSC Server and raise an exception
            if self.osc_server.udp_server_running == True:
                self.osc_server.stop_udp_osc_server()
            elif self.osc_server.tcp_server_running == True:
                self.osc_server.start_tcp_osc_server()

            self.osc_server_running = False
            raise Unable_To_Start_Exception(e)

    def stop_osc_server(self):
        """Stops the OSC server."""
        if self.osc_server_running == True:
            self.__unmap_osc_handlers()
            self.osc_server.stop_udp_osc_server()
            self.osc_server.stop_tcp_osc_server()
            del self.osc_server
            self.osc_server_running = False
    #--------------------------------TCP------------------------------------------------------------------------------------------
    def start_tcp_server(self) -> bool:
        """Starts the TCP Server"""
        #Create an instance of the threaded TCP Server
        try:
            self.tcp_server = ThreadedTCPServer((self.ip, self.tcp_port), ThreadedTCPRequestHandler)

            #Start the TCP_Server on a seperate thread
            self.tcp_server_thread :threading.Thread = threading.Thread(target=self.tcp_server.serve_forever, daemon=True)
            self.tcp_server_thread.start()
            self.logger.debug(f"TCP Server loop running in thread: {self.tcp_server_thread.name}")
            self.tcp_server_running = True

        except Exception as e:
            #If we run into any issues shutdown the TCP Server and raise an exception
            self.logger.error(f"Unable to start TCP Server, reason:{e}")
            self.tcp_server_running = False
            raise Unable_To_Start_Exception(e)

    def stop_tcp_server(self):
        """Stops the TCP Server"""
        if self.tcp_server_running == True:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()
            self.tcp_server.socket.close()
            del self.tcp_server
            self.tcp_server_running = False
    #--------------------------------GPIO------------------------------------------------------------------------------------------
    def start_gpio_server(self):
        """Starts the TCP Server, returns status True if successful, False is not."""
        try:
            self.gpio_server.start_gpio_server()
            self.gpio_server_running = True

        except Unable_To_Start_Exception as e:
            #If we run into any issues shutdown the GPIO Server and raise an exception
            self.logger.error(f"Unable to start GPIO Server, reason:{e}")
            self.gpio_server_running = False
            raise Unable_To_Start_Exception(e)

    def stop_gpio_server(self):
        """Stops the GPIO Server"""
        self.gpio_server.stop_gpio_server()
        self.gpio_server_running = False
    #-----------------------------------------------------------------------------------------------------------------------------


