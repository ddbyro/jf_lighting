# Jellyfish Lighting API Documentation

## Purpose
The Jellyfish Lighting API allows you to interact with the Jellyfish Lighting System over a Local Area Network using JSON requests and responses via WebSockets. You can control patterns, run patterns, adjust pattern parameters, power the system on/off, and more.

## Summary
- Communication is via JSON over WebSockets.
- Commands are sent from the client to the controller and responses are sent back.
- Main command directions:
  - `toCtlrGet`: Client requests data from the controller.
  - `toCtlrSet`: Client sends commands to change controller state.
  - `fromCtlr`: Controller sends responses/data to the client.

## Command Structure
Each command consists of:
1. **Direction**: The `cmd` key, with values `toCtlrGet`, `toCtlrSet`, or `fromCtlr`.
2. **Command**: The action, such as `get`, `runPattern`, etc.

## Common Commands

### Get Pattern List
- **Request:**
  ```json
  {"cmd": "toCtlrGet", "get": [["patternFileList"]]}
  ```
- **Response:**
  ```json
  {"cmd":"fromCtlr","patternFileList":[{"folders":"<folderName>","name":"<patternName>","readOnly":<readOnlyValue>}]}
  ```

### Get Zone List
- **Request:**
  ```json
  {"cmd": "toCtlrGet", "get": [["zones"]]}
  ```
- **Response:**
  ```json
  {"cmd":"fromCtlr","save":true,"zones":{...}}
  ```

### Run Given Pattern
- **Request:**
  ```json
  {"cmd":"toCtlrSet","runPattern":{"file":"<folderName>/<patternName>","data":"","id":"","state":1,"zoneName":[]}}
  ```
- **Response:**
  ```json
  {"cmd":"fromCtlr","runPattern":{...}}
  ```

### Get Pattern File Data
- **Request:**
  ```json
  {"cmd":"toCtlrGet", "get":[["patternFileData", "<folder>", "<patternName>"]]}
  ```
- **Response:**
  ```json
  {"cmd":"fromCtlr","patternFileData":{...}}
  ```

## Examples

### Example 1: Get Pattern List, Get Zone List, Run Pattern
1. **Get Pattern List**
    - Request: `{ "cmd": "toCtlrGet", "get": [["patternFileList"]] }`
    - Response: `{ "cmd": "fromCtlr", "patternFileList": [...] }`
2. **Get Zone List**
    - Request: `{ "cmd": "toCtlrGet", "get": [["zones"]] }`
    - Response: `{ "cmd": "fromCtlr", "zones": {...} }`
3. **Run Pattern**
    - Request: `{ "cmd": "toCtlrSet", "runPattern": { "file": "Christmas/Christmas Tree", "data": "", "id": "", "state": 1, "zoneName": ["Zone", "Zone1"] } }`

### Example 2: Adjust a Running Pattern
1. **Get Pattern File Data**
    - Request: `{ "cmd": "toCtlrGet", "get": [["patternFileData", "Legacy", "Red Yellow Green Blue"]] }`
    - Response: `{ "cmd": "fromCtlr", "patternFileData": {...} }`
2. **Run Pattern with Adjustments**
    - Request: `{ "cmd": "toCtlrSet", "runPattern": { "file": "", "data": "{...}", "id": "", "state": 1, "zoneName": ["Zone", "Zone1"] } }`

## Command Parameters and Data Fields

### Get Pattern File List
- `cmd`: "toCtlrGet"
- `get`: [["patternFileList"]]

### Get Zones
- `cmd`: "toCtlrGet"
- `get`: [["zones"]]

### Run Pattern (Basic)
- `cmd`: "toCtlrSet"
- `runPattern`: {
    - `file`: "<folder>/<fileName>"
    - `data`: ""
    - `id`: ""
    - `state`: 1 (on) or 0 (off)
    - `zoneName`: ["zone1", "zone2", ...]
  }

### Run Pattern (Advanced)
- `cmd`: "toCtlrSet"
- `runPattern`: {
    - `file`: ""
    - `data`: JSON string with fields:
        - `colors`: [R, G, B, ...]
        - `spaceBetweenPixels`: int
        - `effectBetweenPixels`: string
        - `type`: string
        - `skip`: int
        - `numOfLeds`: int
        - `runData`: {
            - `speed`: int
            - `brightness`: int
            - `effect`: "No Effect"
            - `effectValue`: 0
            - `rgbAdj`: [100, 100, 100]
          }
        - `direction`: "Left" or "Right"
    - `id`: ""
    - `state`: int
    - `zoneName`: ["zone1", ...]
  }

### Get Pattern File Data
- `cmd`: "toCtlrGet"
- `get`: [["patternFileData", "<folderName>", "<fileName>"]]

## Field Details
- **file**: Path to pattern file, e.g. "Christmas/Christmas Tree"
- **data**: JSON string with pattern parameters (advanced)
- **state**: 1 (on), 0 (off)
- **zoneName**: List of zone names
- **colors**: List of RGB values (length must be multiple of 3)
- **spaceBetweenPixels**: Integer
- **effectBetweenPixels**: "No Color Transformation", "Repeat", "Progression", "Fade", "Fill with Black"
- **type**: "Color", "Chase", "Paint", "Stacker", "Sequence", "Multi-Paint"
- **skip**: Integer
- **numOfLeds**: Integer (for Multi-Paint)
- **runData**: Map with speed, brightness, etc.
- **direction**: "Left" or "Right"

## Conclusion
The Jellyfish Lighting API provides robust control and customization of your lighting system. Use the above commands and field descriptions to interact with the system. For further exploration, use a WebSocket tester or the API Explorer application.

