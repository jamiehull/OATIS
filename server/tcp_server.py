import socketserver
from server.router import Router
import struct
import logging
import json
from modules.tcp import build_tcp_response_message

#Based on the example from: https://docs.python.org/3/library/socketserver.html

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.logger = logging.getLogger(__name__)
        
        #Get the address and remote port of the client
        client_ip, client_port = self.client_address

        self.logger.info(f"STARTED Handling Request from {client_ip} at remote port: {client_port}")

        #Convert recioeved data to ascii string
        recieved_data = str(self.request.recv(1024), 'utf-8')
        
        #Convert the recieved JSON to a dict
        recieved_data_dict = json.loads(recieved_data)

        #Extract the elements from the message
        command = recieved_data_dict["command"]
        self.logger.debug(f"Command: {command}")

        arguments = recieved_data_dict["arguments"]
        self.logger.debug(f"Arguments: {arguments}")

        data = recieved_data_dict["data"]
        self.logger.debug(f"data: {data}")

        #Pass the message to the tcp handler in router
        self.router = Router()
        output_command, output_arguments, output_data = self.router.handle_tcp_message(command, arguments, data)

        #If we want to respond to a client with a binary file instead of JSON change the response appropriatley
        if output_arguments["binary_response"] == True:
            response_bytes = output_data
        else:
            response = build_tcp_response_message(output_command, output_arguments, output_data)
            #Encode the response in bytes
            response_bytes = bytes(response, "utf-8")
       
        #Generate a response to send to the client, adding a length prefix
        encoded_response = struct.pack('>I', len(response_bytes)) + response_bytes
        self.request.sendall(encoded_response)
        self.logger.info(f"FINISHED Handling Request from {client_ip} at remote port: {client_port}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass