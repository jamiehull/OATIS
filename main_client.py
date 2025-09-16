from client.launcher import Launcher
import logging

#Setup Logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

#Create an instance of the GUI
launcher = Launcher()
