from flask import Flask, render_template, jsonify, request, session
from utils.facial_expression import get_emotion_stats
from utils.grammar_analysis import grammar_check_detailed
from utils.grammar_correction import correct_grammar_smart
from utils.keyword_analysis import evaluate_keywords
from utils.speech_feedback import get_fluency_feedback
from utils.speech_transcription import transcribe_audio_from_file
from utils.response_suggestions import get_better_response_suggestions, get_score_improvement_tips
from utils.ielts_scorer import get_ielts_band_score
from utils.detailed_weakness import get_detailed_weaknesses
from config import DEBUG_MODE, PORT, HOST
import threading
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'interview-insight-secret-key'

# IELTS Interview Questions (Part 1, 2, 3 style)
questions_keywords = [
    {
        "question": "Tell me about yourself. Where are you from?",
        "keywords": ["hometown", "place", "live", "family", "occupation", "background"],
        "tips": "Keep it natural and conversational. Mention your background, education, and what you do."
    },
    {
        "question": "What do you like to do in your free time?",
        "keywords": ["hobby", "enjoy", "like", "spend", "time", "interested"],
        "tips": "Describe your hobbies with examples. Use present simple tense mainly."
    },
    {
        "question": "Describe a book you have read recently.",
        "keywords": ["book", "read", "author", "story", "character", "enjoyed"],
        "tips": "Speak for 1-2 minutes. Structure: title, author, what it's about, why you liked it."
    },
]

# Store session results
session_results = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/question')
def question_page():
    return render_template('question.html')

@app.route('/get-question/<int:index>')
def get_question(index):
    if index < len(questions_keywords):
        q_data = questions_keywords[index]
        return jsonify({
            "question": q_data["question"],
            "index": index,
            "tips": q_data["tips"],
            "total_questions": len(questions_keywords)
        })
    else:
        return jsonify({"status": "Interview completed"})

@app.route('/transcribe-audio', methods=['POST'])
def transcribe_audio_endpoint():
    """Transcribe audio file using Whisper model"""
    try:
        # Check if audio file is present
        if 'audio' not in request.files:
            print("No audio file in request")
            return jsonify({
                "text": "",
                "error": "No audio file provided",
                "confidence": 0,
                "language": ""
            }), 200  # Return 200 even with error for proper JSON parsing
        
        audio_file = request.files['audio']
        
        if not audio_file:
            print("Audio file is empty/None")
            return jsonify({
                "text": "",
                "error": "Audio file is invalid",
                "confidence": 0,
                "language": ""
            }), 200
        
        if audio_file.filename == '':
            print("Audio file has empty filename")
            return jsonify({
                "text": "",
                "error": "No file selected",
                "confidence": 0,
                "language": ""
            }), 200
        
        print(f"[TRANSCRIPTION] Received audio file: {audio_file.filename}, size: {len(audio_file.read())} bytes")
        audio_file.seek(0)  # Reset file pointer after reading size
        
        # Transcribe using Whisper
        print("[TRANSCRIPTION] Starting transcription...")
        result = transcribe_audio_from_file(audio_file)
        
        if result.get('error'):
            print(f"[TRANSCRIPTION] Error: {result['error']}")
            return jsonify({
                "text": "",
                "error": result['error'],
                "confidence": 0,
                "language": result.get('language', '')
            }), 200
        
        transcribed_text = result.get('text', '').strip()
        print(f"[TRANSCRIPTION] Success! Text: '{transcribed_text[:100]}{'...' if len(transcribed_text) > 100 else ''}'")
        
        return jsonify({
            "text": transcribed_text,
            "error": None,
            "confidence": result.get('confidence', 0),
            "language": result.get('language', 'en')
        }), 200
    
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[TRANSCRIPTION] Endpoint error: {error_msg}")
        return jsonify({
            "text": "",
            "error": f"Server error: {str(e)}",
            "confidence": 0,
            "language": ""
        }), 200

@app.route('/process-answer', methods=['POST'])
def process_answer():
    """
    Comprehensive answer processing with:
    - Grammar correction
    - Response suggestions
    - IELTS band scoring
    - Detailed feedback
    """
    try:
        data = request.get_json()
        index = data.get("index")
        answer = data.get("answer", "").strip()

        if not answer or len(answer) < 10:
            return jsonify({
                "error": "Please provide a more detailed answer",
                "rating": 0,
                "feedback": []
            }), 400

        question_data = questions_keywords[index]
        question = question_data["question"]
        
        print(f"\n[PROCESSING] Question {index}: {question}")
        print(f"[PROCESSING] Answer: {answer[:100]}...")
        
        # =============================================
        # 1. GRAMMAR ANALYSIS WITH CORRECTIONS
        # =============================================
        print("[PROCESSING] Analyzing grammar...")
        grammar_correction = correct_grammar_smart(answer)
        grammar_score = 100 - (len(grammar_correction['corrections']) * 5)  # Deduct 5 per error
        grammar_score = max(0, min(100, grammar_score))
        
        # =============================================
        # 2. FLUENCY & COHERENCE ANALYSIS
        # =============================================
        print("[PROCESSING] Analyzing fluency...")
        fluency_data = get_fluency_feedback(answer)
        fluency_score = fluency_data.get('score', 70)
        
        # =============================================
        # 3. VOCABULARY ANALYSIS
        # =============================================
        print("[PROCESSING] Analyzing vocabulary...")
        keyword_score = evaluate_keywords(answer, question_data["keywords"])
        vocabulary_score = min(100, keyword_score * 10)
        
        # =============================================
        # 4. PRONUNCIATION (from facial expressions as confidence proxy)
        # =============================================
        emotion_stats = get_emotion_stats()
        confidence_score = emotion_stats.get('confidence_score', 70)
        pronunciation_score = confidence_score  # Use confidence as proxy
        
        # =============================================
        # 5. IELTS BAND SCORE CALCULATION
        # =============================================
        print("[PROCESSING] Calculating IELTS band...")
        ielts_result = get_ielts_band_score(
            grammar_score=grammar_score,
            fluency_score=fluency_score,
            vocabulary_score=vocabulary_score,
            pronunciation_score=pronunciation_score
        )
        
        # =============================================
        # 5.5 DETAILED WEAKNESS DETECTION (Professional Level)
        # =============================================
        print("[PROCESSING] Detecting detailed weaknesses...")
        scores_dict = {
            'grammar': grammar_score,
            'fluency': fluency_score,
            'vocabulary': vocabulary_score,
            'pronunciation': pronunciation_score
        }
        weaknesses = get_detailed_weaknesses(question, answer, scores_dict)
        
        # =============================================
        # 6. RESPONSE SUGGESTIONS
        # =============================================
        print("[PROCESSING] Getting response suggestions...")
        suggestions = get_better_response_suggestions(question, answer)
        improvement_tips = get_score_improvement_tips(ielts_result['overall_score'])
        
        # =============================================
        # 7. BUILD COMPREHENSIVE FEEDBACK
        # =============================================
        feedback_items = []
        
        # Grammar feedback with corrections
        if grammar_correction['corrections']:
            feedback_items.append({
                "category": "Grammar & Sentence Structure",
                "icon": "📝",
                "score": round(grammar_score, 1),
                "severity": "critical" if grammar_score < 50 else "high" if grammar_score < 70 else "medium",
                "message": f"Found {len(grammar_correction['corrections'])} grammar issues",
                "corrections": grammar_correction['corrections'][:5],  # Top 5
                "auto_corrected": grammar_correction.get('corrected_text', answer),
                "tips": grammar_correction.get('tips', [])[:3]
            })
        
        # Fluency feedback
        if fluency_score < 75 or fluency_data.get('issues'):
            feedback_items.append({
                "category": "Fluency & Coherence",
                "icon": "🎙️",
                "score": round(fluency_score, 1),
                "severity": "high" if fluency_score < 60 else "medium",
                "message": "Improve speaking flow and coherence",
                "issues": fluency_data.get('issues', []),
                "word_count": len(answer.split()),
                "sentence_count": len([s for s in answer.split('.') if s.strip()])
            })
        
        # Vocabulary feedback
        if vocabulary_score < 75:
            feedback_items.append({
                "category": "Vocabulary & Keyword Usage",
                "icon": "📚",
                "score": round(vocabulary_score, 1),
                "severity": "medium",
                "message": "Expand vocabulary usage",
                "keywords_found": [kw for kw in question_data["keywords"] if kw.lower() in answer.lower()],
                "keywords_missing": [kw for kw in question_data["keywords"] if kw.lower() not in answer.lower()],
                "suggestion": f"Try to incorporate: {', '.join(question_data['keywords'])}"
            })
        
        # Confidence/Pronunciation feedback
        if confidence_score < 70:
            feedback_items.append({
                "category": "Confidence & Pronunciation",
                "icon": "🎤",
                "score": round(confidence_score, 1),
                "severity": "medium",
                "message": "Work on delivery and confidence",
                "tips": [
                    "Maintain clear pronunciation",
                    "Speak with confidence",
                    "Avoid rushing - maintain steady pace",
                    "Make eye contact with camera"
                ]
            })
        
        # Response structure analysis
        if suggestions.get('analysis'):
            feedback_items.append({
                "category": "Answer Structure & Content",
                "icon": "🎯",
                "message": "How well your answer followed the expected structure",
                "strengths": suggestions['analysis'].get('strengths', []),
                "improvements": suggestions['analysis'].get('improvements', []),
                "suggested_structure": suggestions.get('suggested_structure', []),
                "example_answer": suggestions.get('example_answer', ''),
                "tips_for_this_question": suggestions.get('tips', [])
            })
        
        # =============================================
        # DETAILED WEAKNESS ANALYSIS (PROFESSIONAL LEVEL)
        # =============================================
        # Grammar Weaknesses
        if weaknesses.get('grammar', {}).get('issues'):
            feedback_items.append({
                "category": "Grammar Detailed Analysis",
                "icon": "📝",
                "score": round(weaknesses['grammar']['score'], 1),
                "severity": weaknesses['grammar']['severity'],
                "band_target": weaknesses['grammar']['band_target'],
                "message": "Detailed grammar issues found",
                "specific_issues": weaknesses['grammar']['issues'],
                "total_issues": weaknesses['grammar']['total_issues']
            })
        
        # Fluency Weaknesses
        if weaknesses.get('fluency', {}).get('issues'):
            feedback_items.append({
                "category": "Fluency Issues",
                "icon": "🎙️",
                "score": round(weaknesses['fluency']['score'], 1),
                "severity": weaknesses['fluency']['severity'],
                "band_target": weaknesses['fluency']['band_target'],
                "message": "Speech fluency and coherence issues",
                "specific_issues": weaknesses['fluency']['issues'],
                "metrics": weaknesses['fluency'].get('metrics', {}),
                "total_issues": weaknesses['fluency']['total_issues']
            })
        
        # Vocabulary Weaknesses
        if weaknesses.get('vocabulary', {}).get('issues'):
            feedback_items.append({
                "category": "Vocabulary Issues",
                "icon": "📚",
                "score": round(weaknesses['vocabulary']['score'], 1),
                "severity": weaknesses['vocabulary']['severity'],
                "band_target": weaknesses['vocabulary']['band_target'],
                "message": "Vocabulary range and variety issues",
                "specific_issues": weaknesses['vocabulary']['issues'],
                "word_count": weaknesses['vocabulary'].get('word_count', 0),
                "vocabulary_ratio": weaknesses['vocabulary'].get('vocabulary_ratio', 0),
                "total_issues": weaknesses['vocabulary']['total_issues']
            })
        
        # Pronunciation/Delivery Weaknesses
        if weaknesses.get('pronunciation', {}).get('issues'):
            feedback_items.append({
                "category": "Pronunciation Issues",
                "icon": "🎤",
                "score": round(weaknesses['pronunciation']['score'], 1),
                "severity": weaknesses['pronunciation']['severity'],
                "message": "Pronunciation and delivery concerns",
                "specific_issues": weaknesses['pronunciation']['issues'],
                "total_issues": weaknesses['pronunciation']['total_issues']
            })
        
        # Question Coverage Analysis
        if weaknesses.get('question_coverage', {}).get('issues'):
            feedback_items.append({
                "category": "Question Coverage",
                "icon": "🎯",
                "score": weaknesses['question_coverage'].get('coverage_score', 0),
                "severity": weaknesses['question_coverage']['severity'],
                "message": "How well your answer addresses the question",
                "specific_issues": weaknesses['question_coverage']['issues']
            })
        
        # Critical Areas Summary
        if weaknesses.get('critical_areas'):
            feedback_items.append({
                "category": "⚠️ Critical Areas Needing Attention",
                "icon": "🚨",
                "message": "Highest priority improvements",
                "critical_items": weaknesses['critical_areas'],
                "overall_severity": weaknesses.get('overall_severity', 'medium')
            })
        
        # =============================================
        # 8. STORE RESULTS
        # =============================================
        if 'results' not in session_results:
            session_results['results'] = []
        
        session_results['results'].append({
            "question_index": index,
            "question": question,
            "answer": answer,
            "scores": {
                "grammar": round(grammar_score, 1),
                "fluency": round(fluency_score, 1),
                "vocabulary": round(vocabulary_score, 1),
                "pronunciation": round(pronunciation_score, 1),
                "overall": round(ielts_result['overall_score'], 1)
            },
            "ielts_band": ielts_result['ielts_band'],
            "band_number": ielts_result['band_number'],
            "timestamp": datetime.now().isoformat()
        })
        
        # =============================================
        # 9. BUILD RESPONSE
        # =============================================
        return jsonify({
            "success": True,
            "rating": round(ielts_result['overall_score'], 1),
            "ielts_band": {
                "number": ielts_result['band_number'],
                "label": ielts_result['ielts_band'],
                "description": ielts_result['band_description'],
                "recommendation": ielts_result['recommendation']
            },
            "scores": {
                "grammar": round(grammar_score, 1),
                "fluency": round(fluency_score, 1),
                "vocabulary": round(vocabulary_score, 1),
                "pronunciation": round(pronunciation_score, 1),
                "overall": round(ielts_result['overall_score'], 1)
            },
            "breakdown": ielts_result['breakdown'],
            "feedback": feedback_items,
            "detailed_weaknesses": weaknesses,
            "critical_areas": weaknesses.get('critical_areas', []),
            "summary": ielts_result['recommendation'],
            "strengths": ielts_result['strengths'],
            "weaknesses": ielts_result['weaknesses'],
            "improvement_tips": improvement_tips[:5]
        }), 200
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"[PROCESSING] Error: {error_msg}")
        return jsonify({
            "success": False,
            "error": f"Error processing answer: {str(e)}",
            "feedback": []
        }), 500

@app.route('/result')
def result_page():
    """Display comprehensive interview results"""
    if 'results' not in session_results or not session_results['results']:
        return render_template('result.html', report={})
    
    results = session_results['results']
    
    # Calculate averages
    avg_grammar = sum(r['scores']['grammar'] for r in results) / len(results)
    avg_fluency = sum(r['scores']['fluency'] for r in results) / len(results)
    avg_vocabulary = sum(r['scores']['vocabulary'] for r in results) / len(results)
    avg_pronunciation = sum(r['scores'].get('pronunciation', 70) for r in results) / len(results)
    overall_score = (avg_grammar + avg_fluency + avg_vocabulary + avg_pronunciation) / 4
    
    # Get IELTS band score
    ielts = get_ielts_band_score(avg_grammar, avg_fluency, avg_vocabulary, avg_pronunciation)
    
    # Get improvement tips
    improvement_tips = get_score_improvement_tips(overall_score)
    
    report = {
        "results": results,
        "averages": {
            "grammar": round(avg_grammar, 1),
            "fluency": round(avg_fluency, 1),
            "vocabulary": round(avg_vocabulary, 1),
            "pronunciation": round(avg_pronunciation, 1),
            "overall": round(overall_score, 1)
        },
        "ielts_band": {
            "number": ielts['band_number'],
            "label": ielts['ielts_band'],
            "description": ielts['band_description'],
            "recommendation": ielts['recommendation'],
            "gap_to_next": ielts['next_band_gap']
        },
        "breakdown": ielts['breakdown'],
        "strengths": ielts['strengths'],
        "weaknesses": ielts['weaknesses'],
        "improvement_tips": improvement_tips
    }
    
    return render_template('result.html', report=report)

@app.route('/reset')
def reset():
    session_results['results'] = []
    return jsonify({"status": "Session reset"})

if __name__ == '__main__':
    app.run(debug=DEBUG_MODE, host=HOST, port=PORT)
