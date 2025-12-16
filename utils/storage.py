"""
Data Storage and Session Management
Handles caching and persistence of data during user session
"""

import json
import os
from datetime import datetime


class SessionStorage:
    """Manages session data for quiz application"""
    
    def __init__(self, storage_dir="data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_session(self, video_id, transcript, notes, questions):
        """Save complete session data"""
        session_data = {
            'video_id': video_id,
            'timestamp': datetime.now().isoformat(),
            'transcript': transcript,
            'notes': notes,
            'questions': questions
        }
        
        filepath = os.path.join(self.storage_dir, f"{video_id}.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_session(self, video_id):
        """Load session data if it exists"""
        filepath = os.path.join(self.storage_dir, f"{video_id}.json")
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def session_exists(self, video_id):
        """Check if session data exists"""
        filepath = os.path.join(self.storage_dir, f"{video_id}.json")
        return os.path.exists(filepath)


def save_quiz_results(video_id, results, score, topic_performance):
    """Save quiz results"""
    results_dir = "data/results"
    os.makedirs(results_dir, exist_ok=True)
    
    result_data = {
        'video_id': video_id,
        'timestamp': datetime.now().isoformat(),
        'score': score,
        'topic_performance': topic_performance,
        'results': results
    }
    
    filename = f"{video_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(results_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2)
    
    return filepath
