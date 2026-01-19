from customtkinter import CTkFrame
from modules.gui_templates import Title_Entry
from modules.gui_templates import Title_Combobox
from modules.gui_templates import Title_Colour_Picker
from database.database_connection import DB

def get_config_frame(parent, widget_string, database_connection, display_surface_id):
    """Returns a config frame given a widget string."""
    config_frame_dict = {
        "indicator" : Indicator_Config(parent, database_connection, display_surface_id, widget_string),
        "studio_clock" : Studio_Clock_Config(parent, database_connection, display_surface_id, widget_string),
        "analogue_clock" : Analogue_Clock_Config(parent, database_connection, display_surface_id, widget_string),
        "digital_clock" : Digital_Clock_Config(parent, database_connection, display_surface_id, widget_string),
        "static_text" : Static_Text_Config(parent, database_connection, display_surface_id, widget_string),
        "static_image" : Static_Image_Config(parent, database_connection, display_surface_id, widget_string),
        "stacked_image" : Stacked_Image_Config(parent, database_connection, display_surface_id, widget_string),
        "top_banner" : Top_Banner_Config(parent, database_connection, display_surface_id, widget_string)
    }

    return config_frame_dict[widget_string]

class Config_Base_Frame(CTkFrame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent)

        #DB
        self.db = database_connection

        #Make a single column
        self.columnconfigure(0, weight=1)

        #Used to hold widget objects for packing
        self.widget_list = []

        #On_Raise function
        self.raise_function = None

        #Variables
        self.widget_string = widget_string
        self.display_surface_id = display_surface_id

        #Used for clock config
        self.timezones_list = [
            "UTC-12: Baker Island",
            "UTC-11: Midway Islands",
            "UTC-10: Hawaii",
            "UTC-9: Alaska",
            "UTC-8: Los Angeles (PST)",
            "UTC-7: Denver (MST)",
            "UTC-6: Chicago (CST)",
            "UTC-5: New York (EST)",
            "UTC-4: Santo Domingo",
            "UTC-3: Rio de Janeiro",
            "UTC-2: Fernando de Noronha",
            "UTC-1: Azores",
            "UTC+0: London (GMT)",
            "UTC+1: Paris, Berlin",
            "UTC+2: Cairo",
            "UTC+3: Jeddah, Moscow",
            "UTC+3.5: Tehran",
            "UTC+4: Dubai",
            "UTC+4.5: Kabul",
            "UTC+5: Karachi",
            "UTC+5.5: Delhi",
            "UTC+5.75: Kathmandu",
            "UTC+6: Dhaka",
            "UTC+6.5: Yangon",
            "UTC+7: Bangkok, Jakarta",
            "UTC+8: Beijing, Taipei, Singapore, Perth",
            "UTC+9: Tokyo, Seoul",
            "UTC+9.5: Adelaide",
            "UTC+10: Sydney",
            "UTC+11: Nouméa",
            "UTC+12: Wellington, Fiji",
            "UTC+13: Nuku'alofa",
            "UTC+14: Kiritimati"
        ]

    def grid_widgets(self):
        """Adds the widgets to the tkinter grid."""
        number_of_rows = len(self.widget_list)

        column_index=0
        row_index=0
        for widget in self.widget_list:
            widget.grid(column=column_index, row=row_index, sticky="new")
            row_index += 1

    #Triggered when frame raised
    def on_raise_callback(self):
        if self.raise_function != None:
            self.raise_function()

    def set_on_raise_callback(self, on_raise_callback):
        self.raise_function = on_raise_callback

    def get_display_surface_id(self):
        return self.display_surface_id
    
    def get_widget_string(self):
        return self.widget_string

    def set_data(self, data_list:list):
        "Set the data in the entry widgets for the config_frame, in order, top to bottom."
        i=0
        data_list_length = len(data_list)
        for widget in self.widget_list:
            if i <= data_list_length:
                widget.set_value(data_list[i])
                i+=1
            else:
                break

    def get_data(self) -> list:
        "Returns all the data from each entry widget in the config frame"
        data_list = []

        for widget in self.widget_list:
            widget_data = widget.get_value()
            data_list.append(widget_data)

        return data_list

class Indicator_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Indicator Label
        self.label_text = Title_Entry(self, "Indicator Label", 350)
        self.widget_list.append(self.label_text)
        #Indicator Colour
        self.on_colour = Title_Colour_Picker(self, "On Colour")
        self.widget_list.append(self.on_colour)
        #Flash Enable
        self.flash_enable = Title_Combobox(self, "Flash", ["Yes", "No"], None, 350)
        self.widget_list.append(self.flash_enable)
        #Input Logic
        self.input_logic = Title_Combobox(self, "Input Logic", [], None, 350)
        self.widget_list.append(self.input_logic)

        #Add the widgets to the grid
        self.grid_widgets()

        self.set_on_raise_callback(self.update_input_logic_combobox_values)

    def update_input_logic_combobox_values(self):
        values_list = []

        rows = self.db.get_2column_data("input_logic_id", "input_logic_name", "input_logics")

        for row in rows:
            input_logic_id = row[0]
            input_logic_name = row[1]
            input_logic_id_name = f"{input_logic_id}:{input_logic_name}"
            values_list.append(input_logic_id_name)

        self.input_logic.set_values(values_list)

class Studio_Clock_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string
                         )

        #Timezone
        self.timezone = Title_Combobox(self, "Timezone", self.timezones_list, None, 350)
        self.widget_list.append(self.timezone)
        #Display Timezone label
        self.timezone_label = Title_Combobox(self, "Show Timezone label", ["Yes", "No"], None, 350)
        self.widget_list.append(self.timezone_label)
        #Legend Colour
        self.legend_colour = Title_Colour_Picker(self, "Legend Colour")
        self.widget_list.append(self.legend_colour)

        #Add the widgets to the grid
        self.grid_widgets()

class Analogue_Clock_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Timezone
        self.timezone = Title_Combobox(self, "Timezone", self.timezones_list, None, 350)
        self.widget_list.append(self.timezone)
        #Display Timezone label
        self.timezone_label = Title_Combobox(self, "Show Timezone label", ["Yes", "No"], None, 350)
        self.widget_list.append(self.timezone_label)
        #Clock Face Colour
        self.clock_face_colour = Title_Colour_Picker(self, "Clock Face Colour")
        self.widget_list.append(self.clock_face_colour)
        #Legend Colour
        self.legend_colour = Title_Colour_Picker(self, "Legend Colour")
        self.widget_list.append(self.legend_colour)
        #Hours Hand Colour
        self.hours_hand_colour = Title_Colour_Picker(self, "Hours Hand Colour")
        self.widget_list.append(self.hours_hand_colour)
        #Minutes Hand Colour
        self.minutes_hand_colour = Title_Colour_Picker(self, "Minutes Hand Colour")
        self.widget_list.append(self.minutes_hand_colour)
        #Seconds Hand Colour
        self.seconds_hand_colour = Title_Colour_Picker(self, "Seconds Hand Colour")
        self.widget_list.append(self.seconds_hand_colour)
        #Smooth tick
        self.smooth_tick = Title_Combobox(self, "Smooth Tick", ["Yes", "No"], None, 350)
        self.widget_list.append(self.smooth_tick)

        #Add the widgets to the grid
        self.grid_widgets()

class Digital_Clock_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Timezone
        self.timezone = Title_Combobox(self, "Timezone", self.timezones_list, None, 350)
        self.widget_list.append(self.timezone)
        #Display Timezone label
        self.timezone_label = Title_Combobox(self, "Show Timezone label", ["Yes", "No"], None, 350)
        self.widget_list.append(self.timezone_label)
        #Time Format
        self.time_format = Title_Combobox(self, "Time Format", ["24 Hour", "12 Hour"], None, 350)
        self.widget_list.append(self.time_format)
        #Text Colour
        self.legend_colour = Title_Colour_Picker(self, "Text Colour")
        self.widget_list.append(self.legend_colour)

        #Add the widgets to the grid
        self.grid_widgets()

class Static_Text_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Label Text
        self.label_text = Title_Entry(self, "Label Text:", 350)
        self.widget_list.append(self.label_text)
        #Text Colour
        self.text_colour = Title_Colour_Picker(self, "Text Colour:")
        self.widget_list.append(self.text_colour)
        #Text Size Mode
        self.text_size_mode = Title_Combobox(self, "Text Size Mode:", ["Auto", "Manual"], self.text_size_mode_callback, 350)
        self.widget_list.append(self.text_size_mode)
        #Text Size
        self.text_size = Title_Entry(self, "Text Size:", 350)
        self.widget_list.append(self.text_size)

        #Add the widgets to the grid
        self.grid_widgets()

    def text_size_mode_callback(self, value):
        if value == "Auto":
            self.text_size.disable_entry()
            self.text_size.set_value("Auto")
        else:
            self.text_size.enable_entry()
            self.text_size.set_value("")



class Static_Image_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Image ID
        self.image = Title_Combobox(self, "Image:", [], None, 350)
        self.widget_list.append(self.image)

        #Add the widgets to the grid
        self.grid_widgets()

        self.set_on_raise_callback(self.update_image_combobox_values)

    def update_image_combobox_values(self):
        values_list = []

        rows = self.db.get_2column_data("image_id", "image_name", "images")

        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_id_name = f"{image_id}:{image_name}"
            values_list.append(image_id_name)

        self.image.set_values(values_list)

class Stacked_Image_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Image Stack ID
        self.image_stack = Title_Combobox(self, "Image Stack:", [], None, 350)
        self.widget_list.append(self.image_stack)

        #Add the widgets to the grid
        self.grid_widgets()

        self.set_on_raise_callback(self.update_logo_combobox_values)

    def update_logo_combobox_values(self):
        values_list = []

        rows = self.db.get_2column_data("image_id", "image_name", "images")

        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_id_name = f"{image_id}:{image_name}"
            values_list.append(image_id_name)

        self.image_stack.set_values(values_list)

class Top_Banner_Config(Config_Base_Frame):
    def __init__(self, parent, database_connection:DB, display_surface_id, widget_string:str):
        super().__init__(parent, database_connection, display_surface_id, widget_string)

        #Timezone
        self.logo = Title_Combobox(self, "Logo", [], None, 350)
        self.widget_list.append(self.logo)

        #Add the widgets to the grid
        self.grid_widgets()

        self.set_on_raise_callback(self.update_logo_combobox_values)

    def update_logo_combobox_values(self):
        values_list = []

        rows = self.db.get_2column_data("image_id", "image_name", "images")

        for row in rows:
            image_id = row[0]
            image_name = row[1]
            image_id_name = f"{image_id}:{image_name}"
            values_list.append(image_id_name)

        self.logo.set_values(values_list)
        
    



        

        