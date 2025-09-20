import pygame
from pygame.locals import *
from client.display_widgets.widget import Widget

class Indicator_Lamps_Vertical(Widget):
    """Creates a single column of indicator lamps."""
    def __init__(self, parent_surface, number_of_indicators:int, indicator_label_list:list, indicator_on_rgb_colour_list:list, indicator_flash_list:list):
        super().__init__()
        #Label Variables
        self.number_of_indicators = number_of_indicators
        self.indicator_label_list = indicator_label_list
        self.resized_indicator_label_list = []

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.text_colour = (0, 0, 0) #Black
        self.indicator_off_colour = (123, 122, 122) #Grey
        self.indicator_on_rgb_colour_list = indicator_on_rgb_colour_list
        self.indicator_current_colour_list = []
        for i in range(number_of_indicators):
            self.indicator_current_colour_list.append(self.indicator_off_colour)

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        print(f"Indicators Display Area:{self.display_width},{self.display_height}")

        #Scale variables
        self.vertical_pad = self.display_height*0.03/(number_of_indicators*0.1)
        self.horizontal_pad = self.display_width*0.07
        self.indicator_text_x_pad = 15
        self.indicator_width = self.display_width - (2 * self.horizontal_pad)
        self.indicator_height = (self.display_height - ((self.number_of_indicators +1) * self.vertical_pad)) / self.number_of_indicators

        #Default Text Size and font
        self.text_size = int(self.indicator_height * 0.8)
        self.font = pygame.font.SysFont('arial', self.text_size)
        self.text_size_list = []

        #List of indicators with flash enabled
        self.flash_enabled_list = indicator_flash_list

        #Flash Frequency
        self.flash_period = 1000 #Time between flashes in ms
        self.flashing_list = [] #List of label indexes currently flashing
        self.change_time = 0 #Time for next flash in ms

        #Calculates teh sizes of each indicators text label so it fits in the indicator and sotres the font object in a list
        self.__calculate_text_sizes()

        self.add_function_to_render(self.__flash)
        self.add_function_to_render(self.draw_indicators)

    def __calculate_text_sizes(self):
        """Make a font object for each label and resize the text to fit in the label, storing the font object in a list."""
        for text_string in self.indicator_label_list:
            resized_string =  self.__resize_text(text_string)
            self.resized_indicator_label_list.append(resized_string)

    def __resize_text(self, text):
        """Resizes text to fit in an indicator and returns a pygame Font object."""
        text_size = self.text_size
        
        while True:
            font = pygame.font.SysFont('arial', text_size)
            label_text = font.render(text, True, self.text_colour)
            label_text_width = label_text.get_width()
            if label_text_width >= (int(self.indicator_width) - self.indicator_text_x_pad):
                print(f"Label Text width:{label_text_width}, indicator width:{self.indicator_width}")
                text_size -= 1
            else:
                break

        return label_text
        
    def draw_indicators(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Origin to start drawing indicators from
        current_x_position = 0 + self.horizontal_pad
        current_y_position = 0 + self.vertical_pad

        #Iterator variable
        i=0

        #Draw each indicator
        for label_text in self.resized_indicator_label_list:
            label_text : pygame.Surface

            self.indicator_current_colour = self.indicator_current_colour_list[i]
            
            #Make a rectangle object
            indicator_rect = pygame.Rect((current_x_position, current_y_position),(self.indicator_width, self.indicator_height))
            pygame.draw.rect(self.display_surface, self.indicator_current_colour, indicator_rect, border_radius=15)

            # create a text surface object and a rectangular object for the text surface object
            label_text_rect = label_text.get_rect()

            #Set the position of the rectangular object.
            label_text_rect.center = (current_x_position + (self.indicator_width/2), current_y_position + (self.indicator_height/2))

            #Copy the text surface object to the display surface object at the center coordinate.
            self.display_surface.blit(label_text, label_text_rect)

            #Update position and iterator variable
            current_y_position += self.indicator_height + self.vertical_pad
            i += 1

    def __flash(self):
        """Flashes an indicator given it's index, starting at 0, top down."""

        #Get the current time in ms
        current_time = pygame.time.get_ticks()

        #If the current time is greater than the next change time and the indicator is in the flashing list
        #flash the indicator
        if current_time >= self.change_time:
            for indicator_number in self.flashing_list:
                #Indicator on
                if self.indicator_current_colour_list[indicator_number] == self.indicator_off_colour:
                    self.indicator_current_colour_list[indicator_number] = self.indicator_on_rgb_colour_list[indicator_number]

                #Indicator Off
                else:
                    self.indicator_current_colour_list[indicator_number] = self.indicator_off_colour

                self.change_time = current_time + self.flash_period

    def __indicator_flash_enable(self, indicator_index_list:list):
        """Makes an indicator Flash."""
        for indicator_index in indicator_index_list:

            if indicator_index not in self.flashing_list:
                self.flashing_list.append(indicator_index)

    def __indicator_flash_disable(self, indicator_index_list:list):
        """Turns flashing off for specified indicators."""
        for indicator_index in indicator_index_list:

            if indicator_index in self.flashing_list:
                self.flashing_list.remove(indicator_index)

    def __indicator_on(self, indicator_index_list:list):
        """Turns an indicator on."""
        for indicator_index in indicator_index_list:

            print(f"Turning indicator {indicator_index} on")

            self.indicator_current_colour_list[indicator_index] = self.indicator_on_rgb_colour_list[indicator_index]
            print(f"Current colour:{self.indicator_current_colour_list[indicator_index]}")

    def __indicator_off(self, indicator_index_list:list):
        """Turns an indicator off."""
        for indicator_index in indicator_index_list:

            print(f"Turning indicator {indicator_index} off")
            
            self.indicator_current_colour_list[indicator_index] = self.indicator_off_colour
            print(f"Current colour:{self.indicator_current_colour_list[indicator_index]}")

    def trigger_indicator_on(self, indicator_index_list:list):
        """Triggers an indicator on, triggers either a steady on or flash depending on display template config."""
        for indicator_index in indicator_index_list:
            if indicator_index in range (0, self.number_of_indicators):
                if self.flash_enabled_list[indicator_index] == "True":
                    self.__indicator_flash_enable(indicator_index_list)
                else:
                    self.__indicator_on(indicator_index_list)

    def trigger_indicator_off(self, indicator_index_list:list):
        """Turns an indicator off."""
        for indicator_index in indicator_index_list:
            if indicator_index in range (0, self.number_of_indicators):
                if self.flash_enabled_list[indicator_index] == "True":
                    self.__indicator_flash_disable(indicator_index_list)
                else:
                    self.__indicator_off(indicator_index_list)





            

        

        