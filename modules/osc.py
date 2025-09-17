from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.osc_tcp_server import ThreadingOSCTCPServer
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.tcp_client import SimpleTCPClient
import logging


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

    def start_udp_osc_server(self):
        try:
            #Start the OSC server in threading mode, handling each incoming message in a seperate thread
            self.udp_server = ThreadingOSCUDPServer((self.ip, self.port), self.dispatcher)
            self.udp_server_running = True
            #Continue running the server forever
            self.udp_server.serve_forever()  # Blocks forever
            
        except Exception as e:
            self.logger.error(f"Unable to start UDP OSC Server, reason:{e}")
            self.udp_server_running = False
    
    def stop_udp_osc_server(self):
        if self.udp_server_running == True:
            self.udp_server.shutdown()
            self.udp_server.socket.close() # Release the listening socket
            self.udp_server_running = False
        else:
            self.logger.warning("Unable to stop the UDP OSC server, it is not running!")

    def start_tcp_osc_server(self):
        try:
            #Start the OSC server in threading mode, handling each incoming message in a seperate thread
            self.tcp_server = ThreadingOSCTCPServer((self.ip, self.port), self.dispatcher)
            self.tcp_server_running = True
            #Continue running the server forever
            self.tcp_server.serve_forever()  # Blocks forever
            
        except Exception as e:
            self.logger.error(f"Unable to start TCP OSC Server, reason:{e}")
            self.tcp_server_running = False
    
    def stop_tcp_osc_server(self):
        if self.tcp_server_running == True:
            self.tcp_server.shutdown()
            self.tcp_server.socket.close() # Release the listening socket
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

class OSC_Client:

    def __init__(self, ip, port, protocol):
        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #IP / Port of OATIS Server - Default parameters for testing
        self.remote_host_ip_address = ip
        self.remote_host_port = port

        if protocol == "tcp":
            self.client: SimpleTCPClient = SimpleTCPClient(address = self.remote_host_ip_address, port = self.remote_host_port)  # Create client
            self.logger.debug("TCP Client Selected")
        else:
            self.client: SimpleUDPClient = SimpleUDPClient(address = self.remote_host_ip_address, port = self.remote_host_port)  # Create client
            self.logger.debug("UDP Client Selected")

    #Sends an OSC message to an OSC server
    def send_osc_message(self, address, data):
        try:
            #Send the message using UDP
            self.logger.debug(f"Sending data: {address}, {data} to remote host at IP:{self.remote_host_ip_address}, Port:{self.remote_host_port}")
            self.client.send_message(address, data)
            self.logger.debug("Message sent successfully")
        except Exception as e:
            self.logger.error(f"Unable to send message to host, reason:{e}")