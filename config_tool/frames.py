import customtkinter as ctk
import tkinter as tk
from tkinter import StringVar
from config_tool.validation import validate_ip
from serial.tools.list_ports import comports
from config_tool.message_boxes import *
from tkinter import messagebox
from tkinter import filedialog
from modules.gui_templates import *
import shutil
import os
import logging
from config_tool.global_variables import *
import datetime
from modules.common import *
from config_tool.config_tool_widgets import *
from modules.tcp import *
from display_widgets.widget_strings import widget_strings_list

class Image_Store(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("", "image_picker", "not_null_not_in_db")
        self.image_picker_widget_index = 0

        row_list = [row1]

        #Initialise the Base Frame with the above rows
        self.build_gui("Image Store", "images", "image_name", "image_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_tree()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            image_path :str = input_data_list[self.image_picker_widget_index]

            #Save the data to the database
            self.__save_input_data(image_path)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            image_unchanged_warning()()

    #Save input data to the database
    def __save_input_data(self, image_path):
        """Saves input data to the database."""

        #Get name of image file from path
        image_name = os.path.basename(image_path)

        #Convert image to a binary object
        blob_image = convert_to_blob(image_path)

        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")
            
            #Add the validated data to the database
            self.db.add_image(image_name, blob_image)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            self.db.update_row(self.table, "image_name", self.id_column, image_name, db_id)
            self.db.update_row(self.table, "image_file", self.id_column, blob_image, db_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            image_name = item_data_list[1]
            blob_image = item_data_list[2]

            #Add all data to the input frame widgets
            image_picker_object : ImagePicker = self.input_frame.get_widget_object(0)
            image_picker_object.set_image(blob_image)
            
            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")
      
class Device_Config(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)
    
        #Rows to make in the frame
        row1 = Input_Row("Device Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0

        row2 = Input_Row("Device IP Address:", "text_entry", "not_null_ip_address")
        self.ip_input_widget_index = 1

        row3 = Input_Row("Device Location:", "text_entry", "not_null")
        self.location_input_widget_index = 2

        row4 = Input_Row("Messaging Group:", "combobox", "not_null")
        self.messaging_group_widget_index = 3

        row5 = Input_Row("Display Instance:", "combobox", "not_null")
        self.display_instance_widget_index = 4

        row6 = Input_Row("Display Instance:", "control_buttons", "n/a")
        self.control_buttons_widget_index = 5
        
        row_list = [row1, row2, row3, row4, row5, row6]

        #Initialise the Base Frame with the above rows
        self.build_gui("Device Configuration", "devices", "device_name", "device_id", row_list)

        #Set Control button Commands
        control_buttons : Control_Buttons = self.input_frame.get_widget_object(self.control_buttons_widget_index)
        control_buttons.set_identify_cmd(self.__identify_device)
        control_buttons.set_reload_cmd(self.__reload_device_display)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""
        self.update_tree()
        self.__update_combobox_values()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            device_name = input_data_list[self.name_input_widget_index]
            device_ip = input_data_list[self.ip_input_widget_index]
            location = input_data_list[self.location_input_widget_index]
            message_group_id = input_data_list[self.messaging_group_widget_index].split(":")[0]
            display_instance_id = input_data_list[self.display_instance_widget_index].split(":")[0]

            #Save the data to the database
            self.__save_input_data(device_name, device_ip, location, message_group_id, display_instance_id)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            #Disable the buttons
            control_buttons_widget : Control_Buttons = self.input_frame.get_widget_object(self.control_buttons_widget_index)
            control_buttons_widget.disable_buttons()

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Save input data to the database
    def __save_input_data(self, device_name, device_ip, location, message_group_id, display_instance_id):
        """Saves input data to the database."""

        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")
            
            #Add the validated data to the database
            self.db.add_device(device_name, device_ip, location, message_group_id, display_instance_id)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            self.db.update_row(self.table, "device_name", self.id_column, device_name, db_id)
            self.db.update_row(self.table, "device_ip", self.id_column, device_ip, db_id)
            self.db.update_row(self.table, "location", self.id_column, location, db_id)
            self.db.update_row(self.table, "message_group_id", self.id_column, message_group_id, db_id)
            self.db.update_row(self.table, "display_instance_id", self.id_column, display_instance_id, db_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            device_name = item_data_list[1]
            device_ip = item_data_list[2]
            location = item_data_list[3]
            message_group_id = item_data_list[4]
            display_instance_id = item_data_list[5]

            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", message_group_id)[0]
            display_instance_name = self.db.get_1column_data("display_instance_name", "display_instances", "display_instance_id", display_instance_id)[0]

            message_group_id_name = f"{message_group_id}:{message_group_name}"
            display_instance_id_name = f"{display_instance_id}:{display_instance_name}"

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(device_name, device_ip, location, message_group_id_name, display_instance_id_name)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            #Enable the buttons
            control_buttons_widget : Control_Buttons = self.input_frame.get_widget_object(self.control_buttons_widget_index)
            control_buttons_widget.enable_buttons()

            self.logger.info("Updated Input widgets")

    def __update_combobox_values(self):
        #Update Messaging Group
        message_group_id_name_list = []
        message_group_rows = self.db.get_2column_data("message_group_id", "message_group_name", "message_groups")
        for row in message_group_rows:
            id=row[0]
            name=row[1]
            message_group_id_name_list.append(f"{id}:{name}")
        self.logger.debug(f"message_group_id_name_list:{message_group_id_name_list}")

        self.set_combobox_values(self.messaging_group_widget_index, message_group_id_name_list)

        #Update Display instance
        display_instance_id_name_list = []
        display_instance_rows = self.db.get_2column_data("display_instance_id", "display_instance_name", "display_instances")
        for row in display_instance_rows:
            id=row[0]
            name=row[1]
            display_instance_id_name_list.append(f"{id}:{name}")
        self.logger.debug(f"display_instance_id_name_list:{display_instance_id_name_list}")

        self.set_combobox_values(self.display_instance_widget_index, display_instance_id_name_list)
        
#-----------------------------------------CUSTOM FUNCTIONS ------------------------------------------------------------------------------------------------
    def get_device_id(self):
        """Returns the database id of the selected treeview item.
          Returns None if no item is in focus."""
        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        return db_id
        
    def __reload_device_display(self):
        try:
            #Get the devices ID
            device_id = self.get_device_id()
            if device_id != None:

                #Read the Server Settings file
                settings_dict = open_json_file("server/settings.json")

                #Only send a command to the server if it has an ip set
                if settings_dict != False:
                        server_ip = (settings_dict["server_ip"])

                        #Send the raise frame command to the server
                        self.tcp_client = TCP_Client()
                        message = self.tcp_client.build_tcp_message("/control/client/reload_display_template", {"device_id" : device_id}, None)
                        response = self.tcp_client.tcp_send(server_ip, 1339, message)
                        self.logger.debug(f"Response from Server: {response}")

                else:
                        self.logger.error(f"Server IP address not set, please set in config tool.")

        except Exception as e:
            self.logger.error(f"Cannot send Reload Message to server: {e}")
            
    def __identify_device(self, state:bool):
        try:
            #Get the devices IP
            device_id = self.get_device_id()
            if device_id != None:

                #Read the Server Settings file
                settings_dict = open_json_file("server/settings.json")

                #Only send a command to the server if it has an ip set
                if settings_dict != False:
                        server_ip = (settings_dict["server_ip"])

                        if state == True:
                            frame = "identify"
                        else:
                            frame = "OATIS"

                        #Send the raise frame command to the server
                        self.tcp_client = TCP_Client()
                        message = self.tcp_client.build_tcp_message("/control/client/identify", {"device_id" : device_id, "frame" : frame}, None)
                        response = self.tcp_client.tcp_send(server_ip, 1339, message)
                        self.logger.debug(f"Response from Server: {response}")

                else:
                        self.logger.error(f"Server IP address not set, please set in config tool.")

        except Exception as e:
            self.logger.error(f"Cannot send Identify Message to server: {e}")

class Controller_Config(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("Controller Name:", "text_entry", "not_null")
        self.controller_name_input_widget_index = 0
        row2 = Input_Row("Location:", "text_entry", "not_null")
        self.location_input_widget_index = 1
        row3= Input_Row("Type:", "combobox", "not_null")
        self.type_input_widget_index = 2
        row4= Input_Row("Port", "combobox", "not_null")
        self.port_input_widget_index = 3
        row5 = Input_Row("Pin Mode Configuration", "title", "n/a")

        row6 = Input_Row(None, "gpio_pin_config", "n/a")
        self.gpio_pin_config_index = 5

        row_list = [row1, row2, row3, row4, row5, row6]

        #Initialise the Base Frame with the above rows
        self.build_gui("GPIO Config", "controllers", "controller_name", "controller_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Overriding the default delete command in base frame for proper handling of foreign key references
        self.set_delete_btn_command(self.del_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.__set_type_combobox_values()
        self.__set_port_combobox_values()
        self.update_tree()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        self.input_frame.set_combobox_command(self.type_input_widget_index, self.__build_gpio_pin_window)
        
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            controller_name = input_data_list[self.controller_name_input_widget_index]
            controller_location :str = input_data_list[self.location_input_widget_index]
            controller_type = input_data_list[self.type_input_widget_index]
            controller_port = input_data_list[self.port_input_widget_index]
            pin_config_list = input_data_list[self.gpio_pin_config_index]

            #Save the data to the database
            successful_save = self.__save_input_data(controller_name, controller_location, controller_type, controller_port, pin_config_list)

            self.update_tree()

            if successful_save == True:

                #Clear All entry Widgets
                self.input_frame.clear_all_entries()

                #Set the state indicator to true - no tree item is selected
                self.set_new_item_state(True)

                #Update the port combobox values
                self.__set_port_combobox_values()

                self.logger.info("Saved Input Data to Database")

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Called when delete button is clicked
    def del_btn_cmd(self):
        """Custom delete function instead of using the one in BaseFrame, 
        this is to handle deletion of Foreign key references properly."""
        self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
        #Get the DB id of the selected treeview item
        in_focus_db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

        if in_focus_db_id != None:
            #Confirm with the user they want to delete
            confirmation = confirm_delete()
            if confirmation == True:
                #Check GPIO Pins are not in use by any input triggers
                controller_references = self.db.get_1column_data("input_trigger_id", "input_triggers", "controller_id", in_focus_db_id)

                #If no references, start deletion
                if controller_references == []:
                
                    #Delete mappping Foreign Key references
                    feedback = self.db.delete_row("pin_modes", "controller_id", in_focus_db_id)
                    
                    if feedback == True:
                        #Delete the item
                        self.db.delete_row(self.table, self.id_column, in_focus_db_id)
                        self.logger.info(f"Deleted rows with {self.id_column}: {in_focus_db_id} in table {self.table}")

                        #Clear the input widgets
                        self.input_frame.clear_all_entries()

                        #Set the State indicator to True
                        self.set_new_item_state(True)

                        #Update the tree
                        self.update_tree()

                        #Update the port combobox values
                        self.__set_port_combobox_values()
                        
                    else:
                        #Warn the user the item cannot be deleted to maintain database integrity
                        delete_warning(feedback)
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    delete_warning(f"Cannot delete Controller, in use by input triggers:{controller_references}")

    #Save input data to the database
    def __save_input_data(self, controller_name, controller_location, controller_type, controller_port, pin_config_list):
        """Saves input data to the database."""
        #Variable returned when this function completes, signals is there were any errors saving
        save_successful = True

        #--------------------------------Saving a new item--------------------------------
        if self.new_item == True:
            self.logger.info("Saving new item to the database")
            self.__save_new_item(controller_name, controller_location ,controller_port, controller_type, pin_config_list)

        #--------------------------------Updating an existing item--------------------------------
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            #Update the name location and port
            self.db.update_row(self.table, "controller_name", self.id_column, controller_name, db_id)
            self.db.update_row(self.table, "controller_location", self.id_column, controller_location, db_id)
            self.db.update_row(self.table, "controller_port", self.id_column, controller_port, db_id)

            #Get the controller_type from the database for comparison
            current_controller_type = self.db.get_1column_data("controller_type", "controllers", "controller_id", db_id)[0]

            #--------------------------------controller type is unchanged--------------------------------
            if controller_type == current_controller_type:
                self.logger.debug("Controller Type Unchanged")

                #Update the pin modes - if any failed to update theyre ids are returned as a list
                failed_update_pins = self.__save_pin_modes(pin_config_list, db_id)
                if failed_update_pins != []:
                    save_successful = False
            #--------------------------------controller type is modified--------------------------------
            else:
                self.logger.debug("Controller Type Modified")

                #Check if any of the pins are currently in use
                in_use_status, in_use_pin_list = self.__check_pins_in_use(db_id)
                self.logger.debug(f"Pins In use: {in_use_status}")

                #If the pins are in use prompt the user and stop updating
                if in_use_status == True:
                    pin_modify_warning(in_use_pin_list)
                    save_successful = False

                #If the pins are not in use delete all pin_mappings and re-make
                else:
                    #Query the database for the pin_modes for the selected controller
                    pin_mode_list = self.db.get_rows_condition_sort_asc("pin_modes", "controller_id", db_id, "pin_id")

                    #Delete each pin_mapping
                    for pin in pin_mode_list:
                        pin_id = pin[1]
                        status = self.db.delete_row_dual_condition("pin_modes", "controller_id", db_id, "pin_id", pin_id)
                        self.logger.debug(f"Deleted Pin Mapping for pin {pin_id} for controller ID {db_id}, successful:{status}")

                    #Update the controller type
                    self.db.update_row(self.table, "controller_type", self.id_column, controller_type, db_id)

                    #Add the new Pin mappings
                    self.__add_new_pin_modes(db_id, controller_type, pin_config_list)


        return save_successful
    
    def __save_new_item(self, controller_name, controller_location ,controller_port, controller_type, pin_config_list:list):
        #Add the validated data to the database
        self.db.add_controller(controller_name, controller_location, None, controller_port, controller_type)

        #Get the id of the new controller
        controller_id = self.db.get_last_insert_row_id()

        #Add the new pin modes to the database
        self.__add_new_pin_modes(controller_id, controller_type, pin_config_list)

    def __add_new_pin_modes(self, controller_id, controller_type, pin_config_list:list):
        #Get the start and end pin indexes for the selected controller type
        controller_type_row = self.db.get_current_row_data("controller_types", "model", controller_type)[0]
        total_gpio_pins = controller_type_row[2]
        start_pin_index = controller_type_row[3]
        end_pin_index = controller_type_row[4]

        #Add pin modes to the database
        for i in range(0, total_gpio_pins):
            pin_id = pin_config_list[i][0]
            pin_mode = pin_config_list[i][1]
            self.db.add_pin_mode(controller_id, pin_id, pin_mode)
    
    def __save_pin_modes(self, pin_config_list:list, controller_id) -> list:
        #Any pins not updated will be referenced here
        self.pins_not_updated_list = []

        for pin_config_row in pin_config_list:
            pin_id = pin_config_row[0]
            pin_mode = pin_config_row[1]

            #Check if the value has changed
            database_pin_mode = self.db.get_1column_data_dual_condition("pin_mode", "controller_id", controller_id, "pin_id", pin_id, "pin_modes")[0]

            self.logger.debug(f"Pin:{pin_id}, selection: {pin_mode}, database: {database_pin_mode}")

            #If the pin_mode has changed
            if database_pin_mode != pin_mode:
                if database_pin_mode == "input":
                    #Check the pin is not currently configured as an input trigger
                    input_trigger_id_list = self.db.get_1column_data_dual_condition("input_trigger_id", "controller_id", controller_id, "address", pin_id, "input_triggers")
                    if input_trigger_id_list == []:
                        #Update the pin mode
                        self.logger.debug(f"Updating entry for pin:{pin_id}, with mode:{pin_mode}")
                        self.db.update_row_dual_condition("pin_modes", "pin_mode", pin_mode, "pin_id", pin_id, "controller_id", controller_id)
                    else:
                        self.pins_not_updated_list.append(pin_id)

                elif database_pin_mode == "output":
                    #Check the pin is not currently configured as an output trigger
                    output_trigger_id_list = self.db.get_1column_data_dual_condition("output_trigger_id", "controller_id", controller_id, "address", pin_id, "output_triggers")
                    if output_trigger_id_list == []:
                        #Update the pin mode
                        self.logger.debug(f"Updating entry for pin:{pin_id}, with mode:{pin_mode}")
                        self.db.update_row_dual_condition("pin_modes", "pin_mode", pin_mode, "pin_id", pin_id, "controller_id", controller_id)
                    else:
                        self.pins_not_updated_list.append(pin_id)

                elif database_pin_mode == "disabled":
                    #Update the pin mode
                    self.logger.debug(f"Updating entry for pin:{pin_id}, with mode:{pin_mode}")
                    self.db.update_row_dual_condition("pin_modes", "pin_mode", pin_mode, "pin_id", pin_id, "controller_id", controller_id)

                else:
                    self.logger.error(f"Invalid pin mode: {pin_mode} used in database for pin: {pin_id}")

            #If the pin mode has not changed, do nothing
            else:
                self.logger.debug(f"Pin mode for pin {pin_id} unchanged.")

        #If some pins failed to update, notify the user and return false
        if self.pins_not_updated_list != []:
            pin_modify_warning(self.pins_not_updated_list)

        return self.pins_not_updated_list
            
    def __check_pins_in_use(self, controller_id):
        """Checks if the pin mode mapings for a specified controller_id are configured in input or output triggers.
        Returns True if they are configured, Flase if not. Also returns a list of pins that are in use."""

        self.logger.debug(f"Checking if pins for controller id {controller_id} are currently in use")

        #Blank list to store pin_id's in use
        self.pins_in_use_list = []
            
        #Query the database for the pin_modes
        pin_mode_list = self.db.get_rows_condition_sort_asc("pin_modes", "controller_id", controller_id, "pin_id")

        for pin in pin_mode_list:
            pin_id = pin[1]
            pin_mode = pin[2]

            if pin_mode == "input":
                #Check the pin is not currently configured as an input trigger or output trigger
                input_trigger_id_list = self.db.get_1column_data_dual_condition("input_trigger_id", "controller_id", controller_id, "address", pin_id, "input_triggers")
                if input_trigger_id_list != []:
                    #Add the pin id to the in_use list
                    self.pins_in_use_list.append(pin_id)
                    
            elif pin_mode == "output":
                #Check the pin is not currently configured as an input trigger or output trigger
                output_trigger_id_list = self.db.get_1column_data_dual_condition("output_trigger_id", "controller_id", controller_id, "address", pin_id, "output_triggers")
                if output_trigger_id_list != []:
                    #Add the pin id to the in_use list
                    self.pins_in_use_list.append(pin_id)

        self.logger.debug(f"Pins Currently in use: {self.pins_in_use_list}")

        if self.pins_in_use_list != []:
            #Pins are in use
            return True ,self.pins_in_use_list
        else:
            #Pins are not in use
            return False ,self.pins_in_use_list

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            name = item_data_list[1]
            location = item_data_list[2]
            port = item_data_list[4]
            type = item_data_list[5]

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(name, location, type, port)

            #Query the database for pin modes for the selected controller
            pin_modes_list = self.db.get_rows_condition_sort_asc("pin_modes", "controller_id", db_id, "pin_id")
            self.logger.debug(f"Pin modes for selected controller:{pin_modes_list}")

            #Build the GPIO config window based on the type
            self.__build_gpio_pin_window("null_event")

            #Get the pin config widget frame
            pin_config : GPIO_Pin_Config = self.input_frame.get_widget_object(5)

            #Set the radio button selections based on the stored database values
            pin_config.set_data(pin_modes_list)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

#-------------------------------------------------------------------------------------------------------------------

    def __set_type_combobox_values(self):
        #Query the database
        controller_types_rows = self.db.get_current_table_data("controller_types")
        self.logger.debug(f"Controller_types_rows: {controller_types_rows}")

        #Remove the first row, this a system defualt row that mnust not be altered by the user
        controller_types_rows.pop(0)

        #Blank list to hold combobox values
        combobox_values = []

        #Extract the model from each row
        for row in controller_types_rows:
            combobox_values.append(row[1])

        #Set the values of the type combobox
        self.input_frame.set_combobox_values(self.type_input_widget_index, combobox_values)

    def __set_port_combobox_values(self):
        #Create a blank list to hold the serial ports
        self.serial_ports_list = []

        for port in comports():
            print(port)
            #Convert the ListPortInfo object to a string
            port_string = str(port)
            #Split the string to extract the address
            port_address = port_string.split()[0]

            #Query the database to find ports already configured
            query_result = self.db.get_1column_data("controller_id", "controllers", "controller_port", port_address)
            print(f"Query Result:{query_result}")

            if query_result == []:
                #Add the address to the list only if it's not already configured
                self.serial_ports_list.append(port_address)

        self.logger.info(f"Available serial ports:{self.serial_ports_list}")   

        #Set the values of the type combobox
        self.input_frame.set_combobox_values(self.port_input_widget_index, self.serial_ports_list)

    def __build_gpio_pin_window(self, event):
        """Builds the GPIO Config Frame depending on the controller type selected."""

        #Get the value in the type combobox
        controller_type = self.input_frame.get_data(2)
        self.logger.debug(f"Controller Type: {controller_type}")

        #Lookup the controller type to get the pin data
        pin_data = self.db.get_current_row_data("controller_types", "model", controller_type)[0]
        start_pin_index = pin_data[3]
        end_pin_index = pin_data[4]
        start_input_only_index = pin_data[5]
        end_input_only_index = pin_data[6]

        self.logger.debug(f"Pin data: {pin_data}")

        #Get the pin config widget frame
        pin_config : GPIO_Pin_Config = self.input_frame.get_widget_object(5)

        #Build the pin config rows
        pin_config.build_rows(start_pin_index, end_pin_index, start_input_only_index, end_input_only_index)
        
class Input_Triggers(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0
        row2 = Input_Row("Controller:", "combobox", "not_null")
        self.controller_input_widget_index = 1
        row3= Input_Row("Address:", "combobox", "not_null_osc_command_input_trigger")
        self.address_widget_index = 2

        row_list = [row1, row2, row3]

        #Initialise the Base Frame with the above rows
        self.build_gui("Input Triggers", "input_triggers", "input_trigger_name", "input_trigger_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_combobox_values()
        self.update_tree()
    
 
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        self.input_frame.set_combobox_command(self.controller_input_widget_index, self.__controller_combobox_callback)
        
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            input_trigger_name = input_data_list[self.name_input_widget_index]
            controller_id_name :str = input_data_list[self.controller_input_widget_index]
            controller_id = controller_id_name.split(":")[0]
            address = input_data_list[self.address_widget_index]

            #Save the data to the database
            self.__save_input_data(input_trigger_name, controller_id, address, False)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Save input data to the database
    def __save_input_data(self, input_trigger_name, controller_id, address, state):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Add the validated data to the database
            self.db.add_input_trigger(input_trigger_name, controller_id, address, state)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            self.db.update_row(self.table, "input_trigger_name", self.id_column, input_trigger_name, db_id)
            self.db.update_row(self.table, "controller_id", self.id_column, controller_id, db_id)
            self.db.update_row(self.table, "address", self.id_column, address, db_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            name = item_data_list[1]
            controller_id = item_data_list[2]
            address = item_data_list[3]

            #Get the name of the controller from the database
            controller_name = self.db.get_1column_data("controller_name", "controllers", "controller_id", controller_id)[0]

            #Combine the controller id and name together
            controller_id_name = f"{controller_id}:{controller_name}"

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(name, controller_id_name, address)
            
            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            #Set the values of the address combobox
            self.__set_address_combobox_values()

            #Set address combobox read only state
            self.__set_address_combobox_state()

            self.logger.info("Updated Input widgets")

#-------------------------------------------------------------------------------------------------------------------

    def __set_address_combobox_values(self):
        """Sets the address combobox values when the controller combobox value has been selected."""

        #Retrieve the controller combobox selected value
        selected_controller:str = self.input_frame.get_data(self.controller_input_widget_index)
        selected_controller_id, selected_controller_name = selected_controller.split(":")

        #If selected controller id is 0, this is the network controller, address combobox can therefore be free-text enabled.
        if selected_controller_id == "0":
            self.input_frame.set_combobox_values(self.address_widget_index, [])

        else:
            #Lookup which pins are configured as inputs for the selected controller
            self.logger.debug(f"Looking up configured input pins for selected controller.")
            input_pins_int_list = self.db.get_1column_data_dual_condition("pin_id", "controller_id", selected_controller_id, "pin_mode", "input", "pin_modes")

            #Convert the pin integers to strings
            input_pins_list = []
            for input_pin_int in input_pins_int_list:
                input_pins_list.append(str(input_pin_int))

            #Lookup if any of these pins have already been configured in another input trigger
            configured_pins_list = self.db.get_1column_data("address", "input_triggers", "controller_id", selected_controller_id)
            self.logger.debug(f"Pins already assigned to input triggers: {configured_pins_list}")
            
            #Remove assigned pins from the input_pins list
            for pin_id in configured_pins_list:
                input_pins_list.remove(pin_id)

            self.logger.debug(f"{selected_controller_name} has input pins: {input_pins_int_list}, Pin's: {input_pins_list} are available to be assigned to an input trigger.")
            self.input_frame.set_combobox_values(self.address_widget_index, input_pins_list)
    
    def __set_address_combobox_state(self):
        """Sets the readonly state of the address combobox based on the value selected in the controller combobox."""

        #Get the current value in the controller combobox
        controller_id_name = self.input_frame.get_data(1)

        if controller_id_name == "0:Network":
            #Set readonly state to false
            self.input_frame.change_combobox_readonly_state(self.address_widget_index, "normal")
            self.logger.debug(f"Set Address Combobox to readonly state to False")
        else:
            #Set readonly state to true
            self.input_frame.change_combobox_readonly_state(self.address_widget_index, "readonly")
            self.logger.debug(f"Set Address Combobox to readonly state to True")
        
    def __controller_combobox_callback(self, event):
        """Calback called when the controller combobox value is selected."""
        #Clear the Address Combobox
        self.input_frame.clear_entry(self.address_widget_index)

        #Set the values of the address combobox
        self.__set_address_combobox_values()

        #Set address combobox read only state
        self.__set_address_combobox_state()

    def update_combobox_values(self):
        """Set the selection list of values for the comboboxes."""

        #Blank list to hold concatenated id and controller names
        combobox_values = []

        #Query the database
        controller_list = self.db.get_2column_data("controller_id", "controller_name", "controllers")

        #Extract the id and name of each controller and then concatenate into a single string
        for controller in controller_list:
            id = controller[0]
            name = controller[1]
            combined = f"{id}:{name}"
            combobox_values.append(combined)

        self.set_combobox_values(self.controller_input_widget_index, combobox_values)

class Input_Logics(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)
    
        #Rows to make in the frame
        row1 = Input_Row("Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0

        row2 = Input_Row("High Condition:", "combobox", "not_null")
        self.high_condition_widget_index = 1

        row3 = Input_Row("Source Input Triggers", "title", "n/a")
        
        row4 = Input_Row(None, "dual_selection_columns", "n/a", ["Input Triggers", "Active Input Triggers"])
        self.dual_selection_columns_index = 3
        
        row_list = [row1, row2, row3, row4]

        #Initialise the Base Frame with the above rows
        self.build_gui("Input Logics", "input_logics", "input_logic_name", "input_logic_id", row_list)

        #Hard coding combobox values for high_condition, these do not change.
        self.set_combobox_values(1 ,["AND", "NAND", "OR", "NOR"])

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)
        #Overriding the default delete command in base frame for proper handling of foreign key references
        self.set_delete_btn_command(self.del_btn_cmd)

        #Set on raise callback - this is the callback triggered when this frame is raised to the top
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Set widget Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

        #Update the selection tree with current data
        self.__update_selection_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    #This function is called by the GUI  Menu Buttons when this frame is selected
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_tree()
        self.__update_selection_tree()

    def __set_bindings(self):
        """Sets callbacks for widgets."""

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            input_logic_name = input_data_list[self.name_input_widget_index]
            high_condition = input_data_list[self.high_condition_widget_index]
            input_trigger_list = input_data_list[self.dual_selection_columns_index]

            #Save the data to the database
            self.__save_input_data(input_logic_name, high_condition, input_trigger_list)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    def del_btn_cmd(self):
          """Custom delete function instead of using the one in BaseFrame, 
          this is to handle deletion of Foreign key references properly."""
          self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
          #Get the DB id of the selected treeview item
          in_focus_db_id = self.tree.get_in_focus_item_db_id()
          self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

          if in_focus_db_id != None:
               #Confirm with the user they want to delete
               confirmation = confirm_delete()

               if confirmation == True:
                    #Check not in use by a widget
                    widget_feedback = True
                    rows = self.db.get_current_row_data("indicator", "input_logic_id", in_focus_db_id)

                    if rows != []:
                        widget_feedback = False
                            

                    if widget_feedback == True:
                        #Delete mappping Foreign Key references
                        feedback = self.db.delete_row("input_logic_mapping", "input_logic_id", in_focus_db_id)
                    
                        if feedback == True:
                            #Delete the item
                            feedback = self.db.delete_row(self.table, self.id_column, in_focus_db_id)

                            if feedback == True:
                                self.logger.info(f"Deleted rows with {self.id_column}: {in_focus_db_id} in table {self.table}")

                                #Clear the input widgets
                                self.input_frame.clear_all_entries()

                                #Set the State indicator to True
                                self.set_new_item_state(True)

                                #Update the tree
                                self.update_tree()

                            else:
                                #Warn the user the item cannot be deleted to maintain database integrity
                                delete_warning(feedback)

                        else:
                            #Warn the user the item cannot be deleted to maintain database integrity
                            delete_warning(feedback)

                    else:
                         #Warn the user the item cannot be deleted to maintain database integrity
                         delete_warning("Input Logic in use by a widget instance.")

    #Save input data to the database
    def __save_input_data(self, input_logic_name, high_condition, input_triggers_list):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Add the validated data to the database
            self.db.add_input_logic(input_logic_name, high_condition)

            #Get the id of the newly added row
            #row_id = self.db.get_1column_data("input_logic_id", "input_logics", "input_logic_name", input_logic_name)[0]
            db_id = self.db.get_last_insert_row_id()
            self.logger.debug(f"Input Logic saved, database ID: {db_id}")

            #Add the input logic mappings
            for mapping in input_triggers_list:
                input_logic_id :str = db_id
                input_trigger_id = mapping[0]
                self.db.add_input_logic_mapping(input_logic_id, input_trigger_id)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            #Update the input logic row
            self.logger.debug(f"Updating Input Logics Row with id {db_id}")
            self.db.update_row(self.table, "input_logic_name", self.id_column, input_logic_name, db_id)
            self.db.update_row(self.table, "high_condition", self.id_column, high_condition, db_id)

            #Update the Input Logic mappings
            self.logger.debug(f"Retrieving Input logic mappings for Input Logic {db_id}")
            db_mappings_list : list = self.db.get_1column_data("input_trigger_id", "input_logic_mapping", "input_logic_id", db_id)
            add_mappings_list : list = []

            self.logger.debug(f"Comparing Database mappings with those currently selected by the user.")
            for mapping in input_triggers_list:
                input_trigger_id = mapping[0]
                if input_trigger_id in db_mappings_list:
                    db_mappings_list.remove(input_trigger_id)
                else:
                    add_mappings_list.append(input_trigger_id)

            remove_mappings_list = db_mappings_list

            #Add
            self.logger.debug(f"Adding new mappings to the database")
            for input_trigger_id in add_mappings_list:
                self.logger.debug(f"Adding mapping with Input Logic ID {db_id} and Input Trigger ID {input_trigger_id}")
                self.db.add_input_logic_mapping(db_id, input_trigger_id)
            #Remove
            self.logger.debug("Removing redundant mappings from the database")
            for input_trigger_id in remove_mappings_list:
                self.logger.debug(f"Removing mapping with Input Logic ID {db_id} and Input Trigger ID {input_trigger_id}")
                self.db.delete_row_dual_condition("input_logic_mapping", "input_logic_id", db_id, "input_trigger_id", input_trigger_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            name = item_data_list[1]
            high_condition = item_data_list[2]

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(name, high_condition)

            #Get the input trigger mappings from the database
            self.logger.debug(f"Retrieving Input trigger mappings for Input_Logic {db_id}")
            input_trigger_id_list = self.db.get_1column_data("input_trigger_id", "input_logic_mapping", "input_logic_id", db_id)

            #Get the name of each Input Trigger ID and add to a list
            input_trigger_name_list = []
            for input_trigger_id in input_trigger_id_list:
                self.logger.debug(f"Looking up name associated to Input Trigger ID: {input_trigger_id}")
                input_trigger_name = self.db.get_1column_data("input_trigger_name", "input_triggers", "input_trigger_id", input_trigger_id)[0]
                input_trigger_name_list.append(input_trigger_name)

            #Combine the id and name lists
            self.logger.debug(f"Combining ID an Name lists")
            input_trigger_id_name_list = combine_lists(input_trigger_id_list, input_trigger_name_list)
            self.logger.debug(f"Combined List result: {input_trigger_id_name_list}")

            #Add the mappings to the selection column tree
            self.logger.debug(f"Updating Selection Column with combined list data.")
            dual_selection_column_widget :Dual_Selection_Columns = self.input_frame.get_widget_object(self.dual_selection_columns_index)
            dual_selection_column_widget.set_column_values(1, input_trigger_id_name_list)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

#-------------------------------------------------------------------------------------------------------------------

    def __update_selection_tree(self):
        """Updates the Dual Selection Tree with current database values."""
        self.logger.debug("Updating the Dual Selection Tree with current database values.")
        dual_selection_column_widget :Dual_Selection_Columns = self.input_frame.get_widget_object(self.dual_selection_columns_index)
        
        input_trigger_rows = self.db.get_2column_data("input_trigger_id", "input_trigger_name", "input_triggers")
        dual_selection_column_widget.set_column_values(0, input_trigger_rows)
 
class Output_Logics(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)
    
        #Rows to make in the frame
        row1 = Input_Row("Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0

        row2 = Input_Row("Source Input Logic:", "combobox", "not_null")
        self.source_input_logic_widget_index = 1

        row3 = Input_Row("Target Output Triggers", "title", "n/a")
        
        row4 = Input_Row(None, "dual_selection_columns", "n/a", ["Output Triggers", "Active Output Triggers"])
        self.dual_selection_columns_index = 3
        
        row_list = [row1, row2, row3, row4]

        #Initialise the Base Frame with the above rows
        self.build_gui("Output Logics", "output_logics", "output_logic_name", "output_logic_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)
        #Overriding the default delete command in base frame for proper handling of foreign key references
        self.set_delete_btn_command(self.del_btn_cmd)

        #Set on raise callback - this is the callback triggered when this frame is raised to the top
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Set widget Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

        #Update the selection tree with current data
        self.__update_selection_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    #This function is called by the GUI  Menu Buttons when this frame is selected
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_tree()
        self.update_combobox_values()
        self.__update_selection_tree()

    def __set_bindings(self):
        """Sets callbacks for widgets."""

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            input_logic_name = input_data_list[self.name_input_widget_index]
            source_input_logic_id_name = input_data_list[self.source_input_logic_widget_index]
            source_input_logic_id = source_input_logic_id_name.split(":")[0]
            output_trigger_list = input_data_list[self.dual_selection_columns_index]

            #Save the data to the database
            self.__save_input_data(input_logic_name, source_input_logic_id, output_trigger_list, False)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    def del_btn_cmd(self):
          """Custom delete function instead of using the one in BaseFrame, 
          this is to handle deletion of Foreign key references properly."""
          self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
          #Get the DB id of the selected treeview item
          in_focus_db_id = self.tree.get_in_focus_item_db_id()
          self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

          if in_focus_db_id != None:
               #Confirm with the user they want to delete
               confirmation = confirm_delete()
               if confirmation == True:
                    
                    #Delete mappping Foreign Key references
                    feedback = self.db.delete_row("output_logic_mapping", "output_logic_id", in_focus_db_id)
                    
                    if feedback == True:
                        #Delete the item
                        self.db.delete_row(self.table, self.id_column, in_focus_db_id)
                        self.logger.info(f"Deleted rows with {self.id_column}: {in_focus_db_id} in table {self.table}")

                        #Clear the input widgets
                        self.input_frame.clear_all_entries()

                        #Set the State indicator to True
                        self.set_new_item_state(True)

                        #Update the tree
                        self.update_tree()
                    else:
                         #Warn the user the item cannot be deleted to maintain database integrity
                         delete_warning(feedback)

    #Save input data to the database
    def __save_input_data(self, output_logic_name, source_input_logic_id, output_triggers_list, state):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Add the validated data to the database
            self.logger.debug(f"Output Logic Name: {output_logic_name}, Input_logic_id:{source_input_logic_id}, state:{state}")
            self.db.add_output_logic(output_logic_name, source_input_logic_id, state)

            #Get the id of the newly added row
            db_id = self.db.get_last_insert_row_id()
            self.logger.debug(f"Output Logic saved, database ID: {db_id}")

            #Add the output logic mappings
            for mapping in output_triggers_list:
                output_logic_id :str = db_id
                output_trigger_id = mapping[0]
                self.db.add_output_logic_mapping(output_logic_id, output_trigger_id)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            #Update the output logic row
            self.logger.debug(f"Updating Input Logics Row with id {db_id}")
            self.db.update_row(self.table, "output_logic_name", self.id_column, output_logic_name, db_id)
            self.db.update_row(self.table, "input_logic_id", self.id_column, source_input_logic_id, db_id)

            #Update the Output Logic mappings
            self.logger.debug(f"Retrieving Output logic mappings for Output Logic {db_id}")
            db_mappings_list : list = self.db.get_1column_data("output_trigger_id", "output_logic_mapping", "output_logic_id", db_id)
            add_mappings_list : list = []

            self.logger.debug(f"Comparing Database mappings with those currently selected by the user.")
            for mapping in output_triggers_list:
                output_trigger_id = mapping[0]
                if output_trigger_id in db_mappings_list:
                    db_mappings_list.remove(output_trigger_id)
                else:
                    add_mappings_list.append(output_trigger_id)

            remove_mappings_list = db_mappings_list

            #Add
            self.logger.debug(f"Adding new mappings to the database")
            for output_trigger_id in add_mappings_list:
                self.logger.debug(f"Adding mapping with Output Logic ID {db_id} and Output Trigger ID {output_trigger_id}")
                self.db.add_output_logic_mapping(db_id, output_trigger_id)
            #Remove
            self.logger.debug("Removing redundant mappings from the database")
            for output_trigger_id in remove_mappings_list:
                self.logger.debug(f"Removing mapping with Output Logic ID {db_id} and Output Trigger ID {output_trigger_id}")
                self.db.delete_row_dual_condition("output_logic_mapping", "output_logic_id", db_id, "output_trigger_id", output_trigger_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            name = item_data_list[1]
            source_input_logic_id = item_data_list[2]

            #Get the source input_logic_name
            source_input_logic_name = self.db.get_1column_data("input_logic_name", "input_logics", "input_logic_id", source_input_logic_id)[0]

            #Combine the input_logic id and name together
            source_input_logic_id_name = f"{source_input_logic_id}:{source_input_logic_name}"

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(name, source_input_logic_id_name)

            #Get the output trigger mappings from the database
            self.logger.debug(f"Retrieving Output trigger mappings for Output_Logic {db_id}")
            output_trigger_id_list = self.db.get_1column_data("output_trigger_id", "output_logic_mapping", "output_logic_id", db_id)

            #Get the name of each Output Trigger ID and add to a list
            output_trigger_name_list = []
            for output_trigger_id in output_trigger_id_list:
                self.logger.debug(f"Looking up name associated to Output Trigger ID: {output_trigger_id}")
                output_trigger_name = self.db.get_1column_data("output_trigger_name", "output_triggers", "output_trigger_id", output_trigger_id)[0]
                output_trigger_name_list.append(output_trigger_name)

            #Combine the id and name lists
            self.logger.debug(f"Combining ID an Name lists")
            output_trigger_id_name_list = combine_lists(output_trigger_id_list, output_trigger_name_list)
            self.logger.debug(f"Combined List result: {output_trigger_id_name_list}")

            #Add the mappings to the selection column tree
            self.logger.debug(f"Updating Selection Column with combined list data.")
            dual_selection_column_widget :Dual_Selection_Columns = self.input_frame.get_widget_object(self.dual_selection_columns_index)
            dual_selection_column_widget.set_column_values(1, output_trigger_id_name_list)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

#-------------------------------------------------------------------------------------------------------------------

    def __update_selection_tree(self):
        """Updates the Dual Selection Tree with current database values."""
        self.logger.debug("Updating the Dual Selection Tree with current database values.")
        dual_selection_column_widget :Dual_Selection_Columns = self.input_frame.get_widget_object(self.dual_selection_columns_index)
        
        output_trigger_rows = self.db.get_2column_data("output_trigger_id", "output_trigger_name", "output_triggers")
        dual_selection_column_widget.set_column_values(0, output_trigger_rows)            

    def update_combobox_values(self):
        """Set the selection list of values for the comboboxes."""

        #Blank list to hold concatenated id and controller names
        combobox_values = []

        #Query the database
        input_logic_list = self.db.get_2column_data("input_logic_id", "input_logic_name", "input_logics")

        #Extract the id and name of each controller and then concatenate into a single string
        for input_logic in input_logic_list:
            id = input_logic[0]
            name = input_logic[1]
            combined = f"{id}:{name}"
            combobox_values.append(combined)

        self.set_combobox_values(self.source_input_logic_widget_index, combobox_values)

class Output_Triggers(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0
        row2 = Input_Row("Type:", "combobox", "not_null")
        self.type_input_widget_index = 1
        row3= Input_Row("Controller:", "combobox", "not_null")
        self.controller_input_widget_index = 2
        row4= Input_Row("GPO Config:", "title", "n/a")

        row5= Input_Row("Address:", "combobox", "not_null")
        self.address_input_widget_index = 4
        row6= Input_Row("OSC Output Config:", "title", "n/a")

        row7= Input_Row("IP Address:", "text_entry", "not_null_ip_address_or_n/a")
        self.ip_input_widget_index = 6
        row8= Input_Row("Port:", "text_entry", "not_null")
        self.port_input_widget_index = 7
        row9= Input_Row("Protocol:", "combobox", "not_null")
        self.protocol_input_widget_index = 8
        
        row10= Input_Row("OSC Output on High:", "title", "n/a")

        row11= Input_Row("Command:", "text_entry", "null_or_osc_command")
        self.command_high_input_widget_index = 10
        row12= Input_Row("Arguments:", "text_entry", "null_or_osc_args")
        self.arguments_high_input_widget_index = 11

        row13= Input_Row("OSC Output on Low:", "title", "n/a")

        row14= Input_Row("Command:", "text_entry", "null_or_osc_command")
        self.command_low_input_widget_index = 13
        row15= Input_Row("Arguments:", "text_entry", "null_or_osc_args")
        self.arguments_low_input_widget_index = 14

        row_list = [row1, row2, row3, row4, row5, row6, row7, row8, row9, row10, row11, row12, row13, row14, row15]

        #Initialise the Base Frame with the above rows
        self.build_gui("Output Triggers", "output_triggers", "output_trigger_name", "output_trigger_id", row_list)

        #Hard coding combobox values for type and protocol these do not change.
        self.set_combobox_values(self.type_input_widget_index ,["Network", "GPO"])
        self.set_combobox_values(self.protocol_input_widget_index ,["UDP", "TCP"])

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

    #-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_combobox_values()
        self.update_tree()

    def __set_bindings(self):
        """Sets callbacks for widgets."""
        self.input_frame.set_combobox_command(self.type_input_widget_index, self.__type_combobox_callback)
        self.input_frame.set_combobox_command(self.controller_input_widget_index, self.__controller_combobox_callback)
        
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            output_trigger_name = input_data_list[self.name_input_widget_index]
            output_type = input_data_list[self.type_input_widget_index]
            controller_id_name : str = input_data_list[self.controller_input_widget_index]
            controller_id = controller_id_name.split(":")[0]
            address = input_data_list[self.address_input_widget_index]
            ip_address = input_data_list[self.ip_input_widget_index]
            port = input_data_list[self.port_input_widget_index]
            protocol = input_data_list[self.protocol_input_widget_index]
            command_high = input_data_list[self.command_high_input_widget_index]
            arguments_high = input_data_list[self.arguments_high_input_widget_index]
            command_low = input_data_list[self.command_low_input_widget_index]
            arguments_low = input_data_list[self.arguments_low_input_widget_index]

            #Save the data to the database
            self.__save_input_data(output_trigger_name, output_type, controller_id, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Save input data to the database
    def __save_input_data(self, output_trigger_name, output_type, controller_id, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Add the validated data to the database
            self.db.add_output_trigger(output_trigger_name, output_type, controller_id, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            self.db.update_row(self.table, "output_trigger_name", self.id_column, output_trigger_name, db_id)
            self.db.update_row(self.table, "output_type", self.id_column, output_type, db_id)
            self.db.update_row(self.table, "controller_id", self.id_column, controller_id, db_id)
            self.db.update_row(self.table, "address", self.id_column, address, db_id)
            self.db.update_row(self.table, "ip_address", self.id_column, ip_address, db_id)
            self.db.update_row(self.table, "port", self.id_column, port, db_id)
            self.db.update_row(self.table, "protocol", self.id_column, protocol, db_id)
            self.db.update_row(self.table, "command_high", self.id_column, command_high, db_id)
            self.db.update_row(self.table, "arguments_high", self.id_column, arguments_high, db_id)
            self.db.update_row(self.table, "command_low", self.id_column, command_low, db_id)
            self.db.update_row(self.table, "arguments_low", self.id_column, arguments_low, db_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            output_trigger_name = item_data_list[1]
            output_type = item_data_list[2]
            controller_id = item_data_list[3]
            address = item_data_list[4]
            ip_address = item_data_list[5]
            port = item_data_list[6]
            protocol = item_data_list[7]
            command_high = item_data_list[8]
            arguments_high = item_data_list[9]
            command_low = item_data_list[10]
            arguments_low = item_data_list[11]

            #Get the name of the controller from the database
            controller_name = self.db.get_1column_data("controller_name", "controllers", "controller_id", controller_id)[0]

            #Combine the controller id and name together
            controller_id_name = f"{controller_id}:{controller_name}"

            #Set the type
            self.input_frame.set_data(self.type_input_widget_index, output_type)

            #Set the OSC Config widgets state
            self.__type_combobox_callback(None)

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(output_trigger_name, output_type, controller_id_name, address, ip_address, port, protocol, command_high, arguments_high, command_low, arguments_low)
            
            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            #Set the values of the address combobox
            self.__set_address_combobox_values()

            #Set address combobox read only state
            self.__set_address_combobox_state()

            self.logger.info("Updated Input widgets")

    #-------------------------------------------------------------------------------------------------------------------
    def update_combobox_values(self):
        """Set the selection list of values for the comboboxes."""

        #Blank list to hold concatenated id and controller names
        combobox_values = []

        #Query the database
        controller_list = self.db.get_2column_data("controller_id", "controller_name", "controllers")

        #Extract the id and name of each controller and then concatenate into a single string
        for controller in controller_list:
            id = controller[0]
            name = controller[1]
            combined = f"{id}:{name}"
            combobox_values.append(combined)

        self.set_combobox_values(self.controller_input_widget_index, combobox_values)

    def __type_combobox_callback(self, event):
        """Calback called when the type combobox value is selected. Disables and enables the appropriate widgets based on selection."""
        #Get the current selection from the type combobox
        input_type :str = self.input_frame.get_data(self.type_input_widget_index)

        #Clear all widgets below the type combobox
        self.input_frame.clear_entry(self.controller_input_widget_index)
        self.input_frame.clear_entry(self.address_input_widget_index)
        self.input_frame.clear_entry(self.ip_input_widget_index)
        self.input_frame.clear_entry(self.port_input_widget_index)
        self.input_frame.clear_entry(self.protocol_input_widget_index)
        self.input_frame.clear_entry(self.command_high_input_widget_index)
        self.input_frame.clear_entry(self.arguments_high_input_widget_index)
        self.input_frame.clear_entry(self.command_low_input_widget_index)
        self.input_frame.clear_entry(self.arguments_low_input_widget_index)

        #Set the values of the controller combobox
        self.__set_controller_combobox_values(input_type)

        if input_type == "Network":
            self.input_frame.change_combobox_readonly_state(self.address_input_widget_index, "disabled")
            self.input_frame.set_data(self.address_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.ip_input_widget_index, "normal")
            self.input_frame.change_entry_readonly_state(self.port_input_widget_index, "normal")
            self.input_frame.change_combobox_readonly_state(self.protocol_input_widget_index, "readonly")
            self.input_frame.change_entry_readonly_state(self.command_high_input_widget_index, "normal")
            self.input_frame.change_entry_readonly_state(self.arguments_high_input_widget_index, "normal")
            self.input_frame.change_entry_readonly_state(self.command_low_input_widget_index, "normal")
            self.input_frame.change_entry_readonly_state(self.arguments_low_input_widget_index, "normal")
        elif input_type == "GPO":
            self.input_frame.change_combobox_readonly_state(self.address_input_widget_index, "readonly")
            self.input_frame.change_entry_readonly_state(self.ip_input_widget_index, "disabled")
            self.input_frame.set_data(self.ip_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.port_input_widget_index, "disabled")
            self.input_frame.set_data(self.port_input_widget_index, "N/A")
            self.input_frame.change_combobox_readonly_state(self.protocol_input_widget_index, "disabled")
            self.input_frame.set_data(self.protocol_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.command_high_input_widget_index, "disabled")
            self.input_frame.set_data(self.command_high_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.arguments_high_input_widget_index, "disabled")
            self.input_frame.set_data(self.arguments_high_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.command_low_input_widget_index, "disabled")
            self.input_frame.set_data(self.command_low_input_widget_index, "N/A")
            self.input_frame.change_entry_readonly_state(self.arguments_low_input_widget_index, "disabled")
            self.input_frame.set_data(self.arguments_low_input_widget_index, "N/A")
        else:
            self.logger.error(f"Invalid input type specified:{input_type}")

    def __set_controller_combobox_values(self, input_type :str):
        """Sets the values for the controller combobox based on the type selection."""

        #Query the database to get all controllers
        controller_list = self.db.get_2column_data("controller_id", "controller_name", "controllers")

        #Blank list to hold concatenated id and controller names
        controller_id_name_list = []

        #Extract the id and name of each controller and then concatenate into a single string
        for controller in controller_list:
            id = controller[0]
            name = controller[1]
            combined = f"{id}:{name}"
            controller_id_name_list.append(combined)

        #If the selection is Netowork
        if input_type == "Network":
            #Set the controller combobox to 0:Network
            self.input_frame.set_data(self.controller_input_widget_index, controller_id_name_list[0])
            self.set_combobox_values(self.controller_input_widget_index, "")

        #If the selection is GPO
        else:
            #Extract the rest of the controllers from the list, negating the network controller
            controller_list_length = len(controller_id_name_list)
            physical_controller_id_name_list = controller_id_name_list[1:controller_list_length:1]

            #Set the combobox values
            self.set_combobox_values(self.controller_input_widget_index, physical_controller_id_name_list)

    def __controller_combobox_callback(self, event):
        #Clear the address combobox
        self.input_frame.clear_entry(self.address_input_widget_index)

        #Set the values of the address combobox
        self.__set_address_combobox_values()

    def __set_address_combobox_values(self):
        #Get the current value from the controller combobox
        controller_id_name : str = self.input_frame.get_data(self.controller_input_widget_index)
        controller_id = controller_id_name.split(":")[0]

        #If the network controller is not selected
        if controller_id != "0":
            #Lookup configured output pin ids for selected controller
            output_pins_int_list = self.db.get_1column_data_dual_condition("pin_id", "controller_id", controller_id, "pin_mode", "output", "pin_modes")
            self.logger.debug(f"Output Addresses associated with controller_id {controller_id} : {output_pins_int_list}")

            #Convert the pin integers to strings
            output_pins_list = []
            for output_pin_int in output_pins_int_list:
                output_pins_list.append(str(output_pin_int))

            #Lookup if any of these pins have already been configured in another output trigger
            configured_pins_list = self.db.get_1column_data("address", "output_triggers", "controller_id", controller_id)
            self.logger.debug(f"Pins already assigned to output triggers: {configured_pins_list}")
            
            #Remove assigned pins from the output_pins list
            for pin_id in configured_pins_list:
                output_pins_list.remove(pin_id)
        
        #If the network controller is selected
        else:
            output_pins_list = []

        #Set the address combobox values
        self.set_combobox_values(self.address_input_widget_index, output_pins_list)

    def __set_address_combobox_state(self):
        """Sets the readonly state of the address combobox based on the value selected in the controller combobox."""

        #Get the current value in the controller combobox
        controller_id_name = self.input_frame.get_data(self.controller_input_widget_index)

        if controller_id_name == "0:Network":
            #Set readonly state to false
            self.input_frame.change_combobox_readonly_state(self.address_input_widget_index, "disabled")
            self.logger.debug(f"Set Address Combobox to state to disabled")
        else:
            #Set readonly state to true
            self.input_frame.change_combobox_readonly_state(self.address_input_widget_index, "readonly")
            self.logger.debug(f"Set Address Combobox to  state to readonly")
        
class Display_Templates(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

         #Rows to make in the frame
        row1 = Input_Row(None, "display_builder", "not_null_display_builder")
        self.name_input_widget_index = 0

        row_list = [row1]

        #Initialise the Base Frame with the above rows
        self.build_gui("Display Builder", "display_templates", "display_template_name", "display_template_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)
        self.set_delete_btn_command(self.delete_btn_command)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_tree()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            self.logger.debug(f"Input data list: {input_data_list}")

            display_template_obj : Display_Template = input_data_list[0]

            display_template_name = display_template_obj.display_template_name
            number_of_columns = display_template_obj.number_of_columns
            number_of_rows = display_template_obj.number_of_rows
            layout_matrix = display_template_obj.layout_matrix
            display_area_dict = display_template_obj.display_area_dict

            #Save the data to the database
            self.__save_input_data(display_template_name, number_of_columns, number_of_rows, layout_matrix, display_area_dict)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Called when delete button is clicked
    def delete_btn_command(self):
        self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
        #Get the DB id of the selected treeview item
        in_focus_db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

        if in_focus_db_id != None:
            #Confirm with the user they want to delete
            confirmation = confirm_delete()
            if confirmation == True:
                #Check the display template is not in use by any display instances
                query_result = self.db.get_1column_data("display_instance_id", "display_instances", "display_template_id", in_focus_db_id)
                if query_result == []:
                    #Delete display surface entries
                    feedback_1 = self.db.delete_row("display_surfaces", "display_template_id", in_focus_db_id)

                    #Delete Display Template entry
                    feedback_2 = self.db.delete_row("display_templates", "display_template_id", in_focus_db_id)
                    if (feedback_1 and feedback_2) == True:
                            self.logger.info(f"Deleted row with {self.id_column} of {in_focus_db_id} in table {self.table}")

                            #Clear the input widgets
                            self.input_frame.clear_all_entries()

                            #Set the State indicator to True
                            self.set_new_item_state(True)

                            #Update the tree
                            self.update_tree()
                else:
                        #Warn the user the item cannot be deleted to maintain database integrity
                        delete_warning("Unable to delete display template, the template is in use by a display instance.")

    #Save input data to the database
    def __save_input_data(self, display_template_name, number_of_columns, number_of_rows, layout_matrix, display_area_dict):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Generate a timesatamp to show when last modified
            timestamp = str(datetime.datetime.now())

            #Convert the layout matrix to json to store as text
            json_layout_matrix = json.dumps(layout_matrix)
            self.logger.debug(f"Converted JSON Layout Matrix: {json_layout_matrix}")

            #Add the validated data to the database
            self.db.add_display_template(display_template_name, number_of_columns, number_of_rows, json_layout_matrix, timestamp)

            #Get the id of the newly inserted template
            display_template_id = self.db.get_last_insert_row_id()
            self.logger.debug(f"Display Template ID:{display_template_id}")

            #Save the display surfaces
            for display_surface_id in display_area_dict:
                display_area_obj : Display_Section = display_area_dict[display_surface_id]

                widget_string = display_area_obj.widget_string
                top_left_coord_column = display_area_obj.top_left_coordinate[0]
                top_left_coord_row = display_area_obj.top_left_coordinate[1]
                block_width = display_area_obj.block_width
                block_height = display_area_obj.block_height

                self.db.add_display_surface(display_template_id, 
                                            display_surface_id, 
                                            widget_string, 
                                            top_left_coord_column, 
                                            top_left_coord_row, 
                                            block_width, 
                                            block_height)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            #Check the Display template is not in use by any display instances
            display_instance_ids_list = self.db.get_1column_data("display_instance_id", "display_instances", "display_template_id", db_id)
            
            if display_instance_ids_list == []:

                #Generate a timesatamp to show when last modified
                timestamp = str(datetime.datetime.now())

                #Convert the layout matrix to json to store as text
                json_layout_matrix = json.dumps(layout_matrix)
                self.logger.debug(f"Converted JSON Layout Matrix: {json_layout_matrix}")

                #Update the dipslay template database entries
                self.db.update_row("display_templates", "display_template_name", "display_template_id", display_template_name, db_id)
                self.db.update_row("display_templates", "total_columns", "display_template_id", number_of_columns, db_id)
                self.db.update_row("display_templates", "total_rows", "display_template_id", number_of_rows, db_id)
                self.db.update_row("display_templates", "layout_matrix", "display_template_id", json_layout_matrix, db_id)
                self.db.update_row("display_templates", "last_changed", "display_template_id", timestamp, db_id)

                #Clear current display surface db entries
                self.db.delete_row("display_surfaces", "display_template_id", db_id)

                #Store the new display surface entries
                for display_surface_id in display_area_dict:
                    display_area_obj : Display_Section = display_area_dict[display_surface_id]

                    widget_string = display_area_obj.widget_string
                    top_left_coord_column = display_area_obj.top_left_coordinate[0]
                    top_left_coord_row = display_area_obj.top_left_coordinate[1]
                    block_width = display_area_obj.block_width
                    block_height = display_area_obj.block_height

                    self.db.add_display_surface(db_id, 
                                                display_surface_id, 
                                                widget_string, 
                                                top_left_coord_column, 
                                                top_left_coord_row, 
                                                block_width, 
                                                block_height)
            else:
                self.logger.debug(f"Display Template:{db_id} in use by display instances:{display_instance_ids_list}")
                self.logger.debug(f"Cannot modify display template whilst it is being used.")
                cannot_modify_warning(f"Display Template:{db_id} in use by display instances:{display_instance_ids_list}")

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            display_template_id = item_data_list[0]
            display_template_name = item_data_list[1]
            number_of_columns = item_data_list[2]
            number_of_rows = item_data_list[3]
            layout_matrix = json.loads(item_data_list[4])

            #Get all rows mathcing the display template id
            display_surface_rows = self.db.get_current_row_data("display_surfaces", "display_template_id", display_template_id)
            self.logger.debug(f"Display Surface Rows: {display_surface_rows}")

            #Get the Display Builder Base frame object
            display_builder_obj : Display_Builder_Base_Frame = self.input_frame.get_widget_object(0)

            #Build the display layout columns / rows
            #Add all data to the Display Builder Widgets
            display_builder_obj.set_data(display_template_id, display_template_name, number_of_rows, number_of_columns, layout_matrix, display_surface_rows)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

class Display_Instances(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

         #Rows to make in the frame
        row1 = Input_Row(None, "display_instance_config", "not_null_display_instance_config")
        self.name_input_widget_index = 0

        row_list = [row1]

        #Initialise the Base Frame with the above rows
        self.build_gui("Display Instances", "display_instances", "display_instance_name", "display_instance_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)
        self.set_delete_btn_command(self.delete_btn_command)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        #self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""
        self.update_tree()
        self.__update_cbox_values()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            self.logger.debug(f"Input data list: {input_data_list}")

            display_instance_name : str = input_data_list[0][0]
            display_template_id : str = input_data_list[0][1]
            config_frame_list :list[Config_Frame] = input_data_list[0][2]

            #Save the data to the database
            self.__save_input_data(display_instance_name, display_template_id, config_frame_list)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Called when delete button is clicked
    def delete_btn_command(self):
        self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
        #Get the DB id of the selected treeview item
        in_focus_db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

        if in_focus_db_id != None:
            #Confirm with the user they want to delete
            confirmation = confirm_delete()

            #Check the display_instance is not assigned to a device
            rows = self.db.get_1column_data("device_name", "devices", "display_instance_id", in_focus_db_id)
            if rows == []:

                if confirmation == True:
                    for widget_table in widget_strings_list:
                        #Delete Widget entries
                        self.db.delete_row(widget_table, "display_instance_id", in_focus_db_id)

                    self.logger.debug(f"Deleted widget config DB entries for display instance: {in_focus_db_id}")

                    #Delete display instance row
                    feedback_1 = self.db.delete_row("display_instances", "display_instance_id", in_focus_db_id)

                    if feedback_1 == True:
                            self.logger.info(f"Deleted row with {self.id_column} of {in_focus_db_id} in table {self.table}")

                            #Clear the input widgets
                            self.input_frame.clear_all_entries()

                            #Set the State indicator to True
                            self.set_new_item_state(True)

                            #Update the tree
                            self.update_tree()
                    else:
                            #Warn the user the item cannot be deleted to maintain database integrity
                            delete_warning(str(feedback_1))
            else:
                #Warn the user the item cannot be deleted to maintain database integrity
                delete_warning("Unable to delete display instance, the instance is being used on a device.")

    #Save input data to the database
    def __save_input_data(self, display_instance_name, display_template_id, config_frame_list):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Generate a timesatamp to show when last modified
            timestamp = str(datetime.datetime.now())

            #Add the validated data to the database
            self.db.add_display_instance(display_instance_name, display_template_id, timestamp)
            display_instance_id = self.db.get_last_insert_row_id()

            #Save the widget config to the database
            self.__save_widget_config(display_instance_id, config_frame_list)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Generate a timesatamp to show when last modified
            timestamp = str(datetime.datetime.now())

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            #Delete any previous entries
            self.db.delete_row("indicator", "display_instance_id", db_id)
            self.db.delete_row("studio_clock", "display_instance_id", db_id)
            self.db.delete_row("analogue_clock", "display_instance_id", db_id)
            self.db.delete_row("digital_clock", "display_instance_id", db_id)
            self.db.delete_row("static_text", "display_instance_id", db_id)
            self.db.delete_row("static_image", "display_instance_id", db_id)
            self.db.delete_row("stacked_image", "display_instance_id", db_id)
            self.db.delete_row("top_banner", "display_instance_id", db_id)

            #Update the dipslay template database entries
            self.db.update_row("display_instances", "display_instance_name", "display_instance_id", display_instance_name, db_id)
            self.db.update_row("display_instances", "display_template_id", "display_instance_id", display_template_id, db_id)
            self.db.update_row("display_instances", "last_changed", "display_instance_id", timestamp, db_id)
            
            #Re-add the widget configs
            self.__save_widget_config(db_id, config_frame_list)

    def __save_widget_config(self, display_instance_id:str, config_frame_list:list[Config_Frame]):
        """Used to save widget config data to the DB used by the save_input_data function"""
        #Add the widget configs
        for config_frame in config_frame_list:
            config_frame : Config_Frame

            #Find out what widget the config is for
            widget_string = config_frame.widget_string

            if widget_string == "indicator":
                input_logic_id_name :str = config_frame.config_list.pop(3)
                input_logic_id = input_logic_id_name.split(":")[0]
                config_frame.config_list.insert(4, input_logic_id)
                self.db.add_indicator(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "studio_clock":
                self.db.add_studio_clock(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "analogue_clock":
                self.db.add_analogue_clock(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "digital_clock":
                self.db.add_digital_clock(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "static_text":
                self.db.add_static_text(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "static_image":
                image_id_name :str = config_frame.config_list.pop(0)
                image_id = image_id_name.split(":")[0]
                config_frame.config_list.insert(1, image_id)
                self.db.add_static_image(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

            elif widget_string == "stacked_image":
                image_id_name :str = config_frame.config_list.pop(0)
                image_id = image_id_name.split(":")[0]
                config_frame.config_list.insert(1, image_id)
                self.db.add_stacked_image(display_instance_id, config_frame.display_surface_id, config_frame.config_list)
            
            elif widget_string == "top_banner":
                image_id_name :str = config_frame.config_list.pop(0)
                image_id = image_id_name.split(":")[0]
                config_frame.config_list.insert(1, image_id)
                self.db.add_top_banner(display_instance_id, config_frame.display_surface_id, config_frame.config_list)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Display_instance data
            display_instance_id = item_data_list[0]
            display_instance_name = item_data_list[1]
            display_template_id = item_data_list[2]

            #List to store config frames
            config_frames_list = []

            #Retrieve all widget data and convert into a config frame adding to the config frame list
            for widget_string in widget_strings_list:
                rows = self.db.get_current_row_data(widget_string, "display_instance_id", display_instance_id)
                for row in rows:
                    row : tuple
                    display_instance_id = row[0]
                    display_surface_id = row[1]

                    config_list = list(row[2:len(row)])

                    #Add names to ids
                    if widget_string == "indicator":
                        input_logic_id = config_list.pop(3)
                        input_logic_name = self.db.get_1column_data("input_logic_name", "input_logics", "input_logic_id", input_logic_id)[0]
                        input_logic_id_name = f"{input_logic_id}:{input_logic_name}"
                        config_list.insert(4, input_logic_id_name)

                    elif (widget_string == "top_banner") or (widget_string == "static_image") or (widget_string == "stacked_image"):
                        image_id = config_list.pop(0)
                        image_name = self.db.get_1column_data("image_name", "images", "image_id", image_id)[0]
                        image_id_name = f"{image_id}:{image_name}"
                        config_list.insert(1, image_id_name)

                    config_frame = Config_Frame(widget_string, display_surface_id, config_list)
                    config_frames_list.append(config_frame)

            #Get the Display Instance Base frame object
            display_instance_obj : Display_Instance_Config_Base_Frame = self.input_frame.get_widget_object(0)

            #Build the display layout columns / rows
            #Add all data to the Display Builder Widgets
            display_instance_obj.set_data(display_instance_name, display_template_id, config_frames_list)

            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

    def __update_cbox_values(self):
        #Get all current display template entries
        rows = self.db.get_2column_data("display_template_id", "display_template_name", "display_templates")
        self.logger.debug(f"Rows:{rows}")

        id_name_list = []

        #Concatenate the id and names and add to a list
        for row in rows:
            display_template_id = str(row[0])
            display_template_name = str(row[1])
            id_name = f"{display_template_id}:{display_template_name}"
            id_name_list.append(id_name)

        #Add the list to the combobox
        display_instance_frame : Display_Instance_Config_Base_Frame = self.input_frame.get_widget_object(0)
        display_instance_frame.set_display_template_combobox_values(id_name_list)
#-------------------------------------------------------------------------------------------------------------------
   
class Messaging_Groups(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("Name:", "text_entry", "not_null")
        self.name_input_widget_index = 0

        row_list = [row1]

        #Initialise the Base Frame with the above rows
        self.build_gui("Message Groups", "message_groups", "message_group_name", "message_group_id", row_list)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Bindings
        self.__set_bindings()

        #Update treeviewer with currrent data
        self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        self.update_tree()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        """Validates and collects input data. \n Determins whether a new item is being saved or existing one updated. \n Then saves the data to the database."""
        self.logger.info("#######---Save Button Clicked---#######")

        valid_status, input_data_list = self.get_and_validate_input_data()

        if valid_status == True:
            #Extract all the data from the list of tuples
            message_group_name :str = input_data_list[self.name_input_widget_index]

            #Save the data to the database
            self.__save_input_data(message_group_name)

            self.input_frame.clear_all_entries()

            #Set the state indicator to true - no tree item is selected
            self.set_new_item_state(True)

            self.logger.info("Saved Input Data to Database")

            self.update_tree()

        else:
            #Show a message box stating cannot save data
            invalid_data_warning()

    #Save input data to the database
    def __save_input_data(self, message_group_name):
        """Saves input data to the database."""
        #Saving a new item
        if self.new_item == True:
            self.logger.info("Saving new item to the database")

            #Add the validated data to the database
            self.db.add_message_group(message_group_name)

        #Updating an existing item
        else:
            self.logger.info("Updating existing database entry")

            #Get the db_id of the selected item
            db_id = self.tree.get_in_focus_item_db_id()

            self.db.update_row(self.table, self.name_column, self.id_column, message_group_name, db_id)

    def __update_input_widgets(self, event):
        """Updates the input widgets with data for the selected treeview item"""

        self.logger.info(f"Updating Input widgets for selected treeviever item.")

        #Get the db id of the selected item
        db_id = self.tree.get_in_focus_item_db_id()
        self.logger.debug(f"Selected item DB ID: {db_id}")

        if db_id != None:
            #Get all data from the db for the currently selected item
            item_data_list = self.db.get_current_row_data(self.table, self.id_column, db_id)[0]
            self.logger.debug(f"Item data: {item_data_list}")

            #Extract the data from the item data list
            name = item_data_list[1]

            #Get the name of the message group from the database
            message_group_name = self.db.get_1column_data("message_group_name", "message_groups", "message_group_id", db_id)[0]

            #Add all data to the input frame widgets
            self.input_frame.set_all_data(message_group_name)
            
            #Set the state indicator to false, an existing item has been loaded into the input widgets
            self.set_new_item_state(False)

            self.logger.info("Updated Input widgets")

#-------------------------------------------------------------------------------------------------------------------

class Server_Config(BaseFrameNew):
    def __init__(self, parent, database_connection, scrollable):
        super().__init__(parent, database_connection, scrollable)

        #Rows to make in the frame
        row1 = Input_Row("", "server_config", "n/a")
        self.server_config_widget_index = 0

        row_list = [row1]

        #Initialise the Base Frame with the above rows
        self.build_gui("Server Configuration", "", "", "", row_list)

        #Hide treeviewer and add / remove buttons / save button
        self.tree.grid_forget()
        self.add_btn.grid_forget()
        self.del_btn.grid_forget()
        self.save_btn.grid_forget()

        #Reposition input frame
        self.input_frame.grid_forget()
        self.input_frame.grid(column=0, row=0, sticky="nsew", columnspan=4)

        #Set the Button Commands
        self.set_save_btn_command(self.save_btn_cmd)

        #Set on raise callback
        self.set_on_raise_callback(self.menu_select_callbacks)

        #Set the database reference
        server_config_widget : Server_Config_Frame = self.input_frame.get_widget_object(self.server_config_widget_index)
        server_config_widget.set_db_reference(self.db)

        #Bindings
        #self.__set_bindings()

        #Update treeviewer with currrent data
        #self.update_tree()

#-----------------------------------------COMMON FUNCTIONS - Included in all children of Base Frame----------------------------------------------------------
    def menu_select_callbacks(self):
        """Executes listed callbacks when this frame is raised by selecting it in the gui menu."""

        #self.update_tree()
    
    def __set_bindings(self):
        """Sets callbacks for widgets."""
        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__update_input_widgets)

    #Called when the save button is clicked
    def save_btn_cmd(self):
        pass

    #Save input data to the database
    def __save_input_data(self, message_group_name):
        pass

    def __update_input_widgets(self, event):
        pass
    