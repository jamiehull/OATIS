import pygame
from pygame.locals import *
from client.display_widgets.clocks import *
from client.display_widgets.top_banners import *
from client.display_widgets.indicators import *
from client.display_widgets.text_fields import *
from client.display_widgets.fullscreen_slates import *
from dataclasses import dataclass
import logging
from modules.osc import *
from modules.tcp import TCP_Client
from modules.common import *
from modules.osc import *
import threading
from time import sleep
import json
from PIL import ImageColor
import time
from os import path

#Dataclass to store a display_surface and it's attributes
@dataclass
class Display_Section:
    id : int
    top_left_screen_coord : tuple
    width : int
    height : int
    surface : pygame.Surface

class Window:
    def __init__(self):

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Client listen Socket - Defaults
        self.client_ip_address = "127.0.0.1"
        self.client_listen_port = 1338

        #Server listen Socket - Defaults
        self.server_ip_address = "127.0.0.1"
        self.server_tcp_port = 1339

        #Paths
        self.default_display_template_path = path.abspath(path.join(path.dirname(__file__), "data/default_display_template.json"))
        self.display_template_path = path.abspath(path.join(path.dirname(__file__), "data/display_template.json"))
        self.settings_path = path.abspath(path.join(path.dirname(__file__), "data/settings.json"))

        #Device information store
        self.device_information_dict = {}

        #Create a pygame clock object for limiting FPS
        self.clock = pygame.time.Clock()
       
        #Default Display Colours
        self.bg_colour = (0,0,255) #Black

        #Initialises all pygame modules
        pygame.init()

        #Get the resolution of the display and store a reference
        self.screen_resolution = pygame.display.get_desktop_sizes()[0]
        self.display_width = self.screen_resolution[0]
        self.display_height = self.screen_resolution[1]
        print(f"Display Resolution:{self.screen_resolution}")

        #List of widgets to render on the surfaces
        self.widget_dict = {}

        #Dictionary of surfaces to blit to the display
        self.blit_dict_lock = threading.Lock()
        self.blit_dict = {}

        #Create the Main Display Window Surface
        self.display_surface = pygame.display.set_mode((self.display_width, self.display_height), pygame.NOFRAME | pygame.SCALED | pygame.FULLSCREEN)

        #Find the centre of the display
        self.horizontal_center = self.display_surface.get_width() / 2
        self.vertical_center = self.display_surface.get_height() / 2

        self.display_template_columns = ["display_template_id",
                                        "display_template_name",
                                        "layout", 
                                        "logo", 
                                        "clock_type", 
                                        "indicators_displayed", 
                                        "indicator_1_label", 
                                        "indicator_1_flash", 
                                        "indicator_1_colour", 
                                        "indicator_2_label", 
                                        "indicator_2_flash", 
                                        "indicator_2_colour",
                                        "indicator_3_label", 
                                        "indicator_3_flash", 
                                        "indicator_3_colour",
                                        "indicator_4_label", 
                                        "indicator_4_flash", 
                                        "indicator_4_colour", 
                                        "indicator_5_label", 
                                        "indicator_5_flash", 
                                        "indicator_5_colour",
                                        "indicator_6_label", 
                                        "indicator_6_flash", 
                                        "indicator_6_colour",
                                        "timestamp"]
        
        #Do the setup Commands
        self.__setup()

        #State variables to signal to functions state of program
        self.running = True #Signals if app is running
        self.reloading_display = False  #Signals if we are re-rendering the display

#--------------------------------Py-Game-Logic--------------------------------------------
    #Start the App
    def on_execute(self):

        #While self.running is True
        while( self.running ):
            #Action each event as they occur
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        #When Loop is broken Cleanup and Quit
        self.on_cleanup()
 
    #Pygame Event Handler
    def on_event(self, event):
        #Checks if there has been a Quit event, if there has been set running to False and break the loop
        if event.type == pygame.QUIT:
            self._running = False

    #Procedures to call on each loop iteration
    def on_loop(self):
        pass
    
    #Update the Display
    def on_render(self):
        with self.blit_dict_lock:
            #Fill the screen with a color to wipe away anything from last frame
            self.display_surface.fill(self.bg_colour)

            #Render each display surface onto the main surface
            for display_section_id in self.blit_dict:
                display_section : Display_Section = self.blit_dict[display_section_id]
                self.display_surface.blit(display_section.surface, display_section.top_left_screen_coord)

            #Render the widgets on each display surface
            for display_section_id in self.widget_dict:
                widget : Widget = self.widget_dict[display_section_id]
                widget.render()


            #flip() the display to put your work on screen
            pygame.display.flip()

            #limits FPS
            self.clock.tick(50)

    #Quits Pygame Modules
    def on_cleanup(self):
        pygame.quit()
#--------------------------------------------------------------------------------------- 

#--------------------------------Display-rendering-Logic--------------------------------------------

    def build_layout_custom(self, layout_matrix:int, top_banner:bool, messaging:bool):

        #Check the layout matrix is valid
        valid_matrix = self.validate_layout_matrix(layout_matrix)

        #If matrix is valid build the layout
        if valid_matrix == True:

            #Defines rows / columns and which are merged
            self.grid = layout_matrix
            self.grid_screen_x_origin = 0
            self.grid_screen_y_origin = 0
            self.remaining_display_width = self.display_width
            self.remaining_display_height = self.display_height

            #If messaging or top_banner are enabled we render these first so we know what display area we have left
            #to render the rest of the screen
            if (top_banner == True) and (messaging == True):
                top_banner_height = self.display_height*0.15

                self.surface_top_banner = pygame.Surface((self.display_width, top_banner_height))
                self.display_section_top_banner = Display_Section(-1, (0,0), self.display_width, self.display_height, self.surface_top_banner)
                self.__add_surface_to_blit(self.display_section_top_banner)

                self.top_banner_logo_date_location = Logo_Date_Location_Top_Banner(self.surface_top_banner)
                self.__add_widget_to_render(-1, self.top_banner_logo_date_location)

                self.top_banner_ticker = Ticker_Banner(self.surface_top_banner)
                self.__add_widget_to_render(-2, self.top_banner_ticker)
                
                #Calculate new plot origin and remaining display height for rendering the rest of the screen
                self.grid_screen_y_origin += (top_banner_height)
                self.remaining_display_height -= self.grid_screen_y_origin

            #MATRIX PROGRAMMING

            #Use the layout matrix to calculate number of columns / rows and sizes
            total_columns = len(self.grid[0])
            total_rows = len(self.grid)
            column_size = self.remaining_display_width/total_columns
            row_size = self.remaining_display_height/total_rows
            print(f"Layout Total Columns:{total_columns}, width:{column_size}")
            print(f"Layout Total Rows:{total_rows}, height:{row_size}")

            #Find the display secions in the layout matrix and their top_left_coordinate
            display_section_dict :dict = self.find_display_sections(self.grid)

            #List to hold display surfaces
            self.display_surface_list = []

            #Find width and height of each display section
            for display_section_id in display_section_dict:
                top_left_coord = display_section_dict.get(display_section_id)
                width, height = self.find_display_section_dimensions(display_section_id, top_left_coord, total_columns, total_rows)

                #Translate matrix coordinate to actual screen coordinates
                display_section_matrix_coordinates = display_section_dict.get(display_section_id)
                display_section_screen_coordinates = (display_section_matrix_coordinates[0]*column_size + self.grid_screen_x_origin, display_section_matrix_coordinates[1]*row_size + self.grid_screen_y_origin)
               
                #Translate matrix widths/heights to screen widths/heights
                display_section_screen_width = width*column_size
                display_section_screen_height = height*row_size

                print(f"Display Section:{display_section_id} Martix Width:{width}, Matrix Height:{height}, Screen Width:{display_section_screen_width}, Screen Height:{display_section_screen_height}") 
                print(f"Top Left Matrix Coordinate:{display_section_matrix_coordinates}, Top Left Screen Coordinate:{display_section_screen_coordinates}")


                #Create each surface and add to blit
                surface = pygame.Surface((display_section_screen_width, display_section_screen_height))

                #Create a display section object
                display_section = Display_Section(display_section_id,
                                                  display_section_screen_coordinates,
                                                  display_section_screen_width,
                                                  display_section_screen_height,
                                                  surface)

                #Add the surface to Blit
                self.__add_surface_to_blit(display_section)

        else:
            print("Cannot build layout, invalid layout matrix.")
    
        #Messaging only no top banner - this results in message being overlayed on the GUI when enabled
        if (top_banner == False) and (messaging == True):
            messaging_top_banner_height = self.display_height*0.15
            #Transparent surface
            self.surface_top_banner = pygame.Surface((self.display_width, top_banner_height), pygame.SRCALPHA, 32)
            self.display_section_top_banner = Display_Section(-1, (0,0), self.display_width, self.display_height, self.surface_top_banner)
            self.__add_surface_to_blit(self.display_section_top_banner)

            self.top_banner_ticker = Ticker_Banner(self.surface_top_banner)
            self.__add_widget_to_render(self.top_banner_ticker)

        #Build the fullscreen logo slate
        self.surface_fullscreen_logo_slate = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA, 32)
        self.display_section_fullscreen_logo_slate = Display_Section(-3, (0,0), self.display_width, self.display_height, self.surface_fullscreen_logo_slate)
        self.__add_surface_to_blit(self.display_section_fullscreen_logo_slate)
        self.fullscreen_logo_slate = Logo_Slate(self.surface_fullscreen_logo_slate)
        self.__add_widget_to_render(-3, self.fullscreen_logo_slate)

        #Build the identify slate
        self.surface_identify_slate = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA, 32)
        self.display_section_identify_slate = Display_Section(-4, (0,self.grid_screen_y_origin), self.display_width, self.remaining_display_height, self.surface_identify_slate)
        self.__add_surface_to_blit(self.display_section_identify_slate)
        self.fullscreen_identify_slate = Identify_Slate(self.surface_identify_slate)
        self.__add_widget_to_render(-4, self.fullscreen_identify_slate)

    def find_display_section_dimensions(self, display_section_id:int, top_left_coord:tuple, total_columns:int, total_rows:int):
        """Finds the dimension of a display section"""
        width=0
        height=0

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding width
        for i in range(total_columns - top_left_coord[0]):
            if self.grid[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                width += 1
                x += 1

        #Origin to start scanning from
        x=top_left_coord[0]
        y=top_left_coord[1]

        #Finding height
        for i in range(total_rows - top_left_coord[1]):
            if self.grid[y][x] == display_section_id:
                #print(f"Position:{x},{y}")
                height += 1
                y += 1

        return width, height

    def validate_layout_matrix(self, layout_matrix:list) -> bool:
        """Validates an input layout matrix"""
        valid_matrix = True
        row_length = len(layout_matrix[0])

        for row in layout_matrix:
            #Check each row is the same length
            if len(row) != row_length:
                valid_matrix = False

        return valid_matrix
    
    def find_display_sections(self, layout_matrix):
        """Finds the display secions in the layout matrix and their top_left_coordinate, returning a dict.
        Keys are display section id's, values are the top_left_coordinate as a tuple."""
        #Working Dict storing section id's and their top left coordinate
        display_section_id_dict = {}

        #Origin to start scanning from
        x=0
        y=0

        #Loop to find each area id and its origin
        for row in layout_matrix:
            for column in row:
                if column not in display_section_id_dict:
                    display_section_id_dict[column] = (x, y)
                x += 1 #Advance to next column
            y += 1 #Advance to next row
            x = 0 #Reset column position to 0 as we are in a new row

        return display_section_id_dict

    def add_widget_to_surface(self, widget, surface_id, **args):
        """Adds a widget to a surface, optional args for widget configuration"""
        if widget == "Leitch Clock":
            clock = Studio_Clock(self.blit_dict[surface_id].surface)
            self.__add_widget_to_render(surface_id, clock)
        if widget == "Analogue Clock":
            clock = Traditional_Clock(self.blit_dict[surface_id].surface)
            self.__add_widget_to_render(surface_id, clock)
        if widget == "Indicators":
            indicator = Indicator_Lamps_Vertical(self.blit_dict[surface_id].surface, args["number_of_indicators"], args["indicator_label_list"], args["indicator_on_rgb_colour_list"], args["indicator_flash_list"] )
            self.__add_widget_to_render(surface_id, indicator)

    def __add_surface_to_blit(self, display_section:Display_Section):
        """Adds a surface to the blit list for copying to the main window"""
        self.blit_dict[display_section.id] = display_section
    
    def __add_widget_to_render(self, display_surface_id, widget):
        """Adds a widget to the widget dict for rendering on a surface"""
        self.widget_dict[display_surface_id] = widget

    def __render_diplay_template_file(self):
        #Get the timestamp of the cached display template
        self.logger.debug("******************Rendering Display Template******************")
        try:
            template_dict = open_json_file(self.display_template_path)
            self.layout : str = template_dict["layout"]
            self.total_indicators : int = template_dict["indicators_displayed"]
            clock_type : str = template_dict["clock_type"]
        except Exception as e:
            self.logger.error(f"Unable to open display template file:{e}")
            template_dict = open_json_file(self.default_display_template_path)
            self.layout : str = template_dict["layout"]
            self.total_indicators : int = template_dict["indicators_displayed"]
            clock_type : str = template_dict["clock_type"]

        self.logger.debug(f"Layout is {self.layout}")
        if self.layout == "Clock With Indicators":
            
            layout_matrix = [[0,1],
                                [0,1]]
            self.build_layout_custom(layout_matrix, True, True)
            self.add_widget_to_surface(clock_type, 0)

            #make a list of indicator labels
            indicator_label_list = []
            indicator_on_rgb_colour_list = []
            indicator_flash_list = []
            for i in range(1, self.total_indicators+1):
                #Labels
                indicator_label = template_dict[f"indicator_{i}_label"]
                indicator_label_list.append(indicator_label)
                #Colours
                indicator_colour_hex = template_dict[f"indicator_{i}_colour"]
                indicator_colour_rgb = ImageColor.getcolor(indicator_colour_hex, "RGB")
                indicator_on_rgb_colour_list.append(indicator_colour_rgb)
                #Flash
                indicator_flash = template_dict[f"indicator_{i}_flash"]
                indicator_flash_list.append(indicator_flash)

            self.add_widget_to_surface("Indicators", 1, number_of_indicators=self.total_indicators, indicator_label_list=indicator_label_list, indicator_on_rgb_colour_list=indicator_on_rgb_colour_list, indicator_flash_list=indicator_flash_list)

        elif self.layout == "Fullscreen Clock":
            layout_matrix = [[0,0],
                                [0,0]]
            self.build_layout_custom(layout_matrix, True, True)
            self.add_widget_to_surface(clock_type, 0)


#----------------------------------Module Specific Code---------------------------------

    #Sets up and renders the GUI
    def __setup(self):

        self.__read_and_set_ip_settings()

        self.logger.debug("Creating instance of the OSC server")
        #Create an instance of the OSC server passing in a reference to the GUI
        self.osc = OSC_Server(self.client_ip_address, self.client_listen_port)
        self.__start_osc()

        #Request display template from server - only updates if it has changed
        self.__request_display_template()

        #Render the Display
        self.__render_diplay_template_file()

        #Start background Threads
        self.logger.info("Starting Background Threads")
        self.__start_daemon_threads()

        #Map GUI handlers to allow GUI to update on recieved command
        self.__map_gui_handlers()

        #Request config info to populate identify frame widgets
        self.__request_device_config()

        self.logger.info("Setup Done - Let's go!")

    def __start_daemon_threads(self):
        self.server_heartbeat_thread = threading.Thread(target=self.__server_heartbeat, daemon=True)
        self.server_heartbeat_thread.start()

    def __stop_daemon_threads(self):
        self.reloading_display = True

    def __start_osc(self):
        #Start the server in a seperate thread
        self.logger.debug("Starting OSC Server in background thread")
        threading.Thread(target=self.osc.start_udp_osc_server, daemon=True).start()
        #threading.Thread(target=self.osc.start_tcp_osc_server, daemon=True).start()

    def __stop_osc(self):
        self.logger.debug("Stopping OSC Server")
        self.osc.start_udp_osc_server()
        #self.osc.stop_tcp_osc_server()

    def __map_gui_handlers(self):
        #Global Handlers
        self.osc.map_osc_handler('/signal-lights/*', self.signal_light_handler)
        self.osc.map_osc_handler("/*/ticker", self.ticker_handler)
        self.osc.map_osc_handler('/client/control/reload_display_template', self.reload_display_handler)
        self.osc.map_osc_handler('/client/control/frames', self.show_frame_handler)

    def __unmap_gui_handlers(self):
        #Global Handlers
        self.osc.unmap_osc_handler('/signal-lights/*', self.signal_light_handler)
        self.osc.unmap_osc_handler("/*/ticker", self.ticker_handler)
        self.osc.unmap_osc_handler('/client/control/reload_display_template', self.reload_display_handler)
        #self.osc.unmap_osc_handler('/client/control/frames', self.show_frame_handler)

    #Reads ip settings from the settings file and applies them
    def __read_and_set_ip_settings(self):
        self.logger.info("Setting Ip settings from File")

        #Read Settings file
        settings_dict = open_json_file(self.settings_path)

        #Set ip's if settings file exists - otherwise defaults are used
        if settings_dict != False:
            self.client_ip_address = settings_dict["client_ip"]
            self.server_ip_address = settings_dict["server_ip"]
            self.logger.info(f"Ip Settings set, Client IP:{self.client_ip_address}, Server IP:{self.server_ip_address}")

        else:
            self.logger.info("Settings file corrupt or missing!")

        #Writes recieved display template to JSON file
    
    def write_display_template_to_file(self, display_template_list:list):
        try:
            #Create a blank dicrtionary to parse the display template into
            self.display_template_dict = {}
            #Iterator variable
            i=0
            #Add each item to the dictionary
            self.logger.debug("Parsing display_template_list into dictionary.")
            for item in self.display_template_columns:
                self.display_template_dict[item] = display_template_list[i]
                i += 1

            #Extract the image_id from the display_template
            self.logger.debug("Extracting image_id from display template")
            image_id = self.display_template_dict["logo"]

            self.logger.debug(f"Writing display template to file.")
            write_dict_to_file(self.display_template_dict, self.display_template_path)
            self.logger.debug(f"Display Template Saved")
            self.__update_logo_file(image_id)
            self.logger.info("JSON Display Template Recieved From Server and stored on device local cache.")

        except Exception as e:
            self.logger.error(f"Error Parsing recieved JSON: {e}")

#----------------TCP Network Commands-----------------------
    #----------Requestors-retrieving data from the server-USES TCP FILE TRANSFER------------------------

    #Requests logo image file from server
    def __update_logo_file(self, image_id):
        try:
            #Request the new logo file
            self.logger.debug("Requesting new logo file.")
            tcp_client = TCP_Client()
            #Build the Message and send
            command = "/assets/images/get"
            arguments = {"image_id":image_id}
            message = tcp_client.build_tcp_message(command, arguments)
            image_blob = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)
            self.logger.debug("Converting Recieved logo file from bytes to png.")
            convert_from_blob(image_blob, "client/data/logo.png")
            self.logger.debug("New logo file saved locally on device.")
        except Exception as e:
            self.logger.error(f"Unable to get new logo file from server, reason: {e}")

    #Requests the device configuration from the server
    def __request_device_config(self):
        self.logger.debug(f"Requesting Device Configuration from Server: {self.server_ip_address}")
        try:
            tcp_client = TCP_Client()
            #Build the Message and send
            command = "/config/device/get"
            arguments = {
                        "client_ip" : self.client_ip_address
                        }
            data = None

            message = tcp_client.build_tcp_message(command, arguments, data)
            response_bytes = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)
            response = tcp_client.decode_data(response_bytes)
            self.logger.debug(f"Response from server: {response}")

            #Read the response
            response_dict = json.loads(response)
            arguments = response_dict["arguments"]

            #Store the recieved information locally
            self.device_information_dict = arguments

            device_information_widget : Identify_Slate = self.widget_dict[-4]
            device_information_widget.set_information(self.device_information_dict) 

            #Set the location field on the display
            device_location = arguments["device_location"]
            top_banner : Logo_Date_Location_Top_Banner = self.widget_dict[-1]
            top_banner.set_location(device_location)


        except ConnectionRefusedError as e:
            self.logger.error(f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
        except Exception as e:
            self.logger.error(f"Cannot connect to server: {e}")

    #Requests the display template from the server
    def __request_display_template(self):
        try:
            #Get the timestamp of the cached display template
            cached_template_dict = open_json_file(self.display_template_path)

            if cached_template_dict != False:
                #Extract the timestamp from the display_template
                timestamp = cached_template_dict["timestamp"]
            #If there is no existing display template use a timestamp of 0 to signal this
            else:
                timestamp = 0

            #Request a new display template from the server
            tcp_client = TCP_Client()
            message = tcp_client.build_tcp_message("/config/display_template/get", {"timestamp":timestamp, "client_ip":self.client_ip_address})
            response_bytes = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)
            response = tcp_client.decode_data(response_bytes)
            self.logger.debug(f"Data recieved from server: {response}")

            #Read the response
            response_dict = json.loads(response)
            arguments = response_dict["arguments"]
            display_template_match_status = arguments["display_template_current"]
            display_template = response_dict["data"]

            if display_template_match_status == True:
                self.logger.debug(f"Cached Display template matches the one held on the server")

            else:
                self.logger.debug("Commiting Recieved Display Template to file")
                self.write_display_template_to_file(display_template)

        except ConnectionRefusedError as e:
            self.logger.error(f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
        except Exception as e:
            self.logger.error(f"Cannot connect to server: {e}")

    #----------Heartbeat------------------------

    def __server_heartbeat(self):
        sleep(3)
        while self.reloading_display == False:
            #Default wait time until a connection is made
            self.wait_time = 5
            try:
                #Send a heartbeat message to the server
                tcp_client = TCP_Client()
                message = tcp_client.build_tcp_message("heartbeat", {"client_ip":self.client_ip_address}, None)
                response = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)
                
                #Read the response
                response_dict = json.loads(response)
                self.logger.debug(f"Data recieved from server: {response_dict}")
                arguments = response_dict["arguments"]

                status = arguments["status"]
                timestamp = arguments["timestamp"]

                if status == "OK":
                    self.logger.debug(f"Server last seen at: {timestamp}")
                    self.alarm_indicator_off()
                    self.wait_time = 60

                else:
                    self.logger.warning("Server Offline")
                    self.alarm_indicator_on()
                    self.wait_time = 5

            except ConnectionRefusedError as e:
                self.logger.error(f"Cannot connect to server, the server may not be running or IP set incorrectly: {e}")
                self.alarm_indicator_on()
                self.wait_time = 5
            except Exception as e:
                self.logger.error(f"Cannot connect to server: {e}")
                self.alarm_indicator_on()
                self.wait_time = 5

            sleep(self.wait_time)

            
#----------------------Handlers-------------------------------------

    def signal_light_handler(self, address, *args):
        """Handles an incoming OSC command to change hte state of an indicator light"""
        indicator_address = int(address[-1:]) -1
        state = args[0]
        print(f"Incoming Data: Indicator Address:{indicator_address}, State:{state}")

        if self.layout == "Clock With Indicators":
            indicators_widget : Indicator_Lamps_Vertical = self.widget_dict[1]
            if state == 1:
                indicators_widget.trigger_indicator_on([indicator_address])
                print("Indicator On")
            else:
                indicators_widget.trigger_indicator_off([indicator_address])
                print("Indicator Off")

    def ticker_handler(self, address, *args):
        state = args[0]

        self.logger.debug(f"Incoming Data:{address}, {args}")
        ticker_widget : Ticker_Banner = self.widget_dict[-2]
        
        if state == True:
            text= args[1]
            bg_colour_hex = args[2]
            bg_colour_rgb = ImageColor.getcolor(bg_colour_hex, "RGB")

            self.logger.debug("Ticker On")
            ticker_widget.set_ticker_text(text)
            ticker_widget.set_bg_colour(bg_colour_rgb)
            ticker_widget.ticker_on()
            
        else:
            self.logger.debug("Ticker Off")
            ticker_widget.ticker_off()

    def reload_display_handler(self, address, *args):
        self.logger.info("***************Reloading Display***************")
        self.show_frame(0)

        self.__unmap_gui_handlers()
        self.logger.debug("Unmapped OSC Handlers")

        self.__stop_daemon_threads()
        self.logger.debug("Stopped Background Threads")
        
        self.logger.info("Rendering new display...")

        #Request display template from server - only updates if it has changed
        self.__request_display_template()

        time.sleep(5)

        with self.blit_dict_lock:

            #Create a copy of the current blit list used when clearing the current one
            copy_of_blit_dict = {}
            for display_section_id in self.blit_dict:
                copy_of_blit_dict[display_section_id] = self.blit_dict[display_section_id]

            #Clear the current blit list except for the surface with id -3 this is the fullscreen slate
            for display_section_id in copy_of_blit_dict:
                self.blit_dict.pop(display_section_id)

            #Render OATIS Display based on display template
            self.__render_diplay_template_file()

            #Request config info to populate identify frame widgets
            self.__request_device_config()

            #Start GUI background Threads
            self.logger.info("Starting GUI Background Threads")
            self.__start_daemon_threads()

            #Map GUI handlers to allow GUI to update on recieved command
            self.__map_gui_handlers()

            #Raise the OATIS frame into view
            self.show_frame(2)

            self.logger.info("Reloaded Display Successfully")

    def show_frame_handler(self, address, *args):
        self.logger.info(f"***************Raising Frame***************")
        if args[0] == "identify":
            self.show_frame(1)
        elif args[0] == "OATIS":
            self.show_frame(2)

    def alarm_indicator_on(self):
        clock_widget = self.widget_dict[0]
        clock_widget.alarm_indicator_flash_enable()

    def alarm_indicator_off(self):
        clock_widget = self.widget_dict[0]
        clock_widget.alarm_indicator_flash_disable()

    #Raises a stacked frame to the top visible layer
    def show_frame(self, frame_number):
        """Raise a display surface into view, Frame 0: Logo Frame, Frame 1:Device Information, Frame 2: OATIS"""
        #Logo Slate
        if frame_number == 0:
            self.logger.info("Raising Logo Screen")
            logo_slate_widget : Logo_Slate = self.widget_dict[-3]
            logo_slate_widget.make_visible()
            identify_slate_widget : Identify_Slate = self.widget_dict[-4]
            identify_slate_widget.hide()
            self.logger.debug(f"Logo Slate State:{logo_slate_widget.active}")
            self.logger.debug(f"Identify Slate State:{identify_slate_widget.active}")
        #Device Information
        elif frame_number == 1:
            self.logger.info("Raising Information Screen")
            logo_slate_widget : Logo_Slate = self.widget_dict[-3]
            logo_slate_widget.hide()
            identify_slate_widget : Identify_Slate = self.widget_dict[-4]
            identify_slate_widget.make_visible()
            self.logger.debug(f"Logo Slate State:{logo_slate_widget.active}")
            self.logger.debug(f"Identify Slate State:{identify_slate_widget.active}")
        #OATIS
        elif frame_number == 2:
            self.logger.info("Raising OATIS Screen")
            logo_slate_widget : Logo_Slate = self.widget_dict[-3]
            logo_slate_widget.hide()
            identify_slate_widget : Identify_Slate = self.widget_dict[-4]
            identify_slate_widget.hide()
            self.logger.debug(f"Logo Slate State:{logo_slate_widget.active}")
            self.logger.debug(f"Identify Slate State:{identify_slate_widget.active}")

        

        
        
