import json
import os
from datetime import datetime, timedelta

class HealthDataStorage:
    """Store and retrieve historical health data and tags"""
    
    def __init__(self, filename='health_data.json'):
        self.filename = filename
        self.data = self._load_data()
    
    def _load_data(self):
        """Load existing data from JSON file"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    return json.load(f)
            except:
                return {'daily_entries': [], 'tags': []}
        return {'daily_entries': [], 'tags': []}
    
    def _save_data(self):
        """Save data to JSON file"""
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_daily_entry(self, date, sleep_score, readiness_score, activity_score, 
                       heart_rate=None, hrv=None, temperature=None, total_sleep=None):
        """Add a daily health entry"""
        # Convert 'N/A' to None for proper handling
        entry = {
            'date': str(date),
            'sleep_score': sleep_score if sleep_score != 'N/A' and sleep_score is not None else 0,
            'readiness_score': readiness_score if readiness_score != 'N/A' and readiness_score is not None else 0,
            'activity_score': activity_score if activity_score != 'N/A' and activity_score is not None else 0,
            'heart_rate': heart_rate if heart_rate != 'N/A' else None,
            'hrv': hrv if hrv != 'N/A' else None,
            'temperature': temperature if temperature != 'N/A' else None,
            'total_sleep': total_sleep if total_sleep != 'N/A' else None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Check if entry for this date already exists
        existing_index = None
        for i, existing_entry in enumerate(self.data['daily_entries']):
            if existing_entry['date'] == str(date):
                existing_index = i
                break
        
        if existing_index is not None:
            self.data['daily_entries'][existing_index] = entry
        else:
            self.data['daily_entries'].append(entry)
        
        self._save_data()
    
    def add_tag(self, date, tag_name, tag_category='stress', impact='neutral', notes=''):
        """Add a tag/event for tracking experiments"""
        tag = {
            'date': str(date),
            'tag_name': tag_name,
            'tag_category': tag_category,
            'impact': impact,
            'notes': notes,
            'timestamp': datetime.now().isoformat()
        }
        self.data['tags'].append(tag)
        self._save_data()
        return True
    
    def get_recent_entries(self, days=7):
        """Get entries from the last N days"""
        if not self.data['daily_entries']:
            return []
        
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days)
        
        recent = [
            entry for entry in self.data['daily_entries']
            if datetime.fromisoformat(entry['date']).date() >= cutoff_date
        ]
        return sorted(recent, key=lambda x: x['date'])
    
    def get_all_entries(self):
        """Get all daily entries"""
        return sorted(self.data['daily_entries'], key=lambda x: x['date'])
    
    def get_tags_by_date_range(self, days=30):
        """Get tags from the last N days"""
        if not self.data['tags']:
            return []
        
        today = datetime.now().date()
        cutoff_date = today - timedelta(days=days)
        
        recent_tags = [
            tag for tag in self.data['tags']
            if datetime.fromisoformat(tag['date']).date() >= cutoff_date
        ]
        return sorted(recent_tags, key=lambda x: x['date'], reverse=True)
    
    def get_all_tags(self):
        """Get all tags sorted by date"""
        return sorted(self.data['tags'], key=lambda x: x['date'], reverse=True)
    
    def get_weekly_summary(self):
        """Calculate weekly averages and insights"""
        recent = self.get_recent_entries(7)
        if not recent:
            return None
        
        valid_sleep = [e['sleep_score'] for e in recent if e['sleep_score'] and e['sleep_score'] > 0]
        valid_readiness = [e['readiness_score'] for e in recent if e['readiness_score'] and e['readiness_score'] > 0]
        valid_activity = [e['activity_score'] for e in recent if e['activity_score'] and e['activity_score'] > 0]
        valid_hours = [e['total_sleep'] for e in recent if e['total_sleep'] and e['total_sleep'] > 0]
        
        return {
            'sleep_avg': round(sum(valid_sleep) / len(valid_sleep)) if valid_sleep else 0,
            'readiness_avg': round(sum(valid_readiness) / len(valid_readiness)) if valid_readiness else 0,
            'activity_avg': round(sum(valid_activity) / len(valid_activity)) if valid_activity else 0,
            'avg_sleep_hours': round(sum(valid_hours) / len(valid_hours), 1) if valid_hours else 0,
            'best_day': max(recent, key=lambda x: x['readiness_score'] if x['readiness_score'] else 0) if recent else None,
            'worst_day': min(recent, key=lambda x: x['readiness_score'] if x['readiness_score'] else 100) if recent else None,
            'total_days': len(recent)
        }
    
    def analyze_tag_impact(self, tag_category=None):
        """Analyze how tags correlate with next-day readiness"""
        results = []
        
        for tag in self.data['tags']:
            tag_date = datetime.fromisoformat(tag['date']).date()
            next_day = tag_date + timedelta(days=1)
            
            # Find readiness score for next day
            next_day_entry = None
            for entry in self.data['daily_entries']:
                entry_date = datetime.fromisoformat(entry['date']).date()
                if entry_date == next_day:
                    next_day_entry = entry
                    break
            
            if next_day_entry and next_day_entry['readiness_score']:
                if tag_category is None or tag['tag_category'] == tag_category:
                    results.append({
                        'tag': tag['tag_name'],
                        'category': tag['tag_category'],
                        'date': tag['date'],
                        'next_day_readiness': next_day_entry['readiness_score'],
                        'next_day_sleep': next_day_entry['sleep_score']
                    })
        
        return results
