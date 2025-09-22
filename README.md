# OATIS - On Air Tally Indicator System

<img width="3000" height="900" alt="logo" src="https://github.com/user-attachments/assets/ebfe4164-bf57-485f-ac5b-b7220c551612" />

## Overview

OATIS is a tally indicator system for use in Radio and TV that is platform agnostic, designed to run on Mac OSX and Linux, support is not gauranteed for Windows as it has not currently been tested (I don't own a Windows PC...).

Designed to operate in a server-client model, multiple displays can be centrally managed using a lightweight server application and configuration tool.

Tally's can be triggered either from Physical GPI's or via OSC commands.

## Features
### Customizable displays:
- Configure the number of indicators to display(currently up to 6), their colour and text. (More indicators will be available in the next release)
- Customizable logos.
- Choose between Analogue and Studio Style Clocks.
- Choice of a variety of display layouts.
<img width="1920" height="1080" alt="Layout" src="https://github.com/user-attachments/assets/d8e9900e-d576-4c17-9b3d-c7b6fee38491" />
<img width="1920" height="1080" alt="Layout" src="https://github.com/user-attachments/assets/2a8b6503-20bd-499d-9b97-fbee920f59d6" />
<img width="1920" height="1080" alt="Layout" src="https://github.com/user-attachments/assets/6a45b3d0-873c-40bb-bb42-ab1a3d11b12a" />
<img width="1920" height="1080" alt="Layout" src="https://github.com/user-attachments/assets/1312290b-82ff-4588-9428-3f1b35e401c9" />

### Messaging:
- Client displays can be used to show short messages by way of a scrolling ticker at the top of the screen.
- The background colour of each message can be chosen by the user.
- Clients are segregated into logical Messaging groups for sending messages to a group of clients.
- Message console application for sending messages to clients.
  
<img width="1920" height="1080" alt="Client Showing Messaging Function" src="https://github.com/user-attachments/assets/7a54719f-49f8-444b-b443-20b84035e70c" />
<img width="1920" height="1080" alt="Message Console" src="https://github.com/user-attachments/assets/5b0f7757-2cda-49ff-b7be-2ad6e8e895cb" />

### Physical and Network triggers:
- Support for physical GPI's using the Arduino Uno R3 - (Arduino Mega support to be added in next release)
- Support for network triggers using the OSC Protocol
  
### Remote management of Display Devices:
- Device settings can be changed remotley using the configuration tool
- Display customizations can be sent to the device for rendering
- Devices can be idented using the configuration tool, bringing up a device information screen showing the clients configuration.
<img width="1920" height="1080" alt="Identify Screen" src="https://github.com/user-attachments/assets/13749a5b-f4fc-4f19-9ea2-eda29f7db0d4" />

## Terminology

Controllers - Physical GPIO Controllers used for inputs / outputs.\
Trigger Group - A logical group of OSC Network Triggers and Physical Controller triggers used to change the state of client widgets.\
Message Group - A logical group of devices messages can be sent to.\
Display Template - A template used to render a client display with the correct colours, labels and layout.\
Devices - A client display device.

# Setup
## Install the Dependencies in the requirements.txt file
```
pip3 install -r requirements.txt
```

## Microcontroller Setup 
If you are using Physical GPI's the Arduino needs to be flashed with the Firmata code to enable communication via serial with OATIS. See below for steps how to do this.\
Currently the application has been designed to use the Arduino Uno R3 Microcontroller for GPI's using the Firmata protocol to notify the application of GPI state changes.

Open Arduino IDE, navigate to Tools > Manage Libraries

![Screenshot 2025-02-22 at 16 07 03](https://github.com/user-attachments/assets/8ba3c31c-c4d7-42f0-9012-6cce2492962d)

In the search box type "firmata express"

Select version 1.2.0 and hit install, you will probably get a prompt asking if you want to install with dependencies, select yes!

![Screenshot 2025-02-22 at 16 07 52](https://github.com/user-attachments/assets/9e6259f0-134b-4466-a463-0c6ea0af62b2)

Open Arduino IDE and navigate to File > Examples > FirmataExpress > FirmataExpress

![Screenshot 2025-02-22 at 15 57 19](https://github.com/user-attachments/assets/1972e753-0c02-4332-9f9f-34424e9a43ed)

Upload the Sketch to your Board, your now ready to use the microcontroller with OATIS.

## Set Server IP Address

Launch the Config tool using the main_config_tool.py script, navigate to the Server Config tab.\
Select IP Settings.\
Use the dropdown to select the interface you would like to use for server communication. Each entry in the dropdown will be an ip address of an active interface on the machine.\
A loopback IP address will also be shown which can be used for system testing if you want to run the client and server on the same machine.

![image](https://github.com/user-attachments/assets/87002b37-bc96-4e45-bfc0-b50d218ab5e9)

Once selected hit save.

## Adding Microcontrollers

Navigate to the GPIO Config tab.\
Hit Add Controller.\
Enter a name for the controller.\
If the controller is running on the same machine as the server - select local\
If the controller is running on another machine - select remote (Not yet implemented - Will be in next release)

![image](https://github.com/user-attachments/assets/a6e568bf-65eb-4089-bae5-73bbf46de76f)

Use the COM port dropdown to select the USB-Serial port to use to communicate with the Arduino

![Screenshot 2025-02-22 at 17 21 56](https://github.com/user-attachments/assets/482cd7b9-3c1d-4942-b402-4ce0fb163967)

Use the Controller type dropdown to select the Arduino Board you are using. At the moment there is only support for the Uno R3.\
Under GPIO Configuration select the pins you are going to use as inputs and mark any unused pins as disabled.

![image](https://github.com/user-attachments/assets/e4ac1af4-0a93-4158-ac67-5d155ead418f)

Once done, hit save.

## Creating Trigger Groups
Trigger Groups are used to group physical and logical triggers to target indicator lights.\
Trigger Types:
- Controller: A Physical GPI on a microcontroller
- Network: An inbound OSC Message

Go to the Trigger Groups Tab\
Set a name for the Trigger Group.\
For each indicator choose the controller that will be the source trigger.\
If the network controller is selected, an OSC address for triggering that indicator will automatically populate.\
If a physical controller is selected select the source GPI.\
If you are not planning on using all the indicators leave these set to Network.

<img width="949" height="725" alt="Screenshot 2025-09-19 at 08 21 30" src="https://github.com/user-attachments/assets/f1cd32c7-2c61-4beb-9c46-d3f5b8bc1695" />

## Creating Message Groups
Message groups are used to logically group displays when sending messages to them.\
Go to the Messaging Groups tab, enter a name for your message group and hit save.

<img width="1280" height="201" alt="Screenshot 2025-09-19 at 08 29 43" src="https://github.com/user-attachments/assets/07837c0f-6f9e-4d6c-89f5-a000b18c9b93" />

## Adding logos to the database
Logos should have an aspect ratio of 30:9 to avoid scaling issues, e.g. 300 x 90 or 600x180, add an appropriatley sized logo depending on your intended display resolution.\
Images must be in PNG format.\
To add a logo image head to the Image Store tab.\
Click add image then click select an image file.\
Once the preview is shown, hit save.

<img width="594" height="138" alt="Screenshot 2025-09-19 at 08 40 57" src="https://github.com/user-attachments/assets/893fdcc3-c29c-4b88-ae85-a98c172768db" />

## Creating Display Templates

Head to the Display Templates tab.\
Name the display template.\
Select the desired layout, currently the options are fullscreen clock or clock with indicators.\
Select the logo you want to use, the ones uploaded should appear in the dropdown.\
Select your clock type.\
Select the number of indicators to display.
<img width="948" height="307" alt="Screenshot 2025-09-19 at 23 30 41" src="https://github.com/user-attachments/assets/0b781708-da01-4d02-81fb-fd7c0021915e" />

In the indicators section, set the label for the indicator.\
The True / False dropdown is used to determine whether the indicator flashes or not. True = Flash, False = No Flash, Steady On.\
Select "Click to choose colour" to select the indicator on colour.\
Do this for each indicator then hit save.

<img width="947" height="383" alt="Screenshot 2025-09-19 at 23 34 33" src="https://github.com/user-attachments/assets/c2364829-7e54-413d-a977-7cf63b827a9c" />

## Adding a Client Display Device

Click on the Device Config tab.\
Name the device.\
Set it's IP address.\
Set it's location, this is used for logical grouping.\
Select the Messaging and Trigger Group from the dropdown.\
Select the Display Template from the dropdown.\
Hit save.

When a client has been added three buttons will be available below the device settings allowing the user to reload the display template if changes are made, and identify the device.

<img width="1280" height="800" alt="Screenshot 2025-09-19 at 23 38 14" src="https://github.com/user-attachments/assets/9d45b9a0-8c8f-405b-b1f7-f4a6401df074" />

# Launching the Server
Launch the server using the main_server.py script.\
Make sure any physical GPIO controllers are plugged in when launching hte server application and that you have set the server IP address in config tool before launching.\
If you don't set the IP address the server will default to the loopback address of 127.0.0.1.\
If you change the server IP address when the server is running, you will need to restart the server for this to take affect.

The server will report it's status at regular intervals, if everything is ok the terminal output should look similar to below:
<img width="665" height="100" alt="Screenshot 2025-09-20 at 18 33 09" src="https://github.com/user-attachments/assets/2015ddc8-ed01-4b26-9be2-f7eed497ba38" />

# Launching the Remote Client
Launch the main_client.py script.
On the first run the terminal window will prompt you to set the IP address to use for the client and the server, follow the prompts.\
Once these IP's have been set the client will boot straight up in future.\
If you need to change these in the future amend the settings file in /client/data/settings.json and reboot the client.

<img width="523" height="113" alt="Screenshot 2025-09-20 at 20 16 45" src="https://github.com/user-attachments/assets/27fe70be-9ff4-4b91-9150-aad5876c3f86" />

If the client has a successfull connection to the server, the small circular indicator in the bottom of the clockface will remain grey. If the server cannot be reached this will flash red.

#Launching the Message Console
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

#### Sending a message to one or more Message groups
```
/messaging/send_to_multiple => Args: ("ticker_text", "bg_colour_hex", [["message_group_id","message_group_name"],...])
```
#### Stopping a message to one or more Message groups
```
/messaging/stop_message => Args: ([["message_group_id","message_group_name"],...])
```
#### Triggering a Signal Light on or off
```
/{trigger_group_name}/signal-lights/{indicator_number} => Args: ("state")
```
state = True => Signal Light On \
state = False => Signal Light Off









