"""
IELTS Evaluator Pipeline
Combines Step 2 through Step 9 to process transcribed text and provide full feedback.
"""

from utils.step2_grammar_detection import detect_grammar_errors, tool
from utils.step3_grammar_correction_t5 import correct_paragraph_t5
from utils.step4_sentence_complexity import analyze_sentence_complexity
from utils.step5_vocabulary_richness import analyze_vocabulary_richness
from utils.step6_fluency_indicators import analyze_fluency_indicators
from utils.step7_metrics_to_scores import convert_metrics_to_scores
from utils.step8_ielts_band_predictor import predict_ielts_band
from utils.step9_gpt_feedback import generate_gpt_feedback

def evaluate_ielts_response(text: str) -> dict:
    print(f"\nAnalyzing Response: '{text}'...")
    
    # STEP 2: Grammar Error Detection
    print("\n=> STEP 2: Running Grammar Check...")
    grammar_result = detect_grammar_errors(text)
    grammar_error_count = grammar_result.get('total_errors', 0)
    accuracy_score = grammar_result.get('accuracy_score', 0)
    print(f"Total Grammar Errors: {grammar_error_count}")
    
    # STEP 3: Grammar Correction
    print("\n=> STEP 3: Running Grammar Correction...")
    correction_result = correct_paragraph_t5(text)
    corrected_text = correction_result.get('corrected', text)
    print(f"Corrected Response: {corrected_text}")

    # STEP 4: Sentence Complexity
    print("\n=> STEP 4: Analyzing Sentence Complexity...")
    complexity_result = analyze_sentence_complexity(text)
    complex_structures = complexity_result.get('complex_structures', 0)
    complexity_score_val = complexity_result.get('complexity_score', 5.0)
    print(f"Complex Structures Found: {complex_structures}")

    # STEP 5: Vocabulary Richness
    print("\n=> STEP 5: Analyzing Vocabulary Richness...")
    vocab_result = analyze_vocabulary_richness(text)
    vocab_richness = vocab_result.get('vocabulary_richness', 0.0)
    vocab_score_val = vocab_result.get('vocabulary_score', 5.0)
    print(f"Vocabulary Richness Ratio: {vocab_richness}")

    # STEP 6: Fluency Indicators
    print("\n=> STEP 6: Detecting Fluency Indicators...")
    fluency_result = analyze_fluency_indicators(text)
    filler_count = fluency_result.get('filler_count', 0)
    fluency_score_val = fluency_result.get('fluency_score', 5.0)
    print(f"Filler Words: {filler_count}")

    # STEP 7: Convert Metrics to Scores
    print("\n=> STEP 7: Converting to Scores...")
    word_count = len(text.split())
    scores = convert_metrics_to_scores(
        grammar_error_count=grammar_error_count,
        vocab_richness=vocab_richness,
        complex_count=complex_structures,
        filler_count=filler_count,
        total_words=word_count,
        accuracy_score=accuracy_score,
        complexity_score=complexity_score_val,
        fluency_score=fluency_score_val,
        vocabulary_score=vocab_score_val
    )
    overall_score = scores.get('overall_score', 5.0)

    # STEP 8: IELTS Band Predictor
    print("\n=> STEP 8: Predicting IELTS Band...")
    band_prediction = predict_ielts_band(overall_score)
    predicted_band = band_prediction.get('band', 'N/A')
    print(f"Predicted IELTS Band: {predicted_band}")

    # STEP 9: GPT Feedback
    print("\n=> STEP 9: Generating GPT Feedback...")
    gpt_feedback = generate_gpt_feedback(
        text=text,
        grammar_error_count=grammar_error_count,
        vocab_richness=vocab_richness,
        complex_count=complex_structures
    )
    print("\nGPT Feedback:")
    print(gpt_feedback)

    return {
        "text": text,
        "corrected_text": corrected_text,
        "grammar": grammar_result,
        "complexity": complexity_result,
        "vocabulary": vocab_result,
        "fluency": fluency_result,
        "scores": scores,
        "ielts_band": band_prediction,
        "gpt_feedback": gpt_feedback
    }

if __name__ == "__main__":
    # Example typical of speech-to-text input
    test_text = "Well, like, she go to market yesterday, you know, and buy vegetables because she, um, needed cooking ingredients."
    
    evaluate_ielts_response(test_text)
