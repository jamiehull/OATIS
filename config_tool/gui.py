import customtkinter as ctk
from tkinter import ttk
from config_tool.frames import *
from tkinter import messagebox
from config_tool.global_variables import *
import logging
import tkinter.font as tkFont

class GUI:

    def __init__(self):
        #This file contains the code for the tkinter main window
        #Set Custom Tkinter Styles
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Create a new instance of the database
        self.logger.debug("Creating a database connection object")
        self.db = DB()

        #Create the Window
        self.logger.debug("Creating the self.root tkinter window")
        self.root = ctk.CTk()

        #Set a style to set row heights for all treeviewers
        style = ttk.Style()
        style.configure('Treeview', rowheight=40)

        #Set Window title and size.
        self.logger.debug("Setting self.root window attributes")
        self.root.title("OATIS - Configuration Tool")
        self.root.attributes("-fullscreen", True)

        #Check if the database has been initialised
        self.logger.debug("Determining state of the database")
        status = self.db.verify_database_setup()
        #If the database is valid proceed to create the GUI
        if status == True:
            self.logger.info("Database is valid, Lets Go!")
        #If the database is invalid, prompt to initialise the database before proceeding
        else:
            self.logger.error("Database Invalid or corrupt")
            answer =  messagebox.askyesno("Database Error", "The database is either not initialised or corrupt. Would you like me to re-initialise the database? Please note this will clear all data?")
            if answer == True:
                #Initialise the database
                self.db.initialise_database()
            else:
                self.logger.info("Terminating Program")
                self.root.destroy()
        
        self.default_font = ctk.CTkFont(default_font, default_size)
        default_tk_font = tkFont.nametofont('TkDefaultFont')
        default_tk_font.configure(family='Arial', size=15)

        #Add the widgets        
        self.__add_widgets()

        self.logger.info("Entering Main Loop")
        self.root.mainloop()

    def __add_widgets(self):
        #------------------------------MAIN WINDOW FRAME--------------------------------------------------
        self.logger.debug("Adding widgets to the self.root window")
        #Main Frame to hold all widgets / sub-frames in the window
        window_frame = ctk.CTkFrame(master=self.root)
        window_frame.pack(pady=20, padx=20, fill="both", expand=True)

        #Setup Columns / rows for window_frame
        window_frame.columnconfigure(0, weight=1)
        window_frame.rowconfigure(0, weight=0)
        window_frame.rowconfigure(1, weight=1)

        #------------------------------MAIN WINDOW FRAME-MENU FRAME--------------------------------------------------
        menu_frame = ctk.CTkFrame(master=window_frame)
        menu_frame.grid(column=0, row=0, columnspan=1, sticky="ew")

        #------------------------------MAIN WINDOW FRAME-TAB FRAMES STACKED--------------------------------------------------
        image_store_frame = Image_Store(window_frame, self.db)
        config_frame = Device_Config(window_frame, self.db)
        gpio_conf_frame = GPIO_Config(window_frame, self.db)
        trig_grp_frame = Trigger_Config(window_frame, self.db)
        display_tmplt_frame = Display_Templates(window_frame, self.db)
        messaging_grp_frame = Messaging_Groups(window_frame, self.db)
        server_config_frame = Server_Config(window_frame, self.db)

        ##------------------------------Pack all the tab frames stacked, allows TkRaise() to be used--------------------------------------------------
        for frame in (image_store_frame, config_frame, gpio_conf_frame, trig_grp_frame, display_tmplt_frame, messaging_grp_frame, server_config_frame):
            frame.grid(column=0, row=1, columnspan=1, sticky="nsew")

        #------------------------------MENU FRAME WIDGETS--------------------------------------------------
        #Creates the button menu to switch between tabs
        self.image_store_btn = ctk.CTkButton(master=menu_frame, text="Image Store", font=self.default_font, command=lambda:self.show_frame(image_store_frame, 0))
        self.image_store_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.device_config_btn = ctk.CTkButton(master=menu_frame, text="Device Config", font=self.default_font, command=lambda:self.show_frame(config_frame, 1))
        self.device_config_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.gpio_config_btn = ctk.CTkButton(master=menu_frame, text="GPIO Config", font=self.default_font, command=lambda:self.show_frame(gpio_conf_frame, 2))
        self.gpio_config_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.trig_grp_btn = ctk.CTkButton(master=menu_frame, text="Trigger Groups", font=self.default_font, command=lambda:self.show_frame(trig_grp_frame, 3))
        self.trig_grp_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.display_tmplt_btn = ctk.CTkButton(master=menu_frame, text="Display Templates", font=self.default_font, command=lambda:self.show_frame(display_tmplt_frame, 4))
        self.display_tmplt_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.messaging_grp_btn = ctk.CTkButton(master=menu_frame, text="Messaging Groups", font=self.default_font, command=lambda:self.show_frame(messaging_grp_frame, 5))
        self.messaging_grp_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        self.server_config_btn = ctk.CTkButton(master=menu_frame, text="Server Config", font=self.default_font, command=lambda:self.show_frame(server_config_frame, 6))
        self.server_config_btn.pack(side="left", pady=5, padx=10, fill="both", expand=True)

        #Setup binding to GUI elements
        #Binds device config button to a function that refreshes the combo vox options from the database
        self.device_config_btn.bind("<ButtonRelease-1>", config_frame.refresh_cboxs)

        #Binds image store button to a function that refreshes the combo box options from the database
        self.display_tmplt_btn.bind("<ButtonRelease-1>", display_tmplt_frame.refresh_cboxs)

        #Binds trigger groups button to a function that refreshes the combo box options from the database
        self.trig_grp_btn.bind("<ButtonRelease-1>", trig_grp_frame.refresh_cboxs)

        #Binds gpio config button to a function that refreshes the combo box options from the database
        self.gpio_config_btn.bind("<ButtonRelease-1>", gpio_conf_frame.refresh_cboxs)

    #Function to raise a stacked frame to the top, also changes selected button colour
    def show_frame(self, frame, btn_id):
        self.logger.debug(f"Raising frame: {frame} on button click from button: {btn_id}")
        frame.tkraise()
        menu_btn_list = [self.image_store_btn, self.device_config_btn, self.gpio_config_btn, self.trig_grp_btn, self.display_tmplt_btn, self.messaging_grp_btn, self.server_config_btn]
        #Change all buttons back to default colour
        self.logger.debug("Changing all buttons back to default colour")
        for btn in menu_btn_list:
            btn.configure(fg_color="#1F6AA5")
        #Change the selected button
        self.logger.debug(f"Changing selected button: {btn_id} green")
        menu_btn_list[btn_id].configure(fg_color="green")

    def set_scaling(self):
        self.root.update_idletasks()
        #Get the size of the window for other classees to use for scaling
        self.width = self.root.winfo_width()
        self.height = self.root.winfo_height()
        self.logger.info(f"The screen size is {self.width}x{self.height}")

        #Store the screen size in the global dictionary
        screen_info["width"] = self.width
        screen_info["height"] = self.height

        #Set Font sizes based on window size - store these in the global dictionary
        if self.width > 1920:
            screen_info["date_text_size"] = xlarge_font_size
            screen_info["location_text_size"] = xlarge_font_size
            screen_info["clock_text_size"] = xlarge_font_size
            screen_info["indicator_text_size"] = xlarge_font_size
            screen_info["ticker_text_size"] = alt1_xlarge_font_size
            screen_info["logo_dimensions"] = xlarge_image
        if self.width == 1920:
            screen_info["date_text_size"] = large_font_size
            screen_info["location_text_size"] = large_font_size
            screen_info["clock_text_size"] = large_font_size
            screen_info["indicator_text_size"] = large_font_size
            screen_info["ticker_text_size"] = alt1_large_font_size
            screen_info["logo_dimensions"] = large_image
        if (self.width >= 1280) & (self.width < 1920):
            screen_info["date_text_size"] = medium_font_size
            screen_info["location_text_size"] = medium_font_size
            screen_info["clock_text_size"] = medium_font_size
            screen_info["indicator_text_size"] = medium_font_size
            screen_info["ticker_text_size"] = alt1_medium_font_size
            screen_info["logo_dimensions"] = medium_image
        if self.width < 1280:
            screen_info["date_text_size"] = small_font_size
            screen_info["location_text_size"] = small_font_size
            screen_info["clock_text_size"] = small_font_size
            screen_info["indicator_text_size"] = small_font_size
            screen_info["ticker_text_size"] = alt1_small_font_size
            screen_info["logo_dimensions"] = small_image