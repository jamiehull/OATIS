import customtkinter as ctk
import logging
from tkinter import ttk
from tkinter import colorchooser
import json
import tkinter as tk
import time
import threading
from tkinter import messagebox
import sys
from modules.common import *
from modules.gui_templates import *

from modules.tcp import TCP_Client

class Message_Console:

    def __init__(self):
        #This file contains the code for the tkinter main window
        #Set Custom Tkinter Styles
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create the Window
        self.logger.debug("Creating the self.root tkinter window")
        self.root = ctk.CTk()
        self.root.configure(pady=10, padx=10)

        #Default wait time until a connection is made
        self.heartbeat_poll_time = 5
        self.server_status_var = tk.StringVar()
        self.sync_status_var = tk.StringVar()

        #Set Default font
        self.default_font = ctk.CTkFont('Arial', 25)
        self.small_font = ctk.CTkFont('Arial', 18)
        self.indicator_font = ctk.CTkFont('Arial', 10)

        #Set a style to set row heights for all treeviewers
        style = ttk.Style()
        style.configure('Treeview', rowheight=20)

        #Set Window title and size.
        self.logger.debug("Setting self.root window attributes")
        self.root.title("OATIS Message Console")
        self.root.attributes("-fullscreen", True)

        #StringVars
        self.message_text_input_var = tk.StringVar()
        self.bg_colour_var = tk.StringVar()

        #Client listen Socket - Defaults
        self.ip_address_var = tk.StringVar()
        self.listen_port = 1338

        #Server listen Socket - Defaults
        self.server_ip_address_var = tk.StringVar()
        self.server_port = 1339

        #Add the widgets        
        self.__add_widgets()

        #Attempt to set the ip addresses from saved settings
        self.read_and_set_ip_settings()

        self.network = TCP_Client()

        #Start Background threads
        heartbeat_thread = threading.Thread(target=self.__heartbeat, daemon=True).start()
        gui_updater_thread = threading.Thread(target=self.__update_gui, daemon=True).start()

        #Setup bindings
        self.root.bind("<Escape>", self.raise_settings_frame)

        self.root.mainloop()

    def __add_widgets(self):

        #Setup root
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        #Create and stack the frames
        self.settings_frame = Settings(self.root, self)
        self.settings_frame.grid(column=0, row=0, sticky="nsew")
        self.message_console_frame = ctk.CTkFrame(self.root)
        self.message_console_frame.grid(column=0, row=0, sticky="nsew")
        

        self.message_console_frame.columnconfigure(0, weight=1, uniform="columns")

        self.message_console_frame.rowconfigure(0, weight=10)
        self.message_console_frame.rowconfigure(1, weight=100)
        self.message_console_frame.rowconfigure(2, weight=1)

        #Add Frames
        #Input Frame

        self.input_frame = ctk.CTkFrame(self.message_console_frame)
        self.input_frame.grid(column=0, row=0, columnspan=5, sticky="nsew")

        self.input_frame.columnconfigure(0, weight=1)
        self.input_frame.rowconfigure(0, weight=1, uniform="rows")
        self.input_frame.rowconfigure(1, weight=1, uniform="rows")

        self.message_input = ctk.CTkEntry(self.input_frame, placeholder_text="Enter message here", font=self.default_font, textvariable=self.message_text_input_var)
        self.message_input.grid(column=0, row=0, sticky="nsew", pady=20)

        self.bg_colour_picker_btn = ctk.CTkButton(master=self.input_frame, command=self.choose_colour, width=350, font=self.default_font, textvariable=self.bg_colour_var)
        self.bg_colour_picker_btn.grid(column=0, row=1, sticky="nsew", pady=20)
        #Set placeholder text on colour picker button
        self.bg_colour_var.set("Click to Choose a background colour")

        #Container Frame
        self.tree_container_frame = ctk.CTkFrame(self.message_console_frame)
        self.tree_container_frame.grid(column=0, row=1, sticky="nsew")
        #Setup container Frame
        self.tree_container_frame.columnconfigure(0, weight=1, uniform="columns")
        self.tree_container_frame.columnconfigure(1, weight=1, uniform="controls")
        self.tree_container_frame.columnconfigure(2, weight=1, uniform="columns")
        self.tree_container_frame.columnconfigure(3, weight=1, uniform="controls")
        self.tree_container_frame.columnconfigure(4, weight=1, uniform="columns")
        self.tree_container_frame.rowconfigure(0, weight=1)

        #Column 1
        self.column1_frame = Selection_Column(self.tree_container_frame, "Message Groups", "Select All", self.default_font, self.__select_all_groups)
        self.column1_frame.grid(column=0, row=0, sticky="nsew")

        #Column 2
        self.column2_frame = ctk.CTkFrame(self.tree_container_frame)
        self.column2_frame.columnconfigure(0, weight=1)
        self.column2_frame.rowconfigure(0, weight=1, uniform="btn_row")
        self.column2_frame.rowconfigure(1, weight=1, uniform="btn_row")
        self.column2_frame.grid(column=1, row=0, sticky="nsew")

        self.msg_grp_add_btn = ctk.CTkButton(self.column2_frame, text=">>", width=50, height=50, command=self.__move_group_to_selected)
        self.msg_grp_add_btn.grid(column=0, row=0, sticky="")
        self.msg_grp_remove_btn = ctk.CTkButton(self.column2_frame, text="<<", width=50, height=50, command=self.__remove_group_from_selected)
        self.msg_grp_remove_btn.grid(column=0, row=1, sticky="")

        #Column 3
        self.column3_frame = Selection_Column(self.tree_container_frame, "Selected Groups", "Clear Selected Groups", self.default_font, self.__clear_selections)
        self.column3_frame.grid(column=2, row=0, sticky="nsew")

        #Column 4
        self.column4_frame = ctk.CTkFrame(self.tree_container_frame)
        self.column4_frame.columnconfigure(0, weight=1)
        self.column4_frame.rowconfigure(0, weight=1, uniform="btn_row")
        self.column4_frame.rowconfigure(1, weight=1, uniform="btn_row")
        self.column4_frame.grid(column=3, row=0, sticky="nsew")

        self.send_btn = ctk.CTkButton(self.column4_frame, text=">>", width=50, height=50, fg_color="green", command=self.__send_message)
        self.send_btn.grid(column=0, row=0, sticky="")

        self.stop_btn = ctk.CTkButton(self.column4_frame, text="<<", width=50, height=50, fg_color="red", command=self.__stop_message)
        self.stop_btn.grid(column=0, row=1, sticky="")

        #Column 5
        self.column5_frame = Selection_Column(self.tree_container_frame, "Active Messages", "Select All", self.default_font, self.__select_all_groups_column5)
        self.column5_frame.grid(column=4, row=0, sticky="nsew")

        #Control Frame
        self.control_frame = ctk.CTkFrame(self.message_console_frame, fg_color="#494949")
        self.control_frame.grid(column=0, row=2, columnspan=5, sticky="nsew")

        
        self.control_frame.columnconfigure(0, weight=1, uniform="indicator")
        self.control_frame.columnconfigure(1, weight=1, uniform="indicator")
        self.control_frame.columnconfigure(2, weight=1, uniform="indicator")
        self.control_frame.columnconfigure(3, weight=1, uniform="indicator")

        self.control_frame.rowconfigure(0, weight=1)

        self.server_ind = ctk.CTkLabel(self.control_frame, textvariable=self.server_status_var, font=self.small_font, corner_radius=5, fg_color="orange", width=200)
        self.server_ind.grid(column=0, row=0, sticky="ew", padx=20)

        self.database_ind = ctk.CTkLabel(self.control_frame, textvariable=self.sync_status_var, font=self.small_font, corner_radius=5, fg_color="orange")
        self.database_ind.grid(column=1, row=0, sticky="ew", padx=20)

        self.server_ip_label = ctk.CTkLabel(self.control_frame, text="Server IP Address:", font=self.small_font, corner_radius=5, fg_color="grey")
        self.server_ip_label.grid(column=2, row=0, sticky="ew", padx=20)

        self.server_ip_data_label = ctk.CTkLabel(self.control_frame, textvariable=self.server_ip_address_var, font=self.small_font, corner_radius=5, fg_color="grey")
        self.server_ip_data_label.grid(column=3, row=0, sticky="ew", padx=20)

    #Reads ip settings from the settings file and applies them
    def read_and_set_ip_settings(self):
        """Opens settings file and sets IP address variables."""
        #Read Settings file
        settings_dict = open_json_file("message_console/data/settings.json")

        #Set ip's if settings file exists - otherwise defaults are used
        if settings_dict != False:
            self.ip_address_var.set(settings_dict["client_ip"])
            self.settings_frame.set_device_ip(settings_dict["client_ip"])
            self.server_ip_address_var.set(settings_dict["server_ip"])
            self.settings_frame.set_server_ip(settings_dict["server_ip"])
    
    #Callback used to raise settings frame
    def raise_settings_frame(self, event):
        #Populate ip combobox before raising
        self.settings_frame.populate_ip_combobox()
        self.settings_frame.tkraise()

    #Raises message console frame
    def raise_message_console_frame(self):
        self.message_console_frame.tkraise()

    #Opens a colour picker
    def choose_colour(self):
        #Generate a colour picker window returning the hex value of the colour picked
        try:
            self.logger.info("User is selecting a background colour")
            rdg, hex_colour = colorchooser.askcolor(title="Pick a background Colour", )
            self.bg_colour_picker_btn.configure(fg_color=hex_colour)
            self.bg_colour_var.set(hex_colour)
            self.logger.info(f"User selcted background colour: {hex_colour}")
        except Exception as e:
            self.logger.warning("User selected no colour")

    #Moves selected message groups from the first column to the middle selected column
    def __move_group_to_selected(self):
        #Get the selected items as a list
        items_list = self.column1_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {items_list}")

        #Check the selected items are not already in the selected tree
        selected_tree : ttk.Treeview = self.column3_frame.get_tree()
        selected_tree_item_ids = selected_tree.get_children()
        self.logger.debug(f"Selected Items Tree: {selected_tree_item_ids}")

        #Check the selected items are not active
        active_tree : ttk.Treeview = self.column5_frame.get_tree()
        active_tree_item_ids = active_tree.get_children()
        self.logger.debug(f"Active Items Tree: {active_tree_item_ids}")

        #A blank list to hold id's of groups already in the selected list
        selected_groups_id_list = []
        active_groups_id_list = []

        #Extract the id from each item and add to the list
        for item_id in selected_tree_item_ids:
            id, name = selected_tree.item(item_id)["values"]
            selected_groups_id_list.append(id)

        self.logger.debug(f"Selected Groups ID list: {selected_groups_id_list}")

        #Extract the id from each item and add to the list
        for item_id in active_tree_item_ids:
            id, name = active_tree.item(item_id)["values"]
            active_groups_id_list.append(id)

        self.logger.debug(f"Active Groups ID list: {active_groups_id_list}")

        #Add the newly selected groups to the selected tree only if not already added
        for tree_id in items_list:
            id, name = self.column1_frame.get_item(tree_id)

            if (id not in selected_groups_id_list) and (id not in active_groups_id_list):
                self.column3_frame.add_item(id, name)
                
    #Removes a selected message group from the middle selected column
    def __remove_group_from_selected(self):
        items_list = self.column3_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {items_list}")
        for tree_id in items_list:
            self.column3_frame.remove_item(tree_id)
    #Removes selected items from the active message groups column
    def __remove_group_from_active(self):
        items_list = self.column5_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {items_list}")
        for tree_id in items_list:
            self.column5_frame.remove_item(tree_id)

    #Clears all items from the middle column
    def __clear_selections(self):
        self.column3_frame.clear_tree()

    #Selects all groups in the first column
    def __select_all_groups(self):
        self.column1_frame.focus_all_items()

    #Selects all groups in the third column
    def __select_all_groups_column5(self):
        self.column5_frame.focus_all_items()

    #Updates active messages tree given a list of message groups in [[id, name],...] format.
    def __update_active_messages_tree(self, active_message_groups_list):
        self.column5_frame.clear_tree()
        for message_group in active_message_groups_list:
            id = message_group[0]
            name = message_group[1]
            self.column5_frame.add_item(id, name)

    #Changes the appearance of the server status indicator between red and green
    def __change_server_status_indicator(self, state):
        if state == "OK":
            self.server_ind.configure(fg_color="green")
            self.server_status_var.set("Connected to Server")

        else:
            self.server_ind.configure(fg_color="red")
            self.server_status_var.set("Server Offline")

    #Used to periodically update both the active_message groups lsite and message_groups list.
    def __update_gui(self):
        while True:
            self.database_ind.configure(fg_color="orange")
            self.sync_status_var.set("Database Syncing")
            time.sleep(3)
            status_message_groups = self.update_message_groups()
            status_active_message_groups = self.update_active_message_groups()
            if (status_message_groups == True) and (status_active_message_groups == True):
                self.database_ind.configure(fg_color="green")
                self.sync_status_var.set("Database Synced")
                self.logger.info("Synced Message groups and Active Message Groups Lists with server.")
                time.sleep(60)
            else:
                time.sleep(5)
        
#--------------Network Commands-------------------------
  #Gathers all input data and attempts to send to the selected groups
    def __send_message(self):
        self.logger.info("Attempting to send message...")
        #Retrieve the message text and selected colour
        message_text = self.message_text_input_var.get()
        bg_colour = self.bg_colour_var.get()

        #Proceed only if the above are not empty
        if (message_text != "") and (bg_colour != "Click to Choose a background colour"):
            try:
                #Collect the entries stored in the selected groups tree
                selected_tree : ttk.Treeview = self.column3_frame.get_tree()
                selected_tree_item_ids = selected_tree.get_children()
                #Create a blank list to hold the entries
                selected_list = []
                #Get the id and name for each entry and store in the list
                for tree_id in selected_tree_item_ids:
                    id, name = self.column3_frame.get_item(tree_id)
                    selected_list.append([id,name])

                #Build the Message and send
                command = "/messaging/send_to_multiple"
                arguments = {
                            "message" : message_text,
                            "bg_colour" : bg_colour}
                data = selected_list
                message = self.network.build_tcp_message(command, arguments, data)
                output_command, output_arguments, output_data = self.network.tcp_send(self.server_ip_address_var.get(), self.server_port, message)
              
                status = output_arguments["status"]
                message_id = output_arguments["message_id"]
                active_message_groups = output_arguments["active_message_groups"]

                if status == "OK":
                    self.column5_frame.clear_tree()
                    for message_group in active_message_groups:
                        id = message_group[0]
                        name = message_group[1]
                        self.column5_frame.add_item(id, name)

                    #Clear the selected tree
                    self.column3_frame.clear_tree()

            except ConnectionRefusedError as e:
                self.logger.error(f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
                messagebox.showwarning("Unable to Send Message", f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
            except Exception as e:
                self.logger.error(f"Cannot connect to server: {e}")
                messagebox.showwarning("Unable to Send Message", f"Cannot connect to server: {e}")
        else:
            self.logger.warning("Cannot send message as one or more fields are empty!")
            messagebox.showwarning("Unable to Send Message", "Cannot send message as one or more fields are empty!")
    
    #Sends a stop message to the selected groups
    def __stop_message(self):
        self.logger.info("Attempting to send stop message...")

        #Get the currently selected in-focus items
        tree_id_list = self.column5_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {tree_id_list}")

        #Only proceed if an item is selected
        if tree_id_list != ():
            stop_group_list = []
            for tree_id in tree_id_list:
                id, name = self.column5_frame.get_item(tree_id)
                stop_group_list.append([id, name])

            #Build the Message and send
            command = "/messaging/stop_message"
            arguments = {"state" : False}
            data = stop_group_list
            message = self.network.build_tcp_message(command, arguments, data)
            output_command, output_arguments, output_data = self.network.tcp_send(self.server_ip_address_var.get(), self.server_port, message)
            
            status = output_arguments["status"]
            active_message_groups = output_arguments["active_message_groups"]

            #If the response is ok, update the active messages column with active message groups
            if status == "OK":
                self.__update_active_messages_tree(active_message_groups)

        else:
            self.logger.warning("Unable to send stop message, nothing has been selected to stop!")
            messagebox.showwarning("Unable to Send Stop Message", "Unable to send stop message, nothing has been selected to stop!")
       #Requests a list of all in use message groups from the server and updates the message groups tree.
    
    #Requests a list of configured message Groups and updates the Message Groups tree
    def update_message_groups(self):
        try:
            self.logger.info("Updating Message Groups list.")
            #Build the Message and send
            command = "/config/message_groups/get_used"
            message = self.network.build_tcp_message(command)
            output_command, output_arguments, output_data = self.network.tcp_send(self.server_ip_address_var.get(), self.server_port, message)

            status = output_arguments["status"]
            message_group_list = output_arguments["message_groups"]
            
            #If the response is ok, update the message groups column
            if status == "OK":
                self.column1_frame.update_tree(message_group_list)
                self.logger.info("Message Groups list updated.")
                return True
            else:
                self.database_ind.configure(fg_color="red")
                self.sync_status_var.set("NOT SYNCED")
                return False

        except Exception as e:
            self.logger.error(f"Unable to update message groups list, reason: {e}")
            self.database_ind.configure(fg_color="red")
            self.sync_status_var.set("NOT SYNCED")
            return False
    #Requests a list of active message groups from the server and updates the active messages tree.
    def update_active_message_groups(self) -> bool:
        try:
            #Build the Message and send
            command = "/messaging/get_active_groups"
            arguments = None
            data = None
            message = self.network.build_tcp_message(command, arguments, data)
            output_command, output_arguments, output_data = self.network.tcp_send(self.server_ip_address_var.get(), self.server_port, message)
            
            status = output_arguments["status"]
            active_message_groups = output_arguments["active_message_groups"]

            #If the response is ok, update the active messages column with active message groups
            if status == "OK":
                self.column5_frame.update_tree(active_message_groups)
                return True
            else:
                self.database_ind.configure(fg_color="red")
                self.sync_status_var.set("NOT SYNCED")
                return False
        except Exception as e:
            self.logger.error(f"Unable to update message group list, reason: {e}")
            self.database_ind.configure(fg_color="red")
            self.sync_status_var.set("NOT SYNCED")
            return False
        
    #Sends a heartbeat message to the server and updated the server gui status indicator
    def __heartbeat(self):
        while True:
            try:
                message = self.network.build_tcp_message("heartbeat", None, None)
                output_command, output_arguments, output_data = self.network.tcp_send(self.server_ip_address_var.get(), self.server_port, message)

                status = output_arguments["status"]
                timestamp = output_arguments["timestamp"]

                if status == "OK":
                    self.logger.debug(f"Server last seen at: {timestamp}")
                    self.__change_server_status_indicator("OK")
                    self.heartbeat_poll_time = 30

                else:
                    self.logger.warning("Server Offline")
                    self.__change_server_status_indicator("ERROR")
                    self.heartbeat_poll_time = 5

            except ConnectionRefusedError as e:
                self.logger.error(f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
                self.__change_server_status_indicator("ERROR")
                self.heartbeat_poll_time = 5
            except Exception as e:
                self.logger.error(f"Cannot connect to server: {e}")
                self.__change_server_status_indicator("ERROR")
                self.heartbeat_poll_time = 5

            time.sleep(self.heartbeat_poll_time)

#Provides an interface to configure client ip and server ip
class Settings(ctk.CTkFrame):
    def __init__(self, parent, message_console_display):
        super().__init__(parent)

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #RDS_Display Instance - allows gui interaction to raise the RDS frame
        self.message_console_display : Message_Console = message_console_display

        #Variables
        self.device_ip_var = tk.StringVar()
        self.server_ip_var = tk.StringVar()
        self.mode_var = tk.StringVar()

        #Set Default font
        #font_size = screen_info.get("top_level_text_size")
        font_size = 30
        self.default_font = ctk.CTkFont('Arial', font_size)


        #Set column spanning for Top Level Window
        self.columnconfigure(0, weight = 1)
        self.rowconfigure(0, weight = 1)

        self.container_frame = ctk.CTkFrame(self, fg_color='#303030', width=800, height=800, border_color="green", border_width=1)
        self.container_frame.grid(column = 0, row = 0, sticky = "", columnspan = 1, ipadx=20, ipady=20)
        
        #Set column spanning for container_frame
        for i in range(2):
            self.container_frame.columnconfigure(i, weight = 1)
        for i in range(8):
            self.container_frame.rowconfigure(i, weight = 1)

        #Add Widgets
        self.ip_label = ctk.CTkLabel(self.container_frame, text="Device IP:", anchor="w", font = self.default_font)
        self.ip_label.grid(column = 0, row = 0, sticky = "ew", columnspan = 2, padx=10, pady=20)

        self.ip_combobox = ctk.CTkComboBox(self.container_frame, font=self.default_font, state="readonly", variable=self.device_ip_var, dropdown_font=self.default_font)
        self.ip_combobox.grid(column = 0, row = 1, sticky = "ew", columnspan = 2, padx=10, pady=20)
        
        self.server_ip_label = ctk.CTkLabel(self.container_frame, text="Server IP:", anchor="w", font = self.default_font)
        self.server_ip_label.grid(column = 0, row = 2, sticky = "ew", columnspan = 2, padx=10, pady=20)

        self.server_ip_entry = ctk.CTkEntry(self.container_frame, font=self.default_font, textvariable=self.server_ip_var)
        self.server_ip_entry.grid(column = 0, row = 3, sticky = "ew", columnspan = 2, padx=10, pady=20)
        """
        self.mode_label = ctk.CTkLabel(self.container_frame, text="Mode:", anchor="w", font = self.default_font)
        self.mode_label.grid(column = 0, row = 4, sticky = "ew", columnspan = 2, padx=10, pady=20)

        self.mode_combobox = ctk.CTkComboBox(self.container_frame, width=300, font=self.default_font, state="readonly", variable=self.mode_var, dropdown_font=self.default_font)
        self.mode_combobox.grid(column = 0, row = 5, sticky = "ew", columnspan = 2, padx=10, pady=20)
        """
        self.save_btn = ctk.CTkButton(self.container_frame, text="Save", font=self.default_font, fg_color="green", command=lambda:self.__save_entry_data(), width=500)
        self.save_btn.grid(column = 0, row = 6, sticky = "", columnspan = 1, padx=10, pady=20)

        self.back_btn = ctk.CTkButton(self.container_frame, text="Back", font=self.default_font, command=lambda:self.__return_to_main_screen(), width=500)
        self.back_btn.grid(column = 1, row = 6, sticky = "", columnspan = 1, padx=10, pady=20)

        self.exit_btn = ctk.CTkButton(self.container_frame, text="Exit Application", font=self.default_font, fg_color="red", command=lambda:self.__exit_program())
        self.exit_btn.grid(column = 0, row = 7, sticky = "ew", columnspan = 2, padx=20, pady=20)

    def __exit_program(self):
        self.logger.info("Exiting Application")
        sys.exit(0)

    def __save_entry_data(self):
        self.logger.debug("Saving Ip Configuration")
        client_ip = self.device_ip_var.get()
        server_ip = self.server_ip_var.get()

        #Validate IP inputs
        if validate_ip(client_ip) and validate_ip(server_ip):

            settings_dict = {"client_ip":client_ip, "server_ip":server_ip}

            write_dict_to_file(settings_dict, "message_console/data/settings.json")
            
            #Update the ip settings with the new values
            self.message_console_display.read_and_set_ip_settings()
            
            self.message_console_display.raise_message_console_frame()
        
        #If inputs are invalid prompt the user
        else:
            messagebox.showwarning("IP Address Error", "The entered IP address is not valid.")

    def __return_to_main_screen(self):
        self.message_console_display.raise_message_console_frame()

    def populate_ip_combobox(self):
        ip_list=get_machine_ip()
        self.ip_combobox.configure(values = ip_list)

    def set_device_ip(self, ip):
        self.device_ip_var.set(ip)
        print("Updated Device IP")

    def set_server_ip(self, ip):
        self.server_ip_var.set(ip)
        print("Updated Server IP")


 