from database.database_connection import *
from modules.tcp import build_tcp_response_message
from modules.osc import OSC_Client
import logging
import json
import threading
import datetime

class Router:
    #Routes GPI signals to the assigned devices
    def __init__(self):
        #Store a reference to the database, explicitly stating the variable type - makes calling function easier
        self.db: DB = DB()

        #Setup Logging
        self.logger = logging.getLogger(__name__)

    #--------------------------------EXTERNAL-FACING-OSC-HANDLERS---------------------------------------------------

    def handle_signal_light_osc_message(self, address, *args):
        self.logger.debug(f"SIGNAL LIGHT OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            #Store reference to the OSC_address and data arguments
            osc_address = address
            data = args

            #Connect to the database
            self.db.connect()

            #Query the database to find the trigger_group associated with the OSC Address
            trigger_group_id_list = self.db.get_1column_data("trigger_group_id", "trigger_mappings", "gpi", osc_address)

            #If a valid trigger group has been found, proceed
            if trigger_group_id_list != []:
                trigger_group_id = trigger_group_id_list[0]
                self.logger.debug(f"OSC Address Targeting Trigger Group:{trigger_group_id}")

                #Query the database for devices associated with this trigger_group_id - this may return a blank list if no devices assigned
                self.logger.debug(f"Getting list of devices associated with this trigger")
                device_list = self.db.get_1column_data("device_ip", "devices", "trigger_group_id", trigger_group_id)
                self.logger.debug(f"Devices associated with trigger group ID:{trigger_group_id}, {device_list}")

                #Query the database to get the shortened OSC address to send to the client devices
                client_osc = self.db.get_1column_data("trigger", "trigger_mappings", "gpi", osc_address)[0]
                self.logger.debug(f"OSC Address to send to Client:{client_osc}")

                #Forward OSC message to clients
                self.forward_osc_message(device_list, client_osc, data)

            else:
                self.logger.debug(f"Invalid OSC Address recieved: {osc_address}")
        
        except Exception as e:
            self.logger.error(f"Unable to handle Signal Light OSC message, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()

    def handle_ticker_on_osc_message(self, address, *args):
        """Expects address: /messaging/send_to_multiple
        Args: ("ticker_text", "bg_colour_hex", [["message_group_id","message_group_name"],["message_group_id","message_group_name"])"""

        self.logger.debug(f"TICKER OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            message_text = args[0]
            bg_colour = args[1]
            message_group_list = args[2]
            
            command = address
            arguments = {
                "message" : message_text,
                "bg_colour" : bg_colour}
            data = message_group_list

            self.db.connect()
            self.handle_ticker_on_message(command, arguments, data)

        except Exception as e:
            self.logger.error(f"Unable to handle ticker OSC message, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()

    def handle_ticker_off_osc_message(self, address, *args):
        """Expects address: /messaging/stop_message
        Args: ([["message_group_id","message_group_name"],["message_group_id","message_group_name"])"""

        self.logger.debug(f"TICKER OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            message_group_list = args[0]
            
            command = address
            arguments = None
            data = message_group_list

            self.db.connect()
            self.handle_ticker_off_message(command, arguments, data)

        except Exception as e:
            self.logger.error(f"Unable to handle ticker OSC message, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()
        
    
    #--------------------------------INTERNAL-APP-TCP-HANDLERS---------------------------------------------------

    #Handles incoming tcp requests and returns a response - must return a bytes object
    #All commands below are for network comms between OATIS applications
    def handle_tcp_message(self, message:str) -> bytes:
        try:
            #Convert the recieved JSON to a dict
            self.logger.debug(f"Incoming Message: {message}")
            message_dict = json.loads(message)

            #Extract the elements from the message
            command = message_dict["command"]
            self.logger.debug(f"Command: {command}")
            arguments = message_dict["arguments"]
            self.logger.debug(f"Arguments: {arguments}")
            data = message_dict["data"]
            self.logger.debug(f"data: {data}")

            message_list = []

            #Connect to the database
            self.db.connect()

            #Forwards a request to raise a specified frame to a client
            if command == "/control/client/raise_frame":
                self.logger.debug("#############TCP RAISE FRAME HANDLER INVOKED#############")

                device_id = arguments["device_id"]
                frame = arguments["frame"] #The name of the frame to be raised

                #Lookup the device IP using the recieved device ID
                device_ip = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)[0]
                self.logger.debug(f"IP address of client to raise frame: {device_ip}")

                self.forward_osc_message([device_ip], "/client/control/frames", frame)

                response = build_tcp_response_message("/control/client/raise_frame", {"status" : "OK"}, None)

            elif command == "/control/client/reload_display_template":
                self.logger.debug("#############TCP CONTROL CLIENT HANDLER INVOKED#############")

                device_id = arguments["device_id"]
                #Lookup the device IP using the recieved device ID
                device_ip = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)[0]
                self.logger.debug(f"IP address of client to reload display: {device_ip}")

                self.forward_osc_message([device_ip], "/client/control/reload_display_template", None)

                response = build_tcp_response_message("/control/client/reload_display_template", {"status" : "OK"}, None)
                
            #If an image has been requested
            #Expects ["image", {image_id}]
            elif command == "/assets/images/get":
                self.logger.debug("#############TCP IMAGE HANDLER INVOKED#############")
                image_id = arguments["image_id"]
                #Query the database to return the image
                blob_image : bytes = self.db.get_1column_data("image_file", "images", "image_id", image_id)[0]
                response = blob_image

                self.logger.debug(f"TCP Handler returning response:{response}")
                return response

            #If a display template has been requested
            #Expects ["display_template", {client_timestamp}, {client_ip}]
            elif command == "/config/display_template/get":
                self.logger.debug("#############TCP DISPLAY TEMPLATE HANDLER INVOKED#############")

                #Variable used to indicate whether the display template from the client matches the one on the server
                match_status = False
                #Blank variable used to return the display template if needed to the client
                data = None
                
                client_timestamp = arguments["timestamp"]
                client_ip = arguments["client_ip"]

                #Look up the device ID
                display_template_id = self.db.get_1column_data("display_template_id", "devices", "device_ip", client_ip)[0]
                display_template = self.db.get_current_row_data("display_templates", "display_template_id", display_template_id)[0]

                #Open the display template and compare the timestamp
                database_timstamp = display_template[24]
                #If the timestamps match, do not send the client the display template
                if database_timstamp == client_timestamp:
                    match_status = True
                #If the timestamps do not match, send a new display template to the client
                else:
                    match_status = False
                    data = display_template
        

                arguments = {
                    "display_template_current" : match_status
                }

                response = build_tcp_response_message("/config/display_template/get", arguments, data)

            #Returns the config for a specified device
            elif command == "/config/device/get":
                self.logger.debug("#############TCP CONFIG HANDLER INVOKED#############")

                #Connect to the database
                self.db.connect()
                device_ip = arguments["client_ip"]

                #Look up the device ID using the device IP address
                device_config = self.db.get_current_row_data("devices", "device_ip", device_ip)[0]

                #Device config Indicies
                messaging_group_id = device_config[4]
                trigger_group_id = device_config[5]
                display_template_id = device_config[6]

                #Get the message group associated with the device
                message_group_name = self.db.get_1column_data("messaging_group_name", "messaging_groups", "messaging_group_id", messaging_group_id)[0]
                #Get the trigger group associated with the device
                trigger_group_name = self.db.get_1column_data("trigger_group_name", "trigger_groups", "trigger_group_id", trigger_group_id)[0]
                #Get the display template associated with the device
                display_template_name = self.db.get_1column_data("display_template_name", "display_templates", "display_template_id", display_template_id)[0]

                #Build the response
                arguments = {
                    "device_name" : device_config[1],
                    "device_ip" : device_ip,
                    "device_location" : device_config[3],
                    "message_group" : message_group_name,
                    "trigger_group" : trigger_group_name,
                    "display_template" : display_template_name
                }
                
                response = build_tcp_response_message("/config/device/get", arguments, None)

            #If a heartbeat has been recieved
            elif command == "heartbeat":
                self.logger.debug("#############CLIENT HEARTBEAT HANDLER INVOKED#############")
                
                #Generate a timestamp
                timestamp = str(datetime.datetime.now())
                arguments = {
                    "status" : "OK",
                    "timestamp" : timestamp
                }
                data = None

                response = build_tcp_response_message("heartbeat", arguments, data)

            #Returns a list of all message_groups
            elif command == "/config/message_groups/get":
                self.logger.debug("#############MESSAGE CONSOLE GET MESSAGE GROUPS HANDLER INVOKED#############")

                #Query the database for a list of message groups
                message_group_list :list = self.db.get_2column_data("messaging_group_id", "messaging_group_name", "messaging_groups")
                #self.db.get_current_table_data("messaging_groups")

                #Convert returned list to json
                json_data = json.dumps(message_group_list)

                #Forward OSC message to message console
                response = json_data

            #Returns a list of all message_groups in use with devices associated to them
            elif command == "/config/message_groups/get_used":
                self.logger.debug("#############MESSAGE CONSOLE GET USED MESSAGE GROUPS HANDLER INVOKED#############")

                #Query the database for a list of message groups
                message_group_list :list = self.db.get_2column_data("messaging_group_id", "messaging_group_name", "messaging_groups")
                
                #Blank list for storing in use message groups
                message_group_in_use_list :list = []
                for message_group in message_group_list:

                    message_group_id = message_group[0]
                    message_group_name = message_group[1]

                    #Query the database to get a list of devices that are associated to the message group
                    device_list = self.db.get_1column_data("device_ip", "devices", "messaging_group_id", message_group_id)
                    if device_list != []:
                        self.logger.debug(f"Message Group {message_group_name} in use.")
                        message_group_in_use_list.append(message_group)
                    else:
                        self.logger.debug(f"Message Group {message_group_name} is not currently in use.")

                #Build the response message
                #command - this is a variable stored at the start of this function
                arguments = {
                    "status" : "OK",
                    "message_groups" : message_group_in_use_list
                }
                data = None
                response = build_tcp_response_message(command, arguments, data)

            elif command == "/config/devices/get":
                self.logger.debug("#############MESSAGE CONSOLE GET DEVICES HANDLER INVOKED#############")

                #Query the database for a list of message groups
                device_list :list = self.db.get_2column_data("device_id", "device_name", "devices")

                #Convert returned list to json
                json_data = json.dumps(device_list)

                response = json_data

            #Expects ["/messaging/send_to_multiple", [["msg_grp_id","msg_grp_name"]...]]
            elif command == "/messaging/send_to_multiple":
                response = self.handle_ticker_on_message(command, arguments, data)
                
            elif command == "/messaging/stop_message":
                response = self.handle_ticker_off_message(command, arguments, data)

            elif command == "/messaging/get_active_groups":
                self.logger.debug("#############MESSAGE CONSOLE GET ACTIVE GROUPS HANDLER INVOKED#############")

                #Query the database for a list of active message_groups
                active_messages = self.db.get_current_table_data("active_messages")
                active_message_groups = []
                active_message_ids = []
                for mapping in active_messages:

                    message_id = mapping[0]
                    active_message_ids.append(message_id)

                    message_group_id = mapping[1]
                    message_group_name = self.db.get_1column_data("messaging_group_name", "messaging_groups", "messaging_group_id", message_group_id)[0]
                    active_message_groups.append([message_group_id, message_group_name])

                #Build the response message
                #command - this is a variable stored at the start of this function
                arguments = {
                    "status" : "OK",
                    "active_message_groups" : active_message_groups
                }
                data = None
                response = build_tcp_response_message(command, arguments, data)


            else:
                self.logger.error(f"Error handling tcp request, no matching handlers, the request is invalid.")
                response = "False"


        except IndexError as e:
                    self.logger.error(f"Error handling display template request: The client is not configured on the server, or the clients IP address may be incorrect.")
                    response = "False"
                
        except Exception as e:
            self.logger.error(f"Error handling tcp request: {e}")
            response = "False"

        finally:
            #Close connection to database
            self.db.close_connection()

        self.logger.debug(f"TCP Handler returning response:{response}")
        return bytes(response, "utf-8")
    
    def handle_ticker_on_message(self, command, arguments, data):
            """Must have a database connection before utelising this function!"""
            self.logger.debug("#############MESSAGE CONSOLE SEND TO MULTIPLE HANDLER INVOKED#############")

            #Extract the info from the message - state turns the ticker on and off
            message_text = arguments["message"]
            bg_colour = arguments["bg_colour"]
            message_group_list = data
            timestamp = datetime.datetime.now()

            #Add a message entry in the messages table
            self.logger.debug(f"Adding message entry for message: {message_text}, with timestamp: {timestamp}")
            self.db.add_message(message_text, timestamp)
            self.logger.debug("Added new message database entry.")

            #Get the id of the message - used later
            self.logger.debug("Getting id of message...")
            message_id = self.db.get_1column_data("message_id", "messages", "message_timestamp", timestamp)[0]
            self.logger.debug(f"ID of message: {message_id}")
            
            #Variables used for error tracking
            group_success_list = []
            group_fail_list = []
            status = "OK"

            #Iterate through the list of message groups in the data field and send the message to their associated devices
            for message_group in message_group_list:

                message_group_id = message_group[0]
                message_group_name = message_group[1]

                #First Check if the message group is active, if it is don't proceed
                active_group = self.db.get_1column_data("message_group_id", "active_messages", "message_group_id", message_group_id)

                #If the message group is not already active
                if active_group ==[]:
                    #Get the osc address for the message group
                    osc_address = self.db.get_1column_data("osc_address", "messaging_groups", "messaging_group_id", message_group_id)[0]
                    self.logger.debug(f"OSC ADDRESS: {osc_address}")

                    #Query the database to get a list of devices that are associated to the message group
                    device_list = self.db.get_1column_data("device_ip", "devices", "messaging_group_id", message_group_id)
                    self.logger.debug(f"Devices associated with message group ID:{message_group_id}, {device_list}")

                    #Forward OSC message to clients in the message group
                    self.logger.debug(f"Sending message to client")
                    send_status = self.forward_osc_message(device_list, osc_address, [True, message_text, bg_colour])
                    self.logger.debug(f"Send Status for message group {message_group_name}: {send_status}")

                    if send_status == True:
                        group_success_list.append(message_group)
                        #Create an active message mapping - only if a message was forwarded to a message group
                        self.logger.debug(f"Adding active message mapping for message_id: {message_id} and message_group_id: {message_group_id}")
                        self.db.add_active_message(message_id, message_group_id)
                    else:
                        group_fail_list.append(message_group)
                        status = "ERRORS"

                #If the message group is already active 
                else:
                    self.logger.debug(f"Message Group: {message_group_name} is already active, cannot send a new message until the current message has been stopped.")
                    group_fail_list.append(message_group)
                    status = "ERRORS"

            #Check that a successful message was sent, otherwise remove the message database entry
            if group_success_list == []:
                self.logger.debug(f"No messages sent, deleting message database entry for Message ID: {message_id}")
                self.db.delete_row("messages", "message_id", message_id)       

            #Query the database for a list of active message_groups
            active_messages = self.db.get_current_table_data("active_messages")
            active_message_groups = []
            for mapping in active_messages:
                message_group_id = mapping[1]
                message_group_name = self.db.get_1column_data("messaging_group_name", "messaging_groups", "messaging_group_id", message_group_id)[0]
                active_message_groups.append([message_group_id, message_group_name])

            #Build the response message
            #command - this is a variable stored at the start of this function
            arguments = {
                "status" : status,
                "message_id" : message_id,
                "active_message_groups" : active_message_groups,
            }
            data = None
            response = build_tcp_response_message(command, arguments, data)

            return response

    def handle_ticker_off_message(self, command, arguments, data):
        """Must have a database connection before utelising this function!"""
        self.logger.debug("#############MESSAGE CONSOLE STOP MESSAGE HANDLER INVOKED#############")

        #Extract the info from the message
        message_group_list = data
        
        #Variables used for error tracking
        group_success_list = []
        group_fail_list = []

        #Iterate through the list of message groups in the data field and send the message to their associated devices
        for message_group in message_group_list:

            message_group_id = message_group[0]
            message_group_name = message_group[1]

            #Get the osc address for the message group
            osc_address = self.db.get_1column_data("osc_address", "messaging_groups", "messaging_group_id", message_group_id)[0]
            self.logger.debug(f"OSC ADDRESS: {osc_address}")

            #Query the database to get a list of devices that are associated to the message group
            device_list = self.db.get_1column_data("device_ip", "devices", "messaging_group_id", message_group_id)
            self.logger.debug(f"Devices associated with message group ID:{message_group_id}, {device_list}")

            #Forward OSC message to clients in the message group
            self.logger.debug(f"Sending message to client")
            send_status = self.forward_osc_message(device_list, osc_address, [False])
            self.logger.debug(f"Send Status for message group {message_group_name}: {send_status}")

            if send_status == True:
                group_success_list.append(message_group)
                #Delete the active message mapping - only if a message was forwarded to a message group
                self.logger.debug(f"Removing active message mapping for message_group_id: {message_group_id}")
                self.db.delete_row("active_messages", "message_group_id", message_group_id)
            else:
                group_fail_list.append(message_group)

        #Query the database for a list of active message_groups
        active_messages = self.db.get_current_table_data("active_messages")
        active_message_groups = []
        active_message_ids = []
        for mapping in active_messages:

            message_id = mapping[0]
            active_message_ids.append(message_id)

            message_group_id = mapping[1]
            message_group_name = self.db.get_1column_data("messaging_group_name", "messaging_groups", "messaging_group_id", message_group_id)[0]
            active_message_groups.append([message_group_id, message_group_name])

        #Check to see if the message is still in use - if it is not delete it!
        messages = self.db.get_current_table_data("messages")
        for message in messages:
            message_id = message[0]
            if message_id not in active_messages:
                self.db.delete_row("messages", "message_id", message_id)

        #Build the response message
        #command - this is a variable stored at the start of this function
        arguments = {
            "status" : "OK",
            "active_message_groups" : active_message_groups
        }
        data = None
        response = build_tcp_response_message(command, arguments, data)

        return response
        
    #--------------------------------CONTROLLER-HANDLERS---------------------------------------------------
    #Sends OSC commands over the network given a GPI state change
    def handle_gpi(self, *args):
        self.logger.debug(f"GPI HANDLER - Incoming Data: {args}")
        try:
            controller_id = args[0]
            pin = args[1]
            state = args[2]

            self.logger.debug(f"Controller {controller_id}, pin {pin}, reports {state}")
            controller_id = str(controller_id)
            gpi = str(pin)

            #Connect to the database
            self.db.connect()

            #Lookup in the trigger_mappings table what triggers are actioned on this gpi
            data = self.db.get_current_row_data_dual_condition("trigger_mappings", "controller_id", controller_id, "gpi", gpi)

            for mapping in data:
                #mapping = (trigger_group_id, osc_address)
                #Extract the trigger_group_id from each mapping
                trigger_group_id = mapping[0]
                #Extract the item to be triggered from each mapping (osc_address)
                osc_address = mapping[1]

                #Query the database to identify devices associatied with this trigger group ID
                device_list = self.db.get_1column_data("device_ip", "devices", "trigger_group_id", trigger_group_id)
                self.logger.debug(f"Devices associated with trigger group ID:{trigger_group_id}, {device_list}")
                
                for device_ip in device_list:
                    #Device list contains a list of device_ip's that are associatied with the trigger id
                    #Create a new instance of an OSC client for transmitting information to devices
                    self.tx: OSC_Client = OSC_Client(device_ip, 1338, "udp")
                    #Send command to device
                    send_thread = threading.Thread(target=self.tx.send_osc_message, args=(osc_address, state), daemon=True)
                    send_thread.start()

        except Exception as e:
            self.logger.error(f"Unable to handle GPI change event, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()
                
    #--------------------------------FORWARDERS---------------------------------------------------            
    #Forwards OSC messages to client devices - returns true if successfull, false if not
    def forward_osc_message(self, device_list:list, osc_message:str, data):
        if device_list !=[]:
            for device_ip in device_list:
                    self.logger.info(f"Sending Message to client: {device_ip} using UDP")
                    #Create a new instance of an OSC client for transmitting information to devices
                    self.tx: OSC_Client = OSC_Client(device_ip, 1338, "udp")
                    #Send command to device
                    self.tx.send_osc_message(osc_message, data)
                    #Delete the Socket
                    del self.tx
                    self.logger.info("Message Sent Successfully")

            return True
        else:
            self.logger.debug("No devices assigned to group. Message not sent.")
            return False
        
    #Forwards OSC messages to client devices using TCP - returns true if successfull, false if not
    def forward_tcp_osc_message(self, device_list:list, osc_message:str, data):
        if device_list !=[]:
            for device_ip in device_list:
                    self.logger.info(f"Sending Message to client: {device_ip} using TCP")
                    #Create a new instance of an OSC client for transmitting information to devices
                    self.tx: OSC_Client = OSC_Client(device_ip, 1338, "tcp")
                    #Send command to device
                    self.tx.send_osc_message(osc_message, data)
                    #Delete the Socket
                    del self.tx
                    self.logger.info("Message Sent Successfully")

            return True
        else:
            self.logger.debug("No devices assigned to group. Message not sent.")
            return False

   