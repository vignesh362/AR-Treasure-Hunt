#!/usr/bin/env python3
"""
MongoDB Database Operations for User Management
CRUD operations for user basic information
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserDatabase:
    def __init__(self, connection_string: str = None, database_name: str = "treasure_hunt_db"):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
        """
        self.database_name = database_name
        self.client = None
        self.db = None
        self.users_collection = None
        
        # Default connection string (replace with your actual credentials)
        if not connection_string:
            # Using the credentials from the image
            username = "sorgavasalidiots_db_user"
            password = "Password"
            cluster_url = "cluster0.mongodb.net"  # Replace with your actual cluster URL
            connection_string = f"mongodb+srv://{username}:{password}@{cluster_url}/?retryWrites=true&w=majority"
        
        self.connection_string = connection_string
        self.connect()
    
    def connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            self.users_collection = self.db.users
            
            # Create indexes for better performance
            self.users_collection.create_index("email", unique=True)
            self.users_collection.create_index("username", unique=True)
            
            logger.info("✅ Successfully connected to MongoDB")
            
        except ConnectionFailure as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to MongoDB: {e}")
            raise
    
    def disconnect(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("🔌 Disconnected from MongoDB")
    
    # CREATE Operations
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Dictionary with created user info and success status
        """
        try:
            # Validate required fields
            required_fields = ['username', 'email', 'first_name', 'last_name']
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Add metadata
            user_data['created_at'] = datetime.utcnow()
            user_data['updated_at'] = datetime.utcnow()
            user_data['is_active'] = True
            
            # Insert user
            result = self.users_collection.insert_one(user_data)
            
            logger.info(f"✅ User created successfully: {user_data['username']}")
            return {
                'success': True,
                'user_id': str(result.inserted_id),
                'username': user_data['username'],
                'email': user_data['email'],
                'message': 'User created successfully'
            }
            
        except DuplicateKeyError as e:
            logger.error(f"❌ Duplicate user error: {e}")
            return {
                'success': False,
                'error': 'User with this email or username already exists',
                'message': 'Duplicate user error'
            }
        except Exception as e:
            logger.error(f"❌ Error creating user: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create user'
            }
    
    # READ Operations
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        
        Args:
            user_id: User ID string
            
        Returns:
            User document or None if not found
        """
        try:
            from bson import ObjectId
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])  # Convert ObjectId to string
            return user
        except Exception as e:
            logger.error(f"❌ Error getting user by ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        
        Args:
            email: User email
            
        Returns:
            User document or None if not found
        """
        try:
            user = self.users_collection.find_one({"email": email})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"❌ Error getting user by email: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get user by username
        
        Args:
            username: Username
            
        Returns:
            User document or None if not found
        """
        try:
            user = self.users_collection.find_one({"username": username})
            if user:
                user['_id'] = str(user['_id'])
            return user
        except Exception as e:
            logger.error(f"❌ Error getting user by username: {e}")
            return None
    
    def get_all_users(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all users with pagination
        
        Args:
            limit: Maximum number of users to return
            skip: Number of users to skip
            
        Returns:
            List of user documents
        """
        try:
            users = list(self.users_collection.find().skip(skip).limit(limit))
            for user in users:
                user['_id'] = str(user['_id'])
            return users
        except Exception as e:
            logger.error(f"❌ Error getting all users: {e}")
            return []
    
    def search_users(self, query: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search users with custom query
        
        Args:
            query: MongoDB query dictionary
            limit: Maximum number of results
            
        Returns:
            List of matching user documents
        """
        try:
            users = list(self.users_collection.find(query).limit(limit))
            for user in users:
                user['_id'] = str(user['_id'])
            return users
        except Exception as e:
            logger.error(f"❌ Error searching users: {e}")
            return []
    
    # UPDATE Operations
    def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information
        
        Args:
            user_id: User ID string
            update_data: Dictionary with fields to update
            
        Returns:
            Dictionary with update result
        """
        try:
            from bson import ObjectId
            
            # Add update timestamp
            update_data['updated_at'] = datetime.utcnow()
            
            # Remove fields that shouldn't be updated
            update_data.pop('_id', None)
            update_data.pop('created_at', None)
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            logger.info(f"✅ User updated successfully: {user_id}")
            return {
                'success': True,
                'modified_count': result.modified_count,
                'message': 'User updated successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating user: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update user'
            }
    
    def update_user_by_email(self, email: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user by email
        
        Args:
            email: User email
            update_data: Dictionary with fields to update
            
        Returns:
            Dictionary with update result
        """
        try:
            update_data['updated_at'] = datetime.utcnow()
            update_data.pop('_id', None)
            update_data.pop('created_at', None)
            
            result = self.users_collection.update_one(
                {"email": email},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            logger.info(f"✅ User updated successfully: {email}")
            return {
                'success': True,
                'modified_count': result.modified_count,
                'message': 'User updated successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error updating user by email: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update user'
            }
    
    # DELETE Operations
    def delete_user(self, user_id: str) -> Dict[str, Any]:
        """
        Delete user by ID
        
        Args:
            user_id: User ID string
            
        Returns:
            Dictionary with delete result
        """
        try:
            from bson import ObjectId
            
            result = self.users_collection.delete_one({"_id": ObjectId(user_id)})
            
            if result.deleted_count == 0:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            logger.info(f"✅ User deleted successfully: {user_id}")
            return {
                'success': True,
                'deleted_count': result.deleted_count,
                'message': 'User deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting user: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to delete user'
            }
    
    def delete_user_by_email(self, email: str) -> Dict[str, Any]:
        """
        Delete user by email
        
        Args:
            email: User email
            
        Returns:
            Dictionary with delete result
        """
        try:
            result = self.users_collection.delete_one({"email": email})
            
            if result.deleted_count == 0:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            logger.info(f"✅ User deleted successfully: {email}")
            return {
                'success': True,
                'deleted_count': result.deleted_count,
                'message': 'User deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error deleting user by email: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to delete user'
            }
    
    # Utility Methods
    def get_user_count(self) -> int:
        """Get total number of users"""
        try:
            return self.users_collection.count_documents({})
        except Exception as e:
            logger.error(f"❌ Error getting user count: {e}")
            return 0
    
    def get_active_users_count(self) -> int:
        """Get number of active users"""
        try:
            return self.users_collection.count_documents({"is_active": True})
        except Exception as e:
            logger.error(f"❌ Error getting active users count: {e}")
            return 0
    
    def deactivate_user(self, user_id: str) -> Dict[str, Any]:
        """Deactivate user (soft delete)"""
        return self.update_user(user_id, {"is_active": False})
    
    def activate_user(self, user_id: str) -> Dict[str, Any]:
        """Activate user"""
        return self.update_user(user_id, {"is_active": True})
    
    # Game-Specific Functions for AR Treasure Hunt
    
    def get_number_of_wins(self, user_id: str) -> int:
        """
        Get the number of wins for a user
        
        Args:
            user_id: User ID string
            
        Returns:
            Number of wins
        """
        try:
            from bson import ObjectId
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return user.get('wins', 0)
            return 0
        except Exception as e:
            logger.error(f"❌ Error getting number of wins: {e}")
            return 0
    
    def add_win(self, user_id: str, game_type: str = "treasure_hunt", points: int = 10) -> Dict[str, Any]:
        """
        Add a win to user's record
        
        Args:
            user_id: User ID string
            game_type: Type of game won (treasure_hunt, riddle_solved, etc.)
            points: Points earned for this win
            
        Returns:
            Dictionary with result
        """
        try:
            from bson import ObjectId
            
            # Get current user data
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Update wins count and total points
            current_wins = user.get('wins', 0)
            current_points = user.get('total_points', 0)
            
            update_data = {
                'wins': current_wins + 1,
                'total_points': current_points + points,
                'updated_at': datetime.utcnow()
            }
            
            result = self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            # Log the win
            self.log_game_event(user_id, "win", {
                "game_type": game_type,
                "points_earned": points,
                "total_wins": current_wins + 1,
                "total_points": current_points + points
            })
            
            logger.info(f"✅ Win added for user {user_id}: {game_type}")
            return {
                'success': True,
                'new_wins_count': current_wins + 1,
                'new_total_points': current_points + points,
                'points_earned': points,
                'message': 'Win recorded successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error adding win: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to add win'
            }
    
    def log_game_event(self, user_id: str, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Log a game event
        
        Args:
            user_id: User ID string
            event_type: Type of event (win, loss, riddle_solved, treasure_found, etc.)
            event_data: Additional event data
            
        Returns:
            Dictionary with result
        """
        try:
            from bson import ObjectId
            
            event_log = {
                "user_id": ObjectId(user_id),
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": datetime.utcnow(),
                "created_at": datetime.utcnow()
            }
            
            # Insert into game_logs collection
            result = self.db.game_logs.insert_one(event_log)
            
            logger.info(f"✅ Game event logged: {event_type} for user {user_id}")
            return {
                'success': True,
                'log_id': str(result.inserted_id),
                'message': 'Event logged successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ Error logging game event: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to log event'
            }
    
    def get_user_game_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive game statistics for a user
        
        Args:
            user_id: User ID string
            
        Returns:
            Dictionary with game statistics
        """
        try:
            from bson import ObjectId
            
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return {
                    'success': False,
                    'message': 'User not found'
                }
            
            # Get game logs for this user
            game_logs = list(self.db.game_logs.find({"user_id": ObjectId(user_id)}))
            
            # Calculate statistics
            total_wins = user.get('wins', 0)
            total_points = user.get('total_points', 0)
            total_events = len(game_logs)
            
            # Count different event types
            event_counts = {}
            for log in game_logs:
                event_type = log.get('event_type', 'unknown')
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # Get recent activity (last 10 events)
            recent_events = sorted(game_logs, key=lambda x: x['timestamp'], reverse=True)[:10]
            
            return {
                'success': True,
                'user_id': user_id,
                'username': user.get('username', 'Unknown'),
                'total_wins': total_wins,
                'total_points': total_points,
                'total_events': total_events,
                'event_breakdown': event_counts,
                'recent_activity': [
                    {
                        'event_type': event.get('event_type'),
                        'timestamp': event.get('timestamp'),
                        'data': event.get('event_data', {})
                    } for event in recent_events
                ],
                'rank': self.get_user_rank(user_id)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting user game stats: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to get game statistics'
            }
    
    def get_user_rank(self, user_id: str) -> int:
        """
        Get user's rank based on total points
        
        Args:
            user_id: User ID string
            
        Returns:
            User's rank (1 = highest)
        """
        try:
            from bson import ObjectId
            
            user = self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                return 0
            
            user_points = user.get('total_points', 0)
            
            # Count users with more points
            higher_ranked = self.users_collection.count_documents({
                "total_points": {"$gt": user_points}
            })
            
            return higher_ranked + 1
            
        except Exception as e:
            logger.error(f"❌ Error getting user rank: {e}")
            return 0
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get leaderboard of top players
        
        Args:
            limit: Number of top players to return
            
        Returns:
            List of top players with their stats
        """
        try:
            top_players = list(self.users_collection.find(
                {"is_active": True}
            ).sort("total_points", -1).limit(limit))
            
            leaderboard = []
            for i, player in enumerate(top_players, 1):
                leaderboard.append({
                    'rank': i,
                    'user_id': str(player['_id']),
                    'username': player.get('username', 'Unknown'),
                    'total_points': player.get('total_points', 0),
                    'wins': player.get('wins', 0),
                    'first_name': player.get('first_name', ''),
                    'last_name': player.get('last_name', '')
                })
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"❌ Error getting leaderboard: {e}")
            return []
    
    def log_riddle_attempt(self, user_id: str, riddle_id: str, location: str, 
                          is_correct: bool, time_taken: float) -> Dict[str, Any]:
        """
        Log a riddle attempt
        
        Args:
            user_id: User ID string
            riddle_id: ID of the riddle
            location: Location where riddle was attempted
            is_correct: Whether the answer was correct
            time_taken: Time taken to solve (in seconds)
            
        Returns:
            Dictionary with result
        """
        try:
            event_data = {
                "riddle_id": riddle_id,
                "location": location,
                "is_correct": is_correct,
                "time_taken": time_taken,
                "timestamp": datetime.utcnow()
            }
            
            result = self.log_game_event(user_id, "riddle_attempt", event_data)
            
            # If correct, add points and win
            if is_correct:
                points = max(10, 50 - int(time_taken))  # More points for faster solving
                self.add_win(user_id, "riddle_solved", points)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error logging riddle attempt: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to log riddle attempt'
            }
    
    def log_treasure_found(self, user_id: str, treasure_id: str, location: str, 
                          coordinates: Dict[str, float]) -> Dict[str, Any]:
        """
        Log when a treasure is found
        
        Args:
            user_id: User ID string
            treasure_id: ID of the treasure
            location: Location name
            coordinates: GPS coordinates
            
        Returns:
            Dictionary with result
        """
        try:
            event_data = {
                "treasure_id": treasure_id,
                "location": location,
                "coordinates": coordinates,
                "timestamp": datetime.utcnow()
            }
            
            result = self.log_game_event(user_id, "treasure_found", event_data)
            
            # Add points for finding treasure
            self.add_win(user_id, "treasure_found", 25)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error logging treasure found: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to log treasure found'
            }
    
    def get_user_riddle_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's riddle solving history
        
        Args:
            user_id: User ID string
            limit: Maximum number of records to return
            
        Returns:
            List of riddle attempts
        """
        try:
            from bson import ObjectId
            
            riddle_logs = list(self.db.game_logs.find({
                "user_id": ObjectId(user_id),
                "event_type": "riddle_attempt"
            }).sort("timestamp", -1).limit(limit))
            
            return [
                {
                    'riddle_id': log.get('event_data', {}).get('riddle_id'),
                    'location': log.get('event_data', {}).get('location'),
                    'is_correct': log.get('event_data', {}).get('is_correct'),
                    'time_taken': log.get('event_data', {}).get('time_taken'),
                    'timestamp': log.get('timestamp')
                } for log in riddle_logs
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting riddle history: {e}")
            return []
    
    def get_user_treasure_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get user's treasure finding history
        
        Args:
            user_id: User ID string
            limit: Maximum number of records to return
            
        Returns:
            List of treasures found
        """
        try:
            from bson import ObjectId
            
            treasure_logs = list(self.db.game_logs.find({
                "user_id": ObjectId(user_id),
                "event_type": "treasure_found"
            }).sort("timestamp", -1).limit(limit))
            
            return [
                {
                    'treasure_id': log.get('event_data', {}).get('treasure_id'),
                    'location': log.get('event_data', {}).get('location'),
                    'coordinates': log.get('event_data', {}).get('coordinates'),
                    'timestamp': log.get('timestamp')
                } for log in treasure_logs
            ]
            
        except Exception as e:
            logger.error(f"❌ Error getting treasure history: {e}")
            return []


def main():
    """Demo function to test the database operations"""
    # Initialize database
    db = UserDatabase()
    
    try:
        # Test data
        test_users = [
            {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "age": 25,
                "phone": "+1234567890",
                "location": "New York, NY"
            },
            {
                "username": "jane_smith",
                "email": "jane.smith@example.com",
                "first_name": "Jane",
                "last_name": "Smith",
                "age": 30,
                "phone": "+1234567891",
                "location": "Los Angeles, CA"
            }
        ]
        
        print("🧪 Testing Database Operations...")
        
        # CREATE - Add test users
        print("\n📝 Creating users...")
        for user in test_users:
            result = db.create_user(user)
            print(f"   {result}")
        
        # READ - Get all users
        print("\n📖 Reading all users...")
        users = db.get_all_users()
        print(f"   Found {len(users)} users")
        
        # READ - Get user by email
        print("\n🔍 Getting user by email...")
        user = db.get_user_by_email("john.doe@example.com")
        if user:
            print(f"   Found user: {user['username']}")
        
        # UPDATE - Update user
        print("\n✏️ Updating user...")
        if user:
            update_result = db.update_user(user['_id'], {"age": 26, "location": "Boston, MA"})
            print(f"   Update result: {update_result}")
        
        # READ - Get updated user
        print("\n🔍 Getting updated user...")
        updated_user = db.get_user_by_id(user['_id'])
        if updated_user:
            print(f"   Updated user: {updated_user['username']}, Age: {updated_user['age']}")
        
        # DELETE - Delete user
        print("\n🗑️ Deleting user...")
        delete_result = db.delete_user_by_email("jane.smith@example.com")
        print(f"   Delete result: {delete_result}")
        
        # READ - Get final count
        print("\n📊 Final statistics...")
        total_users = db.get_user_count()
        active_users = db.get_active_users_count()
        print(f"   Total users: {total_users}")
        print(f"   Active users: {active_users}")
        
        # Test game-specific functions
        print("\n🎮 Testing Game-Specific Functions...")
        
        # Test wins and points
        print("\n🏆 Testing wins and points...")
        if user:
            # Add some wins
            db.add_win(user['_id'], "riddle_solved", 15)
            db.add_win(user['_id'], "treasure_found", 25)
            db.add_win(user['_id'], "treasure_hunt", 20)
            
            # Get win count
            wins = db.get_number_of_wins(user['_id'])
            print(f"   User wins: {wins}")
            
            # Get game stats
            stats = db.get_user_game_stats(user['_id'])
            if stats['success']:
                print(f"   Total points: {stats['total_points']}")
                print(f"   Rank: #{stats['rank']}")
                print(f"   Event breakdown: {stats['event_breakdown']}")
        
        # Test riddle logging
        print("\n🧩 Testing riddle logging...")
        if user:
            db.log_riddle_attempt(user['_id'], "riddle_001", "Physical Science Building", True, 30.5)
            db.log_riddle_attempt(user['_id'], "riddle_002", "Mann Library", False, 60.0)
            
            # Get riddle history
            riddle_history = db.get_user_riddle_history(user['_id'])
            print(f"   Riddle attempts: {len(riddle_history)}")
            for attempt in riddle_history[:3]:  # Show first 3
                print(f"     - {attempt['location']}: {'✅' if attempt['is_correct'] else '❌'} ({attempt['time_taken']}s)")
        
        # Test treasure logging
        print("\n🏴‍☠️ Testing treasure logging...")
        if user:
            db.log_treasure_found(user['_id'], "treasure_001", "Physical Science Building", 
                                {"latitude": 42.4483579, "longitude": -76.4800221})
            db.log_treasure_found(user['_id'], "treasure_002", "Mann Library", 
                                {"latitude": 42.4483176, "longitude": -76.4765426})
            
            # Get treasure history
            treasure_history = db.get_user_treasure_history(user['_id'])
            print(f"   Treasures found: {len(treasure_history)}")
            for treasure in treasure_history:
                print(f"     - {treasure['location']} at {treasure['coordinates']}")
        
        # Test leaderboard
        print("\n🏅 Testing leaderboard...")
        leaderboard = db.get_leaderboard(5)
        print(f"   Top {len(leaderboard)} players:")
        for player in leaderboard:
            print(f"     #{player['rank']}: {player['username']} - {player['total_points']} points")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    finally:
        # Clean up
        db.disconnect()


if __name__ == "__main__":
    main()
