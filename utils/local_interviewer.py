import torch
from transformers import pipeline

class PretrainedLocalExaminer:
    def __init__(self):
        # We use a completely offline pre-trained conversational generation model 
        # that doesn't rely on Gemini/OpenAI API keys. 
        # Using Flan-T5-base for fast local generation
        print("[SETUP] Loading completely offline pre-trained response generation model...")
        self.model_name = "google/flan-t5-base"
        try:
            self.generator = pipeline("text2text-generation", model=self.model_name)
            self.is_ready = True
            print("[SETUP] Pre-trained model loaded successfully.")
        except Exception as e:
            print("[SETUP Error] Could not load offline model:", e)
            self.is_ready = False
            
    def generate_question(self, context="Start the interview"):
        if not self.is_ready:
            return "Tell me about your hobbies."
            
        prompt = f"Generate an IELTS speaking test question. Context: {context}"
        try:
            res = self.generator(prompt, max_length=50, num_return_sequences=1)
            return res[0]['generated_text']
        except:
            return "Can you elaborate on that?"

    def generate_feedback(self, text, grammar_errors, vocab_score):
        if not self.is_ready:
            return "Good effort! Work on grammar."
            
        prompt = f"Provide brief feedback for an English learner. They said: '{text}'. They had {grammar_errors} grammar errors."
        try:
            res = self.generator(prompt, max_length=150, num_return_sequences=1)
            return res[0]['generated_text']
        except:
            return "Please focus on speaking more clearly and expanding your vocabulary."

local_examiner = PretrainedLocalExaminer()
