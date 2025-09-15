from client.display_widgets.widget import Widget
import pygame
from pygame.locals import *
import os
from time import strftime

class Ticker_Banner(Widget):
    def __init__(self, parent_surface):
        super().__init__()

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.text_colour = (255, 255, 255) #White

        #Create a variable to store the ticker text
        self.ticker_text_str = ""

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        print(f"Ticker banner Display Area:{self.display_width},{self.display_height}")

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            smallest_dimension = self.display_width
        else:
            smallest_dimension = self.display_height

        #Text Size and font
        self.text_size = int(self.display_height*0.8)
        self.font = pygame.font.SysFont('arial', self.text_size)

        #Ticker Position Variables
        self.x_start = self.display_width
        self.x_end = 0
        self.x = self.x_start
        self.y=self.display_height/2

        #Variable to turn ticker on and off
        self.ticker_enabled = False

        #Add to render
        self.add_function_to_render(self.__scroll_ticker)
        
    def set_ticker_text(self, text):

        #Set the ticker text string
        self.ticker_text_str = text

        # create a text surface object and a rectangular object for the text surface object
        self.ticker_text = self.font.render(self.ticker_text_str, True, self.text_colour, self.bg_colour)
        self.ticker_text_width = self.ticker_text.get_width()

        #Set the position of the rectangular object.
        self.x_start = self.display_width + self.ticker_text_width/2
        self.x_end = -1*self.ticker_text_width/2
        self.x = self.x_start
        self.y=self.display_height/2

    def set_bg_colour(self, bg_colour_rgb):
        self.bg_colour = bg_colour_rgb

    def __scroll_ticker(self):
        if self.ticker_enabled == True:
            if self.x < self.x_end:
                self.x = self.x_start
            else:
                self.x -= 1
            #Fill the screen with a color to wipe away anything from last frame
            self.display_surface.fill(self.bg_colour)

            # create a text surface object and a rectangular object for the text surface object
            self.ticker_text = self.font.render(self.ticker_text_str, True, self.text_colour, self.bg_colour)
            self.ticker_text_rect = self.ticker_text.get_rect()

            #Set the position of the rectangular object.
            self.ticker_text_rect.center = (self.x, self.y)

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(self.ticker_text, self.ticker_text_rect)

        else:
            self.bg_colour = (0,0,0) #Black
            
    def ticker_on(self):
        self.ticker_enabled = True

    def ticker_off(self):
        self.ticker_enabled = False
        
class Logo_Date_Location_Top_Banner:
    def __init__(self, parent_surface):

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.text_colour = (255, 255, 255) #White

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        print(f"Logo_Date_Location banner Display Area:{self.display_width},{self.display_height}")

        #Work out which is the smallest dimension
        if self.display_width <= self.display_height:
            smallest_dimension = self.display_width
        else:
            smallest_dimension = self.display_height

        #Text Size and font
        self.text_size = int(self.display_height*0.4)
        self.font = pygame.font.SysFont('arial', self.text_size)

        #Create the background
        self.display_surface.fill(self.bg_colour)


        #Default Text and logo path
        self.default_logo_path = "client/data/default_logo.png"
        self.logo_path = "client/data/logo.png"
        self.location_str = "Location"

        #Set the logo image
        self.scaled_logo : pygame.Surface
        self.set_logo()

    #Update the Display
    def render(self):
        self.render_bg()
        self.render_date()
        self.__render_logo()
        self.render_location()


    def render_bg(self):
        self.display_surface.fill(self.bg_colour)

    def set_logo(self):
        
        #Load the image from file
        try:
            logo = pygame.image.load(os.path.join(self.logo_path))
        except:
            logo = pygame.image.load(os.path.join(self.default_logo_path))

        logo_original_width = logo.get_width()
        logo_original_height = logo.get_height()


        #Work out logo scaling
        logo_max_height = self.display_height/1.2
        logo_scale_factor = logo_original_height / logo_max_height
        logo_scaled_width = logo_original_width / logo_scale_factor
        logo_scaled_height = logo_original_height / logo_scale_factor

        #Scale the logo to fit
        self.scaled_logo = pygame.transform.scale(logo, (logo_scaled_width, logo_scaled_height))

    def __render_logo(self):
        #Make a copy of the image in native surface pixel format for quicker load time
        self.logo_native = self.scaled_logo.convert()

        #Create a Rectangle object to contain the logo
        self.logo_native_rect = self.logo_native.get_rect()
        #Set the position of the center of the rectangle object
        self.logo_native_rect.center = (self.display_width/2,self.display_height/2)
        #Copy the Logo image to the surface
        self.display_surface.blit(self.logo_native, self.logo_native_rect)
        

    def render_date(self):
        self.date_str = strftime('%a %d %b %Y')
        #self.year_str = strftime('%Y')

        # create a text surface object and a rectangular object for the text surface object
        self.date_text = self.font.render(self.date_str, True, self.text_colour, self.bg_colour)
        self.date_text_rect = self.date_text.get_rect()

        #Get the text width
        date_text_width = self.date_text.get_width()
        date_text_height = self.date_text.get_height()

        #Set the position of the rectangular object.
        self.date_text_rect.center = (date_text_width/2, date_text_height/2)

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.date_text, self.date_text_rect)

    def render_location(self):
        # create a text surface object and a rectangular object for the text surface object
        self.location_text = self.font.render(self.location_str, True, self.text_colour, self.bg_colour)
        self.location_text_rect = self.location_text.get_rect()

        #Get the text width
        location_text_width = self.location_text.get_width()
        location_text_height = self.location_text.get_height()

        #Set the position of the rectangular object.
        self.location_text_rect.center = (self.display_width-(location_text_width/2), location_text_height/2)

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.location_text, self.location_text_rect)

    def set_location(self, location_string):
        """Sets the location string variable."""
        self.location_str = location_string

        

        
        
        
