import pygame
from os.path import join
from display_widgets.pygame_widgets.widget import Widget
from modules.pygame_functions import make_resized_image_object

class Static_Image(Widget):
    """Creates a static image widget."""
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__()

        #Widget Config
        self.logger.info("Extracting Static Text Widget Config from widget_config_dict")
        self.image_id = widget_config_dict["image_id"]
        self.image_filename = f"{self.image_id}.png"
        self.default_image_path = "client/data/defaults/default_logo.png"
        self.image_path = join("client/data/images", self.image_filename)
        self.widget_xpad = 50
        self.widget_ypad = 50
        self.logger.info("Done")

        #Store reference to the surface
        self.display_surface :pygame.Surface = parent_surface

        #Display Colours
        self.bg_colour = (0,0,0) #Black

        #Get the resolution of the surface
        self.logger.info("Getting resolution of surface")
        self.display_width = self.display_surface.get_width()
        self.display_height = self.display_surface.get_height()
        self.logger.debug(f"Static Image Display Surface Resolution:{self.display_width},{self.display_height}")

        self.logger.info("Building Image Widget")
        self.__build_image_object()

        self.logger.info("Adding draw_image function to render call.")
        self.add_function_to_render(self.draw_image)

    def __build_image_object(self):
        """Creates a pygame image object resizing to fit surface."""

        #Load the image from file
        try:
            image = pygame.image.load(join(self.image_path))
        except:
            image = pygame.image.load(join(self.default_image_path))

        #Resize the image to fit the surface dimensions with padding
        resized_image = make_resized_image_object(image, self.display_width, self.display_height, self.widget_xpad, self.widget_ypad)

        #Make a copy of the image in native surface pixel format for quicker load time
        self.image_native = resized_image.convert()

        #Create a Rectangle object to contain the image
        self.image_native_rect = self.image_native.get_rect()

        #Set the position of the center of the rectangle object
        self.image_native_rect.center = (self.display_width/2, self.display_height/2)
    
    def draw_image(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Copy the image surface object to the display surface object at the center coordinate.
        self.display_surface.blit(self.image_native, self.image_native_rect)
