from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.osc_tcp_server import ThreadingOSCTCPServer
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.tcp_client import SimpleTCPClient
import logging
import socket


class OSC_Server:
    def __init__ (self, server_ip, server_port):

        #Server IP Config
        self.ip = server_ip
        self.port = server_port

        #Status of server - used when restarting
        self.udp_server_running = False
        self.tcp_server_running = False

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Dispatcher is usded map incoming OSC messages to callbacks
        self.logger.debug("Setting Up Dispatcher")
        self.dispatcher = Dispatcher()

    def get_udp_server_status(self) -> bool:
        return self.udp_server_running
    
    def get_tcp_server_status(self) -> bool:
        return self.tcp_server_running

    def start_udp_osc_server(self):
        try:
            #Start the OSC server in threading mode, handling each incoming message in a seperate thread
            self.udp_server = ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
            self.udp_server_running = True
            self.logger.debug("UDP OSC Server starting...")
            #Continue running the server forever
            self.udp_server.serve_forever()  # Blocks forever
            
        except Exception as e:
            self.logger.error(f"Unable to start UDP OSC Server, reason:{e}")
            self.udp_server_running = False
    
    def stop_udp_osc_server(self):
        if self.udp_server_running == True:
            self.udp_server.shutdown()
            self.udp_server.server_close()
            self.udp_server.socket.close() # Release the listening socket
            del self.udp_server
            self.udp_server_running = False
        else:
            self.logger.warning("Unable to stop the UDP OSC server, it is not running!")

    def start_tcp_osc_server(self):
        try:
            #Start the OSC server in threading mode, handling each incoming message in a seperate thread
            self.tcp_server = ThreadingOSCTCPServer((self.ip, self.port), self.dispatcher)
            self.tcp_server_running = True
            self.logger.debug("TCP OSC Server starting...")
            #Continue running the server forever
            self.tcp_server.serve_forever()  # Blocks forever
            
        except Exception as e:
            self.logger.error(f"Unable to start TCP OSC Server, reason:{e}")
            self.tcp_server_running = False
    
    def stop_tcp_osc_server(self):
        if self.tcp_server_running == True:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()
            self.tcp_server.socket.close() # Release the listening socket
            del self.tcp_server
            self.tcp_server_running = False
        else:
            self.logger.warning("Unable to stop the TCP OSC server, it is not running!")

    def change_server_ip(self, ip_address:str):
        """Server must be restarted for this change to take effect."""
        self.ip = ip_address

    def map_osc_handler(self, address:str, callback):
        self.dispatcher.map(address, callback)

    def unmap_osc_handler(self, address:str, callback):
        self.dispatcher.unmap(address, callback)

    def set_default_handler(self, callback):
        """Sets default OSC handler."""
        self.dispatcher.set_default_handler(callback)

class OSC_Client:

    def __init__(self, ip, port, protocol):
        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Status to indicate whether an osc client was created successfully
        self.status = "not_running"

        #IP / Port of RDS Server - Default parameters for testing
        self.remote_host_ip_address = ip
        self.remote_host_port = port

        self.logger.debug(f"Protocol is: {protocol}")
        try:
            if protocol == "TCP":
                self.client: SimpleTCPClient = SimpleTCPClient(address = self.remote_host_ip_address, port = self.remote_host_port)  # Create client
                self.logger.debug("TCP Client Selected")
                self.status = "running"
            else:
                self.client: SimpleUDPClient = SimpleUDPClient(address = self.remote_host_ip_address, port = self.remote_host_port)  # Create client
                self.logger.debug("UDP Client Selected")
                self.status = "running"

        except ConnectionRefusedError:
            self.logger.error(f"Unable to connect to client device at {self.remote_host_ip_address}:{self.remote_host_port}")

        except Exception as e:
            self.logger.error(f"Unable to create a {protocol} OSC client, {e}")

    #Sends an OSC message to an OSC server
    def send_osc_message(self, address, data):
        try:
            if (self.status != "not_running"):
                if (address != ""):
                    #Send the message using UDP
                    self.logger.debug(f"Sending data: {address}, {data} to remote host at IP:{self.remote_host_ip_address}, Port:{self.remote_host_port}")
                    self.client.send_message(address, data)
                    self.logger.debug("Message sent successfully")
                else:
                    self.logger.warning("Not sending OSC message, command is empty!")
            else:
                self.logger.error("Cannot send OSC message, OSC client could not connect to remote device.")
        except Exception as e:
            self.logger.error(f"Unable to send message to host, reason:{e}")