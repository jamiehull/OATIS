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
from modules.matrix_operations import *
import threading
from time import sleep
import json
from PIL import ImageColor
import time
from os import path
import os

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
        self.default_display_template_path = path.abspath(path.join(path.dirname(__file__), "data/defaults/default_display_template.json"))
        self.display_template_path = path.abspath(path.join(path.dirname(__file__), "data/display_template.json"))
        self.images_path = path.abspath(path.join(path.dirname(__file__), "data/images"))
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
        self.blit_dict = {}

        #Lock to make accessing the dict from multiple threads safe
        self.blit_dict_lock = threading.Lock()

        #Create the Main Display Window Surface 
        self.display_surface = pygame.display.set_mode((self.display_width, self.display_height), pygame.SCALED | pygame.FULLSCREEN | pygame.NOFRAME)

        #Find the centre of the display
        self.horizontal_center = self.display_surface.get_width() / 2
        self.vertical_center = self.display_surface.get_height() / 2

        #Clock widget surfaces - used to trigger alarm indicator
        self.clock_widget_surfaces_list = []
        self.indicator_surfaces_list = []
        
        #Do the setup Commands
        self.__setup()

        #State variables to signal to functions state of program
        self.running = True #Signals if app is running
        self.reloading_display = False  #Signals if we are re-rendering the display

        #Used for measuring FPS
        self.fps_time = 10000

#--------------------------------Py-Game-Logic--------------------------------------------
    #Start the App
    def on_execute(self):

        #While self.running is True
        while self.running == True:
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

        if event.type == pygame.KEYDOWN:
            #ESC - Keypress
            if event.key == K_ESCAPE:
                self.logger.debug("Escape Key Pressed, shutting down application...")

                #Quit pygame
                self.running = False

            #i - Keypress
            if event.key == K_i:
                self.logger.debug("i Key Pressed, setting flag for ip configuration on next boot and shutting down application...")

                #Open current settings file
                self.settings_dict = open_json_file(self.settings_path)

                #Modify first run flag
                self.settings_dict["first_run"] = True

                #Write to settings file
                write_dict_to_file(self.settings_dict, self.settings_path)

                #Quit pygame
                self.running = False
        
    #Procedures to call on each loop iteration
    def on_loop(self):
        pass
    
    #Update the Display
    def on_render(self):
        with self.blit_dict_lock:
            #Render each display surface onto the main surface
            for display_section_id in self.blit_dict:
                if display_section_id != -2 and display_section_id != -3 and display_section_id != -4:
                    display_section : Display_Section = self.blit_dict[display_section_id]
                    self.display_surface.blit(display_section.surface, display_section.top_left_screen_coord)

            #Render the widgets on each display surface
            for display_section_id in self.widget_dict:
                if display_section_id != -2 and display_section_id != -3 and display_section_id != -4:
                    widget : Widget = self.widget_dict[display_section_id]
                    widget.render()

            #Fullscreen slates rendered last so they are ontop
            logo_display_section : Display_Section = self.blit_dict[-3]
            logo_slate_widget : Widget = self.widget_dict[-3]
            self.display_surface.blit(logo_display_section.surface, logo_display_section.top_left_screen_coord)
            logo_slate_widget.render()

            identify_display_section : Display_Section = self.blit_dict[-4]
            identify_slate_widget : Widget = self.widget_dict[-4]
            self.display_surface.blit(identify_display_section.surface, identify_display_section.top_left_screen_coord)
            identify_slate_widget.render()

            #Ticker surface rendered ontop of everything, transparent when not active
            ticker_display_section : Display_Section = self.blit_dict[-2]
            ticker_widget : Widget = self.widget_dict[-2]
            self.display_surface.blit(ticker_display_section.surface, ticker_display_section.top_left_screen_coord)
            ticker_widget.render()

            #flip() the display to put your work on screen
            pygame.display.flip()

            #limits FPS
            self.clock.tick(25)

            #Measure FPS
            self.__measure_fps()

    #Quits Pygame Modules
    def on_cleanup(self):
        self.__unmap_gui_handlers()
        self.__stop_osc()
        self.__stop_daemon_threads()
        pygame.quit()

#--------------------------------------------------------------------------------------- 

#--------------------------------Display-rendering-Logic--------------------------------------------

    def validate_layout_matrix(self, layout_matrix:list) -> bool:
        """Validates an input layout matrix"""
        valid_matrix = True
        row_length = len(layout_matrix[0])

        for row in layout_matrix:
            #Check each row is the same length
            if len(row) != row_length:
                valid_matrix = False

        return valid_matrix

    def __add_surface_to_blit(self, display_section:Display_Section):
        """Adds a surface to the blit list for copying to the main window"""
        self.blit_dict[display_section.id] = display_section
    
    def __add_widget_to_render(self, display_surface_id:int, widget):
        """Adds a widget to the widget dict for rendering on a surface"""
        self.widget_dict[display_surface_id] = widget

    def __render_diplay_template_file(self):
        #Get the timestamp of the cached display template
        self.logger.debug("******************Rendering Display Template******************")
    
        #Open the display template
        template_dict = open_json_file(self.display_template_path)
        if template_dict != False:
            self.layout_matrix = template_dict["layout_matrix"]
            self.display_surfaces = template_dict["display_surfaces"]
            self.build_layout_custom(self.layout_matrix, self.display_surfaces)
        else:
            self.logger.warning("Display template file not found, using default!")
            default_template_dict = open_json_file(self.default_display_template_path)
            self.layout_matrix = default_template_dict["layout_matrix"]
            self.display_surfaces = default_template_dict["display_surfaces"]
            self.build_layout_custom(self.layout_matrix, self.display_surfaces)
            

    def build_layout_custom(self, layout_matrix:int, display_surfaces_dict:dict):
        """Builds a display layout from a layout matrix and display surface config."""

        #Check the layout matrix is valid
        valid_matrix = self.validate_layout_matrix(layout_matrix)

        #If matrix is valid build the layout
        if valid_matrix == True:

            #Clear caches
            self.clock_widget_surfaces_list.clear()
            self.indicator_surfaces_list.clear()

            #Defines rows / columns and which are merged
            self.grid = layout_matrix
            self.grid_screen_x_origin = 0
            self.grid_screen_y_origin = 0
            self.remaining_display_width = self.display_width
            self.remaining_display_height = self.display_height
                
            #MATRIX PROGRAMMING

            #Use the layout matrix to calculate number of columns / rows and sizes
            total_columns = len(self.grid[0])
            total_rows = len(self.grid)

            column_size = self.remaining_display_width/total_columns
            row_size = self.remaining_display_height/total_rows

            print(f"Layout Total Columns:{total_columns}, width:{column_size}")
            print(f"Layout Total Rows:{total_rows}, height:{row_size}")

            #Find the display secions in the layout matrix and their top_left_coordinate
            display_section_dict :dict = find_display_sections(self.grid)

            #List to hold display surfaces
            self.display_surface_list = []

            #Find width and height of each display section
            for display_section_id in display_section_dict:
                top_left_coord = display_section_dict.get(display_section_id)
                width, height = find_display_section_dimensions(self.grid, display_section_id, top_left_coord, total_columns, total_rows)

                #Translate matrix coordinate to actual screen coordinates
                display_section_matrix_coordinates = display_section_dict.get(display_section_id)
                display_section_screen_coordinates = (display_section_matrix_coordinates[0]*column_size + self.grid_screen_x_origin, display_section_matrix_coordinates[1]*row_size + self.grid_screen_y_origin)
               
                #Translate matrix widths/heights to screen widths/heights
                display_section_screen_width = width*column_size
                display_section_screen_height = height*row_size

                print(f"Display Section:{display_section_id} Martix Width:{width}, Matrix Height:{height}, Screen Width:{display_section_screen_width}, Screen Height:{display_section_screen_height}") 
                print(f"Top Left Matrix Coordinate:{display_section_matrix_coordinates}, Top Left Screen Coordinate:{display_section_screen_coordinates}")

                #Create each surface and add to blit
                display_surface = pygame.Surface((display_section_screen_width, display_section_screen_height))

                #Create a display section object
                display_section = Display_Section(display_section_id,
                                                  display_section_screen_coordinates,
                                                  display_section_screen_width,
                                                  display_section_screen_height,
                                                  display_surface)

                #Add the surface to Blit
                self.__add_surface_to_blit(display_section)

                #Get the widget config for the surface
                surface_config_dict : dict = display_surfaces_dict.get(display_section_id)
                widget_string = surface_config_dict["widget_string"]
                widget_config_dict = surface_config_dict["widget_config"]

                #Add the widget to the surface and pass the widget it's config
                self.add_widget_object_to_surface(widget_string, display_surface, display_section_id, widget_config_dict)

                #If a clock widget add the surface id to the list to allow the alarm to be triggered
                if widget_string == "analogue_clock" or widget_string == "studio_clock" or widget_string == "digital_clock":
                    self.clock_widget_surfaces_list.append(int(display_section_id))
                #If an indicator widget add to the indicator list to allow it to be triggered
                elif widget_string == "indicator":
                    self.indicator_surfaces_list.append(int(display_section_id))


        else:
            print("Cannot build layout, invalid layout matrix.")

    def build_fullscreen_slates(self):
        #Build the fullscreen logo slate
        self.surface_fullscreen_logo_slate = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA, 32)
        self.display_section_fullscreen_logo_slate = Display_Section(-3, (0,0), self.display_width, self.display_height, self.surface_fullscreen_logo_slate)
        self.__add_surface_to_blit(self.display_section_fullscreen_logo_slate)
        self.fullscreen_logo_slate = Logo_Slate(self.surface_fullscreen_logo_slate)
        self.__add_widget_to_render(-3, self.fullscreen_logo_slate)

        #Build the identify slate
        self.surface_identify_slate = pygame.Surface((self.display_width, self.display_height), pygame.SRCALPHA, 32)
        self.display_section_identify_slate = Display_Section(-4, (0,0), self.display_width, self.display_height, self.surface_identify_slate)
        self.__add_surface_to_blit(self.display_section_identify_slate)
        self.fullscreen_identify_slate = Identify_Slate(self.surface_identify_slate)
        self.__add_widget_to_render(-4, self.fullscreen_identify_slate)

    def build_ticker(self):
        messaging_top_banner_height = self.display_height*0.15
        #Transparent surface
        self.surface_top_banner = pygame.Surface((self.display_width, messaging_top_banner_height), pygame.SRCALPHA, 32)
        self.display_section_top_banner = Display_Section(-2, (0,0), self.display_width, self.display_height, self.surface_top_banner)
        self.__add_surface_to_blit(self.display_section_top_banner)

        self.top_banner_ticker = Ticker_Banner(self.surface_top_banner)
        self.__add_widget_to_render(-2, self.top_banner_ticker)

    def add_widget_object_to_surface(self, widget_string, display_surface, display_surface_id, widget_config:dict):
        """Adds a widget object to a surface and configures it."""
        widget = None

        if widget_string == "indicator":
            widget = Indicator_Lamp(display_surface, widget_config)
        elif widget_string == "studio_clock":
            widget = Studio_Clock(display_surface, widget_config)
        elif widget_string == "analogue_clock":
            widget = Analogue_Clock(display_surface, widget_config)
        elif widget_string == "digital_clock":
            widget = Digital_Clock(display_surface, widget_config)
        elif widget_string == "static_text":
            widget = Analogue_Clock(display_surface, widget_config)
        elif widget_string == "static_image":
            widget = Analogue_Clock(display_surface, widget_config)
        elif widget_string == "stacked_image":
            widget = Analogue_Clock(display_surface, widget_config)
        
        
        elif widget_string == "top_banner":
            widget = Logo_Date_Location_Top_Banner(display_surface, widget_config)

        if widget != None:
            self.__add_widget_to_render(int(display_surface_id), widget)

    def __measure_fps(self):
        """Report the FPS to terminal every 10 seconds."""
        current_time = pygame.time.get_ticks()
        if current_time > self.fps_time:
            self.logger.debug(f"FPS:{str(self.clock.get_fps())[0:5]}")
            self.fps_time = current_time + 10000

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

        #Render fullscreen slates
        self.build_fullscreen_slates()

        #Render Ticker banner
        self.build_ticker()

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
        self.osc.stop_udp_osc_server()
        #self.osc.stop_tcp_osc_server()

    def __map_gui_handlers(self):
        #Global Handlers
        self.osc.map_osc_handler('/client/control/signal_lights/', self.signal_light_handler)
        self.osc.map_osc_handler("/client/control/ticker", self.ticker_handler)
        self.osc.map_osc_handler('/client/control/reload_display_template', self.reload_display_handler)
        self.osc.map_osc_handler('/client/control/frames', self.show_frame_handler)

    def __unmap_gui_handlers(self):
        #Global Handlers
        self.osc.unmap_osc_handler('/client/control/signal_lights/', self.signal_light_handler)
        self.osc.unmap_osc_handler("/client/control/ticker", self.ticker_handler)
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
    
    def write_display_template_to_file(self, display_config):
        try:
            self.logger.debug(f"Writing display template to file.")
            write_dict_to_file(display_config, self.display_template_path)
            self.logger.debug(f"Display Template Saved")

            self.logger.info("JSON Display Template Recieved From Server and stored on device local cache.")

        except Exception as e:
            self.logger.error(f"Error Parsing recieved JSON: {e}")

#----------------TCP Network Commands-----------------------
    #----------Requestors-retrieving data from the server-USES TCP FILE TRANSFER------------------------

    #Requests logo image file from server
    def __update_image_files(self, image_id_list:list):
        try:
            #Clear all images from the image directory
            self.logger.debug("Deleting all image files")
            for filename in os.listdir(self.images_path):
                file_path = os.path.join(self.images_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    self.logger.debug(f"Deleted: {filename}")

            #Request the new logo file
            self.logger.debug("Requesting new image files.")
            tcp_client = TCP_Client()

            #Build the Message and send
            command = "/assets/images/get"
            for image_id in image_id_list:
                arguments = {"image_id":image_id}
                message = tcp_client.build_tcp_message(command, arguments)
                image_blob = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message, True)

                #Make the filename from the image_id
                filename = f"{image_id}.png"
                image_save_path = os.path.join(self.images_path, filename)

                self.logger.debug("Converting Recieved logo file from bytes to png.")
                convert_from_blob(image_blob, image_save_path)
                self.logger.debug(f"New image file saved locally on device as {filename} in {image_save_path}.")

        except Exception as e:
            self.logger.error(f"Unable to get new logo file from server, reason: {e} ")

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
            output_command, output_arguments, output_data  = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)

            #Store the recieved information locally
            self.device_information_dict = output_arguments

            #Check server reports ok status
            request_status = output_arguments["status"]
            
            if request_status == "OK":
                #Get the location from the request response
                device_location = output_arguments["device_location"]

                #Update the identify slate
                device_information_widget : Identify_Slate = self.widget_dict[-4]
                self.logger.debug(f"Device_dict: {self.device_information_dict}")
                device_information_widget.set_information(self.device_information_dict)
                device_information_widget.set_location(device_location)

                #Check the display template for top_banner widgets
                top_banner_surface_id_list = []
                display_template_dict : dict = open_json_file(self.display_template_path)
                display_surfaces_dict :dict  = display_template_dict.get("display_surfaces")

                for key in display_surfaces_dict:
                    widget_config_dict : dict = display_surfaces_dict.get(key)
                    if widget_config_dict.get("widget_string") == "top_banner":
                        top_banner_surface_id_list.append(int(key))

                #Update the location on all top_banners
                for surface_id in top_banner_surface_id_list:
                    top_banner : Logo_Date_Location_Top_Banner = self.widget_dict[surface_id]
                    top_banner.set_location(device_location)

            else:
                self.logger.error(f"Server returned invalid status: {request_status}")

        except (ConnectionRefusedError, TimeoutError) as e:
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
                display_template_timestamp = cached_template_dict["display_template_timestamp"]
                display_instance_timestamp = cached_template_dict["display_instance_timestamp"]

            #If there is no existing display template use a timestamp of 0 to signal this
            else:
                display_template_timestamp = "0"
                display_instance_timestamp = "0"

            #Request a new display template from the server
            tcp_client = TCP_Client()
            message = tcp_client.build_tcp_message("/config/display_template/get", {"display_template_timestamp":display_template_timestamp, "display_instance_timestamp":display_instance_timestamp, "client_ip":self.client_ip_address})
            command, arguments, data = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)
            self.logger.debug(f"Data recieved from server:")
            self.logger.debug(f"Command:{command}")
            self.logger.debug(f"Arguments:{arguments}")
            self.logger.debug(f"Data:{data}")

            #Check if the request was successful
            request_status = arguments["status"]

            if request_status == "OK":
                #Check if local display template matches server
                display_template_match_status = arguments["display_template_current"]

                if display_template_match_status == True:
                    self.logger.debug(f"Cached Display template matches the one held on the server")

                else:
                    self.logger.debug("Commiting Recieved Display Template to file")
                    self.write_display_template_to_file(arguments)

                    #Retrieve any image_id's from the display tempalte and get these images from the server
                    image_id_list = []
                    display_surface_config_dict = arguments["display_surfaces"]
                    for key in display_surface_config_dict:
                        display_surface_config = display_surface_config_dict.get(key)
                        self.logger.debug(f"Display Surface Config Dict: {display_surface_config}")
                        if display_surface_config["widget_string"] == "top_banner":
                            widget_config = display_surface_config["widget_config"]
                            image_id = widget_config.get("image_id")
                            image_id_list.append(image_id)

                    self.__update_image_files(image_id_list)
            else:
                self.logger.error(f"Server returned invalid status: {request_status}")

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
                command, arguments, data = tcp_client.tcp_send(self.server_ip_address, self.server_tcp_port, message)

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
        """Handles an incoming OSC command to change the state of an indicator light"""
        display_surface_id = args[0]
        state = args[1]
        print(f"Incoming Data: Indicator Display Surface ID:{display_surface_id}, State:{state}")

        #Check the surface id is valid
        if display_surface_id in self.indicator_surfaces_list:
            #Get the indicator widget
            indicator_widget : Indicator_Lamp = self.widget_dict.get(display_surface_id)
            if state == True:
                indicator_widget.trigger_indicator_on()
                print("Indicator On")
            elif state == False:
                indicator_widget.trigger_indicator_off()
                print("Indicator Off")
            else:
                self.logger.error(f"Error triggering signal light, invalid arguments {args}")

    def ticker_handler(self, address, *args):
        state = args[0]

        self.logger.debug(f"Incoming Data:{address}, {args}")
        ticker_widget : Ticker_Banner = self.widget_dict[-2]
        
        if state == True:
            text= args[1]
            bg_colour_hex = args[2]
            bg_colour_rgb = ImageColor.getcolor(bg_colour_hex, "RGB")

            self.logger.debug("Ticker On")
            ticker_widget.set_ticker_text(text, bg_colour_rgb)
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

            #Clear the current blit list except for the surface with id 3000 and 4000 these are the fullscreen logo and information slates
            for display_section_id in copy_of_blit_dict:
                if display_section_id != -2 and display_section_id != -3 and display_section_id != -4:
                    self.logger.debug(f"Clearing Display Section ID:{display_section_id} from blit dict.")
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

            self.logger.debug(f"Blit Dict: {self.blit_dict}")
            self.logger.debug(f"Widget Dict: {self.blit_dict}")

    def show_frame_handler(self, address, *args):
        self.logger.info(f"***************Raising Frame***************")
        if args[0] == "identify":
            self.show_frame(1)
        elif args[0] == "OATIS":
            self.show_frame(2)
        elif args[0] == "logo":
            self.show_frame(0)

    def alarm_indicator_on(self):
        for surface_id in self.clock_widget_surfaces_list:
            clock_widget : Clock = self.widget_dict[surface_id]
            clock_widget.alarm_indicator_flash_enable()

    def alarm_indicator_off(self):
        for surface_id in self.clock_widget_surfaces_list:
            clock_widget : Clock = self.widget_dict[surface_id]
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

        

        
        
