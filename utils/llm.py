"""
LLM Integration Module
Handles all LLM API calls for notes generation and question creation
"""

import os
import json
import time
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()

# Model fallback chain
MODEL_CHAIN = [
    "gemini/gemini-2.5-flash-lite",
    "gemini/gemini-2.0-flash",
]

def call_llm_with_retry(messages, temperature=0.3, max_tokens=4000, max_retries=3):
    """Call LLM with retry logic and model fallback"""
    
    for model in MODEL_CHAIN:
        for attempt in range(max_retries):
            try:
                response = completion(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response
            
            except Exception as e:
                error_str = str(e)
                
                # If overloaded or rate limited, wait and retry
                if "503" in error_str or "overloaded" in error_str.lower() or "429" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                        print(f"Model {model} busy, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"Model {model} failed after {max_retries} attempts, trying next model...")
                        break
                
                # If 404 or model not found, try next model immediately
                elif "404" in error_str or "not found" in error_str.lower():
                    print(f"Model {model} not available, trying next model...")
                    break
                
                # For other errors, raise immediately
                else:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
                    continue
    
    raise Exception("All models failed. Please check your API keys or try again later.")


def generate_notes(transcript, video_id=None):
    """
    Generate structured lecture notes from transcript using LLM
    
    Args:
        transcript (str): Full video transcript text
        video_id (str, optional): YouTube video ID for timestamp links
        
    Returns:
        dict: {
            'success': bool,
            'notes': {
                'summary': str,
                'key_concepts': list[str],
                'topics': list[dict],  # [{'name': str, 'timestamp': str, 'description': str}]
                'detailed_notes': str
            },
            'error': str (if failed)
        }
    """
    try:
        # Check if transcript is too short
        if len(transcript) < 100:
            return {
                'success': False,
                'error': 'Transcript is too short to generate meaningful notes.'
            }
        
        # Create prompt for structured notes generation
        prompt = f"""You are an expert educational content creator. Analyze this lecture transcript and create comprehensive, structured notes.

TRANSCRIPT:
{transcript}

Please provide your response in the following JSON format (ensure valid JSON):
{{
    "summary": "A 3-4 sentence overview of the entire lecture",
    "key_concepts": ["concept 1", "concept 2", "concept 3", ...],
    "topics": [
        {{
            "name": "Topic Name",
            "description": "Brief description of this topic",
            "keywords": ["keyword1", "keyword2"]
        }}
    ],
    "detailed_notes": "Comprehensive notes in markdown format with sections, subsections, and bullet points"
}}

Requirements:
1. Summary: Capture the main purpose and key takeaways
2. Key Concepts: List 5-10 most important concepts/terms
3. Topics: Identify 5-8 major topics covered (these will be used for quiz categorization)
4. Detailed Notes: Well-organized markdown with:
   - Clear section headers (##)
   - Subsections (###)
   - Bullet points for key information
   - Important formulas, definitions, or code snippets if applicable

IMPORTANT: Return ONLY valid JSON, no additional text before or after."""

        # Call LLM with retry and fallback
        response = call_llm_with_retry(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4000
        )
        
        # Extract response
        content = response.choices[0].message.content
        
        # Try to parse JSON from response
        # Sometimes LLMs wrap JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        notes_data = json.loads(content)
        
        # Validate structure
        required_keys = ['summary', 'key_concepts', 'topics', 'detailed_notes']
        if not all(key in notes_data for key in required_keys):
            raise ValueError("LLM response missing required fields")
        
        return {
            'success': True,
            'notes': notes_data,
            'token_usage': {
                'input': response.usage.prompt_tokens,
                'output': response.usage.completion_tokens,
                'total': response.usage.total_tokens
            }
        }
        
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'Failed to parse LLM response as JSON: {str(e)}',
            'raw_response': content if 'content' in locals() else 'No response'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating notes: {str(e)}'
        }


def format_notes_for_display(notes_data):
    """
    Format notes data into readable markdown for display
    
    Args:
        notes_data (dict): Notes structure from generate_notes()
        
    Returns:
        str: Formatted markdown text
    """
    markdown = f"""# Lecture Notes

## Summary
{notes_data['summary']}

## Key Concepts
"""
    
    for concept in notes_data['key_concepts']:
        markdown += f"- {concept}\n"
    
    markdown += "\n## Topics Covered\n"
    
    for i, topic in enumerate(notes_data['topics'], 1):
        markdown += f"\n### {i}. {topic['name']}\n"
        markdown += f"{topic['description']}\n"
        if 'keywords' in topic:
            markdown += f"**Keywords:** {', '.join(topic['keywords'])}\n"
    
    markdown += f"\n---\n\n## Detailed Notes\n\n{notes_data['detailed_notes']}\n"
    
    return markdown


# Test function
if __name__ == "__main__":
    # Test with sample transcript
    sample_transcript = """
    Welcome to this lecture on Machine Learning. Today we'll cover three main topics.
    
    First, let's discuss supervised learning. Supervised learning is a type of machine learning 
    where we train models on labeled data. The most common algorithms include linear regression, 
    logistic regression, and decision trees.
    
    Second, we'll explore unsupervised learning. Unlike supervised learning, unsupervised learning 
    works with unlabeled data. Common techniques include clustering algorithms like K-means and 
    dimensionality reduction methods like PCA.
    
    Finally, we'll introduce neural networks and deep learning. Neural networks are inspired by 
    the human brain and consist of layers of interconnected nodes. Deep learning uses neural 
    networks with many layers to solve complex problems.
    
    In summary, machine learning encompasses these three major approaches, each with its own 
    use cases and applications.
    """
    
    print("Testing notes generation...")
    print("=" * 50)
    
    result = generate_notes(sample_transcript)
    
    if result['success']:
        print("✅ Success!")
        print(f"\nToken Usage: {result['token_usage']}")
        print("\n" + "=" * 50)
        
        # Display formatted notes
        formatted = format_notes_for_display(result['notes'])
        print(formatted)
        
    else:
        print(f"❌ Error: {result['error']}")
        if 'raw_response' in result:
            print(f"\nRaw response:\n{result['raw_response']}")
