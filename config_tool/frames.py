import customtkinter as ctk
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk
from config_tool.validation import Validation
import logging
from serial.tools.list_ports import comports
from config_tool.message_boxes import Message_Boxes
from tkinter import messagebox
from tkinter import IntVar
from tkinter import filedialog
from PIL import Image
from config_tool.gui_templates import *
from database.database_connection import DB
import shutil
import os
import logging
from config_tool.global_variables import *
import datetime
from modules.common import *
from modules.osc import OSC_Client
from modules.tcp import *



class Device_Config(BaseFrame):

    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #GUI Variables - to allow dynamic updating
        self.device_id_var = StringVar()
        self.device_name_var = StringVar()
        self.device_ip_var = StringVar()
        self.location_var = StringVar()
        self.msg_group_name_var = StringVar()
        self.trig_grp_name_var = StringVar()
        self.display_tmplt_name_var = StringVar()
        self.msg_group_id_var = StringVar()
        self.trig_grp_id_var = StringVar()
        self.display_tmplt_id_var = StringVar()

        #Variables to store the names of combobox items
        self.msg_names_list = []
        self.trig_grp_names_list = []
        self.display_tmplt_names_list = []

        #Variables to store the ID's of combobox items
        self.msg_ids_list = []
        self.trig_grp_ids_list = []
        self.display_tmplt_ids_list = []

        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        #Add the display widgets to the frame
        self.__add_widgets()

        #Refresh the tree view with the current database data so it's not empty on startup
        self.logger.info("Retrieving current devices table data")
        updated_rows = self.db.get_current_table_data("devices")

        self.logger.info("Updating devices tree")
        self.__update_tree(updated_rows)

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)
        

    def __set_id(self, combobox_value, id):
        self.logger.info(f"Combobox:{combobox_value}")
        self.logger.debug(f"msg_names_list: {self.msg_names_list}")
        self.logger.debug(f"trig_grp_names_list: {self.trig_grp_names_list}")
        self.logger.debug(f"display_tmplt_list: {self.display_tmplt_names_list}")
        if id == 0:
            self.logger.debug(f"Combobox value is in msg_names_list, value: {combobox_value}")
            name = self.msg_group_name_var.get()
            id_var = self.msg_group_id_var
            names_list = self.msg_names_list
            ids_list = self.msg_ids_list
        if id == 1:
            self.logger.debug(f"Combobox value is in trig_grp_names_list, value: {combobox_value}")
            name = self.trig_grp_name_var.get()
            id_var = self.trig_grp_id_var
            names_list = self.trig_grp_names_list
            ids_list = self.trig_grp_ids_list
        if id == 2:
            self.logger.debug(f"Combobox value is in display_tmplt_names_list, value: {combobox_value}")
            name = self.display_tmplt_name_var.get()
            id_var = self.display_tmplt_id_var
            names_list = self.display_tmplt_names_list
            ids_list = self.display_tmplt_ids_list

        self.logger.info(f"Combobox selection = {name}")
        #Get the index of the name in the names list
        index = names_list.index(name)
        self.logger.info(f"Index of name in names list: {index}")
        #Use this index to select the corresponding id from the id lis
        id = ids_list[index]
        self.logger.info(f"ID of selection in database: {id}")
        id_var.set(id)

    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update the widgets if a valid tree item is selected
        if self.tree.item(selected)["text"] != '':
            #Set the state indicator variable to False, indicating an item is to be modified
            self.new_item = False
            self.logger.info("Set State Indicator to False - an existing item is being modified")
            #Retrieve the id of the messaging group
            db_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item
            row = self.db.get_current_row_data("devices", "device_id", db_id)
            self.logger.info("Populating entry fields with data for selected tree viewer item")
            #Populate the fields with the data
            self.device_id_var.set(row[0][0])
            self.device_name_var.set(row[0][1])
            self.device_ip_var.set(row[0][2])
            self.location_var.set(row[0][3])
            self.msg_group_id_var.set(row[0][4])
            self.trig_grp_id_var.set(row[0][5])
            self.display_tmplt_id_var.set(row[0][6])

            #Query the database to get the names of message group, trig group and display template given the id's and update the combobox with the name
            self.msg_group_name_var.set(self.db.get_1column_data("messaging_group_name", "messaging_groups", "messaging_group_id", self.msg_group_id_var.get())[0])
            self.trig_grp_name_var.set(self.db.get_1column_data("trigger_group_name", "trigger_groups", "trigger_group_id", self.trig_grp_id_var.get())[0])
            self.display_tmplt_name_var.set(self.db.get_1column_data("display_template_name", "display_templates", "display_template_id", self.display_tmplt_id_var.get())[0])

            self.device_control_frame.grid(column=0, row=9, columnspan=4, sticky="ew")
            

            self.logger.info("Updated all entry Widgets")
        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
            #Set the state indicator variable to True indicating a new item is to be added
            #Clear the entry widgets
            self.__clear_widgets()
            #Set the state indicator variable to True indicating a new item is to be added
            self.new_item = True
            self.logger.info("State indicator set to True")

    
    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Set the state indicator variable to True, indicating a new item is to be added
        self.new_item = True
        self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

        #Clear All entry Widgets
        self.device_id_var.set("")
        self.device_name_var.set("")
        self.device_ip_var.set("")
        self.location_var.set("")
        self.msg_group_id_var.set("")
        self.trig_grp_id_var.set("")
        self.display_tmplt_id_var.set("")
        self.msg_group_name_var.set("")
        self.trig_grp_name_var.set("")
        self.display_tmplt_name_var.set("")
        self.device_control_frame.grid_forget()
        self.logger.info("Cleared all entry Widgets")
    
    #Refreshes Treeviewer data
    def __update_tree(self, updated_rows):
        self.logger.debug(f"#######---Updating Tree Viewer---#######")
        self.logger.debug(f"Data input to Tree: {updated_rows}")
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared devices tree")

        #Create the parents based on device locations
        locations_dict = {} #Used to hold treeviewer parent id's
        for row in updated_rows:
            #Identify the device location
            device_location = str(row[3])
            #If location is not in the dict add it
            if locations_dict.get(device_location) == None:
                #Add the location as a parent in the tree
                id = self.tree.insert("", tk.END, text="", values=(device_location,))
                self.tree.insert(id, tk.END, text=row[0], values=(row[1],))
                #Add the location to the parent dictionary
                locations_dict[device_location] = id
            #If the location exists as a parent, add it to the parent
            else:
                parent_id = locations_dict[device_location]
                self.tree.insert(parent_id, tk.END, text=row[0], values=(row[1],))

        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        self.logger.info("Save Button Clicked")
        #Verify all entries populated
        valid = self.__verify_input()
        #Determine whether a new item or modifying existing
        #Adding a new item
        if self.new_item == True:
            if valid == True:
                self.logger.info("Adding New Item to Database")
                #Add all the current entry data to the database
                self.db.add_device(self.device_name_var.get(), self.device_ip_var.get(), self.location_var.get(), self.msg_group_id_var.get(), self.trig_grp_id_var.get(), self.display_tmplt_id_var.get())
                self.logger.info("Added new item to database")
                #Refresh the tree
                updated_rows = self.db.get_current_table_data("devices")
                self.__update_tree(updated_rows)
                #Clear all entry widget fields
                self.__clear_widgets()
            else:
                self.logger.info("Value Empty - Nothing Added to Database")
            

        #Modifying existing item    
        else:
            #Get the value from the ID and name widgets
            db_id = self.device_id_var.get()
            name = self.device_name_var.get()
            #Check if the entry box contains text
            if valid == True:
                self.logger.info("Modifing existing database entry")
                self.logger.info(f"Updating database entry for trigger group: {name}, ID={db_id}")
                #Update the existing entry in the database
                #self.db.update_display_template(db_id, self.template_name_var.get(), self.ticker_var.get(), self.logo_var.get(), self.studio_name_var.get(), self.show_name_var.get(), self.time_var.get(), self.mic_live_var.get(), self.tx_ind_var.get(), self.cue_ind_var.get(), self.lin1_ind_var.get(), self.lin2_ind_var.get(), self.control_ind_var.get())
                columns_dict = {"device_name" :self.device_name_var.get(), "device_ip" :self.device_ip_var.get(), "location" :self.location_var.get(), "messaging_group_id" :self.msg_group_id_var.get(), "trigger_group_id" :self.trig_grp_id_var.get(), "display_template_id" :self.display_tmplt_id_var.get()}
                for column in columns_dict:
                    self.logger.info(f"Updating column: {column} with {columns_dict[column]}")
                    self.db.update_row("devices", column, "device_id", columns_dict[column], db_id)
                
                #Refresh the tree
                updated_rows = self.db.get_current_table_data("devices")
                self.__update_tree(updated_rows)
                #Clear all entry widget fields
                self.__clear_widgets()

            else:
                self.logger.info("Value Empty - Nothing Added to Database")

    #Removes an entry from the database
    def __remove_device(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        self.logger.debug(f"Selected tree item is:{selected}")
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the display template
                db_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database
                feedback = self.db.delete_row("devices", "device_id", db_id)
                if feedback == True:
                    self.logger.info(f"Deleted trigger group with ID={db_id} from the database")
                    #Clear the entry widgets
                    self.__clear_widgets()
                    #Refresh the tree view
                    updated_rows = self.db.get_current_table_data("devices")
                    self.__update_tree(updated_rows)
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning(feedback)
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")
        

    #Refreshes combobox options
    def refresh_cboxs(self, event):
        self.logger.info("Refreshing device_config combobox options")
        #Query the database for id and names
        query1 = self.db.get_2column_data("messaging_group_id", "messaging_group_name", "messaging_groups")
        query2 = self.db.get_2column_data("trigger_group_id", "trigger_group_name", "trigger_groups")
        query3 = self.db.get_2column_data("display_template_id", "display_template_name", "display_templates")

        #Create lists to allow looping to function
        queries_list = [query1, query2, query3] #List of the above query responses
        ids_lists = [self.msg_ids_list, self.trig_grp_ids_list, self.display_tmplt_ids_list] #List of id lists
        names_lists = [self.msg_names_list, self.trig_grp_names_list, self.display_tmplt_names_list] #List of name lists
        combobox_list = [self.msg_grp_cbox, self.trig_grp_cbox, self.disp_tmplt_cbox] #List of comboboxed
        
        #Clear the id / name lists
        self.logger.info("Clearing id / name lists")
        self.msg_ids_list.clear()
        self.trig_grp_ids_list.clear()
        self.display_tmplt_ids_list.clear()
        self.msg_names_list.clear()
        self.trig_grp_names_list.clear()
        self.display_tmplt_names_list.clear()
        
        for i in range (3):
            self.logger.info(f"Iteration: {i}")
            self.logger.info("Setting up lists for loop")
            #Select the correct list to work on from the lists
            query = queries_list[i]
            id_list = ids_lists[i]
            name_list = names_lists[i]
            combobox = combobox_list[i]
            self.logger.info(f"Database query response: {query}")
            #For each row in the query response, add the row to the id/name list.
            for item in query:
                #Add the name and id to the lists
                self.logger.info(f"Adding name: {item[1]} and id: {item[0]} to lists.")
                id_list.append(item[0])
                name_list.append(item[1])
                
            #Assign values to each combobox
            self.logger.info(f"Assigning values: {name_list}")
            combobox.configure(values=name_list)

    def __verify_input(self):
        valid = True
        self.logger.info("Validating input fields")
        if self.device_name_var.get() == "":
            self.logger.info("Device Name Empty")
            valid = False
        if (self.device_ip_var.get() == "") or (Validation.validate_ip(str(self.device_ip_var.get())) == False):    #TODO:Verify
            self.logger.info("Device IP Empty or invalid format")
            valid = False
        if self.location_var.get() == "":
            self.logger.info("Device Location Empty")
            valid = False
        if self.msg_group_name_var.get() == "":
            self.logger.info("Device Message Group Empty")
            valid = False
        if self.trig_grp_name_var.get() == "":
            self.logger.info("Device Trigger Group Empty")
            valid = False
        if self.display_tmplt_name_var.get() == "":
            self.logger.info("Device Display Template Empty")
            valid = False
        
        self.logger.debug(f"Valid = {valid}")
        return valid

    def __add_widgets(self):
        #------------------------------DEVICE CONFIG FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)

        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(self, text="Add Device", font=self.default_font, fg_color="green", command=lambda:self.__clear_widgets())
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(self, text="Remove Device", font=self.default_font, fg_color="red", command=lambda:self.__remove_device())
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------DEVICE CONFIG FRAME-DEVICE SETUP FRAME--------------------------------------------------
        #Create a frame to contain settings about the individual client device
        self.device_setup_frame = ctk.CTkScrollableFrame(self, border_color="green", border_width=1)
        self.device_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for self.device_setup_frame

        self.device_setup_frame.columnconfigure(0, weight=0, pad=20)
        self.device_setup_frame.columnconfigure(1, weight=1, pad=20)
        self.device_setup_frame.columnconfigure(2, weight=1, pad=20)
        self.device_setup_frame.columnconfigure(3, weight=1, pad=20)

        for i in range(29):
            self.device_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------DEVICE SETUP FRAME WIDGETS--------------------------------------------------
        #------------------------------Device Attributes--------------------------------------------------
        title1_label = ctk.CTkLabel(master=self.device_setup_frame, text="Device Attributes", font=self.default_font)
        title1_label.grid(column=0, row=0, columnspan=4, sticky="ew")

        id_label = ctk.CTkLabel(master=self.device_setup_frame, text="Device ID:", font=self.default_font)
        id_label.grid(column=0, row=1, sticky="w", padx=20)

        id_data_label = ctk.CTkLabel(master=self.device_setup_frame, text="", font=self.default_font, textvariable=self.device_id_var)
        id_data_label.grid(column=1, row=1, sticky="w", padx=20)

        name_label = ctk.CTkLabel(master=self.device_setup_frame, text="Device Name:", font=self.default_font)
        name_label.grid(column=0, row=2, sticky="w", padx=20)

        name_entry = ctk.CTkEntry(master=self.device_setup_frame, textvariable=self.device_name_var, font=self.default_font)
        name_entry.grid(column=1, row=2, columnspan =1, sticky="ew", padx=20)

        ip_label = ctk.CTkLabel(master=self.device_setup_frame, text="Device IP Address:", font=self.default_font)
        ip_label.grid(column=0, row=3, sticky="w", padx=20)

        ip_entry = ctk.CTkEntry(master=self.device_setup_frame, textvariable=self.device_ip_var, font=self.default_font)
        ip_entry.grid(column=1, row=3, columnspan =1, sticky="ew", padx=20)

        location_label = ctk.CTkLabel(master=self.device_setup_frame, text="Device Location:", font=self.default_font)
        location_label.grid(column=0, row=4, sticky="w", padx=20)

        location_entry = ctk.CTkEntry(master=self.device_setup_frame, textvariable=self.location_var, font=self.default_font)
        location_entry.grid(column=1, row=4, columnspan =1, sticky="ew", padx=20)

        msg_grp_label = ctk.CTkLabel(master=self.device_setup_frame, text="Messaging Group:", font=self.default_font)
        msg_grp_label.grid(column=0, row=5, sticky="w", padx=20)

        self.msg_grp_cbox = ctk.CTkComboBox(master=self.device_setup_frame, state="readonly", variable=self.msg_group_name_var, command=lambda value, id=0: self.__set_id(value, id), font=self.default_font, dropdown_font=self.default_font)
        self.msg_grp_cbox.grid(column=1, row=5, columnspan =1, sticky="ew", padx=20)

        msg_grp_id_label = ctk.CTkLabel(master=self.device_setup_frame, text="ID:", font=self.default_font)
        msg_grp_id_label.grid(column=2, row=5, sticky="e", padx=20)

        msg_grp_id = ctk.CTkLabel(master=self.device_setup_frame, text="", font=self.default_font, textvariable=self.msg_group_id_var)
        msg_grp_id.grid(column=3, row=5, sticky="w")

        trig_grp_label = ctk.CTkLabel(master=self.device_setup_frame, text="Trigger Group:", font=self.default_font)
        trig_grp_label.grid(column=0, row=6, sticky="w", padx=20)

        self.trig_grp_cbox = ctk.CTkComboBox(master=self.device_setup_frame, state="readonly", variable=self.trig_grp_name_var, command=lambda value, id=1: self.__set_id(value, id), font=self.default_font, dropdown_font=self.default_font)
        self.trig_grp_cbox.grid(column=1, row=6, columnspan =1, sticky="ew", padx=20)

        trig_grp_id_label = ctk.CTkLabel(master=self.device_setup_frame, text="ID:", font=self.default_font)
        trig_grp_id_label.grid(column=2, row=6, sticky="e", padx=20)

        trig_grp_id = ctk.CTkLabel(master=self.device_setup_frame, text="", font=self.default_font, textvariable=self.trig_grp_id_var)
        trig_grp_id.grid(column=3, row=6, sticky="w")

        ##------------------------------Display Configuration--------------------------------------------------
        title2_label = ctk.CTkLabel(master=self.device_setup_frame, text="Display Configuration", font=self.default_font, pady=15)
        title2_label.grid(column=0, row=7, columnspan=4, sticky="ew")

        disp_tmplt_label = ctk.CTkLabel(master=self.device_setup_frame, text="Display Template:", font=self.default_font)
        disp_tmplt_label.grid(column=0, row=8, sticky="w", padx=20)

        self.disp_tmplt_cbox = ctk.CTkComboBox(master=self.device_setup_frame, state="readonly", variable=self.display_tmplt_name_var, command=lambda value, id=2: self.__set_id(value, id), font=self.default_font, dropdown_font=self.default_font)
        self.disp_tmplt_cbox.grid(column=1, row=8, columnspan =1, sticky="ew", padx=20)

        disp_tmplt_id_label = ctk.CTkLabel(master=self.device_setup_frame, text="ID:", font=self.default_font)
        disp_tmplt_id_label.grid(column=2, row=8, sticky="e", padx=20)

        disp_tmplt_id = ctk.CTkLabel(master=self.device_setup_frame, text="", font=self.default_font, textvariable=self.display_tmplt_id_var)
        disp_tmplt_id.grid(column=3, row=8, sticky="w")

        ##------------------------------Device Control--------------------------------------------------
        self.device_control_frame = ctk.CTkFrame(self.device_setup_frame)
        #self.device_control_frame.grid(column=0, row=9, columnspan=4, sticky="ew")

        for i in range(3):
            self.device_control_frame.columnconfigure(i, weight=1, uniform="group1")

        for i in range(2):
            self.device_control_frame.rowconfigure(i, weight=0)

        title3_label = ctk.CTkLabel(master=self.device_control_frame, text="Device Control", font=self.default_font, pady=15)
        title3_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        reload_display_btn = ctk.CTkButton(master=self.device_control_frame, text="Reload Display Template", font=self.default_font, fg_color="green", command=lambda:self.__reload_device_display())
        reload_display_btn.grid(column=0, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

        identify_btn = ctk.CTkButton(master=self.device_control_frame, text="Identify Device", font=self.default_font, fg_color="green", command=lambda state=True :self.__identify_device(state) )
        identify_btn.grid(column=1, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

        exit_identify_btn = ctk.CTkButton(master=self.device_control_frame, text="Exit Identify Device", font=self.default_font, fg_color="green", command=lambda state=False :self.__identify_device(state) )
        exit_identify_btn.grid(column=2, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

        ##------------------------------Save Settings--------------------------------------------------
        save_btn = ctk.CTkButton(master=self, text="Save", font=self.default_font, fg_color="green", command=lambda:self.__save_entry_data())
        save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)


    def __reboot_device(self):
        pass

    def __reload_device_display(self):
        #Get the devices IP
        device_ip = self.device_ip_var.get()
        device_id = self.device_id_var.get()

        #Read the Server Settings file
        settings_dict = open_json_file("server/settings.json")

        #Only send a command to the server if it has an ip set
        if settings_dict != False:
            server_ip = (settings_dict["server_ip"])

            #Send the raise frame command to the server
            self.tcp_client = TCP_Client()
            message = self.tcp_client.build_tcp_message("/control/client/reload_display_template", {"device_id" : device_id}, None)
            response_bytes = self.tcp_client.tcp_send(server_ip, 1339, message)
            response = self.tcp_client.decode_data(response_bytes)
            self.logger.debug(f"Response from Server: {response}")
        

    def __identify_device(self, state:bool):
        #Get the devices IP
        device_id = self.device_id_var.get()

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
            message = self.tcp_client.build_tcp_message("/control/client/raise_frame", {"device_id" : device_id, "frame" : frame}, None)
            response_bytes = self.tcp_client.tcp_send(server_ip, 1339, message)
            response = self.tcp_client.decode_data(response_bytes)
            self.logger.debug(f"Response from Server: {response}")

class GPIO_Config(BaseFrame):
    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        #Variables for updating combobox options
        self.serial_ports_list = []

        #GUI Variables - to allow dynamic updating
        self.controller_id_var = StringVar()
        self.controller_name_var = StringVar()
        self.loc_rem_var = StringVar()
        self.ip_var = StringVar()
        self.com_port_var = StringVar()
        self.controller_type_var = StringVar()
        self.controller_type_var = StringVar()
        self.pin2_var = StringVar()
        self.pin3_var = StringVar()
        self.pin4_var = StringVar()
        self.pin5_var = StringVar()
        self.pin6_var = StringVar()
        self.pin7_var = StringVar()
        self.pin8_var = StringVar()
        self.pin9_var = StringVar()
        self.pin10_var = StringVar()
        self.pin11_var = StringVar()
        self.pin12_var = StringVar()
        self.pin13_var = StringVar()
        self.pin14_var = StringVar()
        self.pin15_var = StringVar()
        self.pin16_var = StringVar()
        self.pin17_var = StringVar()
        self.pin18_var = StringVar()
        self.pin19_var = StringVar()

        self.pin_var_list = [self.pin2_var,
                        self.pin3_var,
                        self.pin4_var,
                        self.pin5_var,
                        self.pin6_var,
                        self.pin7_var,
                        self.pin8_var,
                        self.pin9_var,
                        self.pin10_var,
                        self.pin11_var,
                        self.pin12_var,
                        self.pin13_var,
                        self.pin14_var,
                        self.pin15_var,
                        self.pin16_var,
                        self.pin17_var,
                        self.pin18_var,
                        self.pin19_var,
                        ]

        #Add the display widgets to the frame
        self.__add_widgets()

        #Refresh the tree view with the current database data so it's not empty on startup
        self.logger.info("Retrieving current gpio_config table data")
        updated_rows = self.db.get_current_table_data("controllers")

        self.logger.info("Updating gpio_config tree")
        self.__update_tree(updated_rows)

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)

    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        #Set the state indicator variable to False, indicating an item is to be modified
        self.new_item = False
        self.logger.info("Set State Indicator to False - an existing item is being modified")

        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update teh widgets if a valid tree item is selected
        if selected != '':
            #Retrieve the id of the messaging group
            db_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item
            self.logger.info("Getting current data for selected item from the Database")
            row = self.db.get_current_row_data("controllers", "controller_id", db_id)
            self.logger.info(f"Data returned from database:{row}")
            self.logger.info("Populating entry fields with data for selected tree viewer item")
            #Populate the fields with the data
            self.controller_id_var.set(row[0][0])
            self.controller_name_var.set(row[0][1])
            self.loc_rem_var.set(row[0][2])
            self.ip_var.set(row[0][3])
            self.com_port_var.set(row[0][4])
            self.controller_type_var.set(row[0][5])
            self.pin2_var.set(row[0][6])
            self.pin3_var.set(row[0][7])
            self.pin4_var.set(row[0][8])
            self.pin5_var.set(row[0][9])
            self.pin6_var.set(row[0][10])
            self.pin7_var.set(row[0][11])
            self.pin8_var.set(row[0][12])
            self.pin9_var.set(row[0][13])
            self.pin10_var.set(row[0][14])
            self.pin11_var.set(row[0][15])
            self.pin12_var.set(row[0][16])
            self.pin13_var.set(row[0][17])
            self.pin14_var.set(row[0][18])
            self.pin15_var.set(row[0][19])
            self.pin16_var.set(row[0][20])
            self.pin17_var.set(row[0][21])
            self.pin18_var.set(row[0][22])
            self.pin19_var.set(row[0][23])
            #Show or hide the ip / com input fields
            self.show_hide_ip_com()
            self.logger.info("Updated all entry Widgets")
        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
    
    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Set the state indicator variable to True, indicating a new item is to be added
        self.new_item = True
        self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

        #Clear All entry Widgets
        self.controller_id_var.set("")
        self.controller_name_var.set("")
        self.loc_rem_var.set("")
        self.ip_var.set("")
        self.com_port_var.set("")
        self.controller_type_var.set("")
        self.controller_type_var.set("")
        self.pin2_var.set("")
        self.pin3_var.set("")
        self.pin4_var.set("")
        self.pin5_var.set("")
        self.pin6_var.set("")
        self.pin7_var.set("")
        self.pin8_var.set("")
        self.pin9_var.set("")
        self.pin10_var.set("")
        self.pin11_var.set("")
        self.pin12_var.set("")
        self.pin13_var.set("")
        self.pin14_var.set("")
        self.pin15_var.set("")
        self.pin16_var.set("")
        self.pin17_var.set("")
        self.pin18_var.set("")
        self.pin19_var.set("")
        #Show or hide the ip / com input fields
        self.show_hide_ip_com()
        self.logger.info("Cleared all entry Widgets")
    
    #Refreshes Treeviewer data
    def __update_tree(self, updated_rows):
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared gpio_config tree")

        for row in updated_rows:
            #Add items to the treeviewer, Indexes: 0=ID, 1=Message Group Name
            #Format: (Parent=(iid), index) "" is the top level parent node
            self.tree.insert("", tk.END, text=row[0], values=(row[1],)) 
            self.logger.info(f"Added {row[1]} to the tree")
        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        self.logger.info("Save Button Clicked")
        #Verify all entries populated
        valid = self.__verify_input()
        #Determine whether a new item or modifying existing
        #Adding a new item
        if self.new_item == True:
            if valid == True:
                self.logger.info("Adding New Item to Database")
                #Get the value from the text entry widget
                value = self.controller_name_var.get()
                #Check if the entry box contains text
                if value != "":
                    #Add all the current entry data to the database
                    self.db.add_controller(self.controller_name_var.get(), self.loc_rem_var.get(), self.ip_var.get(), self.com_port_var.get(), self.controller_type_var.get(), self.pin2_var.get(), self.pin3_var.get(), self.pin4_var.get(), self.pin5_var.get(), self.pin6_var.get(), self.pin7_var.get(), self.pin8_var.get(), self.pin9_var.get(), self.pin10_var.get(), self.pin11_var.get(), self.pin12_var.get(), self.pin13_var.get(), self.pin14_var.get(), self.pin15_var.get(), self.pin16_var.get(), self.pin17_var.get(), self.pin18_var.get(), self.pin19_var.get())
                    #Refresh the tree
                    updated_rows = self.db.get_current_table_data("controllers")
                    self.__update_tree(updated_rows)
                    #Clear all entry widget fields
                    self.__clear_widgets()
                else:
                    self.logger.info("Value Empty - Nothing Added to Database")
                

        #Modifying existing item    
        else:
            #Get the value from the ID and name widgets
            db_id = self.controller_id_var.get()
            name = self.controller_name_var.get()
            #Check if the entry box contains text
            if valid == True:
                self.logger.info("Modifing existing database entry")
                self.logger.info(f"Updating database entry for controller: {name}, ID={db_id}")
                #Update the existing entry in the database
                #self.db.update_display_template(db_id, self.template_name_var.get(), self.ticker_var.get(), self.logo_var.get(), self.studio_name_var.get(), self.show_name_var.get(), self.time_var.get(), self.mic_live_var.get(), self.tx_ind_var.get(), self.cue_ind_var.get(), self.lin1_ind_var.get(), self.lin2_ind_var.get(), self.control_ind_var.get())
                columns_dict = {"controller_name" :self.controller_name_var.get(), "controller_location" :self.loc_rem_var.get(), "controller_ip" :self.ip_var.get(), "controller_port" :self.com_port_var.get(), "controller_type" :self.controller_type_var.get(), "pin2" :self.pin2_var.get(), "pin3" :self.pin3_var.get(), "pin4" :self.pin4_var.get(), "pin5" :self.pin5_var.get(), "pin6" :self.pin6_var.get(), "pin7" :self.pin7_var.get(), "pin8" :self.pin8_var.get(), "pin9" :self.pin9_var.get(), "pin10" :self.pin10_var.get(), "pin11" :self.pin11_var.get(), "pin12" :self.pin12_var.get(), "pin13" :self.pin13_var.get(), "pin14" :self.pin14_var.get(), "pin15" :self.pin15_var.get(), "pin16" :self.pin16_var.get(), "pin17" :self.pin17_var.get(), "pin18" :self.pin18_var.get(), "pin19" :self.pin19_var.get()}
                for column in columns_dict:
                    self.logger.info(f"Updating column: {column} with {columns_dict[column]}")
                    self.db.update_row("controllers", column, "controller_id", columns_dict[column], db_id)
                
                #Refresh the tree
                updated_rows = self.db.get_current_table_data("controllers")
                self.__update_tree(updated_rows)
                #Clear all entry widget fields
                self.__clear_widgets()

            else:
                self.logger.info("Value Empty - Nothing Added to Database")

    #Removes an entry from the database
    def __remove_controller(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the display template
                db_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database
                feedback = self.db.delete_row("controllers", "controller_id", db_id)
                #Item is only deleted if there are no database integrity errors thrown
                if feedback == True:
                    self.logger.info(f"Deleted controller with ID={db_id} from the database")
                    #Clear the entry widgets
                    self.__clear_widgets()
                    #Refresh the tree view
                    updated_rows = self.db.get_current_table_data("controllers")
                    self.__update_tree(updated_rows)

                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning(feedback)
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")


    #Creates and adds GUI widgets to the frame
    def __add_widgets(self):
        #------------------------------GPIO CONFIG FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)
        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(master=self, text="Add Controller", font=self.default_font, fg_color="green", command=lambda:self.__clear_widgets())
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(master=self, text="Remove Controller", font=self.default_font, fg_color="red", command=lambda:self.__remove_controller())
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------GPIO CONFIG FRAME-CONTROLLER SETUP FRAME--------------------------------------------------
        #Create a frame to contain settings about the individual client device
        cntrl_setup_frame = ctk.CTkScrollableFrame(master=self, border_color="green", border_width=1)
        cntrl_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for cntrl_setup_frame

        cntrl_setup_frame.columnconfigure(0, weight=0, pad=20)
        cntrl_setup_frame.columnconfigure(1, weight=1, pad=20)
        cntrl_setup_frame.columnconfigure(2, weight=1, pad=20)

        for i in range(29):
            cntrl_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------CONTROLLER SETUP FRAME WIDGETS--------------------------------------------------
        #------------------------------Controller Attributes--------------------------------------------------
        title1_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Controller Setup", font=self.default_font)
        title1_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        ctrl_id_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Controller ID:", font=self.default_font)
        ctrl_id_label.grid(column=0, row=1, sticky="w", padx=20)

        ctrl_id_data_label = ctk.CTkLabel(master=cntrl_setup_frame, text="", font=self.default_font, textvariable=self.controller_id_var)
        ctrl_id_data_label.grid(column=1, row=1, sticky="w", padx=20)

        ctrl_name_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Controller Name:", font=self.default_font)
        ctrl_name_label.grid(column=0, row=2, sticky="w", padx=20)

        ctrl_name_entry = ctk.CTkEntry(master=cntrl_setup_frame, textvariable=self.controller_name_var, font=self.default_font)
        ctrl_name_entry.grid(column=1, row=2, columnspan =2, sticky="ew", padx=20)

        loc_rem_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Local / Remote:", font=self.default_font)
        loc_rem_label.grid(column=0, row=3, sticky="w", padx=20)

        loc_rem_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable=self.loc_rem_var, values=["Local"], state="readonly", command=lambda value:self.show_hide_ip_com(value), font=self.default_font, dropdown_font=self.default_font)
        loc_rem_cbox.grid(column=1, row=3, columnspan =2, sticky="ew", padx=20)

        self.ip_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Controller IP Address:", font=self.default_font)
        #self.ip_label.grid(column=0, row=4)

        self.ip_entry = ctk.CTkEntry(master=cntrl_setup_frame, textvariable=self.ip_var, font=self.default_font)
        #self.ip_entry.grid(column=1, row=4, columnspan =2, sticky="ew", padx=20)
        
        self.com_label = ctk.CTkLabel(master=cntrl_setup_frame, text="COM Port:", font=self.default_font)
        #self.com_label.grid(column=0, row=5)

        #Values assigned to combobox usning event binding
        self.com_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable=self.com_port_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        #self.com_cbox.grid(column=1, row=5, columnspan =2, sticky="ew", padx=20)

        ctrl_type_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Controller Type:", font=self.default_font)
        ctrl_type_label.grid(column=0, row=6, sticky="w", padx=20)

        ctrl_type_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable=self.controller_type_var, values=["Arduino Uno"], state="readonly", font=self.default_font, dropdown_font=self.default_font)
        ctrl_type_cbox.grid(column=1, row=6, columnspan =2, sticky="ew", padx=20)



        ##------------------------------GPIO Configuration--------------------------------------------------
        title2_label = ctk.CTkLabel(master=cntrl_setup_frame, text="GPIO Configuration", font=self.default_font, pady=15)
        title2_label.grid(column=0, row=7, columnspan=3, sticky="ew")

        #List containing the possible modes a GPIO pin can be set to - In the future outputs will be added
        gpio_setting = ["in", "disabled"]

        p2_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 2:", font=self.default_font)
        p2_label.grid(column=0, row=8, sticky="w", padx=100)

        p2_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable=self.pin2_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p2_cbox.grid(column=1, row=8, columnspan =2, sticky="ew", padx=20)

        p3_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 3:", font=self.default_font)
        p3_label.grid(column=0, row=9, sticky="w", padx=100)

        p3_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable=self.pin3_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p3_cbox.grid(column=1, row=9, columnspan =2, sticky="ew", padx=20)

        p4_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 4:", font=self.default_font)
        p4_label.grid(column=0, row=10, sticky="w", padx=100)

        p4_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin4_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p4_cbox.grid(column=1, row=10, columnspan =2, sticky="ew", padx=20)

        p5_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 5:", font=self.default_font)
        p5_label.grid(column=0, row=11, sticky="w", padx=100)

        p5_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin5_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p5_cbox.grid(column=1, row=11, columnspan =2, sticky="ew", padx=20)

        p6_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 6:", font=self.default_font)
        p6_label.grid(column=0, row=12, sticky="w", padx=100)

        p6_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin6_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p6_cbox.grid(column=1, row=12, columnspan =2, sticky="ew", padx=20)

        p7_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 7:", font=self.default_font)
        p7_label.grid(column=0, row=13, sticky="w", padx=100)

        p7_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin7_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p7_cbox.grid(column=1, row=13, columnspan =2, sticky="ew", padx=20)

        p8_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 8:", font=self.default_font)
        p8_label.grid(column=0, row=14, sticky="w", padx=100)

        p8_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin8_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p8_cbox.grid(column=1, row=14, columnspan =2, sticky="ew", padx=20)

        p9_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 9:", font=self.default_font)
        p9_label.grid(column=0, row=15, sticky="w", padx=100)

        p9_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin9_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p9_cbox.grid(column=1, row=15, columnspan =2, sticky="ew", padx=20)

        p10_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 10:", font=self.default_font)
        p10_label.grid(column=0, row=16, sticky="w", padx=100)

        p10_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin10_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p10_cbox.grid(column=1, row=16, columnspan =2, sticky="ew", padx=20)

        p11_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 11:", font=self.default_font)
        p11_label.grid(column=0, row=17, sticky="w", padx=100)

        p11_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin11_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p11_cbox.grid(column=1, row=17, columnspan =2, sticky="ew", padx=20)

        p12_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 12:", font=self.default_font)
        p12_label.grid(column=0, row=18, sticky="w", padx=100)

        p12_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin12_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p12_cbox.grid(column=1, row=18, columnspan =2, sticky="ew", padx=20)

        p13_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 13:", font=self.default_font)
        p13_label.grid(column=0, row=19, sticky="w", padx=100)

        p13_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin13_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p13_cbox.grid(column=1, row=19, columnspan =2, sticky="ew", padx=20)

        p14_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 14:", font=self.default_font)
        p14_label.grid(column=0, row=20, sticky="w", padx=100)

        p14_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin14_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p14_cbox.grid(column=1, row=20, columnspan =2, sticky="ew", padx=20)

        p15_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 15:", font=self.default_font)
        p15_label.grid(column=0, row=21, sticky="w", padx=100)

        p15_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin15_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p15_cbox.grid(column=1, row=21, columnspan =2, sticky="ew", padx=20)

        p16_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 16:", font=self.default_font)
        p16_label.grid(column=0, row=22, sticky="w", padx=100)

        p16_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin16_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p16_cbox.grid(column=1, row=22, columnspan =2, sticky="ew", padx=20)

        p17_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 17:", font=self.default_font)
        p17_label.grid(column=0, row=23, sticky="w", padx=100)

        p17_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin17_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p17_cbox.grid(column=1, row=23, columnspan =2, sticky="ew", padx=20)

        p18_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 18:", font=self.default_font)
        p18_label.grid(column=0, row=24, sticky="w", padx=100)

        p18_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin18_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p18_cbox.grid(column=1, row=24, columnspan =2, sticky="ew", padx=20)

        p19_label = ctk.CTkLabel(master=cntrl_setup_frame, text="Pin 19:", font=self.default_font)
        p19_label.grid(column=0, row=25, sticky="w", padx=100)

        p19_cbox = ctk.CTkComboBox(master=cntrl_setup_frame, variable = self.pin19_var, values=gpio_setting, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        p19_cbox.grid(column=1, row=25, columnspan =2, sticky="ew", padx=20)
        
        save_btn = ctk.CTkButton(master=self, text="Save", font=self.default_font, fg_color="green", command=lambda:self.__save_entry_data())
        save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)

     #Refreshes combobox options
    
    def refresh_cboxs(self, event):
        self.logger.info("Refreshing device_config combobox options")

        #Clear the list of serial ports
        self.serial_ports_list.clear()

        for port in comports():
            print(port)
            #Convert the ListPortInfo object to a string
            port_string = str(port)
            #Split the string to extract the address
            port_address = port_string.split()[0]
            #Add the address to the list
            self.serial_ports_list.append(port_address)

        self.logger.info(f"Available serial ports:{self.serial_ports_list}")        
        #Assign the values to the combobox
        self.com_cbox.configure(values=self.serial_ports_list)

    #Shows / hides ip / com entry fields based on selctions
    def show_hide_ip_com(self, value=None):
        #Get the selection from the local / remote comobox
        selection = self.loc_rem_var.get()
        #If local selected remove ip address input fields, show com ports
        if selection == "Local":
            self.ip_label.grid_forget()
            self.ip_entry.grid_forget()
            self.com_label.grid(column=0, row=5, sticky="w", padx=20)
            self.com_cbox.grid(column=1, row=5, columnspan =2, sticky="ew", padx=20)
            self.ip_var.set("")
            self.logger.debug("Local Selected - IP=hidden, COM=show")
        #If remote selected show ip address input fields, hide com port
        if selection == "Remote":
            self.ip_label.grid(column=0, row=4, sticky="w", padx=20)
            self.ip_entry.grid(column=1, row=4, columnspan =2, sticky="ew", padx=20)
            self.com_label.grid_forget()
            self.com_cbox.grid_forget()
            self.com_port_var.set("")
            self.logger.debug("Remote Selected - IP=show, COM=hidden")
        #If nothing selected hide all
        if selection == "":
            self.ip_label.grid_forget()
            self.ip_entry.grid_forget()
            self.com_label.grid_forget()
            self.com_cbox.grid_forget()
            self.ip_var.set("")
            self.com_port_var.set("")
            self.logger.debug("Nothing Selected - IP=hidden, COM=hidden")

    def __verify_input(self):
        valid = True
        self.logger.info("Validating input fields")
        if self.controller_name_var.get() == "":
            self.logger.info("Controller Name Empty")
            valid = False
        if self.loc_rem_var.get() == "":
            self.logger.info("Local / Remote Empty")
            valid = False
        if ((self.ip_var.get() == "") or (Validation.validate_ip(str(self.ip_var.get())) == False)) & (self.loc_rem_var.get() == "Remote"):    #TODO:Verify
            self.logger.info("Controller IP Empty or invalid format")
            valid = False
        if (self.com_port_var.get() == "") & (self.loc_rem_var.get() == "Local"):
            self.logger.info("Controller Port Empty")
            valid = False
        if self.controller_type_var.get() == "":
            self.logger.info("Controller Type Empty")
            valid = False
        for pin in self.pin_var_list:
            if pin.get() == "":
                self.logger.info("One or more Pin Modes have not been set")
                valid = False
                break
        self.logger.debug(f"Valid = {valid}")
        return valid

class Display_Templates(BaseFrame):

    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        self.parent = parent

        #GUI Variables - to allow dynamic updating
        self.template_id_var = StringVar()
        self.template_name_var = StringVar()
        self.layout_var = StringVar()
        self.logo_var = StringVar()
        self.clock_var = StringVar()
        self.indicator_number_var = StringVar()

        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        #Add the display widgets to the frame
        self.__add_widgets()

        #Store a list of the indicator widgets to allow looping
        self.indicator_list = [
            self.indicator_1,
            self.indicator_2,
            self.indicator_3,
            self.indicator_4,
            self.indicator_5,
            self.indicator_6
        ]

        #Refresh the tree view with the current database data so it's not empty on startup
        self.logger.info("Retrieving current display_templates table data")
        updated_rows = self.db.get_current_table_data("display_templates")

        self.logger.info("Updating display_templates tree")
        self.__update_tree(updated_rows)

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)

    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        #Set the state indicator variable to False, indicating an item is to be modified
        self.new_item = False
        self.logger.info("Set State Indicator to False - an existing item is being modified")

        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update teh widgets if a valid tree item is selected
        if selected != '':
            #Retrieve the id of the messaging group
            db_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item
            row = self.db.get_current_row_data("display_templates", "display_template_id", db_id)
            self.logger.info("Populating entry fields with data for selected tree viewer item")
            #Populate the fields with the data
            self.template_id_var.set(row[0][0])
            self.template_name_var.set(row[0][1])
            self.layout_var.set(row[0][2])

            logo_id = row[0][3]
            #Retrieve logo name from the database
            logo_name = self.db.get_1column_data("image_name", "images", "image_id", logo_id)[0]
            self.logger.debug(f"Logo name:{logo_name}")
            self.logo_var.set(logo_name)
            
            self.clock_var.set(row[0][4])
            self.indicator_number_var.set(row[0][5])
            self.show_hide_indicators(row[0][5])
            self.indicator_1.set_inputs(row[0][6], row[0][7], row[0][8])
            self.indicator_2.set_inputs(row[0][9], row[0][10], row[0][11])
            self.indicator_3.set_inputs(row[0][12], row[0][13], row[0][14])
            self.indicator_4.set_inputs(row[0][15], row[0][16], row[0][17])
            self.indicator_5.set_inputs(row[0][18], row[0][19], row[0][20])
            self.indicator_6.set_inputs(row[0][21], row[0][22], row[0][23])
            self.logger.info("Updated all entry Widgets")
        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
    
    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Set the state indicator variable to True, indicating a new item is to be added
        self.new_item = True
        self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

        #Clear All entry Widgets
        self.template_id_var.set("")
        self.template_name_var.set("")
        self.layout_var.set("")
        self.logo_var.set("")
        self.clock_var.set("")
        self.indicator_number_var.set("6")
        self.show_hide_indicators("6")
        self.indicator_1.clear_inputs()
        self.indicator_2.clear_inputs()
        self.indicator_3.clear_inputs()
        self.indicator_4.clear_inputs()
        self.indicator_5.clear_inputs()
        self.indicator_6.clear_inputs()
        
        self.logger.info("Cleared all entry Widgets")
    
    #Refreshes Treeviewer data
    def __update_tree(self, updated_rows):
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared display_template tree")

        for row in updated_rows:
            #Add items to the treeviewer, Indexes: 0=ID, 1=Message Group Name
            #Format: (Parent=(iid), index) "" is the top level parent node
            self.tree.insert("", tk.END, text=row[0], values=(row[1],)) 
            self.logger.info(f"Added {row[1]} to the tree")
        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        self.logger.info("Save Button Clicked")
        #Verify all entries populated
        valid = self.__verify_input()
        #Determine whether a new item or modifying existing
        #Adding a new item
        if valid == True:
            if self.new_item == True:
                self.logger.info("Adding New Item to Database")
                #Generate a timestamp
                timestamp = datetime.datetime.now()
                #Get the image_id using the image_name from the combobox
                image_id = self.image_dict[self.logo_var.get()]
                #Add all the current entry data to the database
                self.db.add_display_template(self.template_name_var.get(), self.layout_var.get(), image_id, self.clock_var.get(), self.indicator_number_var.get(), self.indicator_1.get_inputs()[0], self.indicator_1.get_inputs()[1], self.indicator_1.get_inputs()[2], self.indicator_2.get_inputs()[0], self.indicator_2.get_inputs()[1], self.indicator_2.get_inputs()[2], self.indicator_3.get_inputs()[0], self.indicator_3.get_inputs()[1], self.indicator_3.get_inputs()[2], self.indicator_4.get_inputs()[0], self.indicator_4.get_inputs()[1], self.indicator_4.get_inputs()[2], self.indicator_5.get_inputs()[0], self.indicator_5.get_inputs()[1], self.indicator_5.get_inputs()[2], self.indicator_6.get_inputs()[0], self.indicator_6.get_inputs()[1], self.indicator_6.get_inputs()[2], timestamp)
                self.logger.info("Added new item to database")

            #Modifying existing item    
            else:
                #Get the value from the ID and name widgets
                db_id = self.template_id_var.get()
                name = self.template_name_var.get()

                self.logger.info("Modifing existing database entry")
                self.logger.info(f"Updating database entry for display template: {name}, ID={db_id}")
                #Get the image_id from the image name
                image_id = self.image_dict[self.logo_var.get()]
                #Update the existing entry in the database
                columns_dict = {"display_template_name": self.template_name_var.get(),  
                            "layout": self.layout_var.get(),
                            "logo_image_id": image_id, 
                            "clock_type": self.clock_var.get(), 
                            "indicators_displayed": self.indicator_number_var.get(), 
                            "indicator_1_label": self.indicator_1.get_inputs()[0], 
                            "indicator_1_flash": self.indicator_1.get_inputs()[1], 
                            "indicator_1_colour": self.indicator_1.get_inputs()[2], 
                            "indicator_2_label": self.indicator_2.get_inputs()[0], 
                            "indicator_2_flash": self.indicator_2.get_inputs()[1], 
                            "indicator_2_colour": self.indicator_2.get_inputs()[2],
                            "indicator_3_label": self.indicator_3.get_inputs()[0], 
                            "indicator_3_flash": self.indicator_3.get_inputs()[1], 
                            "indicator_3_colour": self.indicator_3.get_inputs()[2],
                            "indicator_4_label": self.indicator_4.get_inputs()[0], 
                            "indicator_4_flash": self.indicator_4.get_inputs()[1], 
                            "indicator_4_colour": self.indicator_4.get_inputs()[2],
                            "indicator_5_label": self.indicator_5.get_inputs()[0], 
                            "indicator_5_flash": self.indicator_5.get_inputs()[1], 
                            "indicator_5_colour": self.indicator_5.get_inputs()[2],
                            "indicator_6_label": self.indicator_6.get_inputs()[0], 
                            "indicator_6_flash": self.indicator_6.get_inputs()[1], 
                            "indicator_6_colour": self.indicator_6.get_inputs()[2],
                            "last_changed" : datetime.datetime.now()
                            }
                for column in columns_dict:
                    self.logger.info(f"Updating column: {column} with {columns_dict[column]}")
                    self.db.update_row("display_templates", column, "display_template_id", columns_dict[column], db_id)
                
            #Refresh the tree
            updated_rows = self.db.get_current_table_data("display_templates")
            self.__update_tree(updated_rows)
            #Clear all entry widget fields
            self.__clear_widgets()


    #Removes an entry from the database
    def __remove_display_template(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the display template
                db_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database
                feedback = self.db.delete_row("display_templates", "display_template_id", db_id)
                #Item is only deleted if there are no database integrity errors thrown
                if feedback == True:
                    self.logger.info(f"Deleted display template with ID={db_id} from the database")
                    #Clear the entry widgets
                    self.__clear_widgets()
                    #Refresh the tree view
                    updated_rows = self.db.get_current_table_data("display_templates")
                    self.__update_tree(updated_rows)
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning(feedback)
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")

    #Creates and adds GUI widgets to the frame
    def __add_widgets(self):
        #------------------------------DEVICE CONFIG FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)
        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(self, text="Add Template", font=self.default_font, fg_color="green", command=lambda:self.__clear_widgets())
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(self, text="Remove Template", font=self.default_font, fg_color="red", command=lambda:self.__remove_display_template())
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------DEVICE CONFIG FRAME-DEVICE SETUP FRAME--------------------------------------------------
        #Create a frame to contain settings about the individual client device
        self.display_setup_frame = ctk.CTkScrollableFrame(self, border_color="green", border_width=1)
        self.display_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for self.display_setup_frame

        self.display_setup_frame.columnconfigure(0, weight=0, pad=20)
        self.display_setup_frame.columnconfigure(1, weight=1, pad=20)
        self.display_setup_frame.columnconfigure(2, weight=1, pad=20)

        for i in range(18):
            self.display_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------DEVICE SETUP FRAME WIDGETS--------------------------------------------------
        #------------------------------Device Attributes--------------------------------------------------

        title2_label = ctk.CTkLabel(master=self.display_setup_frame, text="Display Template", font=self.default_font)
        title2_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        template_id_label = ctk.CTkLabel(master=self.display_setup_frame, text="Template ID:", font=self.default_font)
        template_id_label.grid(column=0, row=1, sticky="w", padx=20)

        template_id_data = ctk.CTkLabel(master=self.display_setup_frame, text="", textvariable=self.template_id_var, font=self.default_font)
        template_id_data.grid(column=1, row=1, sticky="w", padx=20)

        template_name_label = ctk.CTkLabel(master=self.display_setup_frame, text="Template Name:", font=self.default_font)
        template_name_label.grid(column=0, row=2, sticky="w", padx=20)

        template_name_entry = ctk.CTkEntry(master=self.display_setup_frame, textvariable=self.template_name_var, font=self.default_font)
        template_name_entry.grid(column=1, row=2, columnspan =2, sticky="ew", padx=20)
        #Layout
        layout_label = ctk.CTkLabel(master=self.display_setup_frame, text="Display Layout:", font=self.default_font)
        layout_label.grid(column=0, row=3, sticky="w", padx=20)

        layout_cbox = ctk.CTkComboBox(master=self.display_setup_frame, state="readonly", variable=self.layout_var, values=["Clock With Indicators", "Fullscreen Clock"], font=self.default_font, dropdown_font=self.default_font)
        layout_cbox.grid(column=1, row=3, columnspan =2, sticky="ew", padx=20)

        #Logo
        logo_label = ctk.CTkLabel(master=self.display_setup_frame, text="Logo:", font=self.default_font)
        logo_label.grid(column=0, row=4, sticky="w", padx=20)

        self.logo_cbox = ctk.CTkComboBox(self.display_setup_frame, font=self.default_font, state="readonly", variable=self.logo_var, dropdown_font=self.default_font)
        self.logo_cbox.grid(column=1, row=4, columnspan=2, sticky='ew', padx=20)

        #Clock
        clock_type_label = ctk.CTkLabel(master=self.display_setup_frame, text="Clock Type:", font=self.default_font)
        clock_type_label.grid(column=0, row=5, sticky="w", padx=20)

        clock_type_cbox = ctk.CTkComboBox(master=self.display_setup_frame, variable=self.clock_var, values=["Leitch Clock", "Analogue Clock"], font=self.default_font, dropdown_font=self.default_font)
        clock_type_cbox.grid(column=1, row=5, columnspan =2, sticky="ew", padx=20)
        #Select Number of Indicators
        number_indicators_label = ctk.CTkLabel(master=self.display_setup_frame, text="Select Number Of Indicators to Display:", font=self.default_font)
        number_indicators_label.grid(column=0, row=6, sticky="w", padx=20)

        number_indicators_cbox = ctk.CTkComboBox(master=self.display_setup_frame, values=["1","2","3","4","5","6"], variable=self.indicator_number_var, command=lambda value:self.show_hide_indicators(value), font=self.default_font, dropdown_font=self.default_font)
        number_indicators_cbox.grid(column=1, row=6, columnspan =2, sticky="ew", padx=20)

        #Indicators
        #Enable/ Disable - Flashing / Non-Flashing - Label - On Colour
        indicator_label = ctk.CTkLabel(master=self.display_setup_frame, text="Indicators", font=self.default_font)
        indicator_label.grid(column=0, row=7, columnspan=3, sticky="ew", pady=15)
        #Indicator Settings
        self.indicator_1 = IndicatorSettings(self.display_setup_frame, "Indicator 1:")
        #self.indicator_1.grid(column=0, row=9, columnspan =3, sticky="nsew", padx=20)
        self.indicator_2 = IndicatorSettings(self.display_setup_frame, "Indicator 2:")
        #self.indicator_2.grid(column=0, row=10, columnspan =3, sticky="nsew", padx=20)
        self.indicator_3 = IndicatorSettings(self.display_setup_frame, "Indicator 3:")
        #self.indicator_3.grid(column=0, row=11, columnspan =3, sticky="nsew", padx=20)
        self.indicator_4 = IndicatorSettings(self.display_setup_frame, "Indicator 4:")
        #self.indicator_4.grid(column=0, row=12, columnspan =3, sticky="nsew", padx=20)
        self.indicator_5 = IndicatorSettings(self.display_setup_frame, "Indicator 5:")
        #self.indicator_5.grid(column=0, row=13, columnspan =3, sticky="nsew", padx=20)
        self.indicator_6 = IndicatorSettings(self.display_setup_frame, "Indicator 6:")
        #self.indicator_6.grid(column=0, row=14, columnspan =3, sticky="nsew", padx=20)

        #Save Button
        save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", command=lambda:self.__save_entry_data(), font=self.default_font)
        save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)

    def select_logo(self):
        path = filedialog.askopenfilename()
        print(path)
        self.logo_var.set(path)

    def show_hide_indicators(self, number_of_indicators:str):
        indicator_list = [self.indicator_1, self.indicator_2, self.indicator_3, self.indicator_4, self.indicator_5, self.indicator_6]

        for indicator in indicator_list:
            indicator.clear_inputs()
            indicator.grid_forget()
            
        for i in range(int(number_of_indicators)):
            indicator_list[i].grid(column=0, row=(i+10), columnspan =3, sticky="nsew", padx=20)
            #Added to fix bug where indicator dropdowns populated blank until hovered with mouse
            self.update()


    def convert_to_blob(self, path:str):
        #Open the image file and convert to binary data
        binary_logo = open(path, "rb")
        blob_logo = binary_logo.read()
        return blob_logo
    
    def convert_from_blob(self, blob):
        blob_logo = open("gui/logo_temp.jpg", "wb")
        blob_logo.write(blob)

    def refresh_cboxs(self, event):
        self.logger.info("Refreshing device_config combobox options")
        #Query the database for all images
        image_table = self.db.get_2column_data("image_id", "image_name", "images")
        self.logger.debug(f"Image_table: {image_table}")
        #Convert table data to a dictionary and list
        self.image_dict = {} #Will store reference to the id of each image
        self.image_list = [] #Will hold all image names to show in dropdown

        #Extract name and id from each row in the table puttin them in the list and dictionary
        for item in image_table:
            id = item[0]
            name = item[1]
            self.image_dict[name] = id
            self.image_list.append(name)

        #Set combobox values
        self.logo_cbox.configure(values = self.image_list)

    def __verify_input(self) -> bool:
        if self.template_name_var.get() == "":
            self.logger.info("Display Template name empty.")
            return False
        if self.layout_var.get() == "":
            self.logger.info("Display Layout empty.")
            return False
        if self.logo_var.get() == "":
            self.logger.info("Logo empty.")
            return False
        if self.clock_var.get == "":
            self.logger.info("Clock Type empty.")
            return False
        if self.indicator_number_var.get() == "":
            self.logger.info("Number of indicators empty.")
            return False
        
        #Get the number of indicator setting rows displayed onscreen
        number_of_indicators = int(self.indicator_number_var.get())
        #Check that all settings have been set
        for i in range(number_of_indicators):
            input1, input2, input3 = self.indicator_list[i].get_inputs()
            if input1 == "" or input2 == "" or input3 == "":
                self.logger.info("One or more indicator settings empty.")
                return False
        #If all fields populated return True
        return True
        
class Messaging_Groups(BaseFrame):

    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #GUI Variables - to allow dynamic updating
        self.message_group_name_var = StringVar()
        self.message_group_id_var = StringVar()

        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        self.__add_widgets()

        #Refresh the tree view with the current database data so it's not empty on startup
        updated_rows = self.db.get_current_table_data("messaging_groups")
        self.__update_tree(updated_rows)

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)
    
    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        #Set the state indicator variable to False, indicating an item is to be modified
        self.new_item = False
        self.logger.info("Set State Indicator to False - an existing item is being modified")

        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update teh widgets if a valid tree item is selected
        if selected != '':
            #Retrieve the id of the messaging group
            db_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item
            row = self.db.get_current_row_data("messaging_groups", "messaging_group_id", db_id)
            self.logger.info("Populating entry fields with data for selected tree viewer item")
            #Populate the fields with the data
            self.message_group_id_var.set(row[0][0]) #ID
            self.message_group_name_var.set(row[0][1]) #Name
            self.logger.info("Updated all entry Widgets")
        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
    
    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Set the state indicator variable to True, indicating a new item is to be added
        self.new_item = True
        self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

        #Clear All entry Widgets
        self.message_group_id_var.set("")
        self.message_group_name_var.set("")
        self.logger.info("Cleared all entry Widgets")
    
    #Refreshes Treeviewer data
    def __update_tree(self, updated_rows):
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared messaging_groups tree")

        for row in updated_rows:
            #Add items to the treeviewer, Indexes: 0=ID, 1=Message Group Name
            #Format: (Parent=(iid), index) "" is the top level parent node
            self.tree.insert("", tk.END, text=row[0], values=(row[1],)) 
            self.logger.info(f"Added {row[1]} to the tree")
        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        #Get the value from the text entry widget
        message_group_name = self.message_group_name_var.get()
        #Check if the entry box contains text
        if message_group_name != "":
            #Determine whether a new item or modifying existing
            #Adding a new item
            if self.new_item == True:
                    self.logger.info("Adding New Item to Database")
                    #Build the osc address for the messaging group, this is used to send messages to the group
                    osc_address = "/" + message_group_name + "/ticker"
                    #Add the value to the database table
                    self.db.add_messaging_group(message_group_name, osc_address)
                    self.logger.info("Added new item to database")
                    
            #Modifying existing item    
            else:
                #Get the value from the ID and name widgets
                db_id = self.message_group_id_var.get()

                self.logger.info("Modifing existing database entry")
                #Build the updated osc address for the messaging group, this is used to send messages to the group
                osc_address = "/" + message_group_name + "/ticker"
                #Update the existing entry in the database
                self.db.update_row("messaging_groups", "messaging_group_name", "messaging_group_id", message_group_name, db_id)
                self.db.update_row("messaging_groups", "osc_address", "messaging_group_id", osc_address, db_id)
            
            #Refresh the tree
            updated_rows = self.db.get_current_table_data("messaging_groups")
            self.__update_tree(updated_rows)
            #Clear all entry widget fields
            self.__clear_widgets()

        else:
            self.logger.info("Message Group Name Empty")

    #Removes an entry from the database
    def __remove_messaging_group(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the messaging group
                db_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database
                feedback = self.db.delete_row("messaging_groups", "messaging_group_id", db_id)
                if feedback == True:
                    self.logger.info(f"Deleted messaging group with ID={db_id} from the database")
                    #Clear the entry widgets
                    self.__clear_widgets()
                    #Refresh the tree view
                    updated_rows = self.db.get_current_table_data("messaging_groups")
                    self.__update_tree(updated_rows)
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning(feedback)
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")

    #Creates and adds GUI widgets to the frame
    def __add_widgets(self):
        #------------------------------DEVICE CONFIG FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)
        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(self, text="Add Group", fg_color="green", command=lambda:self.__clear_widgets(), font=self.default_font)
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(self, text="Remove Group", fg_color="red", command=lambda:self.__remove_messaging_group(), font=self.default_font)
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------DEVICE CONFIG FRAME-DEVICE SETUP FRAME--------------------------------------------------
        #Create a frame to contain settings about the individual client device
        self.messaging_setup_frame = ctk.CTkScrollableFrame(self, border_color="green", border_width=1)
        self.messaging_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for self.messaging_setup_frame

        self.messaging_setup_frame.columnconfigure(0, weight=0, pad=20)
        self.messaging_setup_frame.columnconfigure(1, weight=1, pad=20)
        self.messaging_setup_frame.columnconfigure(2, weight=1, pad=20)

        for i in range(29):
            self.messaging_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------DEVICE SETUP FRAME WIDGETS--------------------------------------------------
        #------------------------------Device Attributes--------------------------------------------------
        title1_label = ctk.CTkLabel(master=self.messaging_setup_frame, text="Messaging Group Creation", font=self.default_font)
        title1_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        id_label = ctk.CTkLabel(master=self.messaging_setup_frame, text="Messaging Group ID:", font=self.default_font)
        id_label.grid(column=0, row=1, sticky="w", padx=20)

        id_data_label = ctk.CTkLabel(master=self.messaging_setup_frame, text="", textvariable=self.message_group_id_var, font=self.default_font)
        id_data_label.grid(column=1, row=1, sticky="w", padx=20)

        name_label = ctk.CTkLabel(master=self.messaging_setup_frame, text="Messaging Group Name:", font=self.default_font)
        name_label.grid(column=0, row=2, sticky="w", padx=20)

        self.name_entry = ctk.CTkEntry(master=self.messaging_setup_frame, textvariable=self.message_group_name_var, font=self.default_font)
        self.name_entry.grid(column=1, row=2, columnspan =2, sticky="ew", padx=20)

        save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", command=lambda:self.__save_entry_data(), font=self.default_font)
        save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)

class Server_Config(BaseFrame):

    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #Variables
        self.server_ip_var = tk.StringVar()

        self.__add_widgets()

    def __add_widgets(self):
        #------------------------------MAIN FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        tree = CustomTree(self)
        tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(self, text="Add Group", fg_color="green", font=self.default_font)
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(self, text="Remove Group", fg_color="red", font=self.default_font)
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------MAIN FRAME-IP CONFIG FRAME--------------------------------------------------
        #Create a frame to contain settings server ip
        self.ip_setup_frame = ctk.CTkFrame(self, border_color="green", border_width=1)
        self.ip_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for self.ip_setup_frame

        self.ip_setup_frame.columnconfigure(0, weight=0, pad=20)
        self.ip_setup_frame.columnconfigure(1, weight=1, pad=20)
        self.ip_setup_frame.columnconfigure(2, weight=1, pad=20)

        for i in range(29):
            self.ip_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------MAIN FRAME-SERVER CONFIG FRAME--------------------------------------------------
        
        #Create a frame to contain settings about the individual client device
        self.server_config_frame = ctk.CTkFrame(self, border_color="green", border_width=1)
        self.server_config_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for self.server_config_frame

        self.server_config_frame.columnconfigure(0, weight=0, pad=20)
        self.server_config_frame.columnconfigure(1, weight=1, pad=20)
        self.server_config_frame.columnconfigure(2, weight=1, pad=20)

        for i in range(29):
            self.server_config_frame.rowconfigure(i, weight=0, pad=10)

        self.frames_list = [self.server_config_frame, self.ip_setup_frame]

        #------------------------------IP CONFIG FRAME WIDGETS--------------------------------------------------
        ip_config_title_label = ctk.CTkLabel(master=self.ip_setup_frame, text="Server IP Configuration", font=self.default_font)
        ip_config_title_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        ip_label = ctk.CTkLabel(master=self.ip_setup_frame, text="Server IP", font=self.default_font)
        ip_label.grid(column=0, row=1, sticky="w", padx=20)

        self.ip_combobox = ctk.CTkComboBox(master=self.ip_setup_frame, state="readonly", variable=self.server_ip_var, font=self.default_font, dropdown_font=self.default_font)
        self.ip_combobox.grid(column=2, row=1, columnspan =1, sticky="ew", padx=20)

        #Save Button
        self.save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", command=lambda:self.__save_ip_entry_data(), font=self.default_font)

        #Back Button
        self.back_btn = ctk.CTkButton(master=self, text="Back", fg_color="red", command=lambda:self.__show_server_config_frame(), font=self.default_font)

        #------------------------------SERVER CONFIG FRAME WIDGETS--------------------------------------------------
        title1_label = ctk.CTkLabel(master=self.server_config_frame, text="Server Configuration", font=self.default_font)
        title1_label.grid(column=0, row=0, columnspan=3, sticky="ew")

        initialise_label = ctk.CTkLabel(master=self.server_config_frame, text="Initialise Database", font=self.default_font)
        initialise_label.grid(column=0, row=1, sticky="w", padx=20)

        initialise_btn = ctk.CTkButton(master=self.server_config_frame, text="Initialise", command= lambda:(self.__initialise_database_warn()), font=self.default_font)
        initialise_btn.grid(column=2, row=1, columnspan =1, sticky="ew", padx=20)

        backup_label = ctk.CTkLabel(master=self.server_config_frame, text="Backup Configuration", font=self.default_font)
        backup_label.grid(column=0, row=2, sticky="w", padx=20)

        backup_btn = ctk.CTkButton(master=self.server_config_frame, text="Backup", command= lambda:(self.__backup_database()), font=self.default_font)
        backup_btn.grid(column=2, row=2, columnspan =1, sticky="ew", padx=20)

        restore_label = ctk.CTkLabel(master=self.server_config_frame, text="Restore Configuration", font=self.default_font)
        restore_label.grid(column=0, row=3, sticky="w", padx=20)

        restore_btn = ctk.CTkButton(master=self.server_config_frame, text="Restore", command= lambda:(self.__restore_database()), font=self.default_font)
        restore_btn.grid(column=2, row=3, columnspan =1, sticky="ew", padx=20)

        ip_label = ctk.CTkLabel(master=self.server_config_frame, text="Set Server IP", font=self.default_font)
        ip_label.grid(column=0, row=4, sticky="w", padx=20)

        ip_btn = ctk.CTkButton(master=self.server_config_frame, text="IP Settings", command= lambda:(self.__show_ip_config_frame()), font=self.default_font)
        ip_btn.grid(column=2, row=4, columnspan =1, sticky="ew", padx=20)

    def __initialise_database_warn(self):
        answer = messagebox.askokcancel("!DANGER! Database Initialisation !DANGER!", "Are you sure you want to initialise the Database? Doing so will clear all data!")
        if answer == True:
            self.logger.info("User confirmed database is to be initialised!")
            self.db.initialise_database()
        else:
            self.logger.info("User aborted Database Initialisation")

    def __backup_database(self):
        try:
            #Copy the current working database to a seperat file
            self.db.backup_db()
            #Open a browser window to copy the backup file to external location
            self.logger.info("Asking user to specify backup save location.")
            path = filedialog.asksaveasfilename()
            #Copy the backup file to the chosen location
            self.logger.info("Copying backup file to user specified path.")
            shutil.copy("./database/backup_rds_db", path)
            self.logger.info("Backup Complete")
            messagebox.showinfo("Database Saved", "The database has been successfully backed up.")
        except FileNotFoundError:
            self.logger.info("Backup Unsuccessful")
            messagebox.showinfo("Database Backup Fail", "The database was not able to be backed up, a valid path was not selected.")
        except Exception as e:
            self.logger.info("Backup Unsuccessful")
            messagebox.showinfo("Database Backup Fail", "The database was not able to be backed up, reason:{e}")



    def __restore_database(self):
        answer = messagebox.askokcancel("Restore Database Backup", "Are you sure you wish to restore the database?\n Doing so will completley erase the current database.")
        if answer == True:
            try:
                #Close the connection to the database
                self.db.close_connection()
                #Get the path to the backup file from the user
                path = filedialog.askopenfilename()
                self.logger.info(path)
                #Rename to current db file name.old
                self.logger.info("Renaming current database rds_db.old")
                os.rename("database/rds_db", "database/rds_db.old")
                #Copy the file specified by the user into the current working dir and rename rds_db
                self.logger.info("Importing backup db and renaming rds_db")
                shutil.copy(path, "./database/rds_db")
                #Reconect to the database
                self.db.connect()
                messagebox.showinfo("Restore Database Backup", "Database Successfully Restored, please restart the application.")
            except Exception as e:
                self.logger.info("Restore Unsuccessful")
            messagebox.showinfo("Database Restore Fail", "The database was not able to be restored, reason:{e}")
        else:
            self.logger.debug("User aborted database restore.")
            
    def __raise_frame(self, frame_number):
        frame = self.frames_list[frame_number]
        self.logger.debug(f"Raising frame:{frame}")
        frame.tkraise()

    def __show_ip_config_frame(self):
        self.__populate_ip_combobox()
        self.back_btn.grid(column=1, row=1, sticky="ns", columnspan=1, rowspan=2, pady=20)
        self.save_btn.grid(column=3, row=1, sticky="ns", columnspan=1, rowspan=2, pady=20)
        self.__raise_frame(1)

    def __show_server_config_frame(self):
        self.back_btn.grid_forget()
        self.save_btn.grid_forget()
        self.__raise_frame(0)

    def __save_ip_entry_data(self):
        server_ip = self.server_ip_var.get()

        settings_dict = {"server_ip":server_ip}

        write_dict_to_file(settings_dict, "server/settings.json")
        
        self.__show_server_config_frame()

    def __populate_ip_combobox(self):
        #Read Settings file
        settings_dict = open_json_file("server/settings.json")
        #Only set ip's if settings file exists - otherwise defaults are used
        if settings_dict != False:
            self.server_ip_var.set(settings_dict["server_ip"])
            
        ip_list=get_machine_ip()
        self.ip_combobox.configure(values = ip_list)

class Image_Store(BaseFrame):
    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #GUI Variables - to allow dynamic updating
        self.image_name_var = StringVar()
        self.image_id_var = StringVar()

        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        #Add widgets to the frame
        self.__add_widgets()

        #Refresh the tree view with the current database data so it's not empty on startup
        self.__update_tree()

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)
    
    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update the widgets if a valid tree item is selected
        if selected != '':
            #Retrieve the id of the image
            image_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item
            image_data = self.db.get_current_row_data("images", "image_id", image_id)[0]
            self.logger.info("Populating entry fields with data for selected tree viewer item")
            #Populate the fields with the data
            self.viewer_frame.set_image_id(image_data[0])
            self.viewer_frame.set_image_name(image_data[1])
            self.viewer_frame.update_logo_preview(image_data[2])
            self.logger.info("Updated all entry Widgets")

            #Raise the image Viewer Frame
            self.__switch_to_view_frame()
        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
    
    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Clear All entry Widgets
        self.editor_frame.clear_image_preview()
        self.viewer_frame.clear_image_preview()
        self.viewer_frame.set_image_id("")
        self.viewer_frame.set_image_name("")
        self.logger.info("Cleared all entry Widgets")
    
    #Refreshes Treeviewer data
    def __update_tree(self):
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.debug(f"Deleted {row} from the tree")
        self.logger.info("Cleared messaging_groups tree")

        updated_rows = self.db.get_2column_data("image_id", "image_name", "images")

        for row in updated_rows:
            #Add items to the treeviewer, Indexes: 0=ID, 1=Message Group Name
            #Format: (Parent=(iid), index) "" is the top level parent node
            self.tree.insert("", tk.END, text=row[0], values=(row[1],)) 
            self.logger.info(f"Added {row[1]} to the tree")
        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        self.logger.info("Saving image to Database")
        #Get the path of the image file
        path = self.editor_frame.get_image_path()
        #Get name of image file from path
        image_name = os.path.basename(path)

        #If the path is not empty
        if path != "":
            #Convert image to a binary object
            blob_image = self.convert_to_blob(path)
            #Save image to database
            self.db.add_image(image_name, blob_image)

            self.logger.info(f"Saved image: {path} to Database")

            #Clear input fields
            self.__clear_widgets()
            #Raise Viewer Frame
            self.__switch_to_view_frame()
            #Update Tree
            self.__update_tree()
        else:
            self.logger.warning("No image selected - Abort save to database")


    def convert_to_blob(self, path:str):
        #Open the image file and convert to binary data
        binary_logo = open(path, "rb")
        blob_logo : bytes = binary_logo.read()
        return blob_logo

    #Removes an entry from the database
    def __remove_image(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the image
                image_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database
                feedback = self.db.delete_row("images", "image_id", image_id)
                if feedback == True:
                    self.logger.info(f"Deleted image with ID={image_id} from the database")
                    #Clear the entry widgets
                    self.__clear_widgets()
                    #Refresh the tree view
                    self.__update_tree()
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning(feedback)
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")

    #Creates and adds GUI widgets to the frame
    def __add_widgets(self):
        #------------------------------MAIN FRAME WIDGETS--------------------------------------------------
        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)
        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(self, text="Add Image", fg_color="green", command=lambda:self.__switch_to_edit_frame(), font=self.default_font)
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(self, text="Remove Image", fg_color="red", command=lambda:self.__remove_image(), font=self.default_font)
        del_btn.grid(column=0, row=2, sticky="nsew")

        self.editor_frame = ImagePicker(self)
        self.editor_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        self.viewer_frame = ImageViewer(self)
        self.viewer_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Store the frames in a tuple allows for raising
        self.image_frames = [self.editor_frame, self.viewer_frame]

        #Save Button
        self.save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", command=lambda:self.__save_entry_data(), font=self.default_font)

    #Raises edit frame to top and grids save button
    def __switch_to_edit_frame(self):
        frame :ctk.CTkScrollableFrame = self.image_frames[0]
        frame.tkraise()
        self.save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)
    #Raises view frame to top and hides save button
    def __switch_to_view_frame(self):
        frame :ctk.CTkScrollableFrame = self.image_frames[1]
        frame.tkraise()
        self.save_btn.grid_forget()
        
class Trigger_Config(BaseFrame):
    def __init__(self, parent, database_connection):
        super().__init__(parent, database_connection)

        #GUI Variables - to allow dynamic updating
        self.trigger_group_id_var = StringVar()
        self.trigger_group_name_var = StringVar()

        self.mic_live_trigger_ctrl_var = StringVar()
        self.mic_live_ctrl_id_var = StringVar()
        self.mic_live_trigger_pin_var = StringVar()

        self.tx_trigger_ctrl_var = StringVar()
        self.tx_ctrl_id_var = StringVar()
        self.tx_trigger_pin_var = StringVar()

        self.cue_trigger_ctrl_var = StringVar()
        self.cue_ctrl_id_var = StringVar()
        self.cue_trigger_pin_var = StringVar()

        self.line1_trigger_ctrl_var = StringVar()
        self.line1_ctrl_id_var = StringVar()
        self.line1_trigger_pin_var = StringVar()

        self.line2_trigger_ctrl_var = StringVar()
        self.line2_ctrl_id_var = StringVar()
        self.line2_trigger_pin_var = StringVar()

        self.control_trigger_ctrl_var = StringVar()
        self.control_ctrl_id_var = StringVar()
        self.control_trigger_pin_var = StringVar()
        
        #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
        # or a new item is being added, default=True for error protection
        self.new_item = True

        #Add the display widgets to the frame
        self.__add_widgets()

        #List variables for updating comboboxes
        #Stores the unique id of the controller
        self.controller_ids_list = []
        #Stores the human readable names of the controllers
        self.controller_names_list = []
        #Stores the selected GPI values for each row
        self.gpi_list = []
        
        self.combobox_list = [
            self.trig_mic_live_ind_ctrl_cbox, 
            self.trig_tx_ind_ctrl_cbox, 
            self.trig_cue_ind_ctrl_cbox, 
            self.trig_lin1_ind_ctrl_cbox, 
            self.trig_lin2_ind_ctrl_cbox, 
            self.trig_control_ind_ctrl_cbox
            ]
        self.pin_combobox_list = [
            self.trig_mic_live_ind_pin_cbox, 
            self.trig_tx_ind_pin_cbox, 
            self.trig_cue_ind_pin_cbox, 
            self.trig_lin1_ind_pin_cbox, 
            self.trig_lin2_ind_pin_cbox, 
            self.trig_control_ind_pin_cbox
            ]
        
        #Variable lists
        self.trigger_group_id_name_var_list = [
            self.trigger_group_id_var,
            self.trigger_group_name_var
        ]

        self.controller_name_cobobox_var_list = [
            self.mic_live_trigger_ctrl_var,
            self.tx_trigger_ctrl_var,
            self.cue_trigger_ctrl_var,
            self.line1_trigger_ctrl_var,
            self.line2_trigger_ctrl_var,
            self.control_trigger_ctrl_var
        ]

        self.controller_id_combobox_var_list = [
            self.mic_live_ctrl_id_var,
            self.tx_ctrl_id_var,
            self.cue_ctrl_id_var,
            self.line1_ctrl_id_var,
            self.line2_ctrl_id_var,
            self.control_ctrl_id_var,
        ]

        self.gpi_combobox_var_list = [
            self.mic_live_trigger_pin_var,
            self.tx_trigger_pin_var,
            self.cue_trigger_pin_var,
            self.line1_trigger_pin_var,
            self.line2_trigger_pin_var,
            self.control_trigger_pin_var
            ]
        #Used for updating combobox values
        #Keys must be correct OSC addresses for the trigger items
        self.controller_name_combobox_var_dict = {
            "/signal-lights/1" : self.mic_live_trigger_ctrl_var,
            "/signal-lights/2" : self.tx_trigger_ctrl_var,
            "/signal-lights/3" : self.cue_trigger_ctrl_var,
            "/signal-lights/4" : self.line1_trigger_ctrl_var,
            "/signal-lights/5" : self.line2_trigger_ctrl_var,
            "/signal-lights/6" : self.control_trigger_ctrl_var
        }
        #Keys must be correct OSC addresses for the trigger items
        self.controller_id_combobox_var_dict = {
            "/signal-lights/1" : self.mic_live_ctrl_id_var,
            "/signal-lights/2" : self.tx_ctrl_id_var,
            "/signal-lights/3" : self.cue_ctrl_id_var,
            "/signal-lights/4" : self.line1_ctrl_id_var,
            "/signal-lights/5" : self.line2_ctrl_id_var,
            "/signal-lights/6" : self.control_ctrl_id_var,
        }
        #Keys must be correct OSC addresses for the trigger items
        self.gpi_combobox_var_dict = {
            "/signal-lights/1" : self.mic_live_trigger_pin_var,
            "/signal-lights/2" : self.tx_trigger_pin_var,
            "/signal-lights/3" : self.cue_trigger_pin_var,
            "/signal-lights/4" : self.line1_trigger_pin_var,
            "/signal-lights/5" : self.line2_trigger_pin_var,
            "/signal-lights/6" : self.control_trigger_pin_var
        }
        #Keys must be correct OSC addresses for the trigger items
        self.trigger_list = [
            "/signal-lights/1",
            "/signal-lights/2",
            "/signal-lights/3",
            "/signal-lights/4",
            "/signal-lights/5",
            "/signal-lights/6"
        ]
        #Refresh the tree view with the current database data so it's not empty on startup
        self.logger.info("Retrieving current trigger_groups table data")
        updated_rows = self.db.get_current_table_data("trigger_groups")

        self.logger.info("Updating trigger_groups tree")
        self.__update_tree(updated_rows)

        #Setup Binding clicking a row to populating the data fields
        self.tree.bind("<ButtonRelease-1>", self.__populate_widget_data)

        #Setup Binding keyboard focus leaving trigger group name entry widget triggers osc strings to update
        self.trig_grp_name_entry.bind("<FocusOut>", self.__update_osc_strings)

        #Setup Binding mouse hover leaving trigger group name entry widget triggers osc strings to update
        self.trig_grp_name_entry.bind("<Leave>", self.__update_osc_strings)

    #Clears all the entry widgets in the GUI
    def __clear_widgets(self):
        #Set the state indicator variable to True, indicating a new item is to be added
        #self.new_item = True
        #self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

        #Clear All entry Widgets
        i = 0
        widgets_list = self.trigger_group_id_name_var_list + self.controller_name_cobobox_var_list + self.controller_id_combobox_var_list + self.gpi_combobox_var_list
        for widget in widgets_list:
            widget.set("")
            i += 1

        #Clear GPI combobox options 
        for combobox in self.pin_combobox_list:
            combobox.configure(values="")

        self.logger.info("Cleared all entry Widgets")

    def __add_trigger_group(self):
        self.logger.debug("##########################--Add Button Clicked--##########################")
        #Set state indicator to true as widgets are to be cleared
        self.new_item = True
        self.logger.info("Set State Indicator to True - No Tree Viewer item selected")
        #Clear entry widgets
        self.__clear_widgets()
    
    #Refreshes Treeviewer data
    def __update_tree(self, updated_rows):
        #Delete all current data in the tree by detecting current children.
        for row in self.tree.get_children():
            self.tree.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared trigger_groups tree")

        for row in updated_rows:
            #Add items to the treeviewer, Indexes: 0=ID, 1=Message Group Name
            #Format: (Parent=(iid), index) "" is the top level parent node
            self.tree.insert("", tk.END, text=row[0], values=(row[1],)) 
            self.logger.info(f"Added {row[1]} to the tree")
        self.logger.info("Tree Updated")

    #Saves entered data from the GUI to the datbase
    #Detecting whether it is a new item or modifying existing
    def __save_entry_data(self):
        self.logger.info("##########################--Save Button Clicked--##########################")
        #Verify all entries populated
        valid = self.__verify_input()
        if valid == True:
            #Determine whether a new item or modifying existing
            #Adding a new item
            if self.new_item == True:
                self.logger.info("Adding New Item to Database")
                self.logger.debug(f"Adding an entry for Trigger Group: {self.trigger_group_name_var.get()} to the database")

                #Add a new trigger group to the database
                self.db.add_trigger_group(self.trigger_group_name_var.get())
                #Get the id of the new trigger group
                trigger_group_id = self.db.get_1column_data("trigger_group_id", "trigger_groups", "trigger_group_name", self.trigger_group_name_var.get())[0]
                
                #Iteration variable for loop to work
                x=0
                #Add each trigger mapping to the database
                for mapping in self.controller_id_combobox_var_list:
                    #Get the controller id
                    if self.controller_id_combobox_var_list[x].get() == 'None':
                        controller_id = None
                    else:
                        controller_id = self.controller_id_combobox_var_list[x].get()
                    #Add the mapping entry in the database
                    self.db.add_trigger_mapping(trigger_group_id, 
                                                self.trigger_list[x],
                                                controller_id, 
                                                self.gpi_combobox_var_list[x].get()
                                                )
                    self.logger.debug(f"Mapping entry added - Trig ID:{trigger_group_id}, Trigger: {self.trigger_list[x]}, Controller:{self.controller_id_combobox_var_list[x].get()}, GPI: {self.gpi_combobox_var_list[x].get()}")
                    #Add 1 to the iteration variable
                    x += 1

                self.logger.info("Added new item to database")

                

            #Modifying existing item    
            else:
                self.logger.info("Modifing existing database entry")

                #Get the value from the ID and name widgets
                trigger_group_id = self.trigger_group_id_var.get()
                name = self.trigger_group_name_var.get()

                self.logger.info(f"Updating database entry for trigger group: {name}, ID={trigger_group_id}")
                #Update the Trigger Group Name
                self.db.update_row("trigger_groups", "trigger_group_name","trigger_group_id", name, trigger_group_id)
                #Iteration variable for loop to work
                x=0
                for mapping in self.controller_id_combobox_var_list:
                    controller_id = self. __get_controller_id(x)
                    #Check if the mapping exists already
                    mapping_check = self.db.get_current_row_data_dual_condition("trigger_mappings", "trigger_group_id", trigger_group_id, "trigger", self.trigger_list[x])

                    #Mapping Exists - Update the mapping
                    if mapping_check != []:
                        self.logger.debug("Mapping Exists, updating mapping")
                        self.db.update_trigger_mapping("trigger_mappings", 
                                                    "trigger_group_id", 
                                                    trigger_group_id, 
                                                    "trigger", 
                                                    self.trigger_list[x], 
                                                    controller_id, 
                                                    self.gpi_combobox_var_list[x].get())
                    #Mapping does not exist - Create a new mapping
                    if mapping_check == []:    
                        self.logger.debug("Mapping DOES NOT Exist, creating mapping")
                        #Add the mapping entry in the database
                        self.db.add_trigger_mapping(trigger_group_id, 
                                                    self.trigger_list[x],
                                                    self.controller_id_combobox_var_list[x].get(), 
                                                    self.gpi_combobox_var_list[x].get()
                                                    )
                        self.logger.info("Added new item to database")


                    #Add 1 to the iteration variable
                    x += 1
            
            #Refresh the tree
            updated_rows = self.db.get_current_table_data("trigger_groups")
            self.__update_tree(updated_rows)
            #Clear all entry widget fields
            self.__clear_widgets()
            #Set state indicator to true as widgets have been cleared
            self.new_item = True
            self.logger.info("Set State Indicator to True - No Tree Viewer item selected")

    #Removes an entry from the database
    def __remove_trigger_group(self):
        self.logger.info("Remove button clicked")
        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only try to delete an item if there is actually one selected.
        if self.tree.item(selected)["text"] != '':
            confirmation = Message_Boxes.confirm_delete()
            if confirmation == True:
                #Retrieve the id of the trigger group template
                db_id = self.tree.item(selected)["text"]
                #Remove the selected item from the database in both the 
                #trigger_groups and trigger_mappings tables

                #Check the trigger group is not in use by any devices before removing mappings
                devices = self.db.get_1column_data("device_name", "devices", "trigger_group_id", db_id)
                
                if devices == []:
                    self.logger.debug("Trigger Group not in use by devices, safe to remove.")
                    feedback1 = self.db.delete_row("trigger_mappings", "trigger_group_id", db_id)
                    feedback2 = self.db.delete_row("trigger_groups", "trigger_group_id", db_id)
                    #Only delete if no database integrity errors are thrown
                    if (feedback1 == True) & (feedback2 == True):
                        self.logger.info(f"Deleted trigger group with ID={db_id} from the database")
                        #Clear the entry widgets
                        self.__clear_widgets()
                        #Refresh the tree view
                        updated_rows = self.db.get_current_table_data("trigger_groups")
                        self.__update_tree(updated_rows)
                    else:
                        #Warn the user the item cannot be deleted to maintain database integrity
                        Message_Boxes.delete_warning("Trigger Group is currently in use by a device.")
                else:
                    #Warn the user the item cannot be deleted to maintain database integrity
                    Message_Boxes.delete_warning("Trigger Group is currently in use by a device.")
        else:
            self.logger.info("No Tree Item selected - cannot delete anything")

    #Sets option for GPI combobox based on crontroller combobox selection
    #clear_combobox is an option to clear the current value stored in the combobox
    def populate_gpi_cbox(self, combobox_value, combobox_index, clear_combobox):
        self.logger.debug(f"Populating GPI Combobox using value: {combobox_value}")

        #Get the id of the selected controller by querying the database
        #If a netowrk controller is used ID = 0
        if combobox_value == "Network":
            id=None
        else:
            #Removing the outer brackets from the query response
            id = self.db.get_1column_data("controller_id", "controllers", "controller_name", combobox_value)[0]
            self.logger.debug(f"ID of {combobox_value} is {id}")

        #Set the controller ID field in the GUI
        self.logger.debug(f"Updating controller id in label with index: {combobox_index}, with {id}")
        self.controller_id_combobox_var_list[combobox_index].set(id)

        #Retrieve the combobox variable
        combobox_var = self.gpi_combobox_var_list[combobox_index]
        #Retrieve the combobox object
        self.logger.debug(f"Pin Combobox index:{combobox_index}")
        combobox = self.pin_combobox_list[combobox_index]

        #If the controller ID is 0 we want to populate the GPI / NET combobox with the OSC address
        #The full osc address is the /trigger_group_name/trigger
        if id == None:
            trigger_group_name = self.trigger_group_name_var.get()
            trigger = self.trigger_list[combobox_index]
            osc_address = "/" + trigger_group_name + trigger

            #Assign value to the GPI / NET combobox
            #Update the combobox variable
            combobox_var.set(osc_address)
            #Clear the combobox values
            combobox.configure(values=[])

        else:
            #Query the database for the GPI pins of the specified controller using the unique id
            #Removing outer brackets fro mteh returned data
            data = self.db.get_current_row_data("controllers", "controller_id", id)
            
            self.logger.info(f"Returned Data:{data}")

            #Extract the Pin info from the query
            #Create a list to hold the pin info
            pin_list = []
            #Add each pin to the list (i-4) to start the pins at 2 - Arduino limitation
            #TODO: Make the range set from a global variable based on board type
            for i in range(6, 24):
                if len(data) > 0:
                    data_item = data[0]
                    self.logger.debug(f"Pin:{i-4} Mode is:{data_item[i]}")
                    #Only if the pin is specified as an input, add it to the list
                    if data_item[i] == "in":
                        #Combobox values can only be strings, so convert int to string
                        pin_list.append(str(i-4))
                        self.logger.debug(f"Pin:{i-4} added to Pin List")
                else:
                    self.logger.debug("Returned data is empty.")

            self.logger.debug(f"Pin List:{pin_list}")

            #Assign values to the GPI combobox
            self.logger.debug(f"Pin Combobox:{combobox}")
            combobox.configure(values=pin_list)
            self.logger.info(f"Values: {pin_list} set for GPI combobox: {combobox}")
        
        if (clear_combobox == True) & (id != None):
            #Clear the value currently in the combobox
            self.logger.debug("Clearing combobox value, a different controller has been selected.")
            combobox_var.set("")

    def __add_widgets(self):

        #------------------------------TRIGGER GROUP FRAME-GROUP SETUP FRAME--------------------------------------------------
        #Create a frame to contain settings about the individual client device
        group_setup_frame = ctk.CTkScrollableFrame(master=self, border_color="green", border_width=1)
        group_setup_frame.grid(column=1, row=0, columnspan=3, sticky="nsew")

        #Setup Columns / rows for group_setup_frame

        group_setup_frame.columnconfigure(0, weight=0, pad=20)
        group_setup_frame.columnconfigure(1, weight=0, pad=20)
        group_setup_frame.columnconfigure(2, weight=0, pad=20)
        group_setup_frame.columnconfigure(3, weight=1, pad=20)

        for i in range(29):
            group_setup_frame.rowconfigure(i, weight=0, pad=10)

        #------------------------------TRIGGER GROUP FRAME WIDGETS --------------------------------------------------

        #Tree Viewer to display all devices in a nested format
        self.tree = CustomTree(self)
        self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

        add_btn = ctk.CTkButton(master=self, text="Add Trigger Group", fg_color="green", command=lambda:self.__add_trigger_group(), font=self.default_font)
        add_btn.grid(column=0, row=1, sticky="nsew")

        del_btn = ctk.CTkButton(master=self, text="Remove Trigger Group", fg_color="red", command=lambda:self.__remove_trigger_group(), font=self.default_font)
        del_btn.grid(column=0, row=2, sticky="nsew")

        #------------------------------GROUP SETUP FRAME-Widgets--------------------------------------------------
        #------------------------------Controller Attributes--------------------------------------------------

        self.title1_label = ctk.CTkLabel(master=group_setup_frame, text="Trigger Group Assign", font=self.default_font)
        self.title1_label.grid(column=0, row=0, columnspan=4, sticky="ew")
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_grp_id_label = ctk.CTkLabel(master=group_setup_frame, text="Trigger Group ID:", font=self.default_font)
        self.trig_grp_id_label.grid(column=0, row=1, sticky="w", padx=20)

        self.trig_grp_id_data_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.trigger_group_id_var, font=self.default_font)
        self.trig_grp_id_data_label.grid(column=1, row=1, columnspan=4, sticky="w", padx=20)

        self.trig_grp_name_label = ctk.CTkLabel(master=group_setup_frame, text="Trigger Group Name:", font=self.default_font)
        self.trig_grp_name_label.grid(column=0, row=2, sticky="w", padx=20)

        self.trig_grp_name_entry = ctk.CTkEntry(master=group_setup_frame, textvariable=self.trigger_group_name_var, font=self.default_font)
        self.trig_grp_name_entry.grid(column=1, row=2, columnspan =4, sticky="ew", padx=20)

#---------------------------------------------------------------------------------------------------------------------------------------
        self.title21_label = ctk.CTkLabel(master=group_setup_frame, text="Controlller Name", font=self.default_font)
        self.title21_label.grid(column=1, row=3, columnspan=1, sticky="ew", pady=15)

        self.title22_label = ctk.CTkLabel(master=group_setup_frame, text="Controller ID", font=self.default_font)
        self.title22_label.grid(column=2, row=3, columnspan=1, sticky="ew", pady=15)

        self.title23_label = ctk.CTkLabel(master=group_setup_frame, text="GPI / NET", font=self.default_font)
        self.title23_label.grid(column=3, row=3, columnspan=1, sticky="ew", pady=15)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_mic_live_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 1:", font=self.default_font)
        self.trig_mic_live_ind_label.grid(column=0, row=4, sticky="w", padx=20)

        self.trig_mic_live_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.mic_live_trigger_ctrl_var, command=lambda value, combobox=0 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_mic_live_ind_ctrl_cbox.grid(column=1, row=4, columnspan =1, sticky="ew", padx=20)

        self.mic_live_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.mic_live_ctrl_id_var, font=self.default_font)
        self.mic_live_ctrl_id_label.grid(column=2, row=4)

        self.trig_mic_live_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.mic_live_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_mic_live_ind_pin_cbox.grid(column=3, row=4, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_tx_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 2:", font=self.default_font)
        self.trig_tx_ind_label.grid(column=0, row=5, sticky="w", padx=20)

        self.trig_tx_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.tx_trigger_ctrl_var, command=lambda value, combobox=1 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_tx_ind_ctrl_cbox.grid(column=1, row=5, columnspan =1, sticky="ew", padx=20)

        self.tx_ind_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.tx_ctrl_id_var, font=self.default_font)
        self.tx_ind_ctrl_id_label.grid(column=2, row=5)

        self.trig_tx_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.tx_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_tx_ind_pin_cbox.grid(column=3, row=5, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_cue_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 3:", font=self.default_font)
        self.trig_cue_ind_label.grid(column=0, row=6, sticky="w", padx=20)

        self.trig_cue_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.cue_trigger_ctrl_var, command=lambda value, combobox=2 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_cue_ind_ctrl_cbox.grid(column=1, row=6, columnspan =1, sticky="ew", padx=20)

        self.cue_ind_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.cue_ctrl_id_var, font=self.default_font)
        self.cue_ind_ctrl_id_label.grid(column=2, row=6)

        self.trig_cue_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.cue_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_cue_ind_pin_cbox.grid(column=3, row=6, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_lin1_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 4:", font=self.default_font)
        self.trig_lin1_ind_label.grid(column=0, row=7, sticky="w", padx=20)

        self.trig_lin1_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.line1_trigger_ctrl_var, command=lambda value, combobox=3 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_lin1_ind_ctrl_cbox.grid(column=1, row=7, columnspan =1, sticky="ew", padx=20)

        self.lin1_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.line1_ctrl_id_var, font=self.default_font)
        self.lin1_ctrl_id_label.grid(column=2, row=7)

        self.trig_lin1_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.line1_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_lin1_ind_pin_cbox.grid(column=3, row=7, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_lin2_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 5:", font=self.default_font)
        self.trig_lin2_ind_label.grid(column=0, row=8, sticky="w", padx=20)

        self.trig_lin2_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.line2_trigger_ctrl_var, command=lambda value, combobox=4 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_lin2_ind_ctrl_cbox.grid(column=1, row=8, columnspan =1, sticky="ew", padx=20)

        self.lin2_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.line2_ctrl_id_var, font=self.default_font)
        self.lin2_ctrl_id_label.grid(column=2, row=8)

        self.trig_lin2_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.line2_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_lin2_ind_pin_cbox.grid(column=3, row=8, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.trig_control_ind_label = ctk.CTkLabel(master=group_setup_frame, text="Indicator 6:", font=self.default_font)
        self.trig_control_ind_label.grid(column=0, row=9, sticky="w", padx=20)

        self.trig_control_ind_ctrl_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.control_trigger_ctrl_var, command=lambda value, combobox=5 :self.populate_gpi_cbox(value, combobox, True), state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_control_ind_ctrl_cbox.grid(column=1, row=9, columnspan =1, sticky="ew", padx=20)

        self.control_ind_ctrl_id_label = ctk.CTkLabel(master=group_setup_frame, text="", textvariable=self.control_ctrl_id_var, font=self.default_font)
        self.control_ind_ctrl_id_label.grid(column=2, row=9)

        self.trig_control_ind_pin_cbox = ctk.CTkComboBox(master=group_setup_frame, variable=self.control_trigger_pin_var, state="readonly", font=self.default_font, dropdown_font=self.default_font)
        self.trig_control_ind_pin_cbox.grid(column=3, row=9, columnspan =1, sticky="ew", padx=20)
#---------------------------------------------------------------------------------------------------------------------------------------
        self.save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", command=lambda:self.__save_entry_data(), font=self.default_font)
        self.save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)

    def __verify_input(self) -> bool:
        #Check Trigger Group name is not tempty
        if self.trigger_group_name_var.get() == "":
            self.logger.info("Trigger Group Name Empty")
            return False
        
        #Check comboboxes are not empty
        for i in range(6):
            if (self.controller_name_cobobox_var_list[i].get() == "") or (self.controller_id_combobox_var_list[i].get() == "") or (self.gpi_combobox_var_list[i] == ""):
                self.logger.info("One or more comboboxes are empty")
                return False
        #If all fields populated return True    
        return True
   
    def __get_controller_id(self, index):
        if self.controller_id_combobox_var_list[index].get() == 'None':
            return None
        else:
            return self.controller_id_combobox_var_list[index].get()


#---CALLBACKS------------------------------------------------------------------------------------------------------------------------------------

    def __update_osc_strings(self, event):
        self.logger.debug("Trigger Group Name changed, updating OSC addresses")
        index = 0
        for combobox in self.combobox_list:
            combobox_value = combobox.get()
            if combobox_value != "":
                self.populate_gpi_cbox(combobox_value, index, False)
            index += 1
        
        #Refreshes combobox options
    
    def refresh_cboxs(self, event):
        self.logger.info("##########################--Refreshing trigger_groups combobox options--##########################")
        #Query the database for id and names
        query1 = self.db.get_2column_data("controller_id", "controller_name", "controllers")

        #Clear the id / name lists
        self.logger.info("Clearing id / name lists")
        self.controller_ids_list.clear()
        self.controller_names_list.clear()
        
        #For each row in the query response, add the row to the id/name list.
        for item in query1:
                #Add the name and id to the lists
                self.logger.info(f"Adding name: {item[1]} and id: {item[0]} to lists.")
                self.controller_ids_list.append(item[0])
                self.controller_names_list.append(item[1])
        #Add a Static Network option for using network OSC inputs
        self.controller_ids_list.append("0")
        self.controller_names_list.append("Network")
        #Assign values to each combobox
        self.logger.info(f"Assigning values: {self.controller_names_list}")
        for combobox in self.combobox_list:
            combobox.configure(values=self.controller_names_list)

    #Populates the entry widgets with data when treeviewer item clicked
    def __populate_widget_data(self, event):
        self.logger.debug("##########################--Treeviewer item clicked--##########################")

        #Get the treeviewer index of the currently selected item
        selected = self.tree.focus()
        #Only update teh widgets if a valid tree item is selected
        if selected != '':
            #Clear the entry boxes before they are updated
            self.__clear_widgets()
            #Set the state indicator variable to False, indicating an item is to be modified
            self.new_item = False
            self.logger.info("Set State Indicator to False - an existing item is being modified")
            #Populate the data fields - NEW VERSION
            #Retrieve the id of the trigger group
            db_id = self.tree.item(selected)["text"]
            #Get the value data held in the database for the selected item - stripping the outer brackets
            data = self.db.get_current_row_data("trigger_groups", "trigger_group_id", db_id)[0]
            self.logger.debug(f"Database Returned:{data}")
            self.logger.info("Populating trigger_group_id and trigger_group_name entry fields with data for selected tree viewer item")

            #Populate the trigger group ID / name
            self.trigger_group_id_var.set(data[0])
            self.trigger_group_name_var.set(data[1])

            #Clear the ids, names and gpi lists
            self.controller_ids_list.clear()
            self.controller_names_list.clear()

            #Query the trigger_mappings table, Select all from trigger-mappings where trigger id = data[0]
            mappings = self.db.get_current_row_data("trigger_mappings", "trigger_group_id", data[0])
            self.logger.debug(f"Data returned from database: {mappings}")

            #Index variable for the loop to function
            x=0
            #Retrieve the controller_ids from the query response, adding these to the id's list
            #  - IDs are every even number starting from 2 ending at 18
            for mapping in mappings:
                self.logger.debug(f"Extrapolating data from mapping: {mapping}")
                #TODO: continue here.....
                #Update the GUI Fields
                trigger = mapping[1]
                controller_id = mapping[2]
                gpi = mapping[3]
                self.logger.debug(f"Trigger:{trigger}, Controller ID:{controller_id}, GPI:{gpi}")
                #Query database for controller name using the controller id
                #If controller id = 0 this is the static network controller
                if controller_id == None:
                    controller_name = "Network"
                else:
                    controller_name = self.db.get_1column_data("controller_name", "controllers", "controller_id", controller_id)[0]
                    self.logger.debug(f"Trigger: {trigger},Controller ID: {controller_id}, Controller Name: {controller_name}, GPI: {gpi}")
                #Update Controller Name Combobox
                controller_name_combobox_var = self.controller_name_combobox_var_dict[trigger]
                controller_name_combobox_var.set(controller_name)
                #Update Controller ID Combobox
                controller_id_label_var = self.controller_id_combobox_var_dict[trigger]
                controller_id_label_var.set(controller_id)
                #Update Controller GPI Combobox
                gpi_combobox_var = self.gpi_combobox_var_dict[trigger]
                gpi_combobox_var.set(gpi)
                #Increse the index variable by one
                x += 1
            self.logger.debug(f"All GUI elements updated")

            self.logger.debug("Assigning values to comboboxes with values in")
            #Assign values to the GPI comboboxes that have values selected
            #Below called funtion is a cllback and requires an "event", this is not used so a null parameter is specified
            self.refresh_cboxs("null_event")

            #Iteration variable used to select the correct combobox from the lists
            i = 0
            for combobox in self.controller_name_cobobox_var_list:
                value = combobox.get()
                self.logger.debug(f"Value held in controller name combobox at index: {i} is: {value}")
                if value != "":
                    self.populate_gpi_cbox(value, i, False)
                i += 1

        else:
            self.logger.info("No valid item selected in tree - cannot populate widgets")
    

