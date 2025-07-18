
import json
import os
import time
import random
import string
from datetime import datetime, timedelta
import threading

class Database:
    def __init__(self, filename='bot_data.json'):
        self.filename = filename
        self.data = {}
        self.lock = threading.Lock()
        self.load_data()

    def load_data(self):
        """Load data from JSON file with enhanced error handling"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        self.data = json.loads(content)
                        print(f"✅ Database loaded successfully: {len(self.data)} keys")
                    else:
                        print("⚠️ Database file is empty, initializing...")
                        self.initialize_data()
            else:
                print("📁 Database file not found, creating new one...")
                self.initialize_data()
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            print("🔄 Creating backup and initializing new database...")
            self.backup_and_reset()
        except Exception as e:
            print(f"❌ Database load error: {e}")
            self.initialize_data()

    def backup_and_reset(self):
        """Create backup of corrupted file and reset database"""
        try:
            if os.path.exists(self.filename):
                backup_name = f"{self.filename}.backup_{int(time.time())}"
                os.rename(self.filename, backup_name)
                print(f"📦 Backup created: {backup_name}")
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
        
        self.initialize_data()

    def initialize_data(self):
        """Initialize database with default structure"""
        self.data = {
            'active_giveaways': {},
            'participants': {},
            'completed_giveaways': [],
            'user_stats': {},
            'last_updated': datetime.now().isoformat(),
            'winners_history': [],
            'user_keys': {},
            'system_stats': {
                'total_giveaways_created': 0,
                'total_participants': 0,
                'uptime_start': datetime.now().isoformat()
            }
        }
        self.save_data()
        print("🆕 Database initialized with default structure")

    def save_data(self):
        """Save data to JSON file with atomic write and error handling"""
        try:
            with self.lock:
                # Update last_updated timestamp
                self.data['last_updated'] = datetime.now().isoformat()
                
                # Write to temporary file first (atomic write)
                temp_filename = f"{self.filename}.tmp"
                with open(temp_filename, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=2, ensure_ascii=False)
                
                # Replace original file with temporary file
                if os.path.exists(self.filename):
                    os.replace(temp_filename, self.filename)
                else:
                    os.rename(temp_filename, self.filename)
                
                print(f"💾 Database saved successfully")
        except Exception as e:
            print(f"❌ Database save error: {e}")
            # Clean up temp file if it exists
            if os.path.exists(f"{self.filename}.tmp"):
                os.remove(f"{self.filename}.tmp")

    def add_giveaway(self, message_id, giveaway_data):
        """Add a new giveaway with enhanced error handling"""
        try:
            msg_id_str = str(message_id)
            self.data['active_giveaways'][msg_id_str] = giveaway_data
            self.data['participants'][msg_id_str] = []
            
            # Update system stats
            if 'system_stats' not in self.data:
                self.data['system_stats'] = {}
            self.data['system_stats']['total_giveaways_created'] = self.data['system_stats'].get('total_giveaways_created', 0) + 1
            
            self.save_data()
            print(f"✅ Giveaway {message_id} added successfully")
        except Exception as e:
            print(f"❌ Error adding giveaway {message_id}: {e}")

    def add_participant(self, message_id, user_id, user_name):
        """Add participant with enhanced validation and error handling"""
        try:
            msg_id_str = str(message_id)
            
            if msg_id_str not in self.data['participants']:
                self.data['participants'][msg_id_str] = []

            # Check if user already participated
            for participant in self.data['participants'][msg_id_str]:
                if participant.get('user_id') == user_id:
                    print(f"⚠️ User {user_id} already participated in giveaway {message_id}")
                    return False

            participant_data = {
                'user_id': user_id,
                'user_name': user_name,
                'joined_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.data['participants'][msg_id_str].append(participant_data)
            
            # Update user stats
            self.update_user_stats(user_id, user_name, 'participation')
            
            self.save_data()
            print(f"✅ Participant {user_name} ({user_id}) added to giveaway {message_id}")
            return True
        except Exception as e:
            print(f"❌ Error adding participant {user_id} to giveaway {message_id}: {e}")
            return False

    def update_user_stats(self, user_id, user_name, action):
        """Update user statistics with enhanced tracking"""
        try:
            user_id_str = str(user_id)
            
            if user_id_str not in self.data['user_stats']:
                self.data['user_stats'][user_id_str] = {
                    'name': user_name,
                    'total_participations': 0,
                    'total_wins': 0,
                    'first_join': datetime.now().strftime('%Y-%m-%d'),
                    'last_activity': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

            # Update name in case it changed
            self.data['user_stats'][user_id_str]['name'] = user_name
            self.data['user_stats'][user_id_str]['last_activity'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if action == 'participation':
                self.data['user_stats'][user_id_str]['total_participations'] += 1
            elif action == 'win':
                self.data['user_stats'][user_id_str]['total_wins'] += 1

            print(f"📊 Updated stats for {user_name}: {action}")
        except Exception as e:
            print(f"❌ Error updating user stats for {user_id}: {e}")

    def record_winner(self, user_id, giveaway_title):
        """Record winner with enhanced tracking"""
        try:
            # Update user stats
            user_id_str = str(user_id)
            if user_id_str in self.data['user_stats']:
                self.update_user_stats(user_id, self.data['user_stats'][user_id_str]['name'], 'win')

            # Add to winners history
            if 'winners_history' not in self.data:
                self.data['winners_history'] = []

            winner_record = {
                'user_id': user_id,
                'giveaway_title': giveaway_title,
                'won_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.data['winners_history'].append(winner_record)
            
            # Keep only last 100 winners
            if len(self.data['winners_history']) > 100:
                self.data['winners_history'] = self.data['winners_history'][-100:]

            self.save_data()
            print(f"🏆 Winner recorded: User {user_id} won '{giveaway_title}'")
        except Exception as e:
            print(f"❌ Error recording winner {user_id}: {e}")

    def remove_giveaway(self, message_id):
        """Remove giveaway and move to completed with enhanced error handling"""
        try:
            msg_id_str = str(message_id)
            
            giveaway_data = self.data['active_giveaways'].get(msg_id_str)
            participants_data = self.data['participants'].get(msg_id_str, [])

            if giveaway_data:
                # Move to completed giveaways
                completed_giveaway = giveaway_data.copy()
                completed_giveaway['participants'] = participants_data
                completed_giveaway['completed_at'] = datetime.now().isoformat()
                completed_giveaway['message_id'] = message_id

                if 'completed_giveaways' not in self.data:
                    self.data['completed_giveaways'] = []
                
                self.data['completed_giveaways'].append(completed_giveaway)

                # Keep only last 50 completed giveaways
                if len(self.data['completed_giveaways']) > 50:
                    self.data['completed_giveaways'] = self.data['completed_giveaways'][-50:]

                # Remove from active
                del self.data['active_giveaways'][msg_id_str]
                if msg_id_str in self.data['participants']:
                    del self.data['participants'][msg_id_str]

                self.save_data()
                print(f"✅ Giveaway {message_id} moved to completed")
            else:
                print(f"⚠️ Giveaway {message_id} not found in active giveaways")
        except Exception as e:
            print(f"❌ Error removing giveaway {message_id}: {e}")

    def generate_user_key(self, user_id, user_name):
        """Generate user key with enhanced security and tracking"""
        try:
            # Generate random 16-character key
            key = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            
            user_id_str = str(user_id)
            expiry_time = datetime.now() + timedelta(hours=24)
            
            key_data = {
                'key': key,
                'user_name': user_name,
                'generated_at': datetime.now().isoformat(),
                'expires_at': expiry_time.isoformat(),
                'is_active': True
            }
            
            if 'user_keys' not in self.data:
                self.data['user_keys'] = {}
                
            self.data['user_keys'][user_id_str] = key_data
            self.save_data()
            
            print(f"🔑 Generated key for {user_name} ({user_id}): {key}")
            return key
        except Exception as e:
            print(f"❌ Error generating key for user {user_id}: {e}")
            return None

    def validate_user_key(self, user_id):
        """Validate user key with enhanced checking"""
        try:
            user_id_str = str(user_id)
            
            if user_id_str not in self.data.get('user_keys', {}):
                return False
                
            key_data = self.data['user_keys'][user_id_str]
            
            if not key_data.get('is_active', False):
                return False
                
            expiry_time = datetime.fromisoformat(key_data['expires_at'])
            
            if datetime.now() > expiry_time:
                # Mark as expired
                key_data['is_active'] = False
                self.save_data()
                print(f"🔑 Key expired for user {user_id}")
                return False
                
            return True
        except Exception as e:
            print(f"❌ Error validating key for user {user_id}: {e}")
            return False

    def get_user_key(self, user_id):
        """Get user key with error handling"""
        try:
            user_id_str = str(user_id)
            
            if user_id_str in self.data.get('user_keys', {}):
                key_data = self.data['user_keys'][user_id_str]
                if key_data.get('is_active', False):
                    return key_data['key']
            return None
        except Exception as e:
            print(f"❌ Error getting key for user {user_id}: {e}")
            return None

    def cleanup_expired_keys(self):
        """Clean up expired keys with enhanced logging"""
        try:
            if 'user_keys' not in self.data:
                return
                
            expired_count = 0
            current_time = datetime.now()
            
            for user_id, key_data in list(self.data['user_keys'].items()):
                try:
                    expiry_time = datetime.fromisoformat(key_data['expires_at'])
                    if current_time > expiry_time:
                        del self.data['user_keys'][user_id]
                        expired_count += 1
                except Exception as e:
                    print(f"❌ Error processing key for user {user_id}: {e}")
                    # Remove malformed key data
                    del self.data['user_keys'][user_id]
                    expired_count += 1
            
            if expired_count > 0:
                self.save_data()
                print(f"🧹 Cleaned up {expired_count} expired keys")
        except Exception as e:
            print(f"❌ Error during key cleanup: {e}")

    def get_analytics_data(self):
        """Get comprehensive analytics data"""
        try:
            analytics = {
                'total_users': len(self.data.get('user_stats', {})),
                'total_giveaways': len(self.data.get('completed_giveaways', [])),
                'active_giveaways': len(self.data.get('active_giveaways', {})),
                'total_participations': sum(stats.get('total_participations', 0) for stats in self.data.get('user_stats', {}).values()),
                'total_wins': sum(stats.get('total_wins', 0) for stats in self.data.get('user_stats', {}).values()),
                'active_keys': len([k for k in self.data.get('user_keys', {}).values() if k.get('is_active', False)]),
                'system_uptime': self.data.get('system_stats', {}).get('uptime_start', datetime.now().isoformat())
            }
            return analytics
        except Exception as e:
            print(f"❌ Error getting analytics data: {e}")
            return {}

# Create global database instance
db = Database()
