# Ekospex Assistive System

Ekospex is an advanced assistive system designed to provide real-time guidance and support to visually impaired individuals. This project was developed by Roshan ,Sukanth, Rithick, Yasir, Kathir, and Mohsin, students of Sathyabama University from class AI A3.

## Features

- Real-time environment analysis
- Audio feedback about surroundings
- Obstacle detection and warning
- Continuous operation

## Installation

1. Clone this repository to your Raspberry Pi:
   ```
   git clone https://github.com/roshan-san/ekospex.git
   cd ekospex
   ```

2. Activate the existing virtual environment:
   ```
   source ven/bin/activate
   ```

3. Make the installation script executable and run it:
   ```
   chmod +x install_ekospex_service.sh
   ./install_ekospex_service.sh
   ```

## Running as a Service

The installation script sets up Ekospex to run automatically when your Raspberry Pi boots up. The service will:

- Start automatically at boot
- Restart automatically if it crashes
- Log output to the system log

### Managing the Service

- Check the status: `sudo systemctl status ekospex.service`
- Stop the service: `sudo systemctl stop ekospex.service`
- Start the service: `sudo systemctl start ekospex.service`
- Restart the service: `sudo systemctl restart ekospex.service`
- Disable autostart: `sudo systemctl disable ekospex.service`
- Enable autostart: `sudo systemctl enable ekospex.service`

### Viewing Logs

To view the logs:
```
sudo journalctl -u ekospex.service
```

To follow the logs in real-time:
```
sudo journalctl -u ekospex.service -f
```

## Manual Operation

If you want to run Ekospex manually instead of as a service:

1. Activate the virtual environment:
   ```
   source ven/bin/activate
   ```

2. Run the application:
   ```
   python eko.py
   ```

## Requirements

- Raspberry Pi 64bit
- Camera module
- Microphone
- Speakers
- Internet connection
- Google API key with access to Gemini API
