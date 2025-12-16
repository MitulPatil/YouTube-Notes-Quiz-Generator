"""
YouTube Transcript Scraper
Extracts transcripts and metadata from YouTube videos
"""

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled, 
        NoTranscriptFound,
        VideoUnavailable
    )
except ImportError:
    print("Error: youtube-transcript-api not installed properly")
    print("Try: pip uninstall youtube-transcript-api")
    print("Then: pip install youtube-transcript-api")
    
import re


def extract_video_id(youtube_url):
    """
    Extract video ID from various YouTube URL formats
    
    Supports:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    
    Args:
        youtube_url (str): YouTube video URL
        
    Returns:
        str: Video ID or None if invalid
    """
    # Pattern to match various YouTube URL formats
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    # If no pattern matches, maybe it's just the video ID
    if len(youtube_url) == 11 and not '/' in youtube_url:
        return youtube_url
        
    return None


def get_transcript(youtube_url, language='en'):
    """
    Download transcript from YouTube video
    
    Args:
        youtube_url (str): YouTube video URL
        language (str): Preferred language code (default: 'en')
        
    Returns:
        dict: {
            'success': bool,
            'video_id': str,
            'transcript': str,
            'language': str,
            'error': str (if failed)
        }
    """
    try:
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        
        if not video_id:
            return {
                'success': False,
                'error': 'Invalid YouTube URL. Please provide a valid video link.'
            }
        
        # Create API instance and fetch transcript
        api = YouTubeTranscriptApi()
        transcript_data = api.fetch(video_id, [language, 'en'])
        
        # Get transcript snippets
        snippets = transcript_data.snippets
        
        # Combine all transcript segments into one text
        transcript_text = ' '.join([snippet.text for snippet in snippets])
        
        # Clean up transcript (remove extra spaces, newlines)
        transcript_text = ' '.join(transcript_text.split())
        
        return {
            'success': True,
            'video_id': video_id,
            'transcript': transcript_text,
            'language': transcript_data.language,
            'duration': snippets[-1].start + snippets[-1].duration if snippets else 0
        }
        
    except TranscriptsDisabled:
        return {
            'success': False,
            'error': 'Transcripts are disabled for this video.'
        }
        
    except NoTranscriptFound:
        return {
            'success': False,
            'error': 'No transcript found for this video. The video may not have captions.'
        }
        
    except VideoUnavailable:
        return {
            'success': False,
            'error': 'Video is unavailable. It may be private or deleted.'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'An error occurred: {str(e)}'
        }


def get_video_metadata(video_id):
    """
    Get video metadata (title, duration, thumbnail)
    Note: This requires additional API or web scraping
    For now, returns basic info
    
    Args:
        video_id (str): YouTube video ID
        
    Returns:
        dict: Video metadata
    """
    return {
        'video_id': video_id,
        'url': f'https://www.youtube.com/watch?v={video_id}',
        'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
        'embed_url': f'https://www.youtube.com/embed/{video_id}'
    }


# Test function
if __name__ == "__main__":
    # Test with a sample video URL
    test_url = "https://www.youtube.com/watch?v=EkZlFPhMB4E"
    
    print("Testing transcript scraper...")
    result = get_transcript(test_url)
    
    if result['success']:
        print(f"✅ Success!")
        print(f"Video ID: {result['video_id']}")
        print(f"Language: {result['language']}")
        print(f"Transcript length: {len(result['transcript'])} characters")
        print(f"First 200 characters: {result['transcript'][:200]}...")
    else:
        print(f"❌ Error: {result['error']}")
