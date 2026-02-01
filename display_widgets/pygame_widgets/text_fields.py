import pygame
from pygame.locals import *
from display_widgets.pygame_widgets.widget import Widget
from modules.pygame_functions import make_resized_text_object

class Title_Data(Widget):
    """Creates a single column containing a title and a data field with two text rows below."""
    def __init__(self, parent_surface, field_title:str, bg_colour:tuple):
        super.__init__()
        #Label Variables
        self.field_title = field_title
        self.resized_title : pygame.Surface
        self.field_data_ln1 = ""
        self.resized_field_data_ln1 : pygame.Surface
        self.field_data_ln2 = ""
        self.resized_field_data_ln2 : pygame.Surface

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black
        self.text_colour = (255, 255, 255) #White
        self.text_field_bg_colour = bg_colour

        #Get the resolution of the surface
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Text Field Display Area:{self.display_width},{self.display_height}")

        #Scale variables
        self.vertical_pad = self.display_height*0.03
        self.horizontal_pad = self.display_width*0.07
        self.text_x_pad = 15
        self.outline_width = self.display_width - (2 * self.horizontal_pad)
        self.outline_height = (self.display_height - (2 * self.vertical_pad))

        #Default Text Size and font
        self.title_text_size = int(self.outline_height * 0.2)
        self.data_text_size = int(self.title_text_size * 0.75)

        #Calculates the sizes of each indicators text label so it fits in the indicator and sotres the font object in a list
        self.__calculate_text_sizes()

        #Render
        self.add_function_to_render(self.draw_title_data_fields)

    def __calculate_text_sizes(self):
        """Make a font object for each label and resize the text to fit in the label, storing the font object in a list."""
        self.resized_title =  self.__resize_text(self.field_title, self.title_text_size)
        self.resized_field_data_ln1 = self.__resize_text(self.field_data_ln1, self.data_text_size)
        self.resized_field_data_ln2 = self.__resize_text(self.field_data_ln2, self.data_text_size)
            

    def __resize_text(self, text, text_size):
        """Resizes text to fit in an indicator and returns a pygame Font object."""
        
        while True:
            font = pygame.font.SysFont('arial', text_size)
            label_text = font.render(text, True, self.text_colour)
            label_text_width = label_text.get_width()
            if label_text_width >= (int(self.outline_width) - (2*self.text_x_pad)):
                self.logger.debug(f"Label Text width:{label_text_width}, diplay section width:{self.indicator_width}")
                text_size -= 1
            else:
                break

        return label_text
        
    def draw_title_data_fields(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Origin to start drawing from
        current_x_position = 0 + self.horizontal_pad
        current_y_position = 0 + self.vertical_pad

        #Make a rectangle object
        outline_rect = pygame.Rect((current_x_position, current_y_position),(self.outline_width, self.outline_height))
        pygame.draw.rect(self.display_surface, self.text_field_bg_colour, outline_rect, border_radius=15)

        #Origin to draw title text from
        current_x_position = 0 + self.horizontal_pad + self.text_x_pad
        current_y_position = 0 + self.vertical_pad

        #Title
        # create a text surface object and a rectangular object for the text surface object
        title_text_rect = self.resized_title.get_rect()
        #Set the position of the rectangular object.
        title_text_rect.topleft = (current_x_position, current_y_position)
        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.resized_title, title_text_rect)

        #Origin to draw data text from
        current_x_position = 0 + self.horizontal_pad + self.text_x_pad
        current_y_position = 0 + 2*self.vertical_pad + title_text_rect.height

        #Data
        # create a text surface object and a rectangular object for the text surface object
        data_text_rect_ln1 = self.resized_field_data_ln1.get_rect()
        #Set the position of the rectangular object.
        data_text_rect_ln1.topleft = (current_x_position, current_y_position)
        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.resized_field_data_ln1, data_text_rect_ln1)

        #Origin to draw data text from
        current_x_position = 0 + self.horizontal_pad + self.text_x_pad
        current_y_position = 0 + 3*self.vertical_pad + title_text_rect.height + data_text_rect_ln1.height

        # create a text surface object and a rectangular object for the text surface object
        data_text_rect_ln2 = self.resized_field_data_ln2.get_rect()
        #Set the position of the rectangular object.
        data_text_rect_ln2.topleft = (current_x_position, current_y_position)
        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.resized_field_data_ln2, data_text_rect_ln2)

    def set_field_data(self, data_string_ln1:str, data_string_ln2:str):
        """Sets the data field text."""
        #Set the data field text label
        self.field_data_ln1 = data_string_ln1
        self.field_data_ln2 = data_string_ln2
        #Re-calculate text sizes
        self.__calculate_text_sizes()

    def clear_field_data(self):
        #Set the data field text label
        self.field_data_ln1 = ""
        self.field_data_ln2 = ""
        #Re-calculate text sizes
        self.__calculate_text_sizes()

class Static_Text(Widget):
    """Creates a static text widget."""
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__()

        #Widget Config
        self.logger.info("Extracting Static Text Widget Config from widget_config_dict")
        self.label_text = widget_config_dict["label_text"]
        self.text_colour = widget_config_dict["text_colour"]
        self.text_size_mode = widget_config_dict["text_size_mode"]
        self.user_text_size = widget_config_dict["text_size"]
        self.logger.info("Done")

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black

        #Get the resolution of the surface
        self.logger.info("Getting resolution of surface")
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Static Text Display Surface Resolution:{self.display_width},{self.display_height}")

        #Widget padding
        self.widget_xpad = 0.1 * self.display_width
        self.widget_ypad = 0.1 * self.display_height

        #If user has set text size to auto, we set an initial text size
        self.logger.debug(f"Text size mode set to {self.text_size_mode}")
        if self.text_size_mode == "Auto":
            self.text_size = self.display_height

        #If the user has set a manual text size value, convert this to an int
        else:
            try:
                self.text_size = int(self.user_text_size)

            except Exception:
                self.logger.warning("Invalid manual text size provided, defaulting to autosize.")
                self.text_size = self.display_height
                self.text_size_mode = "Auto"

        self.logger.info("Building Text Widget")
        self.__build_text_object()

        self.logger.info("Adding draw_text function to render call.")
        self.add_function_to_render(self.draw_text)

    def __build_text_object(self):
        """Creates a pygame text object based on the text size / mode set and sets it's position."""
    
        #If user has chosen autofit
        if self.text_size_mode == "Auto":
            self.label_text = make_resized_text_object(self.label_text, self.text_colour, self.text_size, self.display_width, self.display_height, self.widget_xpad, self.widget_ypad)

        #If user has specified a custom size
        else:
            font = pygame.font.SysFont('arial', self.text_size)
            self.label_text = font.render(self.label_text, True, self.text_colour)

        #Get the text rectangle
        self.label_text_rect = self.label_text.get_rect()

        #Set the position of the rectangular object.
        self.label_text_rect.center = (self.display_width/2, self.display_height/2)

    
    def draw_text(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Copy the text surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.label_text, self.label_text_rect)
