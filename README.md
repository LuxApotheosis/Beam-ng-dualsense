# BeamNG DualSense Adaptive Triggers

A Python-based utility using **pydualsense** and **HidHide** to implement PlayStation 5 DualSense adaptive trigger support for BeamNG.drive via telemetry data.

## 🛠 Prerequisites

1.  **Download & Install HidHide**: [HidHide Releases](https://github.com/ViGEm/HidHide/releases)
2.  **Configure HidHide**:
    * Open the **HidHide Configuration Client**.
    * In the **Applications** tab, add your Python executable to the whitelist to allow it to see the controller.
    * *Example Path:* `C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe`
    * In the **Devices** tab, select your DualSense controller and check **"Enable device hiding"** to prevent double-input in-game.

## 🚀 Installation

1. **Clone the project**:
   ```bash
   git clone https://github.com/LuxApotheosis/Beam-ng-dualsense.git
   cd Beam-ng-dualsense
   python -m pip install -r requirements.txt
   python main.py
