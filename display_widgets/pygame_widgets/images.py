import pygame
from os.path import join
from display_widgets.pygame_widgets.widget import Widget
from modules.pygame_functions import make_resized_image_object
from modules.common import open_json_file
from os import path

class Static_Image(Widget):
    """Creates a static image widget."""
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__()

        #Widget Config
        self.logger.info("Extracting Static Image Widget Config from widget_config_dict")
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

class Stacked_Image(Widget):
    """Creates a stacked image widget."""
    def __init__(self, parent_surface, widget_config_dict:dict):
        super().__init__()

        #Widget Config
        self.logger.info("Extracting Stacked Image Widget Config from widget_config_dict")
        self.image_stack_id = str(widget_config_dict["image_stack_id"])
        
        #self.image_filename = f"{self.image_id}.png"
        self.default_image_path = "client/data/defaults/default_logo.png"
        self.image_stacks_path = "client/data/image_stacks.json"
        self.image_base_path = "client/data/images"

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

        #Dict to hold native image surfaces
        self.native_image_surfaces_dict = {}

        #Blank list to hold image_ids associated with the image_stack
        self.image_ids_list = []

        #The currently active image - default is the OATIS Logo if no images in stack
        self.__active_image_id = -1

        self.logger.info("Building Stacked Image Widget")
        self.__load_images()

        self.logger.info("Adding draw_image function to render call.")
        self.add_function_to_render(self.draw_image)

    def change_image(self, image_id:int):
        """Changes the image show in an image stack."""
        try:
            if image_id in self.image_ids_list:
                self.logger.info(f"Changing Image Stack {self.image_stack_id}'s Image to Image ID:{image_id}.")
                self.__active_image_id = image_id

            else:
                self.logger.warning(f"Image ID:{image_id} does not exist, unable to change image stack image.")

        except Exception as e:
            self.logger.error(f"Unable to change image stack {self.image_stack_id}'s image. Reason:{e}")
            self.__active_image_id = -1
            
    def __load_images(self):
        #Open the image_stacks file
        image_stacks_dict : dict = open_json_file(self.image_stacks_path)
        self.logger.debug(f"Image Stacks Dict:{image_stacks_dict}")

        image_stack_id_dict : dict = image_stacks_dict.get("image_stack_id_dict")
        image_stack_config_dict : dict = image_stack_id_dict.get(self.image_stack_id)

        #Get the image ids list for the image_stack_id
        self.image_ids_list : list = image_stack_config_dict.get("image_ids_list")

        #Build an image object for default logo - this is shown if no images are found
        image_path = self.default_image_path
        image_native, image_native_rect = self.__build_image_object(image_path)
        self.native_image_surfaces_dict[-1] = [image_native, image_native_rect]

        #Build each image object and store in a dict
        for image_id in self.image_ids_list:
            image_filename = f"{image_id}.png"
            image_path = join(self.image_base_path, image_filename)
            image_native, image_native_rect = self.__build_image_object(image_path)
            self.native_image_surfaces_dict[image_id] = [image_native, image_native_rect]

        if self.image_ids_list != []:
            #Set the first image in the stack as default active
            self.__active_image_id = self.image_ids_list[0]

        else:
            #Show default logo image when no other images are found
            self.__active_image_id = -1

        self.logger.debug(f"Native Image Surfaces Dict:{self.native_image_surfaces_dict}")

    def __build_image_object(self, image_path):
        """Creates a pygame image object resizing to fit surface."""

        #Load the image from file
        try:
            image = pygame.image.load(join(image_path))
        except:
            image = pygame.image.load(join(self.default_image_path))

        #Resize the image to fit the surface dimensions with padding
        resized_image = make_resized_image_object(image, self.display_width, self.display_height, self.widget_xpad, self.widget_ypad)

        #Make a copy of the image in native surface pixel format for quicker load time
        image_native = resized_image.convert()

        #Create a Rectangle object to contain the image
        image_native_rect = image_native.get_rect()

        #Set the position of the center of the rectangle object
        image_native_rect.center = (self.display_width/2, self.display_height/2)

        return image_native, image_native_rect
    
    def draw_image(self):
        #Fill the screen with a color to wipe away anything from last frame
        self.display_surface.fill(self.bg_colour)

        #Copy the image surface object to the display surface object at the center coordinate.
        self.image_native = self.native_image_surfaces_dict.get(self.__active_image_id)[0]
        image_native_rect = self.native_image_surfaces_dict.get(self.__active_image_id)[1]
        self.display_surface.blit(self.image_native, image_native_rect)
