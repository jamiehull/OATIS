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
                text_size = int(text_size - 1)

        return label_text