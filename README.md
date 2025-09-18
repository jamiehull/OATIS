# OATIS - On Air Tally Indicator System

## Overview

OATIS is an indicator system for use in Radio and TV that is platform agnostic, designed to run on Mac OSX and Linux, support is not gauranteed for Windows as it has not currently been tested (I don't own a Windows PC...).

Designed to operate in a server-client model, multiple displays can be centrally managed using a lightweight server application and configuration tool.

<img width="1280" height="799" alt="Screenshot 2025-09-17 at 06 47 19" src="https://github.com/user-attachments/assets/16a7c8ef-395b-41d6-92a3-cf1fbccc62e9" />

## Features
Customizable displays:
- Configure the number of indicators to display(currently up to 6), their colour and text.
- Customizable logos
- Choose between Analogue and Studio Style Clocks
- Choice of a variety of display layouts.
  
Messaging:
- Client displays can be used to show short messages by way of a scrolling ticker at the top of the screen.
- The background colour of each message can be chosen by the user.
- Clients are segregated into logical Messaging groups for sending messages to a group of clients.
- Message console application for sending messages to clients.
  
Physical and Network triggers:
- Support for physical GPI's usning the Arduino Uno R3 - (Arduino Mega support to be added in version 2)
- Support for network triggers using the OSC Protocol
  
Remote management of Display Devices:
- Device settings can be changed remotley using the configuration tool
- Display customizations can be sent to the device for rendering

## Terminology

Controllers - Physical GPIO Controllers used for inputs / outputs.\
Trigger Group - A logical group of OSC Network Triggers and Physical Controller triggers used to change the state of client widgets.\
Message Group - A logical group of devices messages can be sent to.\
Display Template - A template used to render a client display with the correct colours, labels and layout.
Devices - A client display device.

# Setup

If you are using Physical GPI's the Arduino needs to be flashed with the Firmata code to enable communication via serial with OATIS. See below for steps how to do this.

## Microcontroller Setup 

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

Launch the Config tool, navigate to the Server Config tab.
Select IP Settings.
Use the dropdown to select the interface you would like to use for server communication. Each entry in the dropdown will be an ip address of an active interface on the machine.
A loopback IP address will also be shown which can be used for system testing if you want to run the client and server on the same machine.

![image](https://github.com/user-attachments/assets/87002b37-bc96-4e45-bfc0-b50d218ab5e9)

Once selected hit save.

## Adding Microcontrollers

Navigate to the GPIO Config tab.

Hit Add Controller.

Enter a name for the controller.

If the controller is running on the same machine as the server - select local\
If the controller is running on another machine - select remote (Not yet implemented - Will be in version 2)

![image](https://github.com/user-attachments/assets/a6e568bf-65eb-4089-bae5-73bbf46de76f)

Use the COM port dropdown to select the serial port to use to communicate with the Arduino

![Screenshot 2025-02-22 at 17 21 56](https://github.com/user-attachments/assets/482cd7b9-3c1d-4942-b402-4ce0fb163967)

Use the Controller type dropdown to select the Arduino Board you are using. At the moment there is only support for the Uno R3.

Under GPIO Configuration select the pins you are going to use as inputs and mark any unused pins as disabled.

![image](https://github.com/user-attachments/assets/e4ac1af4-0a93-4158-ac67-5d155ead418f)

Once done, hit save.

## Creating Trigger Groups

Trigger Types:
- Controller: A Physical GPI on a microcontroller
- Network: An inbound OSC Message

# Server API - For Interaction by external devices and software - OSC - UDP / TCP Port 1337

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


# Internal Server Network Commands - Used between RDS Applications and the server - TCP Port 1339

## Client to Server
Current as of 12/06/2025.
### Requesting the assigned display template from the server
Send a dictionary in JSON format
```
{
    "command" : "/config/display_template/get",
    "arguments" : {
        "timestamp" : timestamp_of_local_template, 
        "client_ip" : client_ip_address},
    "data" : None
}
```
If timestamp == 0 this signals to the server the client has no existing display template.\
Any other timestamp will be the timestamp when the locally stored display template was modified on the server.\
If the timestamp does not match the one held on the server for the given display template, this indicates the display template has been modified on the server, the server will re-send the display template.

Returns:
```
{
    "command": "/config/display_template/get",
    "arguments": {
        "display_template_currrent" : match_status},
    "data": None / display_template
}
```
match_status = True - The display template matches the server. In this case the data field will be None.\
match_status = False - The display template does not match the server. The data field contaions the display template as a list.

### Requesting the Clients Configuration
Send a dictionary in JSON format
```
{
    "command" : "/config/device/get",
    "arguments" : {
        "client_ip" : client_ip_address},
    "data" : None
}
```

Returns:
```
{
    "command": "/config/device/get",
    "arguments": {
        "device_name" : device_name,
        "device_ip" : device_ip,
        "device_location" : device_location,
        "message_group" : message_group_name,
        "trigger_group" : trigger_group_name,
        "display_template" : display_template_name
        },
    "data": null
}
```

### Requesting an Image File
Send a dictionary in JSON format
```
{
    "command" : "/assets/images/get",
    "arguments" : {
        "image_id" : "image_id"
                },
    "data" : None
}
```
Returns an image file in byte format.

### Hearbeat
Send a dictionary in JSON format
```
{
    "command" : "heartbeat",
    "arguments" : {
        "client_ip" : "client_ip"
                },
    "data" : None
}
```
Returns:
```
{
    "command": "heartbeat",
    "arguments": {
        "status" : "OK",
        "timestamp" : timestamp
        },
    "data": None
}
```


## Config Tool to Server
Current as of 12/06/2025.
### Raising a Client Frame
Send a dictionary in JSON format
```
{
    "command" : "/control/client/raise_frame",
    "arguments" : {
        "device_id" : device_id,
        "frame" : frame_name
        },
    "data" : None
}
```
Available frame_names:
- default
- identify
- rds
- settings

Returns:
```
{
    "command": "/control/client/raise_frame",
    "arguments": {
        "status": "OK"},
    "data": null
}
```

### Triggering a Client to Re-render it's display
Send a dictionary in JSON format
```
{
    "command" : "/control/client/reload_display_template",
    "arguments" : {
        "device_id" : device_id
        },
    "data" : None
}
```
Returns:
```
{
    "command": "/control/client/reload_display_template",
    "arguments": {
        "status": "OK"},
    "data": null
}
```

## Message Console to Server

### Get a list of all message groups
Send a dictionary in JSON format
```
{
    "command" : "/config/message_groups/get",
    "arguments" : None
    "data" : None
}
```
Returns => A list of all configured message group id's / names as a JSON list

### Get a list of all devices
Send a dictionary in JSON format
```
{
    "command" : "/config/devices/get",
    "arguments" : None
    "data" : None
}
```
Returns => A list of all configured devices group id's / names as a JSON list

### Sending a message to multiple message groups
Send a dictionary in JSON format
```
{
    "command" : "/messaging/send_to_multiple",
    "arguments" : {
        "message" : "message_text"
        "bg_colour" : "bg_colour_hex"
                },
    "data" : [[message_group_id,"message_group_name"],[message_group_id,"message_group_name"],...]
}
```
Server will respond with:
```
{
    "command" : "/messaging/send_to_multiple",
    "arguments" : {
        "status" : "OK/ERROR",
        "message_id" : message_id,
        "active_message_groups" : [[message_group_id,"message_group_name"],[message_group_id,"message_group_name"],...]
                    }
    "data" : None
}
```

### Cancelling one or more messages
Send a dictionary in JSON format. 
The data field contains a list of lists containing the id and name of the message groups to be stopped.
```
{
    "command": "/messaging/stop_message", 
    "arguments": None, 
    "data": [[message_group_id,"message_group_name"],[message_group_id,"message_group_name"],...]
    }
```

Server will return:
```
{
    "command": "/messaging/stop_message", 
    "arguments": {
        "status" : "OK/ERROR",
        "active_message_groups" : [[message_group_id,"message_group_name"],[message_group_id,"message_group_name"],...]
    }
    "data": None
    }
```

# Client Handlers
## Display template Specific

### Studio Display Scalable
"/text/studio_name" : self.studio_name_handler,
"/text/show_name" : self.show_name_handler,
"/signal-lights/1" : self.indicator_handler,
"/signal-lights/2" : self.indicator_handler,
"/signal-lights/3" : self.indicator_handler,
"/signal-lights/4" : self.indicator_handler,
"/signal-lights/5" : self.indicator_handler,
"/signal-lights/6" : self.indicator_handler,
"/*/ticker" : self.ticker_handler

### Fullscreen Clock Display
"/text/studio_name" : self.studio_name_handler,
"/*/ticker" : self.ticker_handler










