import customtkinter as ctk
from tkinter import colorchooser
from tkinter import StringVar
from tkinter import filedialog
from tkinter import ttk
from PIL import Image
from config_tool.global_variables import *
import logging
from database.database_connection import DB
from config_tool.message_boxes import Message_Boxes


class IndicatorTitle(ctk.CTkFrame):
     def __init__(self, parent, label_text):
          super().__init__(parent)

          #Set column / rowspanning for frame
          self.rowconfigure(0, weight=0)
          self.rowconfigure(1, weight=0)
          for i in range (4):
               self.columnconfigure(i, weight=1)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          self.master = parent

          #GUI Variables
          self.text = ctk.StringVar()
          self.flash = ctk.StringVar()
          self.colour = ctk.StringVar()

          horizontal_padding = 20

          #Widgets
          title1_label = ctk.CTkLabel(master=self, text="Indicator Label", font=self.default_font)
          title1_label.grid(column=1, row=0, sticky="nsew", padx=10)

          title2_label = ctk.CTkLabel(master=self, text="Flash Enable", font=self.default_font)
          title2_label.grid(column=2, row=0, sticky="nsew", padx=10)

          title3_label = ctk.CTkLabel(master=self, text="Indicator Colour", font=self.default_font)
          title3_label.grid(column=3, row=0, sticky="nsew", padx=10)

          indicator_1_label = ctk.CTkLabel(master=self, text=label_text, font=self.default_font)
          indicator_1_label.grid(column=0, row=1, sticky="nsew", padx=horizontal_padding)

          indicator_1_text_entry = ctk.CTkEntry(master=self, textvariable=self.text, font=self.default_font)
          indicator_1_text_entry.grid(column=1, row=1, sticky="nsew", padx=horizontal_padding)
          

          indicator_1_flash_cbox = ctk.CTkComboBox(master=self, values=["True", "False"], state="readonly", variable=self.flash, font=self.default_font, dropdown_font=self.default_font)
          indicator_1_flash_cbox.grid(column=2, row=1, sticky="nsew", padx=horizontal_padding)

          self.indicator_1_colour_btn = ctk.CTkButton(master=self, text="Click to Choose a colour", command=self.choose_colour, width=200, font=self.default_font)
          self.indicator_1_colour_btn.grid(column=3, row=1, sticky="ns", padx=horizontal_padding)

     def choose_colour(self):
          #Generate a colour picker window returning the hex value of the colour picked
          rdg, hex_colour = colorchooser.askcolor(title="Pick an Indicator Colour", )
          self.indicator_1_colour_btn.configure(text=hex_colour, fg_color=hex_colour)
          self.colour.set(hex_colour)
          self.update()

     def get_inputs(self):
          return self.text.get(), self.flash.get(), self.colour.get()
     
     def set_inputs(self, text, flash_enable, colour):
          self.text.set(text)
          self.flash.set(flash_enable)
          self.colour.set(colour)
          self.indicator_1_colour_btn.configure(text=colour, fg_color=colour)
     
     def clear_inputs(self):
          print(self.indicator_1_colour_btn._fg_color)
          self.text.set("")
          self.flash.set("")
          self.colour.set("")
          self.indicator_1_colour_btn.configure(text="Click to Choose a colour", fg_color='#1F6AA5')    


class IndicatorSettings(ctk.CTkFrame):
     def __init__(self, parent, label_text):
          super().__init__(parent)

          #Set column / rowspanning for frame
          self.rowconfigure(0, weight=0)
          for i in range (4):
               self.columnconfigure(i, weight=1)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          self.master = parent

          #GUI Variables
          self.text = ctk.StringVar()
          self.flash = ctk.StringVar()
          self.colour = ctk.StringVar()

          horizontal_padding = 20

          #Widgets
          indicator_1_label = ctk.CTkLabel(master=self, text=label_text, font=self.default_font)
          indicator_1_label.grid(column=0, row=0, sticky="nsew", padx=horizontal_padding)

          indicator_1_text_entry = ctk.CTkEntry(master=self, textvariable=self.text, font=self.default_font)
          indicator_1_text_entry.grid(column=1, row=0, sticky="nsew", padx=horizontal_padding)
          

          indicator_1_flash_cbox = ctk.CTkComboBox(master=self, values=["True", "False"], state="readonly", variable=self.flash, font=self.default_font, dropdown_font=self.default_font)
          indicator_1_flash_cbox.grid(column=2, row=0, sticky="nsew", padx=horizontal_padding)

          self.indicator_1_colour_btn = ctk.CTkButton(master=self, text="Click to Choose a colour", command=self.choose_colour, width=350, font=self.default_font)
          self.indicator_1_colour_btn.grid(column=3, row=0, sticky="ns", padx=horizontal_padding)

     def choose_colour(self):
          #Generate a colour picker window returning the hex value of the colour picked
          rdg, hex_colour = colorchooser.askcolor(title="Pick an Indicator Colour", )
          self.indicator_1_colour_btn.configure(text=hex_colour, fg_color=hex_colour)
          self.colour.set(hex_colour)
          self.update()

     def get_inputs(self):
          return self.text.get(), self.flash.get(), self.colour.get()
     
     def set_inputs(self, text, flash_enable, colour):
          self.text.set(text)
          self.flash.set(flash_enable)
          self.colour.set(colour)
          self.indicator_1_colour_btn.configure(text=colour, fg_color=colour)
     
     def clear_inputs(self):
          print(self.indicator_1_colour_btn._fg_color)
          self.text.set("")
          self.flash.set("")
          self.colour.set("")
          self.indicator_1_colour_btn.configure(text="Click to Choose a colour", fg_color='#1F6AA5')

class LogoPicker(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #Variables
          self.logo_path_var = StringVar()

          #Setup columns / rows for the frame
          self.rowconfigure(0, weight=0)
          self.rowconfigure(1, weight=0)
          for i in range(2):
               self.columnconfigure(i, weight=1)


          self.logo_preview_label = ctk.CTkLabel(master=self, text="Logo Preview", font=self.default_font, width=200, height=50, bg_color="black")
          self.logo_preview_label.grid(column=0, row=0, columnspan =1, sticky="nsew", padx=20)

          self.logo_picker_btn = ctk.CTkButton(master=self, text="Select an Image File", font=self.default_font, command=self.select_logo)
          self.logo_picker_btn.grid(column=1, row=0, columnspan =1, sticky="nsew", padx=20)

          self.logo_path_label = ctk.CTkLabel(master=self, textvariable=self.logo_path_var, width=200, height=50, font=self.default_font)
          self.logo_path_label.grid(column=0, row=1, columnspan =2, sticky="ew", padx=20)

     def select_logo(self):
        path = filedialog.askopenfilename()
        print(path)
        logo_file = ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(200,60))
        self.update_logo_preview(logo_file, path)

     def update_logo_preview(self, img, path="Stored in Database"):
          self.logo_preview_label.configure(image=img, compound="left", text="")
          self.logo_path_var.set(path)

     def clear_logo_preview(self):
          self.logo_preview_label.configure(image="", text="Logo Preview")
          self.logo_path_var.set("")

     def get_logo_path(self):
          return self.logo_path_var.get()

#Generates a frame containing widgets allowing a user to add a new image to the database
class ImagePicker(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)
          self.parent = parent

          #Configure frame appearance
          self.configure(border_color="green", border_width=1)

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

          title1_label = ctk.CTkLabel(master=self, text="Image Store Editor", font=self.default_font)
          title1_label.grid(column=0, row=0, columnspan=3, sticky="ew")

          self.logo_preview_label = ctk.CTkLabel(master=self, text="Image Preview", font=self.default_font, width=200, height=50, bg_color="black")
          self.logo_preview_label.grid(column=0, row=1, rowspan =2, sticky="", padx=20, pady=20)

          self.logo_picker_btn = ctk.CTkButton(master=self, text="Select an Image File", font=self.default_font, command=self.select_logo)
          self.logo_picker_btn.grid(column=1, row=1, columnspan =1, sticky="w")

          self.path_data = ctk.CTkLabel(master=self, text="", textvariable=self.logo_path_var, font=self.default_font)
          self.path_data.grid(column=1, row=2, columnspan =1, sticky="w")

     #Generates a file dialog to select an image from the local machine and updates the preview     
     def select_logo(self):
          try:
               path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png")])
               print(f"Image file selected to upload to database:{path}")
               logo_file = ctk.CTkImage(light_image=Image.open(path), dark_image=Image.open(path), size=(200,60))
               self.update_image_preview(logo_file, path)
          except Exception as e:
               Message_Boxes.invalid_image_warning(e)

     

     #Updates the iamge preview
     def update_image_preview(self, img, path="Stored in Database"):
          self.logo_preview_label.configure(image=img, compound="left", text="")
          self.logo_path_var.set(path)

     #Clears the image preview
     def clear_image_preview(self):
          self.logo_preview_label.configure(image="", text="Image Preview")
          self.logo_path_var.set("")

     #Gets the path of the current preview image
     def get_image_path(self):
          return self.logo_path_var.get()

#Generates a frame containing widgets allowing a user to view a selected image     
class ImageViewer(ctk.CTkFrame):
     def __init__(self, parent):
          super().__init__(parent)
          self.parent = parent

          #Configure frame appearance
          self.configure(border_color="green", border_width=1)

          #Set Default font
          self.default_font = ctk.CTkFont(default_font, default_size)

          #GUI Variables - to allow dynamic updating
          self.image_name_var = StringVar()
          self.image_id_var = StringVar()

          #Setup Columns / rows for device_setup_frame

          self.columnconfigure(0, weight=0, pad=20)
          self.columnconfigure(1, weight=0, pad=20)
          self.columnconfigure(2, weight=1, pad=20)

          self.rowconfigure(0, weight=0, pad=25)
          self.rowconfigure(1, weight=0, pad=10)
          self.rowconfigure(2, weight=0, pad=10)

          #Widgets
          title1_label = ctk.CTkLabel(master=self, text="Image Store Viewer", font=self.default_font)
          title1_label.grid(column=0, row=0, columnspan=3, sticky="ew")

          self.logo_preview_label = ctk.CTkLabel(master=self, text="Image Preview", font=self.default_font, width=200, height=50, bg_color="black")
          self.logo_preview_label.grid(column=0, row=1, rowspan =2, sticky="", padx=20, pady=20)

          id_label = ctk.CTkLabel(master=self, text="Image ID:", font=self.default_font)
          id_label.grid(column=1, row=1, columnspan=1, sticky="w")

          id_data_label = ctk.CTkLabel(master=self, text="", textvariable=self.image_id_var, font=self.default_font, anchor="w")
          id_data_label.grid(column=2, row=1, columnspan=1, sticky="w")

          name_label = ctk.CTkLabel(master=self, text="Image Name:", font=self.default_font)
          name_label.grid(column=1, row=2, columnspan=1, sticky="w")

          name_data_label = ctk.CTkLabel(master=self, text="", textvariable=self.image_name_var, font=self.default_font, anchor="w")
          name_data_label.grid(column=2, row=2, columnspan=1, sticky="w")
     
     #Sets image id
     def set_image_id(self, image_id):
          self.image_id_var.set(image_id)

     #Sets image name
     def set_image_name(self, image_name):
          self.image_name_var.set(image_name)

     #Updates the preview image taking a binary image as input
     def update_logo_preview(self, blob_img):
          self.convert_from_blob(blob_img)
          logo_file = ctk.CTkImage(light_image=Image.open("config_tool/temp.jpg"), dark_image=Image.open("config_tool/temp.jpg"), size=(200,60))
          self.logo_preview_label.configure(image=logo_file, compound="left", text="")

     #Clears the current image from the preview window
     def clear_image_preview(self):
          self.logo_preview_label.configure(image="", text="Logo Preview")

     #Converts a binary image to a jpg file
     def convert_from_blob(self, blob):
        blob_logo = open("config_tool/temp.jpg", "wb")
        blob_logo.write(blob)

class CustomTree(ttk.Treeview):
     def __init__(self, parent):
          super().__init__(parent)

          self.parent = parent

          self.configure(columns=("Name"))

          #-------"#0" is the first column in the tree
          #Column 1
          self.heading("#0", text="ID")
          self.column("#0", width=40, anchor="center", stretch=False)
          #Column 2
          self.heading("Name", text="Name")
          self.column("Name", width=250, anchor="center", stretch=True)

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