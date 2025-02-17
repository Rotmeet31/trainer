import json
from datetime import datetime, timedelta
import json
from collections import defaultdict

class Database:
    def __init__(self):
        """Initialize database and load existing data"""
        self.users = self._load_from_file('users.json')
        self.workouts = self._load_from_file('workouts.json')
        self.progress = self._load_from_file('progress.json')
        self.reminders = self._load_from_file('reminders.json')
        self.feedback = self._load_from_file('feedback.json')

    def save_user_profile(self, user_id, profile_data, telegram_handle=None):
        """Save user profile data with telegram handle"""
        user_id = str(user_id)
        profile_data['telegram_handle'] = telegram_handle
        profile_data['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.users[user_id] = profile_data
        self._save_to_file('users.json', self.users)

    def get_user_profile(self, user_id):
        """Get user profile data"""
        return self.users.get(str(user_id))

    def save_workout_progress(self, user_id, workout_data):
        """Save workout completion data"""
        user_id = str(user_id)
        if user_id not in self.progress:
            self.progress[user_id] = []

        workout_data['date'] = datetime.now().strftime('%Y-%m-%d')
        self.progress[user_id].append(workout_data)
        self._save_to_file('progress.json', self.progress)

    def get_user_progress(self, user_id):
        """Get user's workout progress"""
        return self.progress.get(str(user_id), [])

    def get_workout_streak(self, user_id):
        """Calculate current and longest workout streaks"""
        user_id = str(user_id)
        workouts = self.get_user_progress(user_id)
        if not workouts:
            return {"current_streak": 0, "longest_streak": 0}

        # Sort workouts by date
        workout_dates = sorted(set(
            datetime.strptime(w['date'], '%Y-%m-%d').date()
            for w in workouts
        ))

        if not workout_dates:
            return {"current_streak": 0, "longest_streak": 0}

        # Calculate streaks
        current_streak = 0
        longest_streak = 0
        streak_count = 0
        today = datetime.now().date()

        # Check if the last workout was today or yesterday to continue the streak
        last_workout = workout_dates[-1]
        if last_workout < today - timedelta(days=1):
            current_streak = 0
        else:
            # Count backwards from the last workout
            for i in range(len(workout_dates) - 1, -1, -1):
                if i == len(workout_dates) - 1:
                    streak_count = 1
                    continue

                if workout_dates[i] == workout_dates[i + 1] - timedelta(days=1):
                    streak_count += 1
                else:
                    break

            current_streak = streak_count

        # Calculate longest streak
        streak_count = 1
        for i in range(1, len(workout_dates)):
            if workout_dates[i] == workout_dates[i-1] + timedelta(days=1):
                streak_count += 1
            else:
                longest_streak = max(longest_streak, streak_count)
                streak_count = 1

        longest_streak = max(longest_streak, streak_count, current_streak)

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }

    def get_workout_intensity_stats(self, user_id, days=30):
        """Get workout intensity statistics for the last N days"""
        user_id = str(user_id)
        workouts = self.get_user_progress(user_id)
        if not workouts:
            return []

        # Get date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # Group workouts by date
        daily_stats = defaultdict(lambda: {"total_exercises": 0, "completed_exercises": 0})

        for workout in workouts:
            workout_date = datetime.strptime(workout['date'], '%Y-%m-%d').date()
            if start_date <= workout_date <= end_date:
                daily_stats[workout_date.strftime('%Y-%m-%d')]['total_exercises'] += workout['total_exercises']
                daily_stats[workout_date.strftime('%Y-%m-%d')]['completed_exercises'] += workout['exercises_completed']

        # Convert to list and sort by date
        stats = [
            {
                "date": date,
                "completion_rate": stats['completed_exercises'] / stats['total_exercises'] * 100 if stats['total_exercises'] >0 else 0,
                "total_exercises": stats['total_exercises']
            }
            for date, stats in daily_stats.items()
        ]

        return sorted(stats, key=lambda x: x['date'])

    def save_workout_feedback(self, user_id, workout_id, feedback_data):
        """Save workout feedback"""
        user_id = str(user_id)
        if user_id not in self.feedback:
            self.feedback[user_id] = {}
        self.feedback[user_id][workout_id] = feedback_data
        self._save_to_file('feedback.json', self.feedback)

    def get_user_feedback(self, user_id):
        """Get user's workout feedback history"""
        return self.feedback.get(str(user_id), {})

    def get_workouts_by_date(self, user_id, start_date, end_date):
        """Get workouts within date range"""
        user_progress = self.get_user_progress(user_id)
        return [
            workout for workout in user_progress
            if start_date <= datetime.strptime(workout['date'], '%Y-%m-%d').date() <= end_date
        ]

    def set_reminder(self, user_id, time):
        """Set workout reminder"""
        self.reminders[str(user_id)] = time
        self._save_to_file('reminders.json', self.reminders)

    def get_reminder(self, user_id):
        """Get user's reminder time"""
        return self.reminders.get(str(user_id))

    def _save_to_file(self, filename, data):
        """Save data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving to {filename}: {e}")

    def _load_from_file(self, filename):
        """Load data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}