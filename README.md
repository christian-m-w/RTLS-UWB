# RTLS-UWB Visualiser
This application provides a graphical user interface (GUI) for visualising the data from the Qorvo DWM1001C Ultra-Wideband (UWB) Transceivers.

## Overview/Features
- Visualising serial data from a UWB tag over USB
- Logging of serial data to CSV
- Replaying of recorded CSV data

## System Requirements
**Operating System:** Windows 10 or later
**Python Version:** Python 3.13 (Recommended)

## Required Packages
* PySerial
* PyQt6
* Matplotlib

## Installation

1. Install Python 3.13
2. Install Required Packages (Either Manually or through the `requirements.txt`)
   a) Manually
    `pip install pyserial`
    `pip install pyqt6`
    `pip install matplotlib`

   b) Through the `requirements.txt` 
    `pip install -r requirements.txt`

## Usage
To launch the visualiser, run the following command from the root directory
`python "./UWB Visualiser/main.py"`

## Floorplan Configurations
Floorplan configurations can be created as JSON files and saved in the `configurations` directory.

*FP_IMAGE_PATH:* - Is the relative or absolute file path to the floorplan image.
*FP_ORIGIN_X_IN_PIXELS:* - The X-Value of the origin on the image measured in pixels from the left.
*FP_ORIGIN_Y_IN_PIXELS:* - The Y-Value of the origin on the image measured from the top.
*FP_10M_IN_PIXELS:* - Scales the image to accurately position the Tags and Anchors on the floorplan. Can be calculated by measuring the number of pixels on the image that represents 10 meters.

```json
{
"FP_IMAGE_PATH": "./floorplans/default-floorplan.png",
"FP_ORIGIN_X_IN_PIXELS": "10",
"FP_ORIGIN_Y_IN_PIXELS": "310",
"FP_10M_IN_PIXELS": "1000"
}
```

## Data Logging
Positional data from the serial ports can be saved to CSV files in the `logs` directory.
The application can record up to 4 tags at once.

### Filename format
`{Year}-{Month}-{Day}-{Hour24}-{Min}-{Second}-{COM Port Number}.csv`

*Example:* `2025-09-28-09-58-51-5.csv`

### Data format
`{Timestamp},{Number of Anchors},{Positional Data of Anchors},{Tag Position},{Quality Factor}`

*Timestamp:* Time since receiving data began.
*Number of Anchors:* The number of anchors used in the position calculation, this can be 3 or 4.
*Positional Data of Anchors:* (Includes Data for the 3 or 4 Anchors used in the calculation) 
    - The last 4 characters of the Anchor Hardware ID.
    - X, Y, Z coordinates of the Anchor in meters.
    - How many meters the Anchor is from the Tag.
*Tag Position:* X, Y, Z coordinates of the Tag in meters.
*Quality Factor:* Tag Position Quality Factor in percent.

*Example:*`0.073,4,949C,3.37,3.8,1.99,1.73,4818,0.65,2.49,2.1,2.52,DBA4,0.52,5.3,2.12,2.71,4B05,2.07,6.9,2.01,3.53,2.22,3.69,0.61,34`

Timestamp: 0.073 seconds
Number of Anchors used in the position calculation: 4
Anchor 1: `949C,3.37,3.8,1.99,1.73`
- ID: 949C
- X, Y, Z Position (m): 3.37, 3.8, 1.99
- Distance from the Tag (m): 1.73
Anchor 2: `4818,0.65,2.49,2.1,2.52`
- ID: 4818
- X, Y, Z Position (m): 0.65, 2.49, 2.1
- Distance from the Tag (m): 2.52
Anchor 3: `DBA4,0.52,5.3,2.12,2.71`
- ID: DBA4
- X, Y, Z Position (m): 0.52, 5.3, 2.12
- Distance from the Tag (m): 2.71
Anchor 4: `4B05,2.07,6.9,2.01,3.53`
- ID: 4B05
- X, Y, Z Position (m): 2.07, 6.9, 2.01
- Distance from the Tag (m): 3.53
Tag (X, Y, Z) Position (m): 2.22, 3.69, 0.61 
Quality Factor %: 34%