from config_tool.gui import *
import logging

#Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

#Start an instance of the GUI
logger.info("GUI Started")
hmi = GUI()