import customtkinter as ctk

#Tkinter Window Attributes
global window_title 
window_title = "RDS"

global screen_info
screen_info = {}

global fullscreen_state
fullscreen_state = True


#Fonts

default_font ='Arial'
default_size = 20

small_font_size = 40
medium_font_size = 55
large_font_size = 85
xlarge_font_size = 100

alt1_small_font_size = 35
alt1_medium_font_size = 50
alt1_large_font_size = 80
alt1_xlarge_font_size = 90

#Image Sizes
small_image = (200,60)
medium_image = (300,90)
large_image = (400,120)
xlarge_image = (450,135)

#Server Details
global server_ip_address
server_ip_address = "127.0.0.1"

global server_port
server_port = 1337