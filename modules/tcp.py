import logging
import socket
import struct
import json

class TCP_Client:
    def __init__(self):
        #Setup Logging
        self.logger = logging.getLogger(__name__)

    def tcp_send(self, ip, port, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            #Set timeout for response
            sock.settimeout(1)
            #Connect to Server
            self.logger.debug(f"Establishing connection to server at: {ip}:{port}")
            sock.connect((ip, port))
            self.logger.debug("Connection Established")

            #Send Data
            self.logger.debug("Sending data to server...")
            sock.sendall(bytes(message, 'ascii'))

            #Recieve the first 4 bytes of the message to read it's length
            self.logger.debug("Recieving message length preamble from server...")
            message_length_encoded = self.recvall(sock, 4)
            #Decode the length
            self.logger.debug("Decoding message length preamble...")
            message_length_decoded = struct.unpack('>I', message_length_encoded)[0]
            self.logger.debug(f"Message of length:{message_length_decoded} to be recieved.")
            #Recieve all data now we know the length of the message - stored as a byte array
            self.logger.debug("Recieving data from server...")
            message : bytearray = self.recvall(sock, message_length_decoded)
            #Decode the byte-array
            self.logger.debug("Decoding message...")
            decoded_message = bytes(message)
            
            return decoded_message

    def recvall(self, sock, n):
        # Helper function to recv n bytes or return None if EOF is hit
        data : bytearray = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def decode_data(self, recieved_data : bytes):
        return recieved_data.decode("utf-8")
    
    #Builds a JSON message using a set format- data and args are optional
    def build_tcp_message(self, command:str, arguments:dict=None, data:list=None) -> str:
        json_dictionary = {}
        json_dictionary["command"] = command
        json_dictionary["arguments"] = arguments
        json_dictionary["data"] = data
        
        #Convert the Dictionary to JSON
        json_message = json.dumps(json_dictionary)

        return json_message
    
#Builds a JSON response message using a set format- data and args are optional
def build_tcp_response_message(command:str, arguments:dict=None, data:list=None) -> str:
    json_dictionary = {}
    json_dictionary["command"] = command
    json_dictionary["arguments"] = arguments
    json_dictionary["data"] = data
    
    #Convert the Dictionary to JSON
    json_message = json.dumps(json_dictionary)

    return json_message

