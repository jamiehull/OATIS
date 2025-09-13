import socket
import socketserver
from server.router import *
import struct

#Based on the example from: https://docs.python.org/3/library/socketserver.html

class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):

    def handle(self):
        recieved_data = str(self.request.recv(1024), 'ascii')

        #Get the address and remote port of the client
        client_ip, client_port = self.client_address

        #Pass the message to the tcp handler in router
        router = Router()
        response_bytes :bytes = router.handle_tcp_message(recieved_data)

        #Generate a response to send to the client, adding a length prefix
        encoded_response = struct.pack('>I', len(response_bytes)) + response_bytes
        self.request.sendall(encoded_response)
        print(f"Handled Request from {client_ip} at remote port: {client_port}")

class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass

            
