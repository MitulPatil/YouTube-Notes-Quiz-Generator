"""
Quiz Generation and Management Module
Handles question generation, storage, and quiz logic
"""

import json
import random
import time
from litellm import completion

# Model fallback chain
MODEL_CHAIN = [
    "gemini/gemini-2.5-flash-lite",
    "gemini/gemini-2.0-flash", 
]

def call_llm_with_retry(messages, temperature=0.7, max_tokens=3000, max_retries=3):
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
                
                if "503" in error_str or "overloaded" in error_str.lower() or "429" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2
                        print(f"Model {model} busy, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"Model {model} failed, trying next model...")
                        break
                
                elif "404" in error_str or "not found" in error_str.lower():
                    print(f"Model {model} not available, trying next model...")
                    break
                
                else:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)
                    continue
    
    raise Exception("All models failed. Please check your API keys or try again later.")


def generate_questions(notes_data, num_questions=50, difficulty_mix=None):
    """
    Generate quiz questions from lecture notes
    
    Args:
        notes_data (dict): Structured notes from generate_notes()
        num_questions (int): Number of questions to generate
        difficulty_mix (dict): {'easy': 20, 'medium': 20, 'hard': 10} or None for auto
        
    Returns:
        dict: {
            'success': bool,
            'questions': list[dict],
            'error': str (if failed)
        }
    """
    try:
        # Default difficulty distribution
        if difficulty_mix is None:
            difficulty_mix = {
                'easy': num_questions // 3,
                'medium': num_questions // 3,
                'hard': num_questions - (2 * (num_questions // 3))
            }
        
        all_questions = []
        
        # Generate questions for each difficulty level
        for difficulty, count in difficulty_mix.items():
            if count > 0:
                questions = _generate_questions_by_difficulty(
                    notes_data, 
                    difficulty, 
                    count
                )
                all_questions.extend(questions)
        
        # Shuffle questions
        random.shuffle(all_questions)
        
        return {
            'success': True,
            'questions': all_questions,
            'total_generated': len(all_questions)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating questions: {str(e)}'
        }


def _generate_questions_by_difficulty(notes_data, difficulty, count):
    """Generate questions of specific difficulty level"""
    
    # Create context from notes
    topics_text = "\n".join([
        f"- {topic['name']}: {topic['description']}" 
        for topic in notes_data['topics']
    ])
    
    difficulty_instructions = {
        'easy': 'Focus on basic definitions, facts, and direct recall from the lecture.',
        'medium': 'Focus on understanding concepts and their relationships.',
        'hard': 'Focus on application, analysis, and critical thinking.'
    }
    
    prompt = f"""You are an expert quiz creator. Generate {count} multiple-choice questions based on these lecture notes.

LECTURE SUMMARY:
{notes_data['summary']}

KEY CONCEPTS:
{', '.join(notes_data['key_concepts'])}

TOPICS COVERED:
{topics_text}

DETAILED CONTENT:
{notes_data['detailed_notes'][:2000]}  

DIFFICULTY LEVEL: {difficulty.upper()}
{difficulty_instructions[difficulty]}

Generate {count} questions following this EXACT JSON format:
[
    {{
        "question": "What is...?",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "correct_answer": 0,
        "explanation": "The answer is A because...",
        "topic": "Topic name from the notes",
        "difficulty": "{difficulty}"
    }}
]

Requirements:
1. Each question must have exactly 4 options
2. correct_answer is the index (0-3) of the correct option
3. Explanation should be clear and educational
4. Topic must match one from the notes
5. Questions should cover different topics
6. Return ONLY valid JSON array, no other text

IMPORTANT: Return ONLY the JSON array, nothing else."""

    try:
        response = call_llm_with_retry(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        content = response.choices[0].message.content
        
        # Clean up response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        questions = json.loads(content)
        
        # Ensure it's a list
        if isinstance(questions, dict):
            questions = [questions]
        
        return questions
        
    except Exception as e:
        print(f"Error generating {difficulty} questions: {e}")
        return []


def select_quiz_questions(all_questions, count=15, topics=None):
    """
    Select random questions for a quiz session
    
    Args:
        all_questions (list): Pool of all available questions
        count (int): Number of questions to select
        topics (list): Specific topics to focus on (optional)
        
    Returns:
        list: Selected questions
    """
    if topics:
        # Filter by topics
        filtered = [q for q in all_questions if q['topic'] in topics]
        available = filtered if filtered else all_questions
    else:
        available = all_questions
    
    # Shuffle and select
    selected = random.sample(available, min(count, len(available)))
    return selected


def check_answer(question, user_answer):
    """
    Check if user's answer is correct
    
    Args:
        question (dict): Question object
        user_answer (int): Index of selected option (0-3)
        
    Returns:
        dict: {
            'correct': bool,
            'correct_answer': int,
            'explanation': str
        }
    """
    is_correct = user_answer == question['correct_answer']
    
    return {
        'correct': is_correct,
        'correct_answer': question['correct_answer'],
        'correct_option': question['options'][question['correct_answer']],
        'user_option': question['options'][user_answer] if 0 <= user_answer < len(question['options']) else None,
        'explanation': question['explanation']
    }


def calculate_topic_performance(quiz_results):
    """
    Calculate performance by topic
    
    Args:
        quiz_results (list): List of {question, user_answer, is_correct}
        
    Returns:
        dict: {topic: {'correct': int, 'total': int, 'percentage': float}}
    """
    topic_stats = {}
    
    for result in quiz_results:
        topic = result['question']['topic']
        
        if topic not in topic_stats:
            topic_stats[topic] = {'correct': 0, 'total': 0}
        
        topic_stats[topic]['total'] += 1
        if result['is_correct']:
            topic_stats[topic]['correct'] += 1
    
    # Calculate percentages
    for topic, stats in topic_stats.items():
        stats['percentage'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        stats['status'] = 'Strong' if stats['percentage'] >= 80 else 'Needs Review' if stats['percentage'] >= 60 else 'Weak'
    
    return topic_stats


def get_weak_topics(topic_performance, threshold=60):
    """
    Identify topics that need review
    
    Args:
        topic_performance (dict): Output from calculate_topic_performance()
        threshold (int): Percentage threshold (default 60%)
        
    Returns:
        list: List of weak topics with details
    """
    weak_topics = []
    
    for topic, stats in topic_performance.items():
        if stats['percentage'] < threshold:
            weak_topics.append({
                'topic': topic,
                'score': f"{stats['correct']}/{stats['total']}",
                'percentage': stats['percentage'],
                'status': stats['status']
            })
    
    # Sort by percentage (weakest first)
    weak_topics.sort(key=lambda x: x['percentage'])
    
    return weak_topics


# Test function
if __name__ == "__main__":
    # Test with sample notes
    sample_notes = {
        'summary': 'This lecture covers machine learning basics including supervised and unsupervised learning.',
        'key_concepts': ['Supervised Learning', 'Unsupervised Learning', 'Neural Networks', 'Classification', 'Clustering'],
        'topics': [
            {'name': 'Supervised Learning', 'description': 'Learning from labeled data'},
            {'name': 'Unsupervised Learning', 'description': 'Learning from unlabeled data'},
            {'name': 'Neural Networks', 'description': 'Brain-inspired computing models'}
        ],
        'detailed_notes': 'Supervised learning uses labeled data to train models. Common algorithms include regression and classification.'
    }
    
    print("Testing question generation...")
    result = generate_questions(sample_notes, num_questions=5)
    
    if result['success']:
        print(f"✅ Generated {len(result['questions'])} questions")
        for i, q in enumerate(result['questions'][:2], 1):
            print(f"\nQuestion {i}: {q['question']}")
            print(f"Topic: {q['topic']} | Difficulty: {q['difficulty']}")
    else:
        print(f"❌ Error: {result['error']}")
