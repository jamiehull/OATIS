#Widget Superclass

class Widget:
    """Base Widget class containing functions common to all Widgets."""
    def __init__(self):

        #List of functions to call on render
        self.__render_list = []

    def add_function_to_render(self, function):
        """Adds a function to the render list"""
        self.__render_list.append(function)

    def render(self):
        """Calls all functions in the render list in order"""
        for render_function in self.__render_list:
            render_function()

    
