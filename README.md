# OATIS Web (DEV) - On Air Tally Indicator System - In Active Development

<img width="500" height="150" alt="logo" src="https://github.com/user-attachments/assets/ebfe4164-bf57-485f-ac5b-b7220c551612" />

## Overview

OATIS is currently being heavily modified to run the front-end client display in a browser for maximum compatibility with a wide range of end devices.

The Configuration Tool is also being converted into a Web app alowing engineers to simply navigate to a web address on any laptop to modify the configuration.

Below is a screenshot of the new display builder in the web Configuration tool.
<img width="1512" height="951" alt="Screenshot 2026-06-30 at 09 50 46" src="https://github.com/user-attachments/assets/ca1cb605-c844-441c-a4f0-963fb389b8f3" />

## Planned Features

### Web Configuration Tool
- Simply navigate to a webpage from your machine to modify the configuration.
- No remoting onto servers neccessary.

### All New Layout Builder
- Drag and drop Layout builder (replaces the cumbersome block editor in the python implementation of OATIS).
- Widgets are draggable, resizable and snap to guidelines.

### Client Rendering Performed in Browser
- All clients will navigate to a single web address.
- Server then determins what each client renders via websockets and a unique ID.
  
### Scalable Layouts
- All widgets have been built to scale dynamically from the ground up.
- Resize your browser window - OATIS automatically scales and re-positions the widgets.

### Suggestions?
- Suggestions for further improvements are welcomed, please add an entry in issues.












