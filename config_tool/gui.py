import customtkinter as ctk
from tkinter import ttk
from config_tool.frames import *
from tkinter import messagebox
from config_tool.global_variables import *
import logging
import tkinter.font as tkFont

class GUI:
    """This is the main Config Tool Class."""
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
        self.root.title("OATIS Configuration Tool")
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
                exit(0)
        
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
        window_frame.pack(pady=0, padx=0, fill="both", expand=True)

        #Setup Columns / rows for window_frame
        window_frame.columnconfigure(0, weight=1)
        window_frame.rowconfigure(0, weight=0)
        window_frame.rowconfigure(1, weight=1)

        #------------------------------MAIN WINDOW FRAME-MENU FRAME--------------------------------------------------
        menu_frame = ctk.CTkFrame(master=window_frame)
        menu_frame.grid(column=0, row=0, columnspan=1, sticky="ew")

        #------------------------------MAIN WINDOW FRAME-TAB FRAMES STACKED--------------------------------------------------
        image_store_frame = Image_Store(window_frame, self.db, True)
        config_frame = Device_Config(window_frame, self.db, True)
        gpio_config_frame = Controller_Config(window_frame, self.db, True)
        input_triggers_frame = Input_Triggers(window_frame, self.db, True)
        input_logics_frame = Input_Logics(window_frame, self.db, True)
        output_logics_frame = Output_Logics(window_frame, self.db, True)
        output_triggers_frame = Output_Triggers(window_frame, self.db, True)
        display_template_frame = Display_Templates(window_frame, self.db, False)
        display_instances_frame = Display_Instances(window_frame, self.db, False)
        messaging_group_frame = Messaging_Groups(window_frame, self.db, True)
        server_config_frame = Server_Config(window_frame, self.db, True)

        self.frames_dict = {
            "Image Store":image_store_frame,
            "Device Config":config_frame,
            "GPIO Config":gpio_config_frame,
            "Input Triggers":input_triggers_frame,
            "Input Logics":input_logics_frame,
            "Output Logics":output_logics_frame,
            "Output Triggers":output_triggers_frame,
            "Display Templates":display_template_frame,
            "Display Instances":display_instances_frame,
            "Messaging Groups":messaging_group_frame,
            "Server Config":server_config_frame
            }
        #Create a list of frame widgets used to pack the widgets
        self.frame_widget_list = list(self.frames_dict.values())

        ##------------------------------Pack all the tab frames stacked, allows TkRaise() to be used--------------------------------------------------
        for frame in self.frame_widget_list:
            frame.grid(column=0, row=1, columnspan=1, sticky="nsew")

        #------------------------------MENU FRAME WIDGETS--------------------------------------------------
        #Make the menu options list from the frames dictionary
        self.menu_options_list = list(self.frames_dict.keys())

        self.menu = ctk.CTkSegmentedButton(menu_frame, values=self.menu_options_list, command=self.menu_callback)
        self.menu.pack(side="left", pady=5, padx=10, fill="both", expand=True)
        
    
    #Raises the selected frame to the top
    def menu_callback(self, selection):
        frame_widget : BaseFrameNew = self.frames_dict[selection]
        frame_widget.tkraise()
        self.logger.info(f"Raised {selection} frame.")
        frame_widget.on_raise_callback()
        self.logger.info(f"Updated {selection} tree and combobox values.")

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