
#!/usr/bin/env python3
"""
Simple startup script for HackHub Bot Control Panel
Run this to start the web-based bot control interface
"""

from web_start_bot import start_web_control

if __name__ == '__main__':
    print("🚀 Starting HackHub Bot Control Panel...")
    print("🌐 Access the control panel at: http://localhost:7000")
    print("🎮 Use the web interface to start/stop your bot")
    print("=" * 50)
    
    start_web_control()
