from tkinter import messagebox
import logging

class Message_Boxes:

    def delete_warning(exception):
        messagebox.showwarning("Warning", f"Cannot delete this item as it is in use. \nTechnical info:{exception}")
    
    def invalid_image_warning(exception):
        messagebox.showwarning("Warning", f"Cannot Open Specified Image. \nTechnical info:{exception}")

    def confirm_delete() -> bool: 
        logger = logging.getLogger(__name__)

        choice = messagebox.askyesno("Confirm Delete", "Are you sure you're sure you want to delete this and that your sure?")
        
        if choice == True:
            logger.debug("User Confirmed Delete")
        if choice == False:
            logger.debug("User Aborted Delete")
        
        return choice

    