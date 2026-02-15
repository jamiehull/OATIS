from database.database_connection import *
from display_widgets.widget_columns import widget_columns_dict
from modules.common import make_dict, validate_hex_str
from modules.osc import OSC_Client
import logging
import json
import threading
import datetime
import traceback
from threading import Lock

class Router:
    """Routes GPI / OSC signals to the assigned devices."""
    def __init__(self, gpo_output_function=None):
        #Store a reference to the database, explicitly stating the variable type - makes calling function easier
        self.db: DB = DB()

        #Lock for thread safe access to DB
        self.db_lock = Lock()

        #Map dict for mapping TCP handlers
        self.map_dict = {}

        #Function to trigger a GPO if the router module is used with a microcontroller
        self.gpo_output_function = gpo_output_function

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        self.__map_handlers()

    def __map_handler_function(self, command:str, handler_function):
        """Adds a dictionary entry for a command and handler function."""
        self.map_dict[command] = handler_function

    def __map_handlers(self):
        """Maps tcp commands to handler functions"""
        self.__map_handler_function("heartbeat", self.handle_heartbeat)
        self.__map_handler_function("/config/display_template/get", self.handle_display_template_request)
        self.__map_handler_function("/config/device/get", self.handle_device_config_request)
        self.__map_handler_function("/assets/images/get", self.handle_image_request)
        self.__map_handler_function("/config/message_groups/get", self.handle_message_groups_get_all)
        self.__map_handler_function("/config/message_groups/get_used", self.handle_message_groups_get_used)
        self.__map_handler_function("/config/devices/get", self.handle_devices_config_request)
        self.__map_handler_function("/messaging/send_to_multiple", self.handle_send_message_to_multiple)
        self.__map_handler_function("/messaging/stop_message", self.handle_stop_message)
        self.__map_handler_function("/messaging/get_active_groups", self.handle_get_active_message_groups)
        self.__map_handler_function("/control/client/reload_display_template", self.handle_reload_display)
        self.__map_handler_function("/control/client/identify", self.handle_identify)
        self.__map_handler_function("/config/image_stacks/get_image_ids", self.handle_get_stacked_image_ids)

    #--------------------------------EXTERNAL-FACING-OSC-HANDLERS---------------------------------------------------

    def handle_stacked_image_change_message(self, address, *args):
        """Expects address: /client/control/stacked_image
        Args: ("device_id" "image_stack_id", "image_id)"""

        self.logger.debug(f"IMAGE STACK OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            self.db.connect()

            #Extract the args
            device_id = str(args[0])
            #display_surface_id = str(args[1])
            image_stack_id = str(args[1])
            image_id = str(args[2])

            #Query the database to get the device ip associated with the device_id
            device_list = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)
            self.logger.debug(f"Device associated with device id:{device_id}, {device_list}")

            #Forward OSC message to client
            self.logger.debug(f"Sending message to client")
            send_status = self.forward_osc_message(device_list, "/client/control/stacked_image", [image_stack_id, image_id])
            self.logger.debug(f"Send Status for device {device_id}: {send_status}")


        except IndexError:
            self.logger.error(f"Unable to handle image stack OSC message, the device does not exist in the database.")

        except Exception as e:
            self.logger.error(f"Unable to handle image stack OSC message, reason: {e}")

        finally:
            self.db.close_connection()

    def handle_ticker_on_osc_message(self, address, *args):
        """Expects address: /messaging/send_message
        Args: ("ticker_text", "bg_colour_hex", "message_group_id)"""

        self.logger.debug(f"TICKER OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            self.db.connect()

            #Extract the args
            message_text = str(args[0])
            bg_colour = str(args[1])
            message_group_id = str(args[2])
            
            #Format the data to forward onto handler
            input_command = address
            input_arguments = {
                "message" : message_text,
                "bg_colour" : bg_colour}
            
            #Check Hex colour is valid
            valid_hex = validate_hex_str(bg_colour)
            
            #If hex is valid
            if valid_hex == True:
                #Find the message group name
                message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]

                input_data = [(message_group_id, message_group_name)]

                self.handle_send_message_to_multiple(input_command, input_arguments, input_data)

            #If hex is invalid
            else:
                raise Exception("Invalid Hex colour provided.")
            
        except IndexError:
            self.logger.error(f"Unable to handle ticker OSC message, the specified message group id does not exist in the database.")

        except Exception as e:
            self.logger.error(f"Unable to handle ticker OSC message, reason: {e}")

        finally:
            self.db.close_connection()
        
    def handle_ticker_off_osc_message(self, address, *args):
        """Expects address: /messaging/stop_message
        Args: ([["message_group_id","message_group_name"],["message_group_id","message_group_name"])"""

        self.logger.debug(f"TICKER OSC HANDLER - Incoming Data: {address}, {args}")
        try:
            self.db.connect()

            #Extract the args
            message_group_id = args[0]
            
            #Find the message group name
            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]
            
            #Format the data to forward onto handler
            input_command = address
            input_arguments = None
            input_data = [(message_group_id, message_group_name)]

            self.handle_stop_message(input_command, input_arguments, input_data)

        except IndexError:
            self.logger.error(f"Unable to handle ticker OSC message, the specified message group id does not exist in the database.")

        except Exception as e:
            self.logger.error(f"Unable to handle ticker OSC message, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()
    
    def handle_custom_osc_input_message(self, address, *args):
        """Handles user generated OSC Input Triggers"""
        try:
            self.logger.debug(f"OSC HANDLER - Incoming Command:{address}, args{args}")
            controller_id = 0
            osc_command = address

            #Check if the command is valid
            self.db.connect()

            valid_cmd = any(self.db.get_1column_data("input_trigger_id", "input_triggers", "address", address))

            if valid_cmd == True:
                state = args[0] #0=off, 1=on

                if state == 0 or state == 1:
                    self.handle_gpi(controller_id, osc_command, state)

                else:
                    self.logger.error(f"Error handing incoming OSC Command, invalid arguments:{args}, must be 0 or 1.")

            else:
                self.logger.error(f"Ignoring Invalid Command: {osc_command}")

        except IndexError:
            self.logger.error(f"Error handing incoming OSC Command, invalid arguments:{args}, must be 0 or 1.")

        except Exception as e:
            self.logger.error(f"Error handing incoming OSC Command:{e}")

        finally:
            self.db.close_connection()

    #--------------------------------TCP-HANDLER-MAPPER---------------------------------------------------
    #Handles incoming tcp requests and returns a response
    def handle_tcp_message(self, input_command, input_arguments, input_data):
        """Handles incoming TCP message, routing inputs to correct handler."""
        try:
            with self.db_lock:
                #Connect to the database
                self.db.connect()

                #Get the handler function
                handler_function = self.map_dict.get(input_command)

                if handler_function != None:
                    #Pass the input data to the handler function
                    output_command, output_arguments, output_data = handler_function(input_command, input_arguments, input_data)

                else:
                    self.logger.error(f"Error handling tcp request, no matching handlers, the request is invalid.")
                    output_command = input_command
                    output_arguments = {"status" : "invalid_command",
                                        "binary_response" : False
                                        }
                    output_data = None

        except IndexError as e:
            self.logger.error(f"Error handling tcp request, unable to find the requested data in the Database, this is likley due to a misconfiguration. {e}")
            output_command = input_command
            output_arguments = {
                "status" : "data_not_found",
                "exception" : str(e),
                "binary_response" : False
                }
            output_data = None
            
        except Exception as e:
            self.logger.error(f"Error handling tcp request: {e}")
            #traceback.print_exc()
            output_command = input_command
            output_arguments = {
                "status" : "exception",
                "exception" : str(e),
                "binary_response" : False
                }
            output_data = None

        finally:
            #Close connection to database
            self.db.close_connection()

        return output_command, output_arguments, output_data
    
    #--------------------------------TCP-HANDLERS---------------------------------------------------
    def handle_heartbeat(self, input_command:str, input_arguments:dict, input_data):
        output_command = "heartbeat"
        self.logger.debug("#############CLIENT HEARTBEAT HANDLER INVOKED#############")
        
        #Generate a timestamp
        timestamp = str(datetime.datetime.now())
        output_arguments = {
            "status" : "OK",
            "timestamp" : timestamp,
            "binary_response" : False
        }
        output_data = None

        return output_command, output_arguments, output_data

    def handle_display_template_request(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/config/display_template/get"

        self.logger.debug("#############TCP DISPLAY TEMPLATE HANDLER INVOKED#############")

        #Variable used to indicate whether the display template from the client matches the one on the server
        match_status = False
        
        client_display_template_timestamp = input_arguments["display_template_timestamp"]
        client_display_instance_timestamp = input_arguments["display_instance_timestamp"]
        client_ip = input_arguments["client_ip"]

        #Look up the display instance assigned to the device id
        display_instance_id = self.db.get_1column_data("display_instance_id", "devices", "device_ip", client_ip)[0]

        #Look up display template id
        display_template_id = self.db.get_1column_data("display_template_id", "display_instances", "display_instance_id", display_instance_id)[0]

        #Get the timestamps
        db_display_template_timestamp = self.db.get_1column_data("last_changed", "display_templates", "display_template_id", display_template_id)[0]
        db_display_instance_timestamp = self.db.get_1column_data("last_changed", "display_instances", "display_instance_id", display_instance_id)[0]

        #Open the display template and compare the timestamp
        #If the timestamps match, do not send the client the display template
        if (db_display_template_timestamp == client_display_template_timestamp) and (db_display_instance_timestamp == client_display_instance_timestamp):
            match_status = True
        #If the timestamps do not match, send a new display template to the client
        else:
            match_status = False

        #Get the layout matrix
        layout_matrix_blob = self.db.get_1column_data("layout_matrix", "display_templates", "display_template_id", display_template_id)[0]
        layout_matrix = json.loads(layout_matrix_blob)

        #Find the display surfaces and widget_strings
        display_surface_rows = self.db.get_current_row_data("display_surfaces", "display_template_id", display_template_id)

        #Blank list to hold config for each display surface
        display_surfaces_dict = {}

        for row in display_surface_rows:
            display_surface_id = row[1]
            widget_string = row[2]
            widget_config_list = self.db.get_current_row_data_dual_condition(widget_string, "display_instance_id", display_instance_id, "display_surface_id", display_surface_id)[0]
            
            #Convert the widget config_list to a dict
            widget_config_dict = make_dict(widget_columns_dict[widget_string], widget_config_list)
            
            display_surfaces_dict[display_surface_id] = {
                "widget_string":widget_string,
                "widget_config":widget_config_dict
                }

        #Add arguments to the response
        output_arguments = {
            "status" : "OK",
            "display_template_current" : match_status,
            "display_template_timestamp" : db_display_template_timestamp,
            "display_instance_timestamp" : db_display_instance_timestamp,
            "display_template_id" : display_template_id,
            "display_instance_id" : display_instance_id,
            "layout_matrix" : layout_matrix,
            "display_surfaces" : display_surfaces_dict,
            "binary_response": False
        }

        output_data = None

        return output_command, output_arguments, output_data

    def handle_image_request(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/assets/images/get"
        self.logger.debug("#############TCP IMAGE HANDLER INVOKED#############")
        image_id = input_arguments["image_id"]

        #Query the database to return the image
        blob_image : bytes = self.db.get_1column_data("image_file", "images", "image_id", image_id)[0]

        image_found = False

        if blob_image != []:
            image_found = True
        
        output_arguments = {
            "image_id":image_id,
            "image_found":image_found,
            "binary_response" : True
            }

        return output_command, output_arguments, blob_image
    
    def handle_device_config_request(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/config/devices/get"
        self.logger.debug("#############TCP GET DEVICE CONFIG HANDLER INVOKED#############")

        #Retrieve device IP from the incoming request
        device_ip = input_arguments["client_ip"]

        #Look up the device ID using the device IP address
        device_config = self.db.get_current_row_data("devices", "device_ip", device_ip)[0]

        #Device config Indicies
        device_name = device_config[1]
        device_location = device_config[3]
        message_group_id = device_config[4]
        display_instance_id = device_config[5]

        #Get the message group associated with the device
        message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]

        #Get the display template associated with the device
        display_instance_name = self.db.get_1column_data("display_instance_name", "display_instances", "display_instance_id", display_instance_id)[0]

        #Build the response
        output_arguments = {
            "status" : "OK",
            "device_name" : device_name,
            "device_ip" : device_ip,
            "device_location" : device_location,
            "message_group" : message_group_name,
            "display_instance" : display_instance_name,
            "binary_response" : False
        }
                
        output_data = None

        return output_command, output_arguments, output_data

    def handle_message_groups_get_all(self, input_command:str, input_arguments:dict, input_data):
        #Returns a list of all message_groups
        output_command = "/config/message_groups/get"
        self.logger.debug("#############MESSAGE CONSOLE GET MESSAGE GROUPS HANDLER INVOKED#############")

        #Query the database for a list of message groups
        message_group_list :list = self.db.get_2column_data("message_group_id", "message_group_name", "message_groups")

        output_arguments = {
            "status" : "OK",
            "message_groups" : message_group_list,
            "binary_response" : False
        }

        output_data = None

        return output_command, output_arguments, output_data

    def handle_message_groups_get_used(self, input_command:str, input_arguments:dict, input_data):
        #Returns a list of all message_groups in use with devices associated to them
        output_command = "/config/message_groups/get_used"
        self.logger.debug("#############MESSAGE CONSOLE GET USED MESSAGE GROUPS HANDLER INVOKED#############")

        #Query the database for a list of message groups
        message_group_list :list = self.db.get_2column_data("message_group_id", "message_group_name", "message_groups")
        
        #Blank list for storing in use message groups
        message_group_in_use_list :list = []
        for message_group in message_group_list:

            message_group_id = message_group[0]
            message_group_name = message_group[1]

            #Query the database to get a list of devices that are associated to the message group
            device_list = self.db.get_1column_data("device_ip", "devices", "message_group_id", message_group_id)
            if device_list != []:
                self.logger.debug(f"Message Group {message_group_name} in use.")
                message_group_in_use_list.append(message_group)
            else:
                self.logger.debug(f"Message Group {message_group_name} is not currently in use.")

        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "message_groups" : message_group_in_use_list,
            "binary_response" : False
        }

        output_data = None

        return output_command, output_arguments, output_data

    def handle_devices_config_request(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/config/devices/get"
        self.logger.debug("#############MESSAGE CONSOLE GET DEVICES HANDLER INVOKED#############")

        #Query the database for a list of message groups
        device_list :list = self.db.get_2column_data("device_id", "device_name", "devices")

        output_arguments = {
            "status" : "OK",
            "device_config_list" : device_list,
            "binary_response" : False
        }

        output_data = None

        return output_command, output_arguments, output_data

    def handle_send_message_to_multiple(self, input_command:str, input_arguments:dict, input_data):
        """Must have a database connection before utelising this function!"""
        output_command = "/messaging/send_to_multiple"
    
        self.logger.debug("#############MESSAGE CONSOLE SEND TO MULTIPLE HANDLER INVOKED#############")

        #Extract the info from the message - state turns the ticker on and off
        message_text = input_arguments["message"]
        bg_colour = input_arguments["bg_colour"]
        message_group_list = input_data
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
                #Query the database to get a list of devices that are associated to the message group
                device_list = self.db.get_1column_data("device_ip", "devices", "message_group_id", message_group_id)
                self.logger.debug(f"Devices associated with message group ID:{message_group_id}, {device_list}")

                #Forward OSC message to clients in the message group
                self.logger.debug(f"Sending message to client")
                send_status = self.forward_osc_message(device_list, "/client/control/ticker", [True, message_text, bg_colour])
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
            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]
            active_message_groups.append([message_group_id, message_group_name])

        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : status,
            "message_id" : message_id,
            "active_message_groups" : active_message_groups,
            "binary_response" : False
        }

        output_data = None

        return output_command, output_arguments, output_data

    def handle_stop_message(self, input_command:str, input_arguments:dict, input_data):
        """Must have a database connection before utelising this function!"""
        
        output_command = "/messaging/stop_message"
        self.logger.debug("#############MESSAGE CONSOLE STOP MESSAGE HANDLER INVOKED#############")

        #Extract the info from the message
        message_group_list = input_data
        
        #Variables used for error tracking
        group_success_list = []
        group_fail_list = []

        #Iterate through the list of message groups in the data field and send the message to their associated devices
        for message_group in message_group_list:

            message_group_id = message_group[0]
            message_group_name = message_group[1]

            #Query the database to get a list of devices that are associated to the message group
            device_list = self.db.get_1column_data("device_ip", "devices", "message_group_id", message_group_id)
            self.logger.debug(f"Devices associated with message group ID:{message_group_id}, {device_list}")

            #Forward OSC message to clients in the message group
            self.logger.debug(f"Sending message to client")
            send_status = self.forward_osc_message(device_list, "/client/control/ticker", [False])
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
            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]
            active_message_groups.append([message_group_id, message_group_name])

        #Check to see if the message is still in use - if it is not delete it!
        messages = self.db.get_current_table_data("messages")
        for message in messages:
            message_id = message[0]
            if message_id not in active_messages:
                self.db.delete_row("messages", "message_id", message_id)

        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "active_message_groups" : active_message_groups,
            "binary_response" : False
        }
        output_data = None


        return output_command, output_arguments, output_data
    
    def handle_get_active_message_groups(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/messaging/get_active_groups"
        self.logger.debug("#############MESSAGE CONSOLE GET ACTIVE GROUPS HANDLER INVOKED#############")

        #Query the database for a list of active message_groups
        active_messages = self.db.get_current_table_data("active_messages")
        active_message_groups = []
        active_message_ids = []
        for mapping in active_messages:

            message_id = mapping[0]
            active_message_ids.append(message_id)

            message_group_id = mapping[1]
            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]
            active_message_groups.append([message_group_id, message_group_name])

        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "active_message_groups" : active_message_groups,
            "binary_response" : False
        }
        output_data = None

        return output_command, output_arguments, output_data

    def handle_reload_display(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/control/client/reload_display"
        self.logger.debug("#############RELOAD DISPLAY HANDLER INVOKED#############")

        #Extract the data
        device_id = input_arguments.get("device_id")

        #Get the device IP
        device_ip = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)[0]

        #Send the command to the device
        self.forward_osc_message([device_ip], "/client/control/reload_display_template", None)

        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "device_id" : device_id,
            "device_ip" : device_ip,
            "binary_response" : False
        }
        output_data = None

        return output_command, output_arguments, output_data

    def handle_identify(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/control/client/identify"
        self.logger.debug("#############RELOAD DISPLAY HANDLER INVOKED#############")

        #Extract the data
        device_id = input_arguments.get("device_id")
        frame = input_arguments.get("frame")

        #Get the device IP
        device_ip = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)[0]

        #Send the command to the device
        self.forward_osc_message([device_ip], "/client/control/frames", frame)
        
        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "device_id" : device_id,
            "device_ip" : device_ip,
            "binary_response" : False
        }
        output_data = None

        return output_command, output_arguments, output_data
   
    def handle_get_stacked_image_ids(self, input_command:str, input_arguments:dict, input_data):
        output_command = "/config/image_stacks/get_image_ids"
        self.logger.debug("#############IMAGE STACKS GET IMAGE IDS HANDLER INVOKED#############")

        #Extract the data
        image_stack_id = input_arguments.get("image_stack_id")

        #Get the device IP
        #device_ip = self.db.get_1column_data("device_ip", "devices", "device_id", device_id)[0]

        #Lookup the image ID's associated with the image stack
        image_ids_list = self.db.get_1column_data("image_id", "image_stack_mappings", "image_stack_id", image_stack_id)
        
        #Build the response message
        #command - this is a variable stored at the start of this function
        output_arguments = {
            "status" : "OK",
            "image_ids_list" : image_ids_list,
            "binary_response" : False
        }
        output_data = None

        return output_command, output_arguments, output_data
   
    #--------------------------------CONTROLLER-HANDLERS---------------------------------------------------
    #Sends OSC commands over the network given a GPI state change
    def handle_gpi(self, *args):
        """Handles and Arduino Pin State change."""
        self.logger.debug(f"GPI HANDLER - Incoming Data: {args}")
        try:
            with self.db_lock:
                controller_id = args[0]
                address = args[1]
                state = bool(args[2])

                self.logger.debug(f"Controller {controller_id}, pin {address}, reports {state}")

                #Connect to the database
                self.db.connect()

                #Find the input trigger id
                input_trigger_id_query_result = self.db.get_1column_data_dual_condition("input_trigger_id", "controller_id", controller_id, "address", address, "input_triggers")
                
                if input_trigger_id_query_result != []:
                    input_trigger_id = input_trigger_id_query_result[0]

                    self.logger.debug(f"Input Trigger ID {input_trigger_id} changing state to: {state}")

                    #Update the current DB state of the trigger
                    self.db.update_row("input_triggers", "current_state", "input_trigger_id", state, input_trigger_id)
                    self.logger.debug(f"Updated current state in DB for Input Trigger ID {input_trigger_id}")

                    #Find input logics referencing this trigger id
                    input_logic_id_list = self.db.get_1column_data("input_logic_id", "input_logic_mapping", "input_trigger_id", input_trigger_id)
                    self.logger.debug(f"Input Logics referencing Trigger ID {input_trigger_id}: {input_logic_id_list}")
                    
                    for input_logic_id in input_logic_id_list:
                        #Find the high condition
                        high_condition = self.db.get_1column_data("high_condition", "input_logics", "input_logic_id", input_logic_id)[0]
                        
                        #Find the state of all triggers contributing to this input logic
                        input_trigger_states_list = self.__get_input_trigger_states(input_logic_id)
                        
                        #Test if the input logic is high or low
                        input_logic_state = self.__get_input_logic_state(high_condition, input_logic_id, input_trigger_states_list)

                        #Check if the input logic is used in any display instances
                        display_instance_id_list = self.db.get_1column_data("display_instance_id", "indicator", "input_logic_id", input_logic_id)

                        #Trigger each display instance if any were found to use the input logic
                        self.__trigger_display_instances(input_logic_id, input_logic_state, display_instance_id_list)

                        #Check the DB for any output logics taking this input logic as an input
                        output_logics_id_list = self.db.get_1column_data("output_logic_id", "output_logics", "input_logic_id", input_logic_id)

                        #Check the DB for output_triggers triggered by this output_logic
                        for output_logic_id in output_logics_id_list:
                            output_trigger_id_list = self.db.get_1column_data("output_trigger_id", "output_logic_mapping", "output_logic_id", output_logic_id)

                            #Trigger each output trigger
                            self.__trigger_output_triggers(input_logic_state, output_trigger_id_list)

                else:
                    self.logger.warning(f"Pin {address}, on Controller {controller_id} is not configured as an Input Trigger.")

        except Exception as e:
            self.logger.error(f"Unable to handle GPI change event, reason: {e}")
        
        finally:
            #Close connection to database
            self.db.close_connection()

    #--------------------------------HANDLE GPI SUB FUNCTIONS--------------------------------------------------- 
    def __get_input_trigger_states(self, input_logic_id) -> list:
        input_trigger_id_list = self.db.get_1column_data("input_trigger_id", "input_logic_mapping", "input_logic_id", input_logic_id)
        state_list = []

        for input_trigger_id in input_trigger_id_list:
            state = self.db.get_1column_data("current_state", "input_triggers", "input_trigger_id", input_trigger_id)[0]
            state_list.append(state)

        return state_list

    def __get_input_logic_state(self, high_condition, input_logic_id, state_list) -> bool:
        input_logic_state =  self.compare_states(high_condition, state_list)
        self.logger.debug(f"Input Logic:{input_logic_id} current state {input_logic_state}")

        return input_logic_state
        
    def __trigger_display_instances(self, input_logic_id, input_logic_state, display_instance_id_list):
        for display_instance_id in display_instance_id_list:

            display_surface_id = self.db.get_1column_data_dual_condition("display_surface_id", "display_instance_id", display_instance_id, "input_logic_id", input_logic_id, "indicator")[0]

            #Query the database to identify device ips associatied with this input_logic
            device_list = self.db.get_1column_data("device_ip", "devices", "display_instance_id", display_instance_id)

            for device_ip in device_list:
                #Create a new instance of an OSC client for transmitting information to devices
                self.tx: OSC_Client = OSC_Client(device_ip, 1338, "udp")

                #Send command to device
                send_thread = threading.Thread(target=self.tx.send_osc_message, args=("/client/control/signal_lights/", [display_surface_id, input_logic_state]), daemon=True)
                send_thread.start()

    def __trigger_output_triggers(self, input_logic_state, output_trigger_id_list):
        for output_trigger_id in output_trigger_id_list:
            #Get the output trigger type
            output_type = self.db.get_1column_data("output_type", "output_triggers", "output_trigger_id", output_trigger_id)[0]
            output_controller_id = self.db.get_1column_data("controller_id", "output_triggers", "output_trigger_id", output_trigger_id)[0]
            output_address = self.db.get_1column_data("address", "output_triggers", "output_trigger_id", output_trigger_id)[0]

            if output_type == "GPO":
                self.logger.debug(f"Setting Controller: {output_controller_id} pin:{output_address}, to state:{input_logic_state}")
                self.gpo_output_function(int(output_controller_id), int(output_address), input_logic_state)

            elif output_type == "Network":
                ip_address = self.db.get_1column_data("ip_address", "output_triggers", "output_trigger_id", output_trigger_id)[0]
                port = self.db.get_1column_data("port", "output_triggers", "output_trigger_id", output_trigger_id)[0]
                protocol = self.db.get_1column_data("protocol", "output_triggers", "output_trigger_id", output_trigger_id)[0]

                if input_logic_state == True:
                    command = self.db.get_1column_data("command_high", "output_triggers", "output_trigger_id", output_trigger_id)[0]
                    arguments = self.db.get_1column_data("arguments_high", "output_triggers", "output_trigger_id", output_trigger_id)[0]

                elif input_logic_state == False:
                    command = self.db.get_1column_data("command_low", "output_triggers", "output_trigger_id", output_trigger_id)[0]
                    arguments : str = self.db.get_1column_data("arguments_low", "output_triggers", "output_trigger_id", output_trigger_id)[0]

                else:
                    self.logger.error(f"Invalid Logic State: {input_logic_state}")
                
                #Only send an OSC message if the command has been populated
                if (command != "") and (command != "N/A"):
                    #Create a new instance of an OSC client for transmitting information to devices
                    self.tx: OSC_Client = OSC_Client(ip_address, port, protocol)

                    #Extract the string arguments
                    args = arguments.split()

                    #Send command to device
                    send_thread = threading.Thread(target=self.tx.send_osc_message, args=(command, args), daemon=True)
                    send_thread.start()
            else:
                self.logger.error(f"Output Trigger: {output_trigger_id} has invalid output type specified: {output_type}")

    def compare_states(self, high_condition:str, state_list:list[bool]) -> bool:
        """Takes a list of booleans and compares them given a logic condition, returning the output."""
        if high_condition == "AND":
            return all(state_list)
        elif high_condition == "OR":
            return any(state_list)
        elif high_condition == "NAND":
            return not all(state_list)
        elif high_condition == "NOR":
            return not any(state_list)
        else:
            self.logger.error(f"Incorrect high condition specified:{high_condition}")
            return False        
    
    #--------------------------------FORWARDERS---------------------------------------------------            
    #Forwards OSC messages to client devices - returns true if successfull, false if not
    def forward_osc_message(self, device_list:list, osc_message:str, data):
        if device_list !=[]:
            for device_ip in device_list:
                    self.logger.info(f"Sending Message to client: {device_ip}")
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
                    self.logger.info(f"Sending Message to client: {device_ip}")
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

   