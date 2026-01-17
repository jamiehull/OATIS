#Provides an interface to configure client ip and server ip
from tkinter import StringVar, messagebox
import customtkinter as ctk
from sys import exit
import logging
from modules.common import validate_ip, write_dict_to_file, get_machine_ip


class Settings():
    """Creates a tkinter window to configure ip settings."""
    def __init__(self, settings_file_path):
        super().__init__()

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Path to save settings file
        self.settings_path = settings_file_path

        #This file contains the code for the tkinter main window
        #Set Custom Tkinter Styles
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create the Window
        self.logger.debug("Creating the self.root tkinter window")
        self.root = ctk.CTk()

        #Set Window title and size.
        self.logger.debug("Setting self.root window attributes")
        self.root.title("OATIS Client IP Configuration")
        self.root.attributes("-fullscreen", True)

        #Variables
        self.device_ip_var = StringVar()
        self.server_ip_var = StringVar()

        #Set Default font
        #font_size = screen_info.get("top_level_text_size")
        font_size = 30
        self.default_font = ctk.CTkFont('Arial', font_size)

        #Set column spanning for Top Level Window
        self.root.columnconfigure(0, weight = 1)
        self.root.rowconfigure(0, weight = 1)

        self.__add_widgets()

        self.populate_ip_combobox()

        self.logger.info("Entering Main Loop")
        self.root.mainloop()

    def __add_widgets(self):
        self.container_frame = ctk.CTkFrame(self.root, fg_color='#303030', width=800, height=800, border_color="green", border_width=1)
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

        self.save_btn = ctk.CTkButton(self.container_frame, text="Save", font=self.default_font, fg_color="green", command=lambda:self.__save_entry_data(), width=500)
        self.save_btn.grid(column = 0, row = 6, sticky = "", columnspan = 1, padx=10, pady=20)

        self.back_btn = ctk.CTkButton(self.container_frame, text="Back", font=self.default_font, command=lambda:self.__return_to_main_screen(), width=500)
        self.back_btn.grid(column = 1, row = 6, sticky = "", columnspan = 1, padx=10, pady=20)

        self.exit_btn = ctk.CTkButton(self.container_frame, text="Exit Application", font=self.default_font, fg_color="red", command=lambda:self.__exit_program())
        self.exit_btn.grid(column = 0, row = 7, sticky = "ew", columnspan = 2, padx=20, pady=20)

    def __exit_program(self):
        self.logger.info("Exiting Application")
        exit(0)

    def __save_entry_data(self):
        self.logger.debug("Saving Ip Configuration")
        client_ip = self.device_ip_var.get()
        server_ip = self.server_ip_var.get()

        #Validate IP inputs
        if validate_ip(client_ip) and validate_ip(server_ip):

            self.settings_dict = {}

            #Add all values to the dict
            self.settings_dict["client_ip"] = client_ip
            self.settings_dict["server_ip"] = server_ip
            self.settings_dict["first_run"] = False

            #Write to settings file
            write_dict_to_file(self.settings_dict, self.settings_path)

            self.__close_settings()

        
        #If inputs are invalid prompt the user
        else:
            messagebox.showwarning("IP Address Error", "The entered IP address is not valid.")

    def __close_settings(self):
        self.root.attributes("-fullscreen", False)
        self.root.update_idletasks()
        #self.root.quit()
        self.root.destroy()

    def populate_ip_combobox(self):
        ip_list=get_machine_ip()
        self.ip_combobox.configure(values = ip_list)

    def set_device_ip(self, ip):
        self.device_ip_var.set(ip)
        print("Updated Device IP")

    def set_server_ip(self, ip):
        self.server_ip_var.set(ip)
        print("Updated Server IP")