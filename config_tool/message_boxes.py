from tkinter import messagebox
import logging

def delete_warning(exception):
    messagebox.showwarning("Warning", f"Cannot delete this item as it is in use.")

def pin_modify_warning(failed_pin_list:list):
    messagebox.showwarning("Warning", f"Cannot modify input / output configuration for pins. \nThe following pins are configured as either an input or output trigger: {failed_pin_list}")

def invalid_image_warning(exception):
    messagebox.showwarning("Warning", f"Cannot Open Specified Image. \nTechnical info:{exception}")

def invalid_data_warning():
    messagebox.showwarning("Warning", f"Cannot Save Input Data. Invalid data Input.")

def image_unchanged_warning():
    messagebox.showwarning("Warning", f"Save Image to Database Aborted, No New Image Selected.")

def invalid_layout_matrix_warning():
    messagebox.showwarning("Warning", f"Unable to build layout, each group of surface ID's must make a rectangle and cannot be repeated in seperate rectangles. Every section must also be assigned an ID.")

def cannot_modify_warning(exception):
    messagebox.showwarning("Warning", f"Unable to modify selected entry: {exception}")

def initialised_program_exiting_message():
    messagebox.showinfo("Info", f"Database initialised, please restart config tool. This program will automatically exit on close of this message.")

def unknown_error_message(error=None):
    messagebox.showerror("Unknown Error", "An unexpected error has occured." ,detail = error)

def connection_refused_warning():
    messagebox.showwarning("Server Offline", "Config Tool cannot contact the server. \nPlease check it is running and the IP address has been set correctly.")


def confirm_delete() -> bool: 
    logger = logging.getLogger(__name__)

    choice = messagebox.askyesno("Confirm Delete", "Are you sure you're sure you want to delete this and that your sure?")
    
    if choice == True:
        logger.debug("User Confirmed Delete")
    if choice == False:
        logger.debug("User Aborted Delete")
    
    return choice

    