# OATIS V2 - On Air Tally Indicator System - IN DEVELOPMENT

<img width="1000" height="300" alt="logo" src="https://github.com/user-attachments/assets/ebfe4164-bf57-485f-ac5b-b7220c551612" />

## Overview

OATIS is a tally indicator system for use in Radio and TV that is platform agnostic, designed to run on Linux and Mac OSX, support is not gauranteed for Windows, as it has not currently been tested (I don't own a Windows PC...).

Designed to operate in a server-client model, multiple displays can be centrally managed using a lightweight server application and configuration tool.

## Features
### Physical and Network triggers:
- Support for physical GPI's and GPO's using the Arduino Uno R3 and Arduino Mega, giving you upto 54 inputs / outputs.
- Multiple Arduinos can be connected to the server, giving scope for increased I/O if needed.
- Support for network input and output triggers using the OSC Protocol, both UDP and TCP.
- Inputs can be linked to display indicator lamps to show the state of the input trigger.

### Logic
- Group Physical and Network inputs into a Logical Input using conditions: AND, NAND, OR, NOR.
- Use a single Logical Output to trigger multiple physical or network outputs.
  
### Customizable displays:
- Display Builder allows custom displays to be built and applied to multiple clients.
- Currently available display widgets: Studio Clock, Analogue Clock, Indicator Lamp, Date-Logo-Location Top-Banner (more to be added in the future, suggestions are welcomed!)
- Multiple clocks can be displayed at once with the option to change the timezone depending on location.
- Sync your client device via NTP for accurate time.
- Add your Own Logo to client displays.

### Messaging:
- Client displays can be used to show short messages by way of a scrolling ticker at the top of the screen.
- The background colour of each message can be chosen by the user.
- Clients are segregated into Logical Messaging groups for sending messages to a group of clients.
- Message console application for sending messages to clients.
  
<img width="1920" height="1080" alt="Client Showing Messaging Function" src="https://github.com/user-attachments/assets/7a54719f-49f8-444b-b443-20b84035e70c" />

### Remote management of Display Devices:
- Device Display settings can be changed remotley using the configuration tool.
- Display templates, image files and config are sent to client devices over the network.
- Devices can be identified using the configuration tool, bringing up a device information screen showing the clients configuration and IP information.

# Setup
This version of OATIS is built to run on Python 3.11.8.

## Install the Dependencies in the requirements.txt file
```
pip3 install -r requirements.txt
```

## Install SQlite
```
sudo apt-get install sqlite3
```

## Microcontroller Setup 
If you are using Physical GPI's the Arduino needs to be flashed with the Firmata code to enable communication via serial with OATIS. See below for steps how to do this.\
The Firmata protocol is used to communicate between OASTIS and the Arduino.
Arduino R3 and Arduino Mega are supported only.

Open Arduino IDE, navigate to Tools > Manage Libraries

<img width="1920" height="1080" alt="logo" src="https://github.com/user-attachments/assets/8ba3c31c-c4d7-42f0-9012-6cce2492962d" />

In the search box type "firmata express"

Select version 1.2.0 and hit install, you will probably get a prompt asking if you want to install with dependencies, select yes!

<img width="400" height="300" alt="logo" src="https://github.com/user-attachments/assets/9e6259f0-134b-4466-a463-0c6ea0af62b2" />

Open Arduino IDE and navigate to File > Examples > FirmataExpress > FirmataExpress

<img width="1920" height="1080" alt="logo" src="https://github.com/user-attachments/assets/1972e753-0c02-4332-9f9f-34424e9a43ed" />

Upload the Sketch to your Board, your now ready to use the microcontroller with OATIS.

## Build the Database - It's not as scrary as it sounds...I promise!
OATIS will complain if it does not find a valid database file. The database needs to be built using the config tool.

<img width="289" height="94" alt="Screenshot 2026-01-10 at 07 43 19" src="https://github.com/user-attachments/assets/3ee88b5d-1541-4304-8e15-7c23954a131d" />

Launch the Config tool using the main_config_tool.py script.\
A prompt will show on the first run as below, select yes. The required tables and default data the application needs to run will be built and added.

<img width="261" height="250" alt="Screenshot 2025-09-22 at 21 47 50" src="https://github.com/user-attachments/assets/d1a48e9a-f813-4b85-81fc-4c1fc8a269cd" />

Config tool will then continue to launch.

## OATIS Configuration Tool Tabs
- Image Store - Used for uploading images to the database to be diaplayed on client devices.
- Device Config - Used for adding a client device to the system, assiging a Message Group and Display Instance.
- GPIO Config - Used for configuring Arduino Microcontrollers, their COM port and pin configuration.
- Input Triggers - Configuration of Physical and Network Inputs.
- Input Logics - Provide a method of grouping multiple Physical and Network Input Triggers using the logic functions: AND, NAND, OR, NOR.
- Output Logics - Provide a method of grouping multiple Physical and Network Output Triggers, providing the capability to trigger multiple outputs from a single input.
- Output Triggers - Configuration of Physical and Netowrk Outputs.
- Display Templates - A tool for building client display layouts. 
- Display Instances - Provides a method of configuring a Display Template for use on a client device.
- Messaging Groups - Provides a method to create Logical Groups of devices messages can be sent to.
- Server Config - Used for initialising the Database, Backup and Restore of configuration and setting the IP Address of the Server.

## Set Server IP Address
Launch the Config tool using the main_config_tool.py script, navigate to the Server Config tab.\
Select IP Settings.\
Use the dropdown to select the interface you would like to use for server communication. Each entry in the dropdown will be an ip address of an active interface on the machine.\
A loopback IP address will also be shown which can be used for system testing if you want to run the client and server on the same machine.

<img width="1680" height="193" alt="Screenshot 2026-01-10 at 07 48 25" src="https://github.com/user-attachments/assets/b28305dd-93c0-4a5c-8888-f63f045c10c0" />

Once selected hit save.

## Adding Microcontrollers
Navigate to the GPIO Config tab.\
Hit Add Controller.\
Enter a name for the controller.\
Enter the loation the controller, e.g. equipment room.\
Select which type of Arduino you are using.\
Use the COM port dropdown to select the USB-Serial port to use to communicate with the Arduino.

<img width="1370" height="214" alt="Screenshot 2026-01-10 at 07 54 54" src="https://github.com/user-attachments/assets/72b247ee-ac6a-4e34-a4ae-1ebf1627876b" />

Once the type of Arduino has been selected, the Pin Mode Configuration should load.\
Here you can specify which Arduino pins to use as Inputs, Outputs or Disable.

<img width="629" height="500" alt="Screenshot 2026-01-10 at 07 58 02" src="https://github.com/user-attachments/assets/a0bfaa35-a8c1-45b7-9d2d-b6bf404f44d5" />

Once done, hit save.

PLEASE NOTE: Any changes to the Port, or Pin configuration will require a server restart to push the latest configuration to the Arduino.

## Creating Message Groups
Message groups are used to logically group client devices when sending messages to them.\
Go to the Messaging Groups tab, enter a name for your message group and hit save.

<img width="1680" height="156" alt="Screenshot 2026-01-10 at 08 06 03" src="https://github.com/user-attachments/assets/c12e4d73-35ac-40dd-bbf7-fd9316842941" />

## Adding logos to the database
Logos should have an aspect ratio of 30:9 to avoid scaling issues, e.g. 300 x 90 or 600x180, add an appropriatley sized logo depending on your intended display resolution.\
Images must be in PNG format.\
To add a logo image head to the Image Store tab.\
Click Add then click select an image file.\
Select your image file using the file browser.\
Once the preview is shown, hit save.

<img width="1680" height="626" alt="Screenshot 2026-01-10 at 08 13 49" src="https://github.com/user-attachments/assets/737b5460-0701-4626-8ea9-56122f231bb4" />

## Creating Display Templates

Head to the Display Templates tab.\
Name the display template.\
Select the number of rows and columns you require. A preview will be shown in layout builder window.

<img width="1294" height="417" alt="Screenshot 2026-01-10 at 08 19 51" src="https://github.com/user-attachments/assets/6e06c5a5-0cbc-4110-9cbc-e016365ca64d" />

Now you need to create surfaces on the grid for widgets to be assigned to.\
This is done by assigning each block a surface id.\
From Display Surfaces, select an ID, then select a block on the layout builder window to assign the id.\
Use the id's to create display surfaces. The ID's must be assigned as rectangles and must not be duplicated accross non-adjacent sections.

<img width="1295" height="422" alt="Screenshot 2026-01-10 at 08 26 00" src="https://github.com/user-attachments/assets/87db9d75-5433-4789-be08-632ca0fdc118" />

Once done click Build to create the display sections.\
Hover over the layout builder window to see the display surfaces.

<img width="641" height="359" alt="Screenshot 2026-01-10 at 08 26 25" src="https://github.com/user-attachments/assets/55f20ed7-a497-4a65-a071-02165a0a596c" />

Next assign a widget to each section.\
Click on a widget from the Display Widgets, then click the Display Surface you want to assign it to.\
Each section must contain a widget.

<img width="643" height="359" alt="Screenshot 2026-01-10 at 08 29 09" src="https://github.com/user-attachments/assets/135ea77a-9775-4c70-b8d4-42f182ce409f" />

Once done hit save.

## Creating a Display Instance
Head to the Display Instances tab.\
Click Add.\
Give the Display Instance a Name.\
Select which Display Template you want to use.\
The selected Display Template should render in the preview window.\
Click on each Widget to Configure.

<img width="1432" height="595" alt="Screenshot 2026-01-10 at 14 44 52" src="https://github.com/user-attachments/assets/658dc992-aad0-41c7-9292-092e9fe093d1" />

## Adding a Client Display Device

Click on the Device Config tab.\
Click Add.\
Name the device.\
Set it's IP address.\
Set it's location, this is used for logical grouping.\
Assign a Message Group.\
Assign a Display Instance.\
Hit save.

<img width="1680" height="408" alt="Screenshot 2026-01-10 at 14 47 52" src="https://github.com/user-attachments/assets/1bbcba7a-5674-4e11-b96a-965c7f4ae8c1" />

When a client has been added three buttons will be enabled below the device settings allowing the user to reload the display template if changes are made, and identify the device.

## Adding Input Triggers

Click on the Input Triggers tab.\
Click Add.\
Enter a name for the trigger.\
Select the controller that will sense the trigger, Network for OSC inputs, any others listed will be Physical Arduinos.
Then select the address on that controller for the trigger.\

For a Physical Controller, this will be the pin number.
<img width="1680" height="218" alt="Screenshot 2026-01-13 at 22 56 14" src="https://github.com/user-attachments/assets/6af5b2bd-f90a-46d8-89fa-c9b7a8f423ff" />

For a Netowrk Controller, this will be the OSC address.
<img width="1680" height="216" alt="Screenshot 2026-01-13 at 22 58 37" src="https://github.com/user-attachments/assets/b0f485eb-8cc0-4791-b40e-ba4a951892a1" />

## Adding Input Logics
Input Logics allow a many-to-one relationship to be setup, allowing a group of input triggers to trigger a single Logical Input based on a condition chosen by the user.\
Click on the Input Logics tab.\
Click Add.\
Enter a name for the Input Logic.\
Listed on the left are all the configured Input Triggers, select which ones you would like to trigger this Input Logic and use the arrow buttons to move them into the Active Input Triggers Column. You can select multiple by holding down Ctrl.\
Then select the high-condition for this Input Logic, this determins how the Input Logic behaves when the Active Input Triggers go high or low.. The available options are AND, NAND, OR, NOR.
Once done hit save.

<img width="1680" height="716" alt="Screenshot 2026-01-13 at 23 07 07" src="https://github.com/user-attachments/assets/42c4b4f2-b51a-46cc-81d7-4e74f70c5553" />

## Adding Output Triggers
Physical GPO's or OSC commands can be set as Output Triggers.
Click on the Output Triggers tab.\
Click Add.\
Enter a name for the Output Trigger.\
Select the type of output, GPO for a physical Arduino Output, or Network for an OSC Output.\
If GPO is selected, select the controller to use and the address to trigger.\
The rest of the input fields will be greyed out.\
<img width="1680" height="715" alt="Screenshot 2026-01-13 at 23 37 04" src="https://github.com/user-attachments/assets/cbc1834f-df3a-4edb-86bd-243ea34c4c6a" />

If Network is selected, the Controller will automatically be set to Network, and address will be greyed out.\
Enter the IP address of the OSC Client you want to send a command to.\
Enter the port and select the protocol to use.\
Enter the OSC command to send to the client when this Output Trigger goes high, adding optional arguments, each seperated by a space.\
Enter the OSC command to send to the client when this Output Trigger goes low, adding optional arguments, each seperated by a space.\
Click Save once done.\

<img width="1680" height="712" alt="Screenshot 2026-01-13 at 23 40 35" src="https://github.com/user-attachments/assets/9ed0d8ac-b1ce-4cc0-ad75-21e8d11b1b1b" />


<img width="1680" height="1050" alt="Screenshot 2026-01-13 at 23 13 25" src="https://github.com/user-attachments/assets/799fbec1-1a35-4b2c-bf88-2fd3cd42585a" />

## Adding Output Logics
Output Logics allow a one-to-many relationship to be setup, allowing a single Logical Input to trigger multiple Output Triggers.
Click on the Output Logics tab.\
Click Add.\
Enter a name for the Output Logic.\
Select the Input Logic that will trigger this Output logic.\
Listed on the left are all the configured Output Triggers, select which outputs you want this output Logic to Trigger and use the arrows to move them to the Active outptu Triggers Column.
Once done hit save.

<img width="1680" height="719" alt="Screenshot 2026-01-13 at 23 14 48" src="https://github.com/user-attachments/assets/5080d392-473a-4615-914a-d81e87015b61" />



# Launching the Server
Launch the server using the main_server.py script.\
The status of the server will show stopped.

<img width="294" height="95" alt="Screenshot 2026-01-13 at 09 20 38" src="https://github.com/user-attachments/assets/a3b628b8-67f8-41ff-84e8-4b2a8bbac5c1" />

Before starting the server, make sure any physical GPIO controllers are plugged in and that you have set the server IP address in config tool before launching.\
If you don't set the IP address the server will default to the loopback address of 127.0.0.1.\
If you change the server IP address when the server is running, you will need to restart the server for this to take affect.
Click start to boot the server. The status will change to booting.

<img width="293" height="94" alt="Screenshot 2026-01-13 at 09 24 04" src="https://github.com/user-attachments/assets/f5e3638f-7978-45d0-996c-af1bbc78b6ba" />

If the server starts ok the status will change to running.
If the server does not start, it is likley you have a misconfigured GPIO controller. If the port has changed or the server cannot communicate with the controller the server will not boot. The server will tell you why in the GUI.

<img width="290" height="96" alt="Screenshot 2026-01-13 at 09 26 20" src="https://github.com/user-attachments/assets/f6a218ed-1771-4307-9e84-ec22b1411a22" />

# Launching the Remote Client
Launch the main_client.py script.
On first run a GUI window will open prompting you to set the IP address to use for the client and the server.\
Once these IP's have been set the client will boot without launching this window on subsequent launches.\
To change the IP's in the future hit "i" on a keyboard when OATIS is running, this will close the client and set a flag to bring up the IP configuration menu on next launch.

<img width="1086" height="513" alt="Screenshot 2026-01-13 at 09 42 14" src="https://github.com/user-attachments/assets/9fcb6f7e-a899-42b7-8be3-016f19f96c72" />

If the client has a successful connection to the server, the small circular indicator in the bottom of the clockface will remain grey. If the server cannot be reached this will flash red.

To exit the client, press "ESC" on the keyboard.

# Launching the Message Console
Launch the main_message_console.py script.\
On first run it will default to the loopback address and will probably show Server Offline if the server is using a different IP.

<img width="1918" height="45" alt="Screenshot 2025-09-20 at 20 29 48" src="https://github.com/user-attachments/assets/9ba43ee8-4703-4991-a3b5-33c7e6e10ec1" />

To set the IP of the Message Console, hit ESC to bring up the configuration window.\
Use the dropdown to set the device IP and enter the Server IP.\
Hit Save, you will automatically return to the Message Console main screen.

<img width="1091" height="516" alt="Screenshot 2025-09-20 at 20 33 06" src="https://github.com/user-attachments/assets/0b9d9650-562c-490a-8c09-fdcefc47d949" />

If you've set everything correctly, Message Groups assigned ot devices will populate in the GUI.\
The status bar will show as below:
<img width="1923" height="39" alt="Screenshot 2025-09-20 at 20 34 11" src="https://github.com/user-attachments/assets/bbdc9e9c-f56e-419b-b7c4-6cde4988d7a6" />

## Sending a Message
Use the top free-text field to enter your message.\
Choose a background colour.\
Select which message groups you want to send the message to and move these to the selected groups column using the arrow.\
Once happy click the green arrow to make the message active.\
The message groups will move to the active messages column.

<img width="1917" height="1079" alt="Screenshot 2025-09-20 at 21 16 21" src="https://github.com/user-attachments/assets/d92004ac-bb7c-409a-a827-2b19a4bac440" />

## Stopping a message
Select from the active messages column the messages you want to stop.\
Hit the red arrow button.

# API's 

## Server API - For Interaction by external devices and software - OSC Protocol - UDP Port 1337

#### Triggering a Signal Light on or off
```
/{trigger_group_name}/signal-lights/{indicator_number} => Args: ("state")
```
state = 1 => Signal Light On \
state = 0 => Signal Light Off









