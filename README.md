# CoRe Lab Check-In Service
  
This project implements the RFIO-5222 and some Python code to read the UID of Card Tags. This data is sent into a Firebase database to keep track of the time the card was presented. It keeps record of times the user Checked In or Out of the system.

## -Getting Started-

Please read the documentation in this repository:  https://github.com/miguelbalboa/rfid

### Prerequisites

Hardware:

* Arduino Board, Breadboard, Jumper Cables
* RFIO-522 (Card Reader)
* RFID tags to read

Software:

* Arduino IDE 1.6+
* Python 3.7+
* firebase-admin python package
* pyserial python package

### Arduino Circuit Connection
The table below shows how to wire the RFIO-522 to the arduino pins:

<table>
<tbody>
<tr>
<td width="80"><strong>Pin</strong></td>
<td width="190"><strong>Wiring to Arduino</strong></td>
</tr>
<tr>
<td width="80">SDA</td>
<td width="190">Digital 10</td>
</tr>
<tr>
<td width="80">SCK</td>
<td width="190">Digital 13</td>
</tr>
<tr>
<td width="80">MOSI</td>
<td width="190">Digital 11</td>
</tr>
<tr>
<td width="80">MISO</td>
<td width="190">Digital 12</td>
</tr>
<tr>
<td width="80">IRQ</td>
<td width="190">unconnected</td>
</tr>
<tr>
<td width="80">GND</td>
<td width="190">GND</td>
</tr>
<tr>
<td width="80">RST</td>
<td width="190">Digital 9</td>
</tr>
<tr>
<td width="80">3.3V</td>
<td width="190">3.3V</td>
</tr>
</tbody>
</table>

You can optionally connect a buzzer to pin 7. This buzzer will activate every time a card is present.

### Firebase Database Setup

For this step you will need to set up a Google account. Make sure you are logged in to your Google account before proceeding.

* Visit the Firebase website: https://firebase.google.com/
* Click "Get Started".
* Click the "Add Project" panel. Enter your project name. This project name is up to you.
* Complete the Project setup. You will be taken to the project's Overview page.
* On the left side of the page, go to Settings -> Project Settings
* Go to Service Accounts -> Firebase Admin SDK -> Generate new Private Key
* You will be given a .json file to download. Place this file alongside the "firb.py" file. Rename this file to: "adminsdk.json".

### WARNING: Please keep this .json file in a secure place. DO NOT share this file with anyone or you might risk giving access to your database to other sources.

Your Firebase Database setup is complete. For more information about Firestore Database, refer to the official manual here: https://firebase.google.com/docs/

You may need to manually delete Collections or Documents from the Database during your testing phase.

### Installing python packages

Open a command console and type:
```
py -m pip install firebase-admin
py -m pip install pyserial
py -m pip install colorama
```

You might need to run these commands as sudo on Linux.

## -Running the tests-
### Setting up config.txt
The config.txt file contains basic configuration. The 'port' parameter refers to the Serial port the Arduino is connected to. In Windows, this value typicaly is COM# where "#" is a basic digit. In Linux, this parameter might be something like:
```
/dev/ttyACM0
```

Example in Windows:
```
port=COM5
baud=9600
timeout=10
bluecard=BB42703B
title="Your title goes here"
message="Custom message goes here"
door=0
```

The Devices and Printers in Windows OS or the Arduino IDE will help you determine which COM port the Arduino is currently in.

<table>
<tbody>
<tr>
<td width="80"><strong>Parameter</strong></td>
<td width="250"><strong>Description</strong></td>
</tr>
<tr>
<td width="80">port</td>
<td width="250">Serial port of the Arduino</td>
</tr>
<tr>
<td width="80">baud</td>
<td width="250">Serial baud rate.</td>
</tr>
<tr>
<td width="80">timeout</td>
<td width="250">Seconds to wait for Arduino connection (Not currently implemented).</td>
</tr>
<tr>
<td width="80">bluecard</td>
<td width="250">The UID of the "Master" card or "Blue Tag"*</td>
</tr>
</tbody>
</table>

*The "bluecard" refers to the special rfid tag that comes with some Arduino toolkits. It is usually blue and comes with a keychain. This can be any type of card with an UID, but in my case I used this blue tag as the "Config" card.

This feature is not fully implemented yet.

### Upload the Arduino sketch

Open the RFID_MOD.ino sketch with Arduino IDE and upload it to the Arduino board.

### Run usercheck.py (as sudo in Linux)
From the Console:

Linux:
```
sudo python3 usercheck.py
```

Windows (Power Shell):
```
py usercheck.py
```

### Admin Console
From the Console:

Linux:
```
sudo python3 usercheck.py admin
```

Windows (Power Shell):
```
py usercheck.py admin
```

This will launch the admin console. You will need to make an admin password if running for the first time.

## Authors

* **Pedro Duquesne** - *Python Code*
* **Miguel Balboa** - *RFID Example Arduino Codes: https://github.com/miguelbalboa*


## Acknowledgments

* CoRe Lab. University of Puerto Rico @ Bayamón. For being AWESOME people.

