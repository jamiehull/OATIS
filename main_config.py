from config_tool.gui import *
import logging

#Setup Logging
logger = logging.getLogger(__name__)
logger_format = "[%(filename)s:%(lineno)s => %(funcName)30s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=logger_format)

#Start an instance of the GUI
logger.info("GUI Started")
hmi = GUI()