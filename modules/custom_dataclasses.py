from dataclasses import dataclass
from typing import Optional
from tkinter import StringVar
from customtkinter import CTkComboBox
##-------------------------DATACLASSES-------------------------
@dataclass
class Display_Template:
     """Class to hold all data for a display template when saving. Used with Display Builder base Frame"""
     display_template_name:str
     number_of_columns:int
     number_of_rows:int
     layout_matrix:list
     display_area_dict:dict

@dataclass
class Input_Row:
     """Used with Input Frame"""
     title:str
     widget_type:str
     validation_function:str
     #widget:Optional[object] = None
     custom_widget_titles:Optional[list] = None

@dataclass
class Entry_Widget_Data:
     """Used with Input Frame"""
     type:str
     input_widget:CTkComboBox
     id_values:list
     name_values:list
     string_var:StringVar
     validation_function:str

@dataclass
class Config_Frame:
     """Used with Display Instances"""
     widget_string:str
     display_surface_id:str
     config_list:list