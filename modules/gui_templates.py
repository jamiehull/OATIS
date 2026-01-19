from config_tool.message_boxes import *
from modules.common import *
from modules.matrix_operations import *
from modules.custom_dataclasses import *
from config_tool.global_variables import *
import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser
from tkinter import StringVar
from tkinter import filedialog
from tkinter import ttk
from PIL import Image
import logging



#-------------------------Generic-Widgets-------------------------
class Title_Entry(ctk.CTkFrame):
     def __init__(self, parent, title, entry_width=140):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=1, uniform="row")
     
          self.columnconfigure(0, weight=1)
          self.columnconfigure(1, weight=0)

          #String Variables
          self.title = title
          self.entry_value = StringVar()

          #Add the title widget
          title = ctk.CTkLabel(master=self, text=self.title, font=self.default_font, anchor="w")
          title.grid(column=0, row=0, sticky="ew", padx=10, pady=10)

          self.input_widget = ctk.CTkEntry(master=self, textvariable=self.entry_value, font=self.default_font, justify="left", width=entry_width)
          self.input_widget.grid(column=1, row=0, sticky="ew", padx=10, pady=10)

     def get_value(self):
          return self.entry_value.get()
     
     def set_value(self, value:str):
          self.entry_value.set(value)

     def disable_entry(self):
          self.input_widget.configure(state="disabled")

     def enable_entry(self):
          self.input_widget.configure(state="normal")
     
class Title_Combobox(ctk.CTkFrame):
     def __init__(self, parent, title, values_list:list, callback=None, combobox_width=140):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=1, uniform="row")
     
          self.columnconfigure(0, weight=1)
          self.columnconfigure(1, weight=0)

          #String Variables
          self.title = title
          self.entry_value = StringVar()
          self.values_list = values_list

          #Add the title widget
          title = ctk.CTkLabel(master=self, text=self.title, font=self.default_font, anchor="w")
          title.grid(column=0, row=0, sticky="ew", padx=10, pady=10)

          self.combobox = ctk.CTkComboBox(master=self, values=self.values_list, variable=self.entry_value, state="readonly", font=self.default_font, justify="left", width=combobox_width)
          self.combobox.grid(column=1, row=0, sticky="ew", padx=10, pady=10)

          #Callback
          self.callback = callback

          if self.callback != None:
               self.__set_callback()

     def __set_callback(self):
          """Sets the combobox command."""
          self.combobox.configure(command=self.callback)

     def get_value(self):
          return self.entry_value.get()
     
     def set_value(self, value:str):
          self.entry_value.set(value)

     def set_values(self, values_list:list):
          self.combobox.configure(values=values_list)

     def disable_combobox(self):
          self.combobox.configure(state="disabled")

     def enable_combobox(self):
          self.combobox.configure(state="readonly")

class Title_Colour_Picker(ctk.CTkFrame):
     def __init__(self, parent, title):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=1, uniform="row")
     
          self.columnconfigure(0, weight=1)
          self.columnconfigure(1, weight=0)

          #String Variables
          self.title = title
          self.colour = ctk.StringVar()

          #Make the widgets
          self.title_label = ctk.CTkLabel(master=self, text=self.title, font=self.default_font, anchor="w")
          self.title_label.grid(column=0, row=0, sticky="ew", padx=10, pady=10)

          self.colour_btn = ctk.CTkButton(master=self, text="Click to Choose a colour", command=self.choose_colour, width=350, font=self.default_font)
          self.colour_btn.grid(column=1, row=0, sticky="ew", padx=10, pady=10)

     def choose_colour(self):
          #Generate a colour picker window returning the hex value of the colour picked
          rdg, hex_colour = colorchooser.askcolor(title="Pick an Indicator Colour", )
          if hex_colour != None:
               self.colour_btn.configure(text=hex_colour, fg_color=hex_colour)
               self.colour.set(hex_colour)
               self.update()
          #BugFix - Move focus from button to another widget to avoid it latching and force the colour to update
          self.title_label.focus_set()

     def get_value(self):
          return self.colour.get()
     
     def set_value(self, hex_colour:str):
          self.colour_btn.configure(text=hex_colour, fg_color=hex_colour)
          self.colour.set(hex_colour)
          self.update()

#Generates a frame containing widgets allowing a user to add a new image to the database
class ImagePicker(ctk.CTkFrame):
     """Creates a frame with widgets to select and preview an image."""
     def __init__(self, parent):
          super().__init__(parent)
          self.parent = parent

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Variables
          self.logo_path_var = StringVar()

          #Setup columns / rows for the frame
          self.columnconfigure(0, weight=0, pad=20)
          self.columnconfigure(1, weight=1, pad=20)

          self.rowconfigure(0, weight=0, pad=25)
          self.rowconfigure(1, weight=0, pad=10)
          self.rowconfigure(2, weight=0, pad=10)

          self.logo_label_width = 540
          self.logo_label_height = 360

          self.logo_preview_label = ctk.CTkLabel(master=self, text="", font=self.default_font, width=self.logo_label_width, height=self.logo_label_height, bg_color="grey")
          self.logo_preview_label.grid(column=0, row=0, rowspan =1, columnspan =2, sticky="", padx=20, pady=20)

          self.logo_picker_btn = ctk.CTkButton(master=self, text="Select an Image File", font=self.default_font, command=self.select_logo)
          self.logo_picker_btn.grid(column=0, row=1, columnspan =2, sticky="n")

          self.path_data = ctk.CTkLabel(master=self, text="", textvariable=self.logo_path_var, font=self.default_font)
          self.path_data.grid(column=0, row=2, columnspan =2, sticky="n")

     #Generates a file dialog to select an image from the local machine and updates the preview     
     def select_logo(self):
          """Opens a Dialog box for selecting an image."""
          try:
               path = filedialog.askopenfilename()
               print(f"Image file selected to upload to database:{path}")
               image = Image.open(path)
               print(f"Width:{image.width}")
               print(f"Height:{image.height}")

               #Resize the image to fit into preview window
               resized_image: Image.Image = resize_image_keep_aspect(image, self.logo_label_width, self.logo_label_height)

               logo_file = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width,resized_image.height))
               self.__update_image_preview(logo_file, path)
               
          except Exception as e:
               invalid_image_warning(e)

     #Updates the image preview
     def __update_image_preview(self, img, path="Stored in Database"):
          """Updates image preview and path."""
          self.logo_preview_label.configure(image=img, compound="left")
          self.logo_path_var.set(path)

     def set_image(self, blob_image):
          """Converts blob image, resizes and updates the preview window."""
          temp_image_path = "config_tool/temp.png"
          image = convert_from_blob(blob_image, temp_image_path)
          image = Image.open(temp_image_path)
          print(f"Width:{image.width}")
          print(f"Height:{image.height}")

          #Resize the image to fit into preview window
          resized_image: Image.Image = resize_image_keep_aspect(image, self.logo_label_width, self.logo_label_height)

          logo_file = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width,resized_image.height))
          self.__update_image_preview(logo_file)

     #Clears the image preview
     def clear_image_preview(self):
          """Clears the preview window and path."""
          self.logo_preview_label.configure(image=None)
          self.logo_path_var.set("")

     #Gets the path of the current preview image
     def get_data(self):
          """Returns the current image path."""
          return self.logo_path_var.get()

#Creates a custom 2 column treeview widget with methods for manipulating the widget
class CustomTree(ttk.Treeview):
     def __init__(self, parent):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Store a reference to the parent
          self.parent = parent

          #Show the treeview headings
          self['show'] = 'headings'

          #Setup the Treeviewer columns
          self.configure(columns=("ID", "Name"))

          #Column 1
          self.column("ID", width=50, anchor="center", stretch=False)
          self.heading("ID", text="ID")

          #Column 2
          self.heading("Name", text="Name")
          self.column("Name", anchor="center", stretch=True)

     def get_tree(self):
        """Returns the Treeviever widget"""
        return self
    
     def __add_items(self, updated_rows:list):
          """Add items to the treeviewer widget, takes a list as an input containing:
      [(id, name)...] """
          #Add each item to the tree
          for item in updated_rows:
               id = item[0]
               name = item[1]
               self.insert("", tk.END, values=(id,name))

          self.logger.info("Tree Updated")
     
     def __add_item(self, id, name):
          """Add a single item to the tree."""
          self.insert("", tk.END, values=(id,name))
          self.logger.info("Tree Updated")
     
     def __clear_tree(self):
          """Clear all items from the treeview widget."""
          #Delete all current data in the tree by detecting current children.
          for row in self.get_children():
               self.delete(row)
               self.logger.debug(f"Deleted {row} from the tree")
          self.logger.info("Cleared tree")
          
     def __get_selected_items_id(self):
          """Returns a list of tree ID's currently in focus"""
          #get the item in focus
          selected = self.selection()
          self.logger.debug(f"Selected Items: {selected}")
          return selected
          
     def __get_item(self, tree_id):
          """Returns the row at a specified tree id"""
          item = self.item(tree_id)["values"]
          id = item[0]
          name=item[1]
          return id, name
     
     def get_in_focus_item_db_id(self) -> str:
          """Returns the database id of the selected treeview item.
          Returns None if no item is in focus."""

          #Get the tree item id of the currently selected item
          selected_item_id_tuple :tuple = self.__get_selected_items_id()

          if selected_item_id_tuple != ():
               
               #Select the first selected item
               selected_item_id = selected_item_id_tuple[0]

               #Convert the tree id to database id
               database_id_list = self.__convert_tree_ids_to_database_ids([selected_item_id])
               database_id = database_id_list[0]
          
          else:
               self.logger.warning("No item selected in treeviever")
               database_id = None

          return database_id


     
     def __get_treeview_item_id(self, database_id):
          """Return the treeviewer id of an item given it's database id."""
          #Get a list of all tree items by treeview id
          treeviewer_ids = self.get_children()
          treeviewer_id = ""

          #Get the message group ID / name for each item and add to a list
          for tree_id in treeviewer_ids:
               id, name = self.__get_item(tree_id)
               if id == database_id:
                    treeviewer_id = tree_id
          
          if treeviewer_id == "":
               self.logger.warning(f"Database ID: {database_id}, not found in treeviewer.")

          return treeviewer_id
               
     def __convert_tree_ids_to_database_ids(self, tree_ids_list:list):
          """Converts a list of tree ID's to database ID's"""
          database_ids = []
          for tree_id in tree_ids_list:
               id, name = self.__get_item(tree_id)
               database_ids.append(id)

          return database_ids
          
     def update_tree(self, new_tree_data_list:list):
          """Adds new items to the tree without loosing focus of the currently selected item.
          Takes an input list of new rows in the format: [(id,name), (id,name)....]"""

          self.logger.info(f"#######---Updating Tree Viewer---#######")
          self.logger.debug(f"New tree rows:{new_tree_data_list}")

          #Keep a record of the currently selected (in focus items)
          selected_tree_ids = self.__get_selected_items_id()

          #Convert the selected tree ID's to database ID's
          in_focus_database_ids = self.__convert_tree_ids_to_database_ids(selected_tree_ids)

          #Clear the Tree
          self.__clear_tree()

          #Add the new tree data list to the treeviewer widget
          self.__add_items(new_tree_data_list)

          #Re-focus the previously selected items
          self.__focus_items(in_focus_database_ids)

          self.logger.info("Treeview Updated.")
          
     def __remove_item(self, selected_item):
          """Remove a single item from the treeview widget."""
          self.delete(selected_item)
          self.logger.info("Tree Updated")

     def focus_all_items(self):
          """Focuses all rows in the treeview widget."""

          self.logger.debug("Focusing all items")

          #Get a list of all tree_ids currently in the treeview widget
          items_list = self.get_children()

          self.logger.debug(f"Item to focus: {items_list}")

          #Select all the tree_ids in the treeview widget
          self.selection_add(items_list)

     def __focus_items(self, database_ids_list):
          """Focus a number of specified treeviewer rows."""

          selected_tree_ids_list = []

          for database_id in database_ids_list:
               #Get the tree_id of each item given it's database id
               tree_id = self.__get_treeview_item_id(database_id)
               if tree_id != "":
                    selected_tree_ids_list.append(tree_id)
          #Select each item
          self.selection_add(selected_tree_ids_list)

#Creates a treview selection column with title and bottom button
class Selection_Column(ctk.CTkFrame):
     def __init__(self, parent, top_button_text, bottom_button_text, font, bottom_button_cmd):
        super().__init__(parent)

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0, pad=10)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)

        #self.configure(fg_color="#494949")

        self.top_button = ctk.CTkLabel(self, text=top_button_text, font=font, fg_color="#656565")
        self.top_button.grid(column=0, row=0, sticky="nsew")

        self.treeviewer = ttk.Treeview(self, style='Treeview')
        self.treeviewer['show'] = 'headings'
        self.treeviewer.configure(columns=("ID", "Name"))
        self.treeviewer.column("ID", width=50, anchor="center", stretch=False)
        self.treeviewer.heading("ID", text="ID")
        self.treeviewer.heading("Name", text="Name")

        self.treeviewer.column("Name", anchor="center", stretch=True)
        self.treeviewer.grid(column=0, row=1, sticky="nsew")

        self.bottom_button = ctk.CTkButton(self, text=bottom_button_text, font=font, command=bottom_button_cmd)
        self.bottom_button.grid(column=0, row=2, sticky="nsew")

     def get_tree(self):
        return self.treeviewer
    
     def __add_items(self, updated_rows:list):
        """Adds rows to the tree.
        Accepts a list in format [[id,name],...]"""
        #Add each item to the tree
        for item in updated_rows:
            id = item[0]
            name = item[1]
            self.treeviewer.insert("", tk.END, values=(id,name))

        self.logger.info("Tree Updated")

     def add_item(self, id, name):
        self.treeviewer.insert("", tk.END, values=(id,name))
        self.logger.info("Tree Updated")
    
     def clear_tree(self):
        #Delete all current data in the tree by detecting current children.
        for row in self.treeviewer.get_children():
            self.treeviewer.delete(row)
            self.logger.info(f"Deleted {row} from the tree")
        self.logger.info("Cleared tree")
        
     def get_selected_items_id(self):
        """Returns a list of tree ID's currently in focus"""
        #get the item in focus
        selected = self.treeviewer.selection()
        self.logger.debug(f"Selected Items: {selected}")
        return selected
        
     def get_item(self, tree_id):
        """Returns the row at a specified tree id"""
        item = self.treeviewer.item(tree_id)["values"]
        id = item[0]
        name=item[1]
        return id, name
    
     def get_treeview_item_id(self, message_group_id):
        """Return the treeviewer id of an item given it's database id."""
        #Get a list of all tree items by treeview id
        treeviewer_ids = self.treeviewer.get_children()
        treeviewer_id = ""

        #Get the message group ID / name for each item and add to a list
        for tree_id in treeviewer_ids:
            id, name = self.get_item(tree_id)
            if id == message_group_id:
                treeviewer_id = tree_id
        return treeviewer_id
     
     def get_tree_data(self) -> list:
          """Returns all the data stored in the tree as a list."""
          #Collect the entries stored in the tree
          tree_ids_list  = self.treeviewer.get_children()
          #Create a blank list to hold the converted entries
          data_list = []
          #Get the id and name for each entry and store in the list converted list
          for tree_id in tree_ids_list:
               id, name = self.get_item(tree_id)
               data_list.append([id,name])

          return data_list
     
     def convert_tree_ids_to_database_ids(self, tree_ids_list:list):
        """Converts a list of tree ID's to Message Group ID's"""
        message_group_ids = []
        for tree_id in tree_ids_list:
            id, name = self.get_item(tree_id)
            message_group_ids.append(id)

        return message_group_ids
        
     def update_tree(self, updated_rows:list):
          """Updates the tree, keeping items selected in focus.
          Accepts a list in format [[id,name],...]"""
        
          #Keep a record of the currently selected (in focus items)
          selected_tree_ids = self.get_selected_items_id()
          #Convert the selected tree ID's to database ID's
          in_focus_database_ids = self.convert_tree_ids_to_database_ids(selected_tree_ids)

          #Clear the Tree
          self.clear_tree()
          #Add the updated list
          self.__add_items(updated_rows)

          #Re-focus the previously selected items
          self.focus_items(in_focus_database_ids)
        
     def remove_item(self, selected_item):
        self.treeviewer.delete(selected_item)
        self.logger.info("Tree Updated")

     def focus_all_items(self):
        self.logger.debug("Focusing all items")
        items_list = self.treeviewer.get_children()
        self.logger.debug(f"Item to focus: {items_list}")
        self.treeviewer.selection_add(items_list)

     def focus_items(self, message_ids_list):
        selected_tree_ids_list = []
        for message_group_id in message_ids_list:
            tree_id = self.get_treeview_item_id(message_group_id)
            if tree_id != "":
                selected_tree_ids_list.append(tree_id)
        
        self.treeviewer.selection_add(selected_tree_ids_list)

     def set_bottom_button_cmd(self, button_command):
          self.bottom_button.configure(command = button_command)

#Creates 2 treeview columns one for showing a list of data and the other for selecting the data
class Dual_Selection_Columns(ctk.CTkFrame):
     def __init__(self, parent, column_0_top_title_text, column_2_top_title_text, font):
        super().__init__(parent)

        #Setup Logging
        self.logger = logging.getLogger(__name__)

        #Setup Frame
        self.columnconfigure(0, weight=1, uniform="columns")
        self.columnconfigure(1, weight=1, uniform="controls")
        self.columnconfigure(2, weight=1, uniform="columns")
        self.rowconfigure(0, weight=1)

        #Column 0
        column_0_bottom_button_text = "Select All"
        self.column0_frame = Selection_Column(self, column_0_top_title_text, column_0_bottom_button_text, font, self.focus_all_items_col0)
        self.column0_frame.grid(column=0, row=0, sticky="nsew")

        #Column 1
        self.column1_frame = ctk.CTkFrame(self)
        self.column1_frame.columnconfigure(0, weight=1)
        self.column1_frame.rowconfigure(0, weight=1, uniform="btn_row")
        self.column1_frame.rowconfigure(1, weight=1, uniform="btn_row")
        self.column1_frame.grid(column=1, row=0, sticky="nsew")

        self.add_btn = ctk.CTkButton(self.column1_frame, text=">>", width=50, height=50, command=self.__move_item_to_selected_column)
        self.add_btn.grid(column=0, row=0, sticky="")

        self.remove_btn = ctk.CTkButton(self.column1_frame, text="<<", width=50, height=50, command=self.__remove_item_from_selected_column)
        self.remove_btn.grid(column=0, row=1, sticky="")

        #Column 2
        column_2_bottom_button_text = "Select All"
        self.column2_frame = Selection_Column(self, column_2_top_title_text, column_2_bottom_button_text, font, self.focus_all_items_col2)
        self.column2_frame.grid(column=2, row=0, sticky="nsew")

     def focus_all_items_col0(self):
          """Selects all items in column 0"""
          self.column0_frame.focus_all_items()

     def focus_all_items_col2(self):
          """Selects all items in column 2"""
          self.column2_frame.focus_all_items()

     #Moves selected items from the first column to the selected column
     def __move_item_to_selected_column(self):
        
        #Get the selected items as a list
        items_list = self.column0_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {items_list}")

        #Check the selected items are not already in the selected tree
        selected_tree : ttk.Treeview = self.column2_frame.get_tree()
        selected_tree_item_ids = selected_tree.get_children()
        self.logger.debug(f"Selected Items Tree: {selected_tree_item_ids}")

        #A blank list to hold id's of groups already in the selected list
        selected_groups_id_list = []

        #Extract the id from each item and add to the list
        for item_id in selected_tree_item_ids:
            id, name = selected_tree.item(item_id)["values"]
            selected_groups_id_list.append(id)

        self.logger.debug(f"Selected Groups ID list: {selected_groups_id_list}")

        #Add the newly selected groups to the selected tree only if not already added
        for tree_id in items_list:
            id, name = self.column0_frame.get_item(tree_id)

            if (id not in selected_groups_id_list):
                self.column2_frame.add_item(id, name)

     #Removes a selected item from column 1
     def __remove_item_from_selected_column(self):
        items_list = self.column2_frame.get_selected_items_id()
        self.logger.debug(f"Selected items by ID: {items_list}")
        for tree_id in items_list:
            self.column2_frame.remove_item(tree_id)

     
     def clear_selected_column(self):
          """Clears all data from the right selection column"""
          self.column2_frame.clear_tree()

     def set_column_values(self, column_index, updated_rows):
          """Set the values of the treeview columns, valid indexes are 0 and 1.
          Accepts a list in format [[id,name],...]"""

          columns_list = [self.column0_frame, self.column2_frame]
          if column_index == 0 or column_index == 1:
               column : Selection_Column = columns_list[column_index]
               column.update_tree(updated_rows)

     def get_data(self) -> list:
          """Returns the input data fro mthe selection column."""

          column : Selection_Column = self.column2_frame
          column_data :list  = column.get_tree_data()

          return column_data







