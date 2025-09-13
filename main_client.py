from client.window import *
import logging

#Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

#Create an instance of the GUI
gui = Window()
gui.on_execute()