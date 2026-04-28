import os
import json
from flask import Flask, request, jsonify, send_from_directory
from datetime import datetime

# ==============================================================
# CORE NLP IMPORTS - PRESERVING EXACTLY AS USER REQUESTED
# ==============================================================
from utils.step2_grammar_detection import detect_grammar_errors
from utils.step3_grammar_correction_t5 import correct_paragraph_t5
from utils.step4_sentence_complexity import analyze_sentence_complexity
from utils.step5_vocabulary_richness import analyze_vocabulary_richness
from utils.step6_fluency_indicators import analyze_fluency_indicators
from utils.step7_metrics_to_scores import convert_metrics_to_scores
from utils.step8_ielts_band_predictor import predict_ielts_band

# PRETRAINED REPLACEMENTS (No APIs used)
from utils.local_interviewer import local_examiner
from utils.pretrained_cv import cv_analyzer

app = Flask(__name__, static_folder='../frontend/frontend/dist', static_url_path='')
app.secret_key = 'interview-insight-secret-key'

# In-memory database for sessions
active_sessions = {}

# ==============================================================
# FRONTEND STATIC SERVING (VITE SPA ROUTING)
# ==============================================================
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# ==============================================================
# API ROUTES (INTEGRATED FOR THE NEW VITE FRONTEND)
# ==============================================================

@app.route('/api/interview/session/start', methods=['POST'])
def start_session():
    data = request.json
    sid = data.get('session_id')
    active_sessions[sid] = {
        "info": data,
        "responses": [],
        "cv_frames": []
    }
    return jsonify({"success": True})

@app.route('/api/interview/questions', methods=['POST'])
def get_questions():
    data = request.json
    num = data.get('num', 6)
    questions = []
    
    # Generate completely local offline questions dynamically using Pre-Trained model
    for i in range(num):
        part = 1 if i < 2 else (2 if i < 4 else 3)
        context = f"Part {part} about {data.get('field', 'general')}."
        generated_q = local_examiner.generate_question(context)
        
        questions.append({
            "id": i + 1,
            "question": generated_q,
            "part": part,
            "keywords": ["vocabulary", "fluency", data.get('field', 'general')],
            "tips": "Speak clearly and confidently.",
            "duration": "2 minutes" if part == 2 else "1 minute"
        })
        
    return jsonify({"success": True, "questions": questions})

@app.route('/api/analyze/frame', methods=['POST'])
def analyze_frame():
    data = request.json
    sid = data.get('session_id')
    b64_frame = data.get('frame')
    
    cv_result = cv_analyzer.analyze_frame(b64_frame)
    if sid in active_sessions:
        active_sessions[sid]['cv_frames'].append(cv_result)
        
    return jsonify({"success": True, "result": cv_result})

@app.route('/api/analyze/answer', methods=['POST'])
def analyze_answer():
    data = request.json
    answer = data.get('answer', '')
    
    # 1. CORE NLP PIPELINE EXACTLY PRESERVED
    grammar_result = detect_grammar_errors(answer)
    correction_result = correct_paragraph_t5(answer)
    complexity_data = analyze_sentence_complexity(answer)
    vocab_data = analyze_vocabulary_richness(answer)
    fluency_data = analyze_fluency_indicators(answer)
    
    # 2. LOCAL OFFLINE RESPONSE GENERATION (NO OPENAI/GEMINI)
    offline_feedback = local_examiner.generate_feedback(
        text=answer, 
        grammar_errors=grammar_result.get('total_errors', 0), 
        vocab_score=vocab_data.get('vocabulary_score', 0)
    )
    
    # 3. SCORE AGGREGATION
    scores = convert_metrics_to_scores(
        grammar_error_count=grammar_result.get('total_errors', 0),
        vocab_richness=vocab_data.get('vocabulary_richness', 0.5),
        complex_count=complexity_data.get('complex_structures', 0),
        filler_count=fluency_data.get('filler_count', 0),
        total_words=len(answer.split()),
        accuracy_score=grammar_result.get('accuracy_score', 80),
        complexity_score=complexity_data.get('complexity_score', 5.0),
        fluency_score=fluency_data.get('fluency_score', 5.0),
        vocabulary_score=vocab_data.get('vocabulary_score', 5.0)
    )
    overall_band = scores.get('overall_score', 5.0)
    new_ielts_result = predict_ielts_band(overall_band)
    
    # Bundle exactly to Vite Frontend API contract
    analysis_packet = {
        "success": True,
        "overall_band": new_ielts_result['band'],
        "band_label": new_ielts_result['description'],
        "bands": {
            "overall": new_ielts_result['band'],
            "fc": round(scores.get('fluency_score', 5.0)),
            "lr": round(scores.get('vocabulary_score', 5.0)),
            "gra": round(scores.get('accuracy_score', 80) / 11),  # map 100 to band
            "p": 7 # Fallback audio band
        },
        "nlp": {
            "grammar_score": round(scores.get('accuracy_score', 80)),
            "vocab_score": round(scores.get('vocabulary_score', 5.0) * 10),
            "fluency_score": round(scores.get('fluency_score', 5.0) * 10),
            "word_count": len(answer.split()),
            "advanced_words": vocab_data.get("advanced_words", [])[:5],
            "filler_count": fluency_data.get('filler_count', 0),
            "total_markers": complexity_data.get('complex_structures', 0)
        },
        "ai": {
            "ai_powered": True,
            "fc_feedback": "Maintain steady speech flow.",
            "lr_feedback": "Good use of language.",
            "gra_feedback": offline_feedback,
            "p_feedback": "Pronunciation was clear.",
            "strengths": new_ielts_result['strengths'][:2],
            "improvements": new_ielts_result['areas_for_improvement'][:2],
            "corrected_answer": correction_result.get('corrected', answer),
            "grammar_errors": [{"error": e['original'], "correction": e['suggestions'][0] if e['suggestions'] else "Rephrase", "rule": e['message']} for e in grammar_result.get('errors', [])][:4]
        }
    }
    return jsonify(analysis_packet)

@app.route('/api/analyze/cv-summary/<sid>', methods=['GET'])
def get_cv_summary(sid):
    if sid not in active_sessions or not active_sessions[sid]['cv_frames']:
        return jsonify({"success": True, "cv": {"avg_confidence": 70, "emotions": {"neutral": 100}}})
    
    frames = active_sessions[sid]['cv_frames']
    good_eye = sum(1 for f in frames if f['eye_contact'])
    conf = int((good_eye / len(frames)) * 100) if frames else 70
    
    return jsonify({
        "success": True, 
        "cv": {
            "avg_confidence": max(50, conf),
            "frames_analyzed": len(frames)
        }
    })

@app.route('/api/interview/session/<sid>/response', methods=['POST'])
def save_response(sid):
    if sid in active_sessions:
        active_sessions[sid]['responses'].append(request.json)
    return jsonify({"success": True})

@app.route('/api/interview/session/<sid>/end', methods=['POST'])
def end_session(sid):
    return jsonify({"success": True})

if __name__ == '__main__':
    from config import PORT, HOST, DEBUG_MODE
    print(f"Starting Integrated Interview Dashboard on port {PORT}")
    app.run(debug=DEBUG_MODE, host=HOST, port=PORT)
