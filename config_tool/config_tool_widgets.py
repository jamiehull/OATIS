import customtkinter as ctk
from tkinter import StringVar
import logging
import json
import os
from PIL import Image
from tkinter import messagebox
from tkinter import filedialog
from database.database_connection import DB
from config_tool.global_variables import *
from modules.custom_dataclasses import *
from modules.common import resize_image_keep_aspect, get_machine_ip, write_dict_to_file
from modules.gui_templates import Title_Entry, Title_Combobox, CustomTree, ImagePicker, Dual_Selection_Columns
from display_widgets.widget_image_paths import widget_paths_dict
from modules.matrix_operations import find_display_section_dimensions, find_display_sections, verify_surface_is_rect
from config_tool.validation import validate_inputs
from config_tool.validation import validate_not_null
from config_tool.message_boxes import confirm_delete, delete_warning, invalid_layout_matrix_warning, initialised_program_exiting_message
from modules.common import open_json_file
import shutil

#-------------------------Base-Widgets-------------------------
#Base frame used in each tab in the config window
class BaseFrame(ctk.CTkFrame):
     def __init__(self, parent, database_connection):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Database connection object to be able to manipulate the database
          self.db : DB = database_connection

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup Columns / rows for config_frame
          self.columnconfigure(0, weight=0)
          for i in range(1,4):
               self.columnconfigure(i, weight=1)

          self.rowconfigure(0, weight=1)
          self.rowconfigure(1, weight=0)
          self.rowconfigure(2, weight=0)

#Base frame used in each tab in the config window
"""Base Frame used to construct a config window. Args are used to pass in each row of type Input_Row"""
class BaseFrameNew(ctk.CTkFrame):
     def __init__(self, parent, database_connection, scrollable:bool):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Database connection object to be able to manipulate the database
          self.db : DB = database_connection

          #Flip-Flop variable to sense the state of the GUI - indicates whetther a tree item is selected to modify
          # or a new item is being added, default=True for error protection
          #True = New Item
          #False = Existing Item
          self.new_item = True

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Callback that can be set and triggered when this frame is raised in a stack of frames, 
          # if this is not set then no callbacks are triggered
          self.raise_callback = None

          #Determines whether the input frame is scrollable
          self.scrollable = scrollable


     def build_gui(self, title:str, table:str, name_column:str, id_column:str, row_list:list):
          """Initialises the GUI"""
          #Constants used to make GUI
          self.title = title
          self.table :str = table
          self.name_column :str = name_column
          self.id_column :str = id_column
          self.row_list :list = row_list

          #Setup Columns / rows for base_frame
          self.columnconfigure(0, weight=0)
          for i in range(1,4):
               self.columnconfigure(i, weight=1)

          self.rowconfigure(0, weight=1)
          self.rowconfigure(1, weight=0)
          self.rowconfigure(2, weight=0)

          #------------------------------TREEVIEW AND BUTTONS--------------------------------------------------

          #Tree Viewer to display all devices in a nested format
          self.tree = CustomTree(self)
          self.tree.grid(column=0, row=0, columnspan=1, sticky="nsew")

          self.add_btn = ctk.CTkButton(master=self, text="Add", fg_color="green", font=self.default_font, command=lambda:self.__add_btn_cmd())
          self.add_btn.grid(column=0, row=1, sticky="nsew")

          self.del_btn = ctk.CTkButton(master=self, text="Remove", fg_color="red", font=self.default_font, command=lambda:self.__del_btn_cmd())
          self.del_btn.grid(column=0, row=2, sticky="nsew")

          #------------------------------INPUT FRAME--------------------------------------------------

          self.input_frame = Input_Frame(self, self.title, self.row_list, self.scrollable, self.db)
          self.input_frame.grid(column=1, row=0, sticky="nsew", columnspan=3)

          #Command for save button must be set in the child class
          self.save_btn = ctk.CTkButton(master=self, text="Save", fg_color="green", font=self.default_font)
          self.save_btn.grid(column=1, row=1, sticky="ns", columnspan="3", rowspan=2, pady=20)

          #OATIS LOGO
          self.logo = ctk.CTkLabel(master=self, text="", font=self.default_font, anchor="e")
          self.logo.grid(column=3, row=1, sticky="nse", columnspan="1", rowspan=2, pady=0)

          self.add_btn.update_idletasks()
          self.logo_label_height = self.add_btn.winfo_height() * 2

          image = Image.open("config_tool/default_logo.png")

          #Resize the image to fit into preview window
          resized_image: Image.Image = resize_image_keep_aspect(image, 500, self.logo_label_height)
          logo_file = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width, resized_image.height))

          self.logo.configure(image=logo_file, compound="left", require_redraw=True)

     #Clears all the entry widgets in the GUI ready for adding an item
     def __add_btn_cmd(self):
          #Set the state indicator variable to True, indicating a new item is to be added
          self.set_new_item_state(True)

          #Clear All entry Widgets
          self.input_frame.clear_all_entries()
          self.logger.info("Cleared all entry Widgets")

     def __del_btn_cmd(self):
          self.logger.info(f"#######---Delete Button Pressed - Attempting Deletion of selected item---#######")
          #Get the DB id of the selected treeview item
          in_focus_db_id = self.tree.get_in_focus_item_db_id()
          self.logger.debug(f"In focus dtabase ID:{in_focus_db_id}")

          if in_focus_db_id != None:
               #Confirm with the user they want to delete
               confirmation = confirm_delete()
               if confirmation == True:
                    #Delete the item
                    feedback = self.db.delete_row(self.table, self.id_column, in_focus_db_id)
                    if feedback == True:
                         self.logger.info(f"Deleted row with {self.id_column} of {in_focus_db_id} in table {self.table}")

                         #Clear the input widgets
                         self.input_frame.clear_all_entries()

                         #Set the State indicator to True
                         self.set_new_item_state(True)

                         #Update the tree
                         self.update_tree()
                    else:
                         #Warn the user the item cannot be deleted to maintain database integrity
                         delete_warning(feedback)


     #Updates the treeviewer list to the current database state - called by the gui menu buttons and save button
     def update_tree(self):
          new_tree_rows = self.db.get_2column_data(self.id_column, self.name_column, self.table)

          self.logger.debug(f"Database Query for latest Treeview data returned: {new_tree_rows}")

          #Check for any system rows that should not appear in the user configurable tree list
          #and remove them from the list
          if new_tree_rows != []:
               #Check to see if the first elements id == 0, if it does this is a system row that must remain configured in order for the system to function
               if new_tree_rows[0][0] == 0:
                    #Remove the first row in the list
                    new_tree_rows.pop(0)
                    self.logger.debug("Removed first row of returned data, this is a system row that must not be modified by the user.")

          self.logger.debug(f"New Tree Data with System Rows removed: {new_tree_rows}")
          
          #Add the modified list to the tree.
          self.tree.update_tree(new_tree_rows)

     def get_and_validate_input_data(self):
          #retrieve all data / validation functions from the input frame
          input_widget_object_list = self.input_frame.get_all_widget_objects()

          input_data_valid_list = []
          widget_data_list = []

          #Make a list of widget_data and widget_validation Functions
          for widget_object in input_widget_object_list:
               widget_object : Entry_Widget_Data

               if widget_object.type == "dual_selection_columns":
                    dual_selection_columns_widget :Dual_Selection_Columns = widget_object.input_widget
                    widget_input_data = dual_selection_columns_widget.get_data()

                    input_data_valid_list.append((widget_input_data, widget_object.validation_function))
                    widget_data_list.append(widget_input_data)

               elif widget_object.type == "gpio_pin_config":
                    gpio_pin_config_widget :GPIO_Pin_Config = widget_object.input_widget
                    widget_input_data = gpio_pin_config_widget.get_data()

                    input_data_valid_list.append((widget_input_data, widget_object.validation_function))
                    widget_data_list.append(widget_input_data)

               elif widget_object.type == "image_picker":
                    image_picker_widget : ImagePicker = widget_object.input_widget
                    widget_input_data = image_picker_widget.get_data()

                    input_data_valid_list.append((widget_input_data, widget_object.validation_function))
                    widget_data_list.append(widget_input_data)

               elif widget_object.type == "display_builder":
                    display_builder_widget : Display_Builder_Base_Frame = widget_object.input_widget
                    widget_input_data = display_builder_widget.get_data()

                    input_data_valid_list.append((widget_input_data, widget_object.validation_function))
                    widget_data_list.append(widget_input_data)

               elif widget_object.type == "display_instance_config":
                    display_instance_config_widget : Display_Instance_Config_Base_Frame = widget_object.input_widget
                    widget_input_data = display_instance_config_widget.get_data()

                    input_data_valid_list.append((widget_input_data, widget_object.validation_function))
                    widget_data_list.append(widget_input_data)
                    
               else:
                    input_data_valid_list.append((widget_object.string_var.get(), widget_object.validation_function))
                    widget_data_list.append(widget_object.string_var.get())


          #Validate the data
          valid_status = validate_inputs(input_data_valid_list)

          return valid_status, widget_data_list

     def set_save_btn_command(self, function):
          """Pass in a function to be called when the save button is clicked"""
          self.save_btn.configure(command=function)

     def set_delete_btn_command(self, function):
          """Pass in a function to be called when the delete button is clicked"""
          self.del_btn.configure(command=function)

     def set_combobox_values(self, combobox_index:int, combobox_values:list):
          #Convert the values list to a list of strings to prevent errors
          combobox_values = list(map(str, combobox_values))
          self.input_frame.set_combobox_values(combobox_index, combobox_values)

     def on_raise_callback(self):
          """Triggers the on raise callback."""
          if (self.raise_callback != None):
               self.raise_callback()

     def set_on_raise_callback(self, callback):
          """Sets the callback triggered when this frame is raised in the stack."""
          self.raise_callback = callback

     def set_new_item_state(self, state:bool):
          """Sets the value of the stae indicator variable with logging."""

          self.new_item = state

          if state == True:
               self.logger.info("Set State Indicator to True - No Tree Viewer item selected")
          else:
               self.logger.info("Set State Indicator to False - Tree Viewer item selected")

     def get_db_object(self) -> DB:
          """Returns the database object."""
          self.db : DB
          return self.db


"""Makes an input frame with row's of input widgets.
Takes a list of Input_Rows as arguments.
Input rows are either Input_Row objects, String titles or a custom widget class.
Valid Widget Types: title, combobox, entry, dual_selection_columns"""

class Input_Frame(ctk.CTkFrame):
     def __init__(self, parent, title:str, input_rows:list, scroll:bool, database_connection:DB):
          super().__init__(parent)

          #Configure Parent Frame Rows and Columns
          self.columnconfigure(0, weight=1)
          self.rowconfigure(0, weight=1)

          #Decide whether we are using a scrollable frame or not
          if scroll == True:
               self.base_frame = ctk.CTkScrollableFrame(self)
          else:
               self.base_frame = ctk.CTkFrame(self)

          #Grid the base frame
          self.base_frame.grid(column=0, row=0, sticky="nsew")

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)


          #Calculate the number of rows
          self.number_of_rows = len(input_rows)

          #Configure Frame Rows and Columns
          self.base_frame.columnconfigure(0, weight=0)
          self.base_frame.columnconfigure(1, weight=1)
          self.base_frame.columnconfigure(2, weight=1)

          #Title row
          self.base_frame.rowconfigure(0, weight=0)

          for i in range(1, self.number_of_rows):
               self.base_frame.rowconfigure(i, weight=1)

          #Row index to start adding rows from
          row_start_index = 1
          self.current_row = row_start_index

          #Add the title widget
          frame_title = ctk.CTkLabel(master=self.base_frame, text=title, font=self.default_font)
          frame_title.grid(column=0, row=0, sticky="nsew", padx=10, pady=10, columnspan=3)

          #List to store widget data
          self.entry_widget_list = []

          #Add the row widgets
          for row in input_rows:
               row : Input_Row
               #Add a title to the row if one is configured
               if (row.title != None) and ((row.widget_type == "text_entry") or (row.widget_type == "combobox")):
                    #Title
                    title = ctk.CTkLabel(master=self.base_frame, text=row.title, font=self.default_font, anchor="w")
                    title.grid(column=0, row=self.current_row, sticky="ew", padx=10, pady=5)

               #Input Widget string var for storing input values
               text_var = StringVar()

               if row.widget_type == "text_entry":
                    input_widget = ctk.CTkEntry(master=self.base_frame, textvariable=text_var, font=self.default_font)
                    input_widget.grid(column=1, row=self.current_row, sticky="ew", padx=50, columnspan=2)

                    #Create a dataclass to hold all entry info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "combobox":
                    input_widget = ctk.CTkComboBox(master=self.base_frame, variable=text_var, font=self.default_font, state="readonly")
                    input_widget.grid(column=1, row=self.current_row, sticky="ew", padx=50, columnspan=2)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "title":
                    title_widget = ctk.CTkLabel(master=self.base_frame, text=row.title, font=self.default_font)
                    title_widget.grid(column=0, row=self.current_row, sticky="ew", padx=10, pady=10, columnspan=3)
                    #Create a dataclass to hold all info - not used, for consistency
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "dual_selection_columns":
                    input_widget = Dual_Selection_Columns(self.base_frame, row.custom_widget_titles[0], row.custom_widget_titles[1], self.default_font)
                    input_widget.grid(column=0, row=self.current_row, sticky="nsew", padx=50, columnspan=3)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "gpio_pin_config":
                    input_widget = GPIO_Pin_Config(self.base_frame)
                    input_widget.grid(column=0, row=self.current_row, sticky="ns", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "image_picker":
                    input_widget = ImagePicker(self.base_frame)
                    input_widget.grid(column=0, row=self.current_row, sticky="ns", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "display_builder":
                    input_widget = Display_Builder_Base_Frame(self.base_frame)
                    input_widget.grid(column=0, row=self.current_row, sticky="nsew", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "display_instance_config":
                    input_widget = Display_Instance_Config_Base_Frame(self.base_frame, database_connection)
                    input_widget.grid(column=0, row=self.current_row, sticky="nsew", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "control_buttons":
                    input_widget = Control_Buttons(self.base_frame)
                    input_widget.grid(column=0, row=self.current_row, sticky="nsew", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               elif row.widget_type == "server_config":
                    input_widget = Server_Config_Frame(self.base_frame)
                    input_widget.grid(column=0, row=self.current_row, sticky="nsew", padx=0, columnspan=3, ipadx=5)

                    #Create a dataclass to hold all combobox info
                    combobox_data = Entry_Widget_Data(row.widget_type, input_widget, [], [], text_var, row.validation_function)
                    self.entry_widget_list.append(combobox_data)

               self.current_row += 1

     def get_all_widget_objects(self) -> list:
          """Returns each Entry_Widget_Data object"""
          widget_list = []
          for widget in self.entry_widget_list:
               widget : Entry_Widget_Data
               widget_list.append(widget)

          return widget_list
     
     def get_widget_object(self, widget_index) -> list:
          """Returns a single widget object"""
          if (widget_index <= len(self.entry_widget_list)) and (widget_index >=0):
               widget_data_object : Entry_Widget_Data = self.entry_widget_list[widget_index]
               widget = widget_data_object.input_widget

          return widget
     
     def get_data(self, input_widget_index):
          """Returns the current stringvar value for a single widget"""
          #Check the specified index is not out of range
          if input_widget_index <= len(self.entry_widget_list):
               widget : Entry_Widget_Data = self.entry_widget_list[input_widget_index]
               widget_data = widget.string_var.get()

               return widget_data

     def get_all_data(self) -> list:
          """Returns data from all widgets in the input frame."""
          data_list = []
          for widget in self.entry_widget_list:
               widget : Entry_Widget_Data
               data_list.append(widget.string_var.get())

          return data_list
     
     def set_data(self, input_widget_index:int, input_data:str):
          """Sets the stringvar for a single widget"""
          if input_widget_index <= len(self.entry_widget_list):
               input_widget :Entry_Widget_Data = self.entry_widget_list[input_widget_index]
               string_var = input_widget.string_var
               string_var.set(input_data)

     def set_all_data(self, *args):
          """Sets the stringvars for all widgets"""
          if len(args) <= len(self.entry_widget_list):
               i = 0 #Iterator variable for selecting widget
               for a in range(len(args)):
                    widget_object :Entry_Widget_Data = self.entry_widget_list[i] #Get widget

                    #If the widget is a title, advance to the next widget and retrieve the widget again
                    while widget_object.type == "title":
                         i += 1
                         widget_object :Entry_Widget_Data = self.entry_widget_list[i]
                    
                    #Set the widget value
                    string_var = widget_object.string_var
                    string_var.set(args[a])
                    i += 1

     def clear_all_entries(self):
          for i in range(len(self.entry_widget_list)):
               widget_object :Entry_Widget_Data = self.entry_widget_list[i]
               if widget_object.type == "dual_selection_columns":
                    dual_selection_columns_widget : Dual_Selection_Columns = widget_object.input_widget
                    dual_selection_columns_widget.clear_selected_column()

               elif widget_object.type == "gpio_pin_config":
                    gpio_pin_config_widget :GPIO_Pin_Config = widget_object.input_widget
                    gpio_pin_config_widget.clear_config_frame()

               elif widget_object.type == "image_picker":
                    image_picker_widget : ImagePicker = widget_object.input_widget
                    image_picker_widget.clear_image_preview()

               elif widget_object.type == "display_builder":
                    image_picker_widget : Display_Builder_Base_Frame = widget_object.input_widget
                    image_picker_widget.reset_display_builder()

               elif widget_object.type == "display_instance_config":
                    display_instance_widget : Display_Instance_Config_Base_Frame = widget_object.input_widget
                    display_instance_widget.clear_widgets()

               elif widget_object.type == "control_buttons":
                    display_instance_widget : Control_Buttons = widget_object.input_widget
                    display_instance_widget.disable_buttons()

               else:
                    string_var = widget_object.string_var
                    string_var.set("")

     def clear_entry(self, widget_index):
          #Check the specified index is not out of range
          if widget_index <= len(self.entry_widget_list):
               input_widget :Entry_Widget_Data = self.entry_widget_list[widget_index]
               string_var = input_widget.string_var
               string_var.set("")

     def get_number_of_rows(self):
          return self.number_of_rows
     
     def change_combobox_readonly_state(self, combobox_index:int, state:str):
          """Changes teh state of the widget, valid states are normal, readonly and disabled."""
          #Check the specified index is not out of range
          if combobox_index <= len(self.entry_widget_list):
               widget:Entry_Widget_Data =self.entry_widget_list[combobox_index]
               if state == "readonly":
                    widget.input_widget.configure(state="readonly", fg_color="#343638")
               elif state == "normal":
                    widget.input_widget.configure(state="normal", fg_color="#343638")
               elif state == "disabled":
                    widget.input_widget.configure(state="disabled", fg_color="#555B5E")

     def change_entry_readonly_state(self, entry_index:int, state:str):
          """Changes the state of the widget, valid states are normal, readonly and disabled."""
          #Check the specified index is not out of range
          if entry_index <= len(self.entry_widget_list):
               widget:Entry_Widget_Data =self.entry_widget_list[entry_index]
               if state == "normal":
                    widget.input_widget.configure(state="normal", fg_color="#343638", text_color="#dbe4ed")
               elif state == "disabled":
                    widget.input_widget.configure(state="disabled", fg_color="#555B5E", text_color="#737373")

     def set_combobox_values(self, combobox_index:int, combobox_values:list):
          """Updates the values in a combobox dropdown, provide an index, this will be in order from top down of the screen layout starting at 0. Povide a list of values."""
          combobox_data : Entry_Widget_Data = self.entry_widget_list[combobox_index]
          if combobox_data.type == "combobox":
               combobox_data.input_widget.configure(values=combobox_values)
          else:
               #Do nothing
               pass

     def set_combobox_command(self, combobox_index:int, combobox_command):
          entry_widget_data : Entry_Widget_Data = self.entry_widget_list[combobox_index]
          entry_widget = entry_widget_data.input_widget
          entry_widget.configure(command=combobox_command)


#-------------------------Diplay Template-Widgets-------------------------
class Display_Builder_Base_Frame(ctk.CTkFrame):
     """Container Frame to hold Screen Builder Widgets and methods."""
     def __init__(self, parent):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Store a reference to the parent
          self.parent : ctk.CTkFrame = parent
     
          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=0) 
          self.rowconfigure(1, weight=1)
          self.rowconfigure(2, weight=1)
          self.rowconfigure(3, weight=1)
               
          self.columnconfigure(0, weight=2)
          self.columnconfigure(1, weight=1)

          #Make the 4 frames

          self.grid_builder_frame = Grid_Layout_Builder(self, self.surface_id_assign,
                                                        self.widget_assign)
          self.grid_builder_frame.grid(column=0, row=0, columnspan=1, rowspan=2, sticky="nsew")

          self.grid_settings_frame = Grid_Settings(self, 
                                                   set_cmd=self.build_grid, 
                                                   reset_cmd=self.reset_gui_state, 
                                                   build_cmd=self.build_display_layout)
          self.grid_settings_frame.grid(column=1, row=0, columnspan=1, rowspan=1, sticky="nsew")

          self.surface_selector_frame = Surface_Selector(self, self.set_display_area_number)
          self.surface_selector_frame.grid(column=1, row=1, columnspan=1, rowspan=2, sticky="nsew")

          #self.widget_settings_frame = ctk.CTkFrame(self, fg_color="green")
          #self.widget_settings_frame.grid(column=1, row=1, columnspan=1, rowspan=3, sticky="nsew")

          self.widget_selector_frame = Widget_Selector(self)
          self.widget_selector_frame.grid(column=0, row=2, columnspan=1, rowspan=2, sticky="nsew")

          #Disable widget selector buttons by default
          self.widget_selector_frame.disable_buttons()

          #String Vars
          self.selected_grid_coordinate : tuple = (0,0)
          self.selected_display_area : str = ""

     def build_grid(self, total_rows, total_columns):
          """Builds the display layout builder"""
          self.logger.debug("#######---Building Display Layout Builder Grid---#######")

          #Build the layout builder grid
          self.grid_builder_frame.render_grid_layout_builder(total_columns, total_rows)

     def build_display_layout(self):
          """Builds the display layout from the layout matrix."""
          self.logger.debug("#######---Building Display Layout---#######")

          #Check the display surfaces have been assigned id's
          layout_matrix = self.grid_builder_frame.get_layout_matrix()

          #Validate the layout matrix
          if self.validate_layout_matrix(layout_matrix) == True:
               
          #Only if all id's have been assigned do we proceed to allow hte user to assign widgets

               #lock out the grid settign  build button and rows/columns comboboxes
               self.grid_settings_frame.disable_grid_settings_modify()

               #Lock out the Surface Selector Buttons
               self.surface_selector_frame.disable_buttons()

               #Build the display layout
               self.grid_builder_frame.render_display_layout()

               #Enable the widget selector buttons
               self.widget_selector_frame.enable_buttons()

          else:
               self.logger.warning("Layout matrix is not valid!")
               invalid_layout_matrix_warning()

     def validate_layout_matrix(self, layout_matrix) -> bool:
          """Checks all surfaces have ID's and that the matrix is valid."""
          self.logger.debug("Validating layout matrix...")
          valid = True

          total_columns = len(layout_matrix[0])
          total_rows = len(layout_matrix)

          #Check all surfaces have an id assigned
          for row in range(0, total_rows):
               if valid == True:
                    for column in range(0, total_columns):
                         if layout_matrix[row][column] == '':
                              self.logger.debug(f"Display ID not assigned at coordinate ({row},{column})")
                              valid *= False
                              break
                         else:
                              valid *= True
               else:
                    self.logger.debug("Not all surfaces have id's assigned!")
                    break

          if valid == True:
               #Get the top left coords of each display section
               display_section_dict : dict = find_display_sections(layout_matrix)

               #Check the surface id's have not been duplicated accross blocks and are rectangles
               for display_section_id in display_section_dict:
                    top_left_coord = display_section_dict.get(display_section_id)
                    valid *= verify_surface_is_rect(layout_matrix, display_section_id, top_left_coord)
                    if valid != True:
                         break

          return valid

     def reset_gui_state(self):
          #Enable the surface selector buttons
          self.surface_selector_frame.enable_buttons()

          #Disable widget selector buttons
          self.widget_selector_frame.disable_buttons()

     def set_display_area_number(self, area_number:str):
          """Sets the selected display area variable."""
          self.selected_display_area = area_number
          print(f"Selected Display Area: {self.selected_display_area}")

     def surface_id_assign(self, coordinate:tuple):
          """Sets the selected coordiante and updates the button label with the chosen display area."""
          self.selected_grid_coordinate = coordinate
          print(f"Selected Coordinate: {self.selected_grid_coordinate}")
          if self.selected_display_area != "":
               self.grid_builder_frame.set_display_area_var(coordinate, self.selected_display_area)

     def widget_assign(self, display_area_id):
          self.logger.debug(f"LETS ASSIGN A WIDGET! to {display_area_id}")

          #Retrieve the selected widget
          selected_widget_string = self.widget_selector_frame.get_selected_widget()
          self.logger.debug(f"Selected widget string:{selected_widget_string}")

          if selected_widget_string != "":
               #Assign the widget to the display area
               self.grid_builder_frame.set_display_area_widget(display_area_id, selected_widget_string)
          else:
               self.logger.debug("No Widget selected.")

     def get_layout_matrix(self):
          """Returns the display configuration layout matrix"""
          layout_matrix = self.grid_builder_frame.get_layout_matrix()
          print(f"Layout Matrix:{layout_matrix}")
          return layout_matrix

     def get_data(self):
          """Returns the display layout data as a display template object."""
          #Get the Settings Widget Data
          display_template_name, number_of_columns, number_of_rows = self.grid_settings_frame.get_data()
          #Get the Grid Data
          layout_matrix, display_area_dict = self.grid_builder_frame.get_data()
          #Put all the data into an object
          display_template_obj = Display_Template(display_template_name, number_of_columns, number_of_rows, layout_matrix, display_area_dict)
          return display_template_obj
     
     def set_data(self, display_template_id, display_template_name, total_rows, total_columns, layout_matrix, display_surface_rows):
          """Sets the Display Builder widget data."""
          self.grid_settings_frame.set_data(display_template_name, total_columns, total_rows)
          self.build_grid(total_rows, total_columns)
          self.grid_builder_frame.render_display_layout(layout_matrix)
          self.surface_selector_frame.disable_buttons()
          self.widget_selector_frame.enable_buttons()

          for row in display_surface_rows:
               display_surface_id = row[1]
               widget_string = row[2]
               self.grid_builder_frame.set_display_area_widget(str(display_surface_id), widget_string)

     def reset_display_builder(self):
          """Resets all widgets to defaults."""
          self.grid_settings_frame.reset_grid()
          self.reset_gui_state()
          
class Grid_Layout_Builder(ctk.CTkFrame):
     """A button grid used for assigning display areas."""
     def __init__(self, parent, surface_id_assign_cmd, widget_assign_cmd):
          super().__init__(parent)

          #Store a reference to the parent
          self.parent : Display_Builder_Base_Frame = parent

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Create single row / colunn
          self.rowconfigure(0, weight=1)
          self.columnconfigure(0, weight=1)

          #Frame list used for clearing the grid
          self.frame_list = []

          #Dict to hold button widgets once layout has been built
          #Key is display_area_id, value is the Display Section Class
          self.display_area_dict :dict = {}

          #Matrix used for storing button stingvars
          self.display_area_var_list : list = []

          #Layout Matrix
          self.layout_matrix = []

          #Button Commands
          self.surface_id_assign_cmd = surface_id_assign_cmd #When assigning display section id's
          self.widget_assign_cmd = widget_assign_cmd #When assigning a widget to a display section

          #Grid Size - Fixed for now to avoid scaling issues
          self.grid_width = 640
          self.grid_height = 360

          #Number of rows and columns
          self.total_rows = 0
          self.total_columns = 0

          #Colours
          self.grid_border_colour = "white"
          self.grid_bg_colour = "black"

          #Build Default grid
          self.render_grid_layout_builder(1,1)

     def render_grid_layout_builder(self, total_columns, total_rows):
          """Builds the display layout button grid."""
          self.logger.debug("#######---Building Display Layout Grid---#######")
          #Clear the current widgets and Build the tkinter rows and columns
          self.__build_tkinter_grid(total_columns, total_rows, False)

          #Build the Button Grid
          current_row_index = 0
          current_column_index = 0
          
          for y in range(total_rows):
               current_row_display_area_list = []
               for x in range(total_columns):
                    current_coordinate = (current_row_index, current_column_index)
                    display_area_var = StringVar()
                    btn = ctk.CTkButton(self.grid_frame, corner_radius=0, border_width=2, 
                                        border_color=self.grid_border_colour, 
                                        fg_color=self.grid_bg_colour,
                                        textvariable=display_area_var, 
                                        font= self.default_font, 
                                        width=(self.grid_width/total_columns), 
                                        height=(self.grid_height/total_rows),
                                        command = (lambda coordinate = current_coordinate : self.surface_id_assign_cmd(coordinate)))
                    btn.grid(column=current_column_index, row=current_row_index, sticky="nsew")

                    #Add the button widget var to the display area list
                    current_row_display_area_list.append(display_area_var)
                    current_column_index += 1

               current_row_index +=1
               current_column_index = 0
               self.display_area_var_list.append(current_row_display_area_list)

          print(f"Display Area Var List: {self.display_area_var_list}")

     def render_display_layout(self, layout_matrix=None):
          if layout_matrix == None:
               #Get the layout matrix
               self.layout_matrix = self.get_layout_matrix()
          else:
               self.layout_matrix = layout_matrix

          #Calculate total rows and columns
          total_columns = len(self.layout_matrix[0])
          total_rows = len(self.layout_matrix)

          self.logger.debug(f"Total Columns:{total_columns}, Total Rows:{total_rows}")

          #Find all the display sections and their top left coordinates
          display_section_dict : dict = find_display_sections(self.layout_matrix)

          #Build the tkinter grid
          self.__build_tkinter_grid(total_columns, total_rows, True)

          #Find width and height of each display section
          for display_section_id in display_section_dict:
               top_left_coord = display_section_dict.get(display_section_id)
               print(f"Display_ID:{display_section_id}, top left coord:{top_left_coord}")
               width, height = find_display_section_dimensions(self.layout_matrix, display_section_id, top_left_coord, total_columns, total_rows)
               self.__add_display_section(display_section_id, top_left_coord, width, height)

     def __build_tkinter_grid(self, total_columns, total_rows, keep_layout_matrix:bool):
          """Builds the tkinter grid columns and rows"""
          self.logger.debug("Building Tkinter Grid")
          self.total_rows = total_rows
          self.total_columns = total_columns
          
          #Clear the current grid of widgets
          self.__clear_grid(keep_layout_matrix)

          #Build Tkinter Grid
          for i in range(total_rows):
               self.grid_frame.rowconfigure(i, weight=1, uniform="grid_y")
          for i in range(total_columns):
               self.grid_frame.columnconfigure(i, weight=1, uniform="grid_x")

     def __add_display_section(self, display_area_id:str, top_left_coordinate:tuple, display_section_block_width:int, display_section_block_height:int):
          print(f"Adding display Section {display_area_id} at: {top_left_coordinate} with width {display_section_block_width} and height {display_section_block_height}")

          #Sting Var for storing widget string
          widget_string_var = StringVar()
          widget_string_var.set(display_area_id)
          
          #Calculate button width and height based on size of the display builder window
          btn_width = int((self.grid_width/self.total_columns)*display_section_block_width)
          btn_height = int((self.grid_height/self.total_rows)*display_section_block_height)
          
          #Make a display section button
          display_section = Display_Section(self.grid_frame, display_area_id, top_left_coordinate, self.default_font, btn_width, btn_height, display_section_block_width, display_section_block_height, self.widget_assign_cmd, self.grid_border_colour, self.grid_bg_colour)

          column_index = top_left_coordinate[0]
          row_index = top_left_coordinate[1]

          #Add the button to the grid
          display_section.grid(column=column_index,  row=row_index, columnspan=display_section_block_width, rowspan=display_section_block_height, sticky="nsew")
          print(f"Column={column_index}, Row={row_index}")

          #Add the button to the buttons dict
          self.display_area_dict[display_area_id] = display_section

     def __clear_grid(self, keep_layout_matrix:bool):
          """Clears the current grid widgets and display area var list."""
          #Clear previous grid if present
          for widget in self.frame_list:
               widget :ctk.CTkFrame
               widget.destroy()

          #Clear the Display area list
          self.display_area_var_list = []

          #Clear the buttons list
          self.display_area_dict.clear()

          if keep_layout_matrix == False:
               #Clear the layout matrix
               self.layout_matrix.clear()

          #Grid to hold buttons
          self.grid_frame = ctk.CTkFrame(self)
          self.grid_frame.grid(column=0, row=0)
          self.frame_list.append(self.grid_frame)

     def set_display_area_var(self, coordinate:tuple, display_area_number:str):
          """Sets the selected button's stringvar, updating it's label."""
          row = coordinate[0]
          column = coordinate[1]

          #Get the string var for the button
          button_var : StringVar = self.display_area_var_list[row][column]
          button_var.set(display_area_number)

     def get_layout_matrix(self):
          """Returns the layout matrix"""
          layout_matrix = []

          for row in self.display_area_var_list:
               current_row_display_area_list = []
               for column in row:
                    column : StringVar
                    display_surface_id = column.get()
                    current_row_display_area_list.append(display_surface_id)
               layout_matrix.append(current_row_display_area_list)
          
          self.logger.debug(f"Current Layout Matrix: {layout_matrix}")
          
          return layout_matrix

     def set_display_area_widget(self, display_area_id, widget_string):
          display_section : Display_Section = self.display_area_dict[display_area_id]
          display_section.assign_widget(widget_string)

     def get_data(self):
          """Returns all display template data"""
          return self.layout_matrix, self.display_area_dict

     def set_data(self):
          """Used to populate the stored display template in to the Display Builder"""

class Display_Section(ctk.CTkButton):
     """Creates a Display Section Button for use with the Grid Layout Builder, also stores the info for the display section."""
     def __init__(self, parent, dipslay_area_id, top_left_coord, text_font, btn_width:int, btn_height:int, block_width:int, block_height:int, clicked_cmd, btn_border_colour, btn_colour):
          super().__init__(master=parent, text=dipslay_area_id, corner_radius=0, border_width=0, font=text_font, width=btn_width, height=btn_height, command=self.__btn_command, border_spacing=0, border_color=btn_border_colour, fg_color=btn_colour)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Variables
          self.clicked_cmd = clicked_cmd
          self.surface_id = dipslay_area_id
          self.top_left_coordinate = top_left_coord
          self.block_width = block_width
          self.block_height = block_height
          self.btn_width = btn_width
          self.btn_height = btn_height
          self.widget_string = ""
          self.image_path = ""
          self.ctk_image : ctk.CTkImage
 
     def __btn_command(self):
          self.logger.debug(f"Display Area {self.surface_id} clicked")
          #Call the parent widget assign function
          self.clicked_cmd(self.surface_id)

     def assign_widget(self, widget_string:str):
          #Assign the widget string
          self.widget_string = widget_string

          #Retrieve the iamge path
          self.image_path = widget_paths_dict[widget_string]
          self.logger.debug(f"Selected Widget's iamge path: {self.image_path}")

          #Set the image
          self.set_btn_img()

     def set_btn_img(self):
          self.logger.debug(f"Setting image for display area {self.surface_id}")
          #Open the image
          image_file = Image.open(self.image_path)

          #Resize the image to fit into button
          self.resized_image: Image.Image = resize_image_keep_aspect(image_file, self.btn_width-10, self.btn_height-10)

          self.ctk_image = ctk.CTkImage(light_image=self.resized_image, dark_image=self.resized_image, size=(self.resized_image.width, self.resized_image.height))

          #Add the image to the button
          self.configure(text="")
          self.configure(require_redraw=True, image=self.ctk_image)

class Grid_Settings(ctk.CTkFrame):
     def __init__(self, parent, set_cmd, reset_cmd, build_cmd):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=1, uniform="row")
          self.rowconfigure(1, weight=1, uniform="row")
          self.rowconfigure(2, weight=1, uniform="row")
          self.rowconfigure(3, weight=1, uniform="row")
               
          self.columnconfigure(0, weight=1, uniform="column")
          self.columnconfigure(1, weight=1, uniform="column")

          #Button Commands
          self.reset_cmd = reset_cmd
          self.set_cmd = set_cmd
          self.build_cmd = build_cmd

          self.__add_widgets()

     def __add_widgets(self):
          self.name_widget = Title_Entry(self, "Name:", 250)
          self.name_widget.grid(column=0, row=0, sticky="ew", columnspan=2)

          self.rows_widget = Title_Combobox(self, "Rows:", ["1","2","3","4","5","6","7","8","9","10"], self.set_grid)
          self.rows_widget.set_value("1")
          self.rows_widget.grid(column=0, row=1, sticky="ew", columnspan=2)

          self.columns_widget = Title_Combobox(self, "Columns:", ["1","2","3","4","5","6","7","8","9","10"], self.set_grid)
          self.columns_widget.set_value("1")
          self.columns_widget.grid(column=0, row=2, sticky="ew", columnspan=2)

          reset_btn = ctk.CTkButton(self, text="Reset", font=self.default_font, command=self.reset_grid)
          reset_btn.grid(column=0, row=3, sticky="ew", columnspan=1, padx=5)

          self.build_btn = ctk.CTkButton(self, text="Build", font=self.default_font, command=self.build_layout)
          self.build_btn.grid(column=1, row=3, sticky="ew", columnspan=1, padx=5)


     def set_grid(self, event):
          """Redraws the grid buttons on change of the rows or columns values."""
          total_rows = int(self.rows_widget.get_value())
          total_columns = int(self.columns_widget.get_value())

          self.set_cmd(total_rows, total_columns)

     def build_layout(self):
          #Build the layout
          self.build_cmd()

     def reset_grid(self):
          self.name_widget.set_value("")
          total_rows = 1
          self.rows_widget.set_value("1")
          total_columns = 1
          self.columns_widget.set_value("1")

          self.set_cmd(total_rows, total_columns)
          self.__enable_grid_settings_modify()
          #Reset the parent frame
          self.reset_cmd()

     def reset_widgets(self):
          self.rows_widget.set_value("1")
          self.columns_widget.set_value("1")
          self.__enable_grid_settings_modify()

     def disable_grid_settings_modify(self):
          self.build_btn.configure(state="disabled")
          self.rows_widget.disable_combobox()
          self.columns_widget.disable_combobox()

     def __enable_grid_settings_modify(self):
          self.build_btn.configure(state="normal")
          self.rows_widget.enable_combobox()
          self.columns_widget.enable_combobox()

     def get_data(self):
          """Returns all entry widget data."""
          display_template_name = self.name_widget.get_value()
          number_of_rows = self.rows_widget.get_value()
          number_of_columns = self.columns_widget.get_value()

          return display_template_name, number_of_columns, number_of_rows

     def set_data(self, display_template_name, number_of_columns, number_of_rows):
          """Sets all entry widget data."""
          self.name_widget.set_value(display_template_name)
          self.rows_widget.set_value(number_of_columns)
          self.columns_widget.set_value(number_of_rows)
          self.disable_grid_settings_modify()
     
class Surface_Selector(ctk.CTkFrame):
     def __init__(self, parent, btn_cmd):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Create single row / colunn
          self.rowconfigure(0, weight=1)
          self.columnconfigure(0, weight=1)

          #Widget lists used for clearing the grid
          self.button_list = []
          self.frame_list = []
          self.total_surfaces = 0

          #Rows and columns
          self.total_columns = 2
          self.total_rows = 10
     

          #Display Areas List
          self.display_areas_list = range(1,21)

          #Button command
          self.btn_cmd = btn_cmd

          #Build the buttons
          self.build_buttons(20)

     def build_buttons(self, total_surfaces:int):
          """Builds a grid of display surface selection buttons."""
          #Clear previous grid if present
          for widget in self.frame_list:
               widget :ctk.CTkFrame
               widget.destroy()

          #Grid to hold buttons
          self.grid_frame = ctk.CTkFrame(self)
          self.grid_frame.grid(column=0, row=0, sticky="nsew")
          self.frame_list.append(self.grid_frame)

          #Build Tkinter Grid
          for i in range(self.total_rows+1):
               self.grid_frame.rowconfigure(i, weight=1, uniform="grid_y")
          for i in range(self.total_columns):
               self.grid_frame.columnconfigure(i, weight=1, uniform="grid_x")

          #Add the title
          title = ctk.CTkLabel(master=self.grid_frame, text="Display Surfaces", font=self.default_font)
          title.grid(column=0, row=0, sticky="ew", padx=10, pady=10, columnspan=self.total_columns)

          #Build the Button Grid
          current_row_index = 1
          current_column_index = 0
          current_display_area_index = 0

          for i in range(1, self.total_rows+1):
               for i in range(self.total_columns):
                    if current_display_area_index < total_surfaces:
                         current_display_area = self.display_areas_list[current_display_area_index]
                         btn = ctk.CTkButton(self.grid_frame, text=current_display_area, font=self.default_font, 
                                             command = (lambda display_area = current_display_area : self.btn_cmd(display_area)))
                         btn.grid(column=current_column_index, row=current_row_index, sticky="nsew", padx=5, pady=5)
                         current_column_index += 1
                         current_display_area_index +=1
                         #Add the button widget to the list
                         self.button_list.append(btn)

               current_row_index +=1
               current_column_index = 0

     def disable_buttons(self):
          for btn in self.button_list:
               btn : ctk.CTkButton
               btn.configure(state="disabled")

     def enable_buttons(self):
          for btn in self.button_list:
               btn : ctk.CTkButton
               btn.configure(state="normal")

class Widget_Selector(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Store a reference to the parent
          self.parent : ctk.CTkFrame = parent
     
          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Variables
          #self.total_columns = 2

          #Make a scrollable frame to hold widget items
          self.widget_frame = ctk.CTkScrollableFrame(self, orientation="horizontal", label_text="Display Widgets", label_font=self.default_font, height=300)
          self.widget_frame.pack(side="top", expand=1, fill="both")

          #Setup columns / rows for the frame
          self.widget_frame.rowconfigure(0, weight=1)    

          current_column = 0   

          #Button list
          self.buttons_list = []

          #Selected Widget
          self.selected_widget = ""

          #Make the widget buttons
          for widget_string in widget_paths_dict:
               image_path = widget_paths_dict[widget_string]

               #Open the image
               image = Image.open(image_path)

               #Resize the image to fit into button
               resized_image: Image.Image = resize_image_keep_aspect(image, 290, 290)

               widget_image = ctk.CTkImage(light_image=resized_image, dark_image=resized_image, size=(resized_image.width,resized_image.height))

               #Add a Column
               self.widget_frame.columnconfigure(current_column, weight=0, uniform="columns")

               #Add the button
               btn = ctk.CTkButton(self.widget_frame, image=widget_image, text="", 
                                   font=self.default_font, 
                                   width=290, 
                                   height=290,
                                   fg_color="black",
                                   command = (lambda current_widget_string = widget_string : self.__btn_cmd(current_widget_string)))
               btn.grid(column=current_column, row=0, sticky="ns", padx=5, pady=5)

               #Add the button widget to the button list
               self.buttons_list.append(btn)

               current_column += 1

     def __btn_cmd(self, widget_string:str):
          self.logger.info(f"Selected Widget: {widget_string}")
          #Set the currently selected widget string
          self.__set_selected_widget(widget_string)

     def enable_buttons(self):
          for btn in self.buttons_list:
               btn : ctk.CTkButton
               btn.configure(state="normal")

     def disable_buttons(self):
          for btn in self.buttons_list:
               btn : ctk.CTkButton
               btn.configure(state="disabled")

          #Clear the selected Widget
          self.__set_selected_widget("")

     def __set_selected_widget(self, widget_string):
          self.selected_widget = widget_string

     def get_selected_widget(self) -> str:
          """Returns the selected widget string."""
          return self.selected_widget

#-------------------------Diplay Instance Config-Widgets-------------------------
class Display_Instance_Config_Base_Frame(ctk.CTkFrame):
     """Container Frame to hold Display Instance Config Widgets and methods."""

     def __init__(self, parent, database_connection:DB):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Store a reference to the parent
          self.parent : BaseFrameNew = parent

          #Store a reference to the DB
          self.db : DB = database_connection
     
          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=1) 
          self.rowconfigure(0, weight=1)
          self.rowconfigure(0, weight=1)
               
          self.columnconfigure(0, weight=2)
          self.columnconfigure(1, weight=1)

          #Make the 4 frames

          self.display_preview_frame = Grid_Layout_Builder(self, None, self.raise_config_frame)
          self.display_preview_frame.grid(column=0, row=0, columnspan=1, rowspan=1, sticky="nsew")

          self.instance_settings_frame = Display_Instance_Settings(self, self.show_display_template_preview)
          self.instance_settings_frame.grid(column=1, row=0, columnspan=1, rowspan=1, sticky="nsew")

          #self.widget_settings_frame = Widget_Settings(self)
          #self.widget_settings_frame.grid(column=0, row=1, columnspan=2, rowspan=1, sticky="nsew")

          #Variables
          self.display_template_id : int = None
          self.config_frames_dict = {}

     def set_display_template_combobox_values(self, values_list:list):
          self.instance_settings_frame.set_display_template_combobox_values(values_list)

     def show_display_template_preview(self, event):
          """Shows a preview of the selected display template."""
          #Get the entry data
          instance_name, display_template_id, display_template_name = self.instance_settings_frame.get_data()

          #Query the database for the display template
          item_data_list = self.db.get_current_row_data("display_templates", "display_template_id", display_template_id)[0]
          self.logger.debug(f"Item data: {item_data_list}")

          db_display_template_id = item_data_list[0]
          db_display_template_name = item_data_list[1]
          number_of_columns = item_data_list[2]
          number_of_rows = item_data_list[3]
          layout_matrix = json.loads(item_data_list[4])

          #Set the display template id variable
          self.display_template_id = db_display_template_id

          #Get all rows matching the display template id
          display_surface_rows = self.db.get_current_row_data("display_surfaces", "display_template_id", display_template_id)
          self.logger.debug(f"Display Surface Rows: {display_surface_rows}")

          #Build the grid layout
          self.build_grid(number_of_rows, number_of_columns)
          self.display_preview_frame.render_display_layout(layout_matrix)

          #Clear any previous config frames
          self.clear_config_frames()

          #Add the widgets to the grid
          for row in display_surface_rows:
               display_surface_id = row[1]
               widget_string = row[2]
               self.display_preview_frame.set_display_area_widget(str(display_surface_id), widget_string)

               #Load the widget config frames into memory
               self.load_widget_config_frame(display_surface_id, widget_string)

     def build_grid(self, total_rows, total_columns):
          """Builds the display layout builder"""
          self.logger.debug("#######---Building Display Layout Builder Grid---#######")

          #Build the layout builder grid
          self.display_preview_frame.render_grid_layout_builder(total_columns, total_rows)

     def load_widget_config_frame(self, display_surface_id:int, widget_string:str):
          from display_widgets.config_frames.config_frames import get_config_frame
          
          self.logger.debug(f"Selected display surface: {display_surface_id}")

          #Look up the widget string for the selected display area
          self.logger.debug(f"Selected display surface widget string: {widget_string}")

          #Load the new frame and add to the config frames list
          config_frame = get_config_frame(self, widget_string, self.db, display_surface_id)
          config_frame.grid(column=0, row=1, columnspan=2, rowspan=1, sticky="nsew")
          self.config_frames_dict[display_surface_id] = config_frame

     def raise_config_frame(self, display_surface_id):
          self.logger.debug("Attempting to raise config frame...")
          self.logger.debug(f"Selected display surface: {display_surface_id}")
          config_frame = self.config_frames_dict.get(int(display_surface_id))
          config_frame :ctk.CTkFrame

          #Trigger the on_raise callback
          config_frame.on_raise_callback()

          #Raise the frame
          config_frame.tkraise()

     def get_data(self):
          """Retrieves all data and parses into JSON, returns [display_instance_name, config_json]"""
          from display_widgets.config_frames.config_frames import Config_Base_Frame

          #Get the instance name and selected display template
          display_instance_name, display_template_id, display_template_name = self.instance_settings_frame.get_data()

          #Varible used to state if config is valid
          valid_list = []

          #List ot hold config_frame data classes
          config_frame_dataclass_list = []

          #Retrieve the data from each config frame
          for display_surface_id in self.config_frames_dict:
               config_frame_widget : Config_Base_Frame = self.config_frames_dict[display_surface_id]

               #Tells you which widget the config relates to
               widget_string = config_frame_widget.get_widget_string()

               #Get the config for the widget
               config_frame_data_list : list = config_frame_widget.get_data()

               #Put all the data into a config_frame dataclass
               config_frame_dataclass : Config_Frame = Config_Frame(widget_string, display_surface_id, config_frame_data_list)

               #Add the dataclass to the config_frame_dataclass_list
               config_frame_dataclass_list.append(config_frame_dataclass)

               #Check config frame data is not empty
               for data in config_frame_data_list:
                    valid_list.append(validate_not_null(data))


          #Check the config is valid
          valid_config = False
          for valid in valid_list:
               if valid == True:
                    valid_config = True
               else:
                    valid_config = False
                    break

          return display_instance_name, display_template_id, config_frame_dataclass_list, valid_config

     def set_data(self, display_instance_name, display_template_id, config_frames_list:list):
          from display_widgets.config_frames.config_frames import Config_Base_Frame
          
          #Find the display template name from the DB
          display_template_name = self.db.get_1column_data("display_template_name", "display_templates", "display_template_id", display_template_id)[0]

          self.instance_settings_frame.set_data(display_instance_name, display_template_id, display_template_name)

          #Create the display preview and load the config frames
          self.show_display_template_preview(None)

          #Retrieve the data for each config frame
          for config_frame in config_frames_list:
               config_frame : Config_Frame
               display_surface_id = config_frame.display_surface_id

               #Get the config Frame widget
               config_frame_widget : Config_Base_Frame = self.config_frames_dict[display_surface_id]
               
               #Set the data
               config_frame_widget.set_data(config_frame.config_list)

     def __clear_preview_frame(self):
          """Sets the display preview frame back to the default"""
          self.build_grid(1,1)

     def clear_widgets(self):
          """Clears all entry data and resets widgets to defaults"""
          #Clear settigns frame data
          self.instance_settings_frame.clear_data()

          #Delete all config frames
          self.clear_config_frames()
          #Reset Preview frame
          self.__clear_preview_frame()

     def clear_config_frames(self):
          """Clears all config frames from the gui"""
          #Delete all config frames
          for display_surface_id in self.config_frames_dict:
               config_frame : ctk.CTkFrame = self.config_frames_dict.get(display_surface_id)
               config_frame.grid_forget()
               config_frame.destroy()

          #Clear the config frames dict     
          self.config_frames_dict = {}

class Display_Instance_Settings(ctk.CTkFrame):
     """Container Frame to hold Display Instance Config Widgets and methods."""
     def __init__(self, parent, display_template_callback):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Store a reference to the parent
          self.parent : ctk.CTkFrame = parent
     
          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Callbacks
          self.display_template_callback = display_template_callback

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=0) 
          self.rowconfigure(1, weight=0)
          self.rowconfigure(2, weight=0)
               
          self.columnconfigure(0, weight=1)
          self.columnconfigure(1, weight=1)

          self.name_entry = Title_Entry(self, "Display Instance Name:", 300)
          self.name_entry.grid(column=0, row=0, columnspan=2, sticky="nesw")

          self.display_template_combobox = Title_Combobox(self, "Display Template:", [], self.display_template_callback, 300)
          self.display_template_combobox.grid(column=0, row=1, columnspan=2, sticky="nesw")
          """
          reset_btn = ctk.CTkButton(self, text="Reset", font=self.default_font)
          reset_btn.grid(column=0, row=2, sticky="ew", columnspan=1, padx=5)

          self.select_btn = ctk.CTkButton(self, text="Select", font=self.default_font)
          self.select_btn.grid(column=1, row=2, sticky="ew", columnspan=1, padx=5)
          """
          
     def set_display_template_combobox_values(self, values_list:list):
          self.display_template_combobox.set_values(values_list)

     def get_data(self):
          """Returns entry data, [display_instance_name, display_template_id, display_template_name]"""
          instance_name = self.name_entry.get_value()
          display_template_id_name = self.display_template_combobox.get_value()
          if display_template_id_name != "":
               display_template_id = display_template_id_name.split(":")[0]
               display_template_name = display_template_id_name.split(":")[1]
          else:
               display_template_id = ""
               display_template_name = ""

          return instance_name, display_template_id, display_template_name
     
     def set_data(self, display_instance_name:str, display_template_id, display_template_name):
          self.name_entry.set_value(display_instance_name)
          self.display_template_combobox.set_value(f"{display_template_id}:{display_template_name}")
     
     def clear_data(self):
          self.name_entry.set_value("")
          self.display_template_combobox.set_value("")

#-------------------------GPIO Config-Widgets-------------------------

class GPIO_Pin_Config(ctk.CTkFrame):
     """Makes a row with a title on the left and three radio button selections on right to configure a GPIO pin as Disabled, Input or Output."""
     def __init__(self, parent):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Configure Frame Rows and Columns
          self.columnconfigure(0, weight=0, uniform="label", minsize=100)
          self.columnconfigure(1, weight=0, uniform="rad_btn_column")
          self.columnconfigure(2, weight=0, uniform="rad_btn_column")
          self.columnconfigure(3, weight=0, uniform="rad_btn_column")
          self.columnconfigure(4, weight=0, uniform="capability")

          self.configure(fg_color="#494949")

          #Variable to store the number of radio button rows
          self.number_of_rows = 0

          #Blank list to hold radio button widgets and title widgets
          self.radio_button_widgets_list= []
          self.row_title_widget_list = []

     def build_rows(self, start_pin_index, end_pin_index, start_input_only_index, end_input_only_index):

          #Clear the widgets before rebuilding
          self.clear_config_frame()

          #Offset used to shift radio button rows down for other widgets above
          offset = 1

          #Make Titles for each row
          column_title_1 = ctk.CTkLabel(self, text=f"Disabled", font=self.default_font)
          column_title_1.grid(column=1, row=0, sticky="")
          column_title_2 = ctk.CTkLabel(self, text=f"Input", font=self.default_font)
          column_title_2.grid(column=2, row=0, sticky="")
          column_title_3 = ctk.CTkLabel(self, text=f"Output", font=self.default_font)
          column_title_3.grid(column=3, row=0, sticky="")
          column_title_4 = ctk.CTkLabel(self, text=f"Capability", font=self.default_font)
          column_title_4.grid(column=4, row=0, sticky="")

          #Calculate number of rows
          self.number_of_rows = (end_pin_index - start_pin_index)

          #Variable to increment pin_index with each loop iteration
          working_pin_index = start_pin_index

          for i in range(offset, self.number_of_rows + offset):

               #Make a Row
               self.rowconfigure(i, weight=0)
               
               #Make the row title
               row_title = ctk.CTkLabel(self, text=f"Pin {working_pin_index}", font=self.default_font, anchor="w")
               row_title.grid(column=0, row=i, sticky="ew", pady=5, padx=10)

               #Make the radio buttons
               radio_buttons = GPIO_Radio_Buttons(self, working_pin_index)
               radio_buttons.grid(column=1, row=i, sticky="ew", pady=5, columnspan=4)

               #Add the widgets to the list
               self.row_title_widget_list.append(row_title)
               self.radio_button_widgets_list.append(radio_buttons)

               #Set the Capability Label
               if working_pin_index in range(int(start_input_only_index), int(end_input_only_index)):
                    radio_buttons.set_capability("Input")
                    #Disable Output Selection
                    radio_buttons.disable_radio_button(2)
               else:
                    radio_buttons.set_capability("Input/Output")

               #Add 1 to the working pin_index
               working_pin_index += 1

     def get_data(self) -> list:
          """Returns the radio button selections in format [[pin_index, pin_mode],...]"""
          pin_config_list = []

          for radio_button_widget in self.radio_button_widgets_list:
               radio_button_widget : GPIO_Radio_Buttons
               selection = radio_button_widget.get_selection()
               pin_index = radio_button_widget.get_pin_index()
               pin_config_list.append([pin_index, selection])

          return pin_config_list
     
     def set_data(self, pin_config_list:list):
          #Get the size of the pin config list
          #number_of_pins = len(pin_config_list)

          for i in range(self.number_of_rows):
               radio_button_widget = self.radio_button_widgets_list[i]
               radio_button_widget : GPIO_Radio_Buttons
               selection = pin_config_list[i][2]
               radio_button_widget.set_selection(selection)

     def set_default_selections(self):
          """Sets the radio buttons back to their default selection of disabled"""
          for i in range(self.number_of_rows):
               radio_button_widget = self.radio_button_widgets_list[i]
               radio_button_widget : GPIO_Radio_Buttons
               radio_button_widget.set_selection("disabled")

     def clear_config_frame(self):
          """Clears the gpio config frame of all widgets"""
          self.radio_button_widgets_list.reverse()
          for radio_button_widget in self.radio_button_widgets_list:
               radio_button_widget : GPIO_Radio_Buttons
               radio_button_widget.grid_forget()
               radio_button_widget.destroy()

          self.row_title_widget_list.reverse()
          for title_widget in self.row_title_widget_list:
               title_widget : GPIO_Radio_Buttons
               title_widget.grid_forget()
               title_widget.destroy()
               
          self.radio_button_widgets_list = []
          self.row_title_widget_list = []
          self.number_of_rows = 0

class GPIO_Radio_Buttons(ctk.CTkFrame):
     def __init__(self, parent, pin_index:int):
          super().__init__(parent)

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Configure Frame Rows and Columns
          self.columnconfigure(0, weight=0, uniform="column")
          self.columnconfigure(1, weight=0, uniform="column")
          self.columnconfigure(2, weight=0, uniform="column")
          self.columnconfigure(3, weight=0, uniform="column")

          self.rowconfigure(0, weight=0)

          #Make a variable for the radio buttons and set the default value
          self.gpio_mode_var = StringVar()
          self.gpio_mode_var.set("disabled")

          #make a variable to store the pin index
          self.pin_index = pin_index

          #Make the radio buttons
          rad_btn_0 = ctk.CTkRadioButton(self, text="", variable=self.gpio_mode_var, value="disabled", fg_color="red", width=22, height=22)
          rad_btn_0.grid(column=0, row=0, sticky="")
          rad_btn_1 = ctk.CTkRadioButton(self, text="", variable=self.gpio_mode_var, value="input", fg_color="purple", width=22, height=22)
          rad_btn_1.grid(column=1, row=0, sticky="")
          rad_btn_2 = ctk.CTkRadioButton(self, text="", variable=self.gpio_mode_var, value="output", fg_color="orange", width=22, height=22)
          rad_btn_2.grid(column=2, row=0, sticky="")

          #Make a variable to store the capability of a pin
          self.capability_var = StringVar() 

          #Make the capability Label
          self.capability_label = ctk.CTkLabel(self, font=self.default_font, anchor="w", textvariable=self.capability_var, width=115)
          self.capability_label.grid(column=3, row=0, sticky="w", padx=5)

          #List to hold radio button widgets
          self.radio_button_list = [rad_btn_0, rad_btn_1, rad_btn_2]

     def disable_radio_button(self, button_index):
          """Disables selection of a radio button given it's index, valid indexes are 0,1,2, left to right."""
          rad_btn :ctk.CTkRadioButton = self.radio_button_list[button_index]
          rad_btn.configure(state = "DISABLED")

     def enable_radio_button(self, button_index):
          """Enables selection of a radio button given it's index, valid indexes are 0,1,2, left to right."""
          rad_btn :ctk.CTkRadioButton = self.radio_button_list[button_index]
          rad_btn.configure(state = "ENABLED")

     def get_selection(self) -> str:
          """Returns the current selection radio button value."""
          return self.gpio_mode_var.get()
     
     def set_selection(self, selection:str):
          """Checks a radio button based on the selection value. Valid seleciton values are: disabled, input, output."""

          if selection == "disabled":
               self.gpio_mode_var.set("disabled")
          elif selection == "input":
               self.gpio_mode_var.set("input")
          elif selection == "output":
               self.gpio_mode_var.set("output")
          else:
               self.logger.debug("Invalid Radio Button selection")

     def set_capability(self, capability:str):
          """Sets the value of the capability label."""
          self.capability_var.set(capability)

     def get_pin_index(self) -> int:
          """Returns the pin index"""
          return self.pin_index

#-------------------------Device Config-Widgets-------------------------

class Control_Buttons(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)

          #Store a reference to the parent
          self.parent = parent #Parent is Device_Config

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Configure Frame Rows and Columns
          self.columnconfigure(0, weight=1, uniform="column")
          self.columnconfigure(1, weight=1, uniform="column")
          self.columnconfigure(2, weight=1, uniform="column")

          self.rowconfigure(0, weight=0)
          self.rowconfigure(1, weight=0)

          #Commands
          self.__reload_device_display = None
          self.__identify_device = None

          #Widgets
          title_label = ctk.CTkLabel(master=self, text="Device Control", font=self.default_font, pady=15)
          title_label.grid(column=0, row=0, columnspan=3, sticky="ew")

          self.reload_display_btn = ctk.CTkButton(master=self, text="Reload Display Template", font=self.default_font, fg_color="green", command=lambda:self.__reload_device_display())
          self.reload_display_btn.grid(column=0, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

          self.identify_btn = ctk.CTkButton(master=self, text="Identify Device", font=self.default_font, fg_color="green", command=lambda state=True :self.__identify_device(state) )
          self.identify_btn.grid(column=1, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

          self.exit_identify_btn = ctk.CTkButton(master=self, text="Exit Identify Device", font=self.default_font, fg_color="green", command=lambda state=False :self.__identify_device(state) )
          self.exit_identify_btn.grid(column=2, row=1, sticky="ns", columnspan=1, rowspan=1, pady=20)

          #Disabel the buttons by default
          self.disable_buttons()

     def set_reload_cmd(self, reload_cmd):
          self.__reload_device_display = reload_cmd

     def set_identify_cmd(self, identify_cmd):
          self.__identify_device = identify_cmd

     def disable_buttons(self):
          """Disables the buttons making them darker and not clickable."""
          self.reload_display_btn.configure(state = "disabled")
          self.identify_btn.configure(state = "disabled")
          self.exit_identify_btn.configure(state = "disabled")

     def enable_buttons(self):
          self.reload_display_btn.configure(state = "normal")
          self.identify_btn.configure(state = "normal")
          self.exit_identify_btn.configure(state = "normal")

#-------------------------Server Config-Widgets-------------------------

class Server_Config_Frame(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)

          #Store a reference to the parent
          self.parent = parent #Parent is Server_Config

          #Setup Logging
          self.logger = logging.getLogger(__name__)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Configure Frame Rows and Columns
          self.columnconfigure(0, weight=1, uniform="column")
          self.rowconfigure(0, weight=0)

          #Variables
          self.server_ip_var = StringVar()

          #DB reference must be set before using this class
          self.db = None

          self.__add_widgets()

     def __add_widgets(self):
          #------------------------------MAIN FRAME-IP CONFIG FRAME--------------------------------------------------
          #Create a frame to contain settings server ip
          self.ip_setup_frame = ctk.CTkFrame(self)
          self.ip_setup_frame.grid(column=0, row=0, columnspan=1, sticky="nsew")

          #Setup Columns / rows for self.ip_setup_frame

          self.ip_setup_frame.columnconfigure(0, weight=0, pad=20)
          self.ip_setup_frame.columnconfigure(1, weight=1, pad=20)

          for i in range(29):
               self.ip_setup_frame.rowconfigure(i, weight=0, pad=10)

          #------------------------------IP CONFIG FRAME WIDGETS--------------------------------------------------

          ip_label = ctk.CTkLabel(master=self.ip_setup_frame, text="Server IP", font=self.default_font)
          ip_label.grid(column=0, row=0, sticky="w", padx=20)

          self.ip_combobox = ctk.CTkComboBox(master=self.ip_setup_frame, state="readonly", variable=self.server_ip_var, font=self.default_font, dropdown_font=self.default_font)
          self.ip_combobox.grid(column=1, row=0, columnspan =1, sticky="ew", padx=20)

          #Create a frame to contain the buttons
          self.button_frame = ctk.CTkFrame(self.ip_setup_frame)
          self.button_frame.grid(column=0, row=1, columnspan=2, sticky="ew")

          self.button_frame.columnconfigure(0, weight=1, pad=20, uniform="button")
          self.button_frame.columnconfigure(1, weight=1, pad=20, uniform="button")
          self.button_frame.rowconfigure(0, weight=0, pad=20)

          #Save Button
          self.save_btn = ctk.CTkButton(master=self.button_frame, text="Save", fg_color="green", command=lambda:self.__save_ip_entry_data(), font=self.default_font)
          self.save_btn.grid(column=1, row=0, sticky="ns", columnspan=1, rowspan=1, pady=20)
          
          #Back Button
          self.back_btn = ctk.CTkButton(master=self.button_frame, text="Back", fg_color="red", command=lambda:self.__show_server_config_frame(), font=self.default_font)
          self.back_btn.grid(column=0, row=0, sticky="ns", columnspan=1, rowspan=1, pady=20)
          
          #------------------------------MAIN FRAME-SERVER CONFIG FRAME--------------------------------------------------
          
          #Create a frame to contain settings about the individual client device
          self.server_config_frame = ctk.CTkFrame(self)
          self.server_config_frame.grid(column=0, row=0, columnspan=1, sticky="nsew")

          #Setup Columns / rows for self.server_config_frame

          self.server_config_frame.columnconfigure(0, weight=0, pad=20)
          self.server_config_frame.columnconfigure(1, weight=1, pad=20)
          self.server_config_frame.columnconfigure(2, weight=1, pad=20)

          for i in range(29):
               self.server_config_frame.rowconfigure(i, weight=0, pad=10)

          self.frames_list = [self.server_config_frame, self.ip_setup_frame]

          #------------------------------SERVER CONFIG FRAME WIDGETS--------------------------------------------------
          initialise_label = ctk.CTkLabel(master=self.server_config_frame, text="Initialise Database", font=self.default_font)
          initialise_label.grid(column=0, row=0, sticky="w", padx=20)

          initialise_btn = ctk.CTkButton(master=self.server_config_frame, text="Initialise", command= lambda:(self.__initialise_database_warn()), font=self.default_font)
          initialise_btn.grid(column=2, row=0, columnspan =1, sticky="ew", padx=20)

          backup_label = ctk.CTkLabel(master=self.server_config_frame, text="Backup Configuration", font=self.default_font)
          backup_label.grid(column=0, row=1, sticky="w", padx=20)

          backup_btn = ctk.CTkButton(master=self.server_config_frame, text="Backup", command= lambda:(self.__backup_database()), font=self.default_font)
          backup_btn.grid(column=2, row=1, columnspan =1, sticky="ew", padx=20)

          restore_label = ctk.CTkLabel(master=self.server_config_frame, text="Restore Configuration", font=self.default_font)
          restore_label.grid(column=0, row=2, sticky="w", padx=20)

          restore_btn = ctk.CTkButton(master=self.server_config_frame, text="Restore", command= lambda:(self.__restore_database()), font=self.default_font)
          restore_btn.grid(column=2, row=2, columnspan =1, sticky="ew", padx=20)

          ip_label = ctk.CTkLabel(master=self.server_config_frame, text="Set Server IP", font=self.default_font)
          ip_label.grid(column=0, row=3, sticky="w", padx=20)

          ip_btn = ctk.CTkButton(master=self.server_config_frame, text="IP Settings", command= lambda:(self.__show_ip_config_frame()), font=self.default_font)
          ip_btn.grid(column=2, row=3, columnspan =1, sticky="ew", padx=20)

     def __initialise_database_warn(self):
        answer = messagebox.askokcancel("!DANGER! Database Initialisation !DANGER!", "Are you sure you want to initialise the Database? Doing so will clear all data!")
        if answer == True:
            self.logger.info("User confirmed database is to be initialised!")
            self.db.initialise_database()
            initialised_program_exiting_message()
            exit(0)
        else:
            self.logger.info("User aborted Database Initialisation")

     def __backup_database(self):
          try:
               #Copy the current working database to a seperat file
               self.db.backup_db()
               #Open a browser window to copy the backup file to external location
               self.logger.info("Asking user to specify backup save location.")
               path = filedialog.asksaveasfilename()
               #Copy the backup file to the chosen location
               self.logger.info("Copying backup file to user specified path.")
               shutil.copy("./database/backup_oatis_db", path)
               self.logger.info("Backup Complete")
               messagebox.showinfo("Database Saved", "The database has been successfully backed up.")
          except FileNotFoundError:
               self.logger.info("Backup Unsuccessful")
               messagebox.showinfo("Database Backup Fail", "The database was not able to be backed up, a valid path was not selected.")
          except Exception as e:
               self.logger.info("Backup Unsuccessful")
               messagebox.showinfo("Database Backup Fail", f"The database was not able to be backed up, reason:{e}")

     def __restore_database(self):
          answer = messagebox.askokcancel("Restore Database Backup", "Are you sure you wish to restore the database?\n Doing so will completley erase the current database.")

          if answer == True:
               #Get the path to the backup file from the user
               path = filedialog.askopenfilename()
               self.logger.info(path)
               #If hte path is not empty attempt to restore
               if path != "":
                    try:
                         #Close the connection to the database
                         self.db.close_connection()
                         #Rename to current db file name.old
                         self.logger.info("Renaming current database oatis_db.old")
                         os.rename("database/oatis_db", "database/oatis_db.old")
                         #Copy the file specified by the user into the current working dir and rename oatis_db
                         self.logger.info("Importing backup db and renaming oatis_db")
                         shutil.copy(path, "./database/oatis_db")
                         messagebox.showinfo("Restore Database Backup", "Database Successfully Restored, please restart the application.")
                         exit(0)
                    except Exception as e:
                         self.logger.info("Restore Unsuccessful")
                         messagebox.showinfo("Database Restore Fail", f"The database was not able to be restored, reason:{e}")
                    finally:
                         #Reconect to the database
                         self.db.connect()
               else:
                    self.logger.debug("User aborted database restore.")
          else:
               self.logger.debug("User aborted database restore.")
               
     def __raise_frame(self, frame_number):
          frame = self.frames_list[frame_number]
          self.logger.debug(f"Raising frame:{frame}")
          frame.tkraise()

     def __show_ip_config_frame(self):
          self.__populate_ip_combobox()
          self.__raise_frame(1)

     def __show_server_config_frame(self):
          self.__raise_frame(0)

     def __save_ip_entry_data(self):
          server_ip = self.server_ip_var.get()

          settings_dict = {"server_ip":server_ip}

          write_dict_to_file(settings_dict, "server/settings.json")
          
          self.__show_server_config_frame()

     def __populate_ip_combobox(self):
          #Read Settings file
          settings_dict = open_json_file("server/settings.json")
          #Only set ip's if settings file exists - otherwise defaults are used
          if settings_dict != False:
               self.server_ip_var.set(settings_dict["server_ip"])
               
          ip_list=get_machine_ip()
          self.ip_combobox.configure(values = ip_list)


     def set_db_reference(self, database_instance):
          self.db = database_instance
