import customtkinter as ctk
import logging
import tkinter.font as tkFont
from server.server_control import Server_Control
from threading import Thread
from tkinter import StringVar
from database.database_connection import DB

class Server_GUI:
    """Generates a simple GUI for starting and stopping the OATIS server."""
    def __init__(self):

        #This file contains the code for the tkinter main window
        #Set Custom Tkinter Styles
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        #Setup Logging
        self.logger = logging.getLogger(__name__)
        logger_format = "[%(filename)s:%(lineno)s => %(funcName)30s() ] %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=logger_format)

        #Create the Window
        self.logger.debug("Creating the self.root tkinter window")
        self.root = ctk.CTk()

        #Set Window title and size.
        self.logger.debug("Setting self.root window attributes")
        self.root.title("OATIS Server")
        self.root.attributes("-fullscreen", False)

        self.default_font = ctk.CTkFont('Arial', 20)
        default_tk_font = tkFont.nametofont('TkDefaultFont')
        default_tk_font.configure(family='Arial', size=15)

        #Status Variables
        self.server_running = StringVar()
        self.ip_address = StringVar()

        #Add the widgets        
        self.__add_widgets()

        #Set initial server state to stopped
        self.server_running.set("Stopped")

        self.logger.info("Entering Main Loop")
        self.root.mainloop()

    def __add_widgets(self):
        """Adds the Tkinter widgets to the window."""
        #------------------------------MAIN WINDOW FRAME--------------------------------------------------
        self.logger.debug("Adding widgets to the self.root window")
        #Main Frame to hold all widgets / sub-frames in the window
        self.window_frame = ctk.CTkFrame(master=self.root)
        self.window_frame.pack(pady=5, padx=5, fill="both", expand=True)

        #Setup Columns / rows for window_frame
        for i in range(0, 2):
            self.window_frame.columnconfigure(i, weight=1)
        for i in range(0, 2):
            self.window_frame.rowconfigure(i, weight=1)

        #Add widgets to frame
        self.start_button = ctk.CTkButton(self.window_frame, text="Start Server", command=self.__start_server_thread)
        self.start_button.grid(column=0, row=0, sticky="")

        self.stop_button = ctk.CTkButton(self.window_frame, text="Stop Server", command=self.__stop_server)
        self.stop_button.grid(column=1, row=0, sticky="")

        #------------------------------FOOTER FRAME--------------------------------------------------

        self.footer_frame = ctk.CTkFrame(self.window_frame, fg_color="#1B1B1B")
        self.footer_frame.grid(column=0, row=1, columnspan=2, sticky="esw")

        #Setup Columns / rows for window_frame
        for i in range(0, 2):
            self.footer_frame.columnconfigure(i, weight=1)
        for i in range(0, 1):
            self.footer_frame.rowconfigure(i, weight=1)

        #Add widgets to frame
        self.ip_label = ctk.CTkLabel(self.footer_frame, text="IP Address", textvariable=self.ip_address)
        self.ip_label.grid(column=0, row=0, sticky="w")

        self.status_label = ctk.CTkLabel(self.footer_frame, text="Status", textvariable=self.server_running)
        self.status_label.grid(column=1, row=0, sticky="e")

    def __start_server_thread(self):
        """Called on press of Start button."""
        if (self.server_running.get() == "Stopped") or (self.server_running.get() == "Database not initialised"):
            #Check if the database has been initialised
            db = DB()
            self.logger.debug("Determining state of the database")
            db_status = db.verify_database_setup()

            #DB is Initialised
            if db_status == True:
                self.server_thread = Thread(target=self.__start_server, daemon=True)
                self.server_thread.start()

            #DB not Initialised
            else:
                self.server_running.set("Database not initialised")
                self.logger.info("Cannot start Server, database is not initialised. Please initialise the DB in config tool before launching the server.")

        else:
            self.logger.info("Cannot start Server, a Server Instance is already running!")
        
    def __start_server(self):
        """Called by __start_server_thread()"""
        if (self.server_running.get() == "Stopped") or (self.server_running.get() == "Database not initialised"):
            #Update GUI Server State Variable
            self.server_running.set("Booting")

            #Create an instance of the server
            self.logger.info("Starting Server...")
            self.server = Server_Control(self.server_running)

            #Update GUI Variables
            self.server_running.set(self.server.start_server())
            self.ip_address.set(self.server.get_ip_address())

            self.logger.info(f"Server Status: {self.server_running.get()}")

            #If we get errors clear the server instance
            if self.server_running == "Stopped":
                del self.server

    def __stop_server(self):
        
        if self.server_running.get() == "Running":
            self.server_running.set("Shutting down")
            self.logger.info("Stopping Server...")
            self.server.stop_server()
            del self.server
            self.server_running.set("Stopped")
        else:
            self.logger.debug("Server not Running.")

        

server_gui = Server_GUI()