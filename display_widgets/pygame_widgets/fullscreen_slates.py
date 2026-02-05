from display_widgets.pygame_widgets.widget import Widget
import pygame
from pygame.locals import *
import os
from time import strftime

class Logo_Slate(Widget):
    """Creates a fullscreen slate with default Logo."""
    def __init__(self, parent_surface):
        super().__init__()
        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.transparent_colour = (0,0,0,0)
        self.text_colour = (255,255,255) #White

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Fullscreen Slate Display Area:{self.display_width},{self.display_height}")

        #Scale variables
        self.title_scale_factor = 6
        
        #Default Text Size and font
        self.title_text_size = int(self.display_height / self.title_scale_factor)
        self.title_font = pygame.font.SysFont('arial', self.title_text_size)
        self.default_text_size = int(self.display_height * 0.1)
        self.defualt_font = pygame.font.SysFont('arial', self.default_text_size)

        #Logo path
        self.logo_path = "client/data/defaults/default_logo.png"
        self.logo_string = "OATIS"

        #Open logo file and scale
        self.scaled_logo : pygame.Surface
        self.logo_file_ok = False
        self.__scale_logo()
        self.__convert_logo()

        #Variables to determine whether the slate is in vision
        self.active = False

        #Add to render
        self.add_function_to_render(self.__render_logo)
        
    def __scale_logo(self):
        #Load the image from file
        try:
            logo = pygame.image.load(os.path.join(self.logo_path))
            
            logo_original_width = logo.get_width()
            logo_original_height = logo.get_height()

            #Work out logo scaling
            logo_max_height = self.display_height / self.title_scale_factor
            logo_scale_factor = logo_original_height / logo_max_height
            logo_scaled_width = logo_original_width / logo_scale_factor
            logo_scaled_height = logo_original_height / logo_scale_factor

            #Scale the logo to fit
            self.scaled_logo = pygame.transform.scale(logo, (logo_scaled_width, logo_scaled_height))

            self.logo_file_ok = True

        except:
            self.logo_file_ok = False

    def __convert_logo(self):
        """Converts the logo image file and works out it's position, defaults to text if logo file not found"""
        if self.logo_file_ok == True:
            #Make a copy of the image in native surface pixel format for quicker load time
            self.logo = self.scaled_logo.convert()

            #Create a Rectangle object to contain the logo
            self.logo_rect = self.logo.get_rect()

            #Set the position of the center of the rectangle object
            self.logo_rect.center = (self.display_width/2,self.display_height/2)

        else:
            # create a text surface object and a rectangular object for the text surface object
            self.logo = self.title_font.render(self.logo_string, True, self.text_colour, self.bg_colour)
            self.logo_rect = self.logo.get_rect()

            #Set the position of the rectangular object.
            self.logo_rect.center = (self.display_width/2,self.display_height/2)

    def __render_logo(self):
        if self.active == True:
            self.display_surface.fill(self.bg_colour)

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(self.logo, self.logo_rect)

        else:
            self.display_surface.fill(self.transparent_colour)

    def make_visible(self):
        self.active = True

    def hide(self):
        self.active = False

class Identify_Slate(Widget):
    """Creates a fullscreen slate with top banner and device information."""
    def __init__(self, parent_surface):
        super().__init__()
        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.text_box_colour = (68, 68, 68) #Dark Grey
        self.transparent_colour = (0,0,0,0)
        self.text_colour = (255,255,255) #White

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Fullscreen Slate Display Area:{self.display_width},{self.display_height}")

        #Scale variables
        self.title_scale_factor = 6
        self.banner_scale_factor= 0.1
        self.info_scale_factor = 0.9
        
        #Default Text Size and font
        self.title_text_size = int(self.display_height / self.title_scale_factor)
        self.title_font = pygame.font.SysFont('arial', self.title_text_size)
        self.default_text_size = int(self.display_height * 0.05)
        self.default_font = pygame.font.SysFont('arial', self.default_text_size)

        #Top Banner Text Size and font
        self.banner_text_size = int((self.display_height*self.banner_scale_factor)*0.4)
        self.banner_font = pygame.font.SysFont('arial', self.banner_text_size)

        #Currently rendered date string
        self.current_date_str = ""

        #Variables to determine whether the slate is in vision
        self.active = False

        #Add to render
        self.add_function_to_render(self.render)

        #Device Information Variables
        self.device_name = ""
        self.device_ip = ""
        self.device_location = ""
        self.message_group = ""
        self.display_instance = ""

        #Device Information Titles
        self.device_info_titles_list = ["Device Name:",
                                        "Device IP:",
                                        "Device Location:",
                                        "Messaging Group:",
                                        "Display Instance:"]
        
        #Default data list - used when the device config cannot be retrieved
        self.device_info_data_list = [None, None, None, None, None, None]

        #Default Text and logo path
        self.default_logo_path = "client/data/defaults/default_logo.png"
        self.location_str = "Location"

        #Set the logo image
        self.scaled_logo : pygame.Surface
        self.set_logo()

        #Set the location
        self.set_location(self.location_str)
    
    def render(self):
        if self.active == True:
            self.__render_device_information()
            self.__render_date()
            self.__render_logo()
            self.render_location()
        else:
            #Surface hidden when not active
            self.display_surface.fill(self.transparent_colour)

    def __render_device_information(self):
            self.display_surface.fill(self.bg_colour)

            pad = 20
            x_origin = 0 + pad
            y_origin = (self.display_height*self.banner_scale_factor) + pad

            data_index = 0
            for title in self.device_info_titles_list:

                # create a text surface object and a rectangular object for the text surface object
                data = self.device_info_data_list[data_index]
                self.label_text = self.default_font.render(f"{title} {data}", True, self.text_colour, self.text_box_colour)
                self.label_text_rect = self.label_text.get_rect()

                #Get the text width
                label_text_width = self.label_text.get_width()
                label_text_height = self.label_text.get_height()

                #Set the position of the rectangular object.
                self.label_text_rect.topleft = (x_origin + pad, (y_origin + pad/2))

                #Make a rectangle object
                indicator_rect = pygame.Rect((x_origin, y_origin),((self.display_width - (2*pad)), (label_text_height + pad)))
                pygame.draw.rect(self.display_surface, self.text_box_colour, indicator_rect, border_radius=15)  

                #Copy the text surface object to the display surface object at the center coordinate.
                self.display_surface.blit(self.label_text, self.label_text_rect)

                y_origin += label_text_height + 2*pad
                data_index += 1
 
    def set_information(self, information_dict:dict):
        self.device_name = information_dict["device_name"]
        self.device_ip = information_dict["device_ip"]
        self.device_location = information_dict["device_location"]
        self.set_location(self.device_location)
        self.message_group = information_dict["message_group"]
        self.display_instance = information_dict["display_instance"]
        self.device_info_data_list = [self.device_name,
                                      self.device_ip,
                                      self.device_location,
                                      self.message_group,
                                      self.display_instance]

    def set_logo(self):
        
        #Load the image from file
        logo = pygame.image.load(os.path.join(self.default_logo_path))

        logo_original_width = logo.get_width()
        logo_original_height = logo.get_height()


        #Work out logo scaling
        logo_max_height = (self.display_height*self.banner_scale_factor)
        logo_scale_factor = logo_original_height / logo_max_height
        logo_scaled_width = logo_original_width / logo_scale_factor
        logo_scaled_height = logo_original_height / logo_scale_factor

        #Scale the logo to fit
        self.scaled_logo = pygame.transform.scale(logo, (logo_scaled_width, logo_scaled_height))

        #Make a copy of the image in native surface pixel format for quicker load time
        self.logo_native = self.scaled_logo.convert()

        #Create a Rectangle object to contain the logo
        self.logo_native_rect = self.logo_native.get_rect()
        #Set the position of the center of the rectangle object
        self.logo_native_rect.center = (self.display_width/2, (self.display_height*self.banner_scale_factor)/2)

    def __render_logo(self):
        #Copy the Logo image to the surface
        self.display_surface.blit(self.logo_native, self.logo_native_rect)

    def __set_date(self):
        # create a text surface object and a rectangular object for the text surface object
        self.date_text = self.banner_font.render(self.current_date_str, True, self.text_colour, self.bg_colour)
        self.date_text_rect = self.date_text.get_rect()

        #Get the text width
        date_text_width = self.date_text.get_width()
        date_text_height = self.date_text.get_height()

        #Set the position of the rectangular object.
        self.date_text_rect.center = (date_text_width/2, date_text_height/2)
        
    def __render_date(self):
        date_str = strftime('%a %d %b %Y')
        if self.current_date_str != date_str:
            self.current_date_str = date_str
            self.__set_date()

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.date_text, self.date_text_rect)

    def set_location(self, location_string):
        """Sets the location string variable."""
        self.location_str = location_string

        # create a text surface object and a rectangular object for the text surface object
        self.location_text = self.banner_font.render(self.location_str, True, self.text_colour, self.bg_colour)
        self.location_text_rect = self.location_text.get_rect()

        #Get the text width
        location_text_width = self.location_text.get_width()
        location_text_height = self.location_text.get_height()

        #Set the position of the rectangular object.
        self.location_text_rect.center = (self.display_width-(location_text_width/2), location_text_height/2)

    def render_location(self):
        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.location_text, self.location_text_rect)

    def make_visible(self):
        self.active = True

    def hide(self):
        self.active = False
    