import pygame


def make_resized_text_object(text, text_colour, initial_text_size, max_width, max_height, x_pad=0, y_pad=0) -> pygame.Surface:
        """Resizes text to fit in a specified width and height, with specifed x and y padding. Returns a pygame text surface object."""
        
        text_size = initial_text_size
        text_fits_bounds = False
        
        while text_fits_bounds == False:
            #Make the text
            font = pygame.font.SysFont('arial', text_size)
            label_text = font.render(text, True, text_colour)

            #Find text width and height
            label_text_width = label_text.get_width()
            label_text_height = label_text.get_height()

            #Does it fit the specified bounds with top / bottom and left / right padding?
            if (label_text_width <= (int(max_width) - (2*x_pad))) and (label_text_height <= (int(max_height) - (2*y_pad))):
                text_fits_bounds = True
            
            #If it doesn't reduce the size and try again
            else:
                print(f"Label Text width:{label_text_width}, display section width:{max_width}")
                text_size = int(text_size - 1)

        return label_text

def make_resized_image_object(image:pygame.Surface, max_width, max_height, x_pad=0, y_pad=0) -> pygame.Surface:
        """Resizes image to fit in a specified width and height preserving aspect ratio, with specifed x and y padding. Returns a pygame text surface object."""
        
        #Get original image dimensions
        original_image_width = image.get_width()
        original_image_height = image.get_height()
        print(f"Original Dimensions - Width:{original_image_width}, Height: {original_image_height}")

        print(f"Target Dimensions - Width:{max_width}, Height: {max_height}")

        #Work out what scale factor each dimension needs to be multiplied by to fit
        width_scale_factor = (max_width - (2 * x_pad)) / original_image_width
        height_scale_factor = (max_height - (2 * y_pad)) / original_image_height
        print(f"Scale Factors - Width SF:{width_scale_factor}, Height SF:{height_scale_factor}")
        
        #Determine which SF is smaller and set this as the master_sf
        if width_scale_factor <= height_scale_factor:
            master_scale_factor = width_scale_factor
        else:
            master_scale_factor = height_scale_factor

        #Work out new image dimensions
        resized_image_width = original_image_width * master_scale_factor
        resized_image_height = original_image_height * master_scale_factor
        print(f"Resized Dimensions - Width:{resized_image_width}, Height: {resized_image_height}")

        #Apply the transform to the image
        resized_image = pygame.transform.scale(image, (resized_image_width, resized_image_height))

        return resized_image