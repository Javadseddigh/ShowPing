# PingMonitor - Real-time Network Ping Monitor  

![PingMonitor Screenshot]([https://via.placeholder.com/800x400.png?text=PingMonitor+Demo](http://5.57.32.66:5000/uploads/Screenshot_2025-04-20_072104.png))  

A lightweight system tray application that monitors your network latency in real-time.  

## Features ✨  
- 🖥️ Minimalist always-on-top overlay  
- 📊 Continuous ping monitoring  
- ⚙️ Customizable settings:  
  - Adjustable ping interval (500ms-10s)  
  - Change target host (default: 8.8.8.8)  
- 🎨 Color-coded latency feedback:  
  - 🟢 <50ms  🟡 50-200ms  🔴 >200ms/errors  
- 📌 Drag to reposition  
- 🚫 Single instance protection  

## Installation 🛠️  
### Windows  
1. Download the latest `.exe` from [Releases]()  
2. Double-click to run  

### Linux (Requires Python 3.8+)  
```bash
git clone https://github.com/yourusername/PingMonitor.git
cd PingMonitor
pip install PyQt6
python main.py
