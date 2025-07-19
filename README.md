
# 🚀 HackHub Telegram Bot

A comprehensive Telegram bot for managing giveaways with an integrated web dashboard, key system, and analytics.

## ✨ Features

### 🎁 Giveaway Management
- Create unlimited or timed giveaways
- Automatic winner selection
- Participant tracking
- Custom templates
- Real-time participant count updates

### 🔑 Key System
- 24-hour access keys for users
- Key generation and validation
- Automatic key expiration cleanup
- Admin key management interface

### 📊 Web Dashboard
- Real-time bot monitoring
- Giveaway analytics
- User statistics
- System metrics
- Bot control panel
- Dark/light theme support

### 👥 User Management
- User statistics tracking
- Points system (10 points for joining, 100 for winning)
- Leaderboard functionality
- Activity monitoring

## 🏗️ Project Structure

```
├── main.py              # Main bot application
├── web_dashboard.py     # Web dashboard with integrated services
├── database.py          # Database management
├── keysystem.py         # Key system (integrated into dashboard)
├── web_start_bot.py     # Bot control panel
├── start_control.py     # Control panel startup script
├── bot_data.json        # Database file
└── README.md           # This file
```

## 🚀 Quick Start

### 1. Setup Bot Token
1. Create a new bot with [@BotFather](https://t.me/BotFather) on Telegram
2. Get your bot token
3. Replace the token in `main.py`:
```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
```

### 2. Run the Bot
Click the **"Run"** button in Replit or use:
```bash
python main.py
```

### 3. Access Web Services
- **Main Dashboard**: http://0.0.0.0:5000
- **Bot Control Panel**: http://0.0.0.0:7000
- **Key System**: http://0.0.0.0:3000 (integrated into dashboard)

## 🎮 Bot Commands

### User Commands
- `/start` - Get welcome message and 24-hour key
- `/getkey` - Generate new access key
- `/mykey` - Check current key status
- `/create` - Create a new giveaway
- `/list` - List active giveaways
- `/listjoin` - List participant counts
- `/points` - Check your points
- `/leaderboard` - View top participants

### Admin Commands
- `/end [message_id]` - End unlimited giveaway manually

## 🌐 Web Dashboard Features

### Dashboard (Port 5000)
- **Overview**: Active giveaways, statistics
- **Analytics**: User engagement, participation trends
- **Bot Control**: Start/stop bot remotely
- **Players**: User management and statistics
- **Keys**: Key system management
- **System**: Performance metrics

**Login Credentials:**
- Username: `man`
- Password: `23148`

### Bot Control Panel (Port 7000)
- Start/stop bot remotely
- Real-time bot status monitoring
- System resource usage
- Quick access to all services

## 🔑 Key System

The bot uses a 24-hour key system for access control:

1. **New users** get a free 24-hour key with `/start`
2. **Existing users** can generate new keys with `/getkey`
3. **Keys expire** automatically after 24 hours
4. **Admin panel** available for manual key management

### Key Management
- Generate custom duration keys
- Revoke active keys
- View all active/expired keys
- User activity tracking

## 📊 Database Structure

The bot uses JSON-based storage with the following structure:

```json
{
  "active_giveaways": {},      // Current running giveaways
  "participants": {},          // Giveaway participants
  "completed_giveaways": [],   // Historical giveaways
  "user_stats": {},           // User statistics
  "winners_history": [],      // Winner records
  "user_keys": {},           // Access keys
  "system_stats": {}         // System metrics
}
```

## ⚙️ Configuration

### Admin Credentials
Update credentials in the respective files:

**Web Dashboard** (`web_dashboard.py`):
```python
ADMIN_USERNAME = "man"
ADMIN_PASSWORD = "23148"
```

**Key System** (`keysystem.py`):
```python
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "keysystem123"
```

### Port Configuration
- **Bot Dashboard**: 5000 (forwarded to 80/443 in production)
- **Key System**: 3000 (integrated into dashboard)
- **Bot Control**: 7000
- **Keep Alive**: 8080

## 🛠️ Development

### Adding New Features
1. **Bot Commands**: Add handlers in `main.py`
2. **Web Features**: Extend templates in `web_dashboard.py`
3. **Database**: Add methods in `database.py`

### Customization
- **Templates**: Modify HTML templates in the Python files
- **Styling**: Update CSS in the template strings
- **Bot Messages**: Edit message text in `main.py`

## 🔒 Security Features

- **Key-based access control**
- **Session management**
- **Input validation**
- **XSS protection**
- **Automatic cleanup of expired data**
- **Bot process locking** (prevents multiple instances)

## 📱 Mobile Support

The web dashboard is fully responsive and optimized for:
- Mobile devices
- Tablets
- Desktop computers
- Dark/light theme switching

## 🚀 Deployment on Replit

### Using Workflows
1. **Run Bot**: Starts the main bot application
2. **Bot Control Panel**: Launches the control interface
3. **Bot Control Panel Enhanced**: Alternative control interface

### Environment Setup
The project is configured for Replit with:
- Python 3.11 runtime
- Automatic dependency management
- Port forwarding configuration
- Production deployment settings

## 📈 Analytics & Monitoring

### Built-in Analytics
- **User engagement metrics**
- **Giveaway participation rates**
- **System performance monitoring**
- **Real-time bot status**
- **Resource usage tracking**

### Data Insights
- Top participants
- Win rates
- Activity patterns
- System health

## 🔧 Troubleshooting

### Common Issues

**Bot not responding:**
1. Check bot token is correct
2. Ensure bot is started via dashboard
3. Verify network connectivity

**Web dashboard not accessible:**
1. Check if port 5000 is running
2. Verify login credentials
3. Try accessing via different port (5001 backup)

**Key system issues:**
1. Keys expire after 24 hours automatically
2. Use `/getkey` to generate new key
3. Admin can manage keys via dashboard

### Logs and Debugging
- Bot logs are displayed in console
- Web dashboard shows real-time status
- Database operations are logged
- Error handling with graceful recovery

## 📝 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Test your changes thoroughly
4. Submit a pull request

## 📞 Support

For support and questions:
- Check the troubleshooting section
- Review the code documentation
- Test in the Replit environment

---

**🚀 Ready to launch your giveaway bot? Click the Run button and start engaging your community!**
