from client.launcher import *
import logging

#Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

#Create an instance of the GUI
gui = Launcher()