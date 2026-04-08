import speech_recognition as sr
import os
import tempfile
import time

def transcribe_audio_google(audio_file_path):
    """
    Transcribe audio using Google Speech Recognition API
    """
    try:
        recognizer = sr.Recognizer()
        
        print(f"[TRANSCRIPTION] Loading audio file: {audio_file_path}")
        
        # Load audio file
        with sr.AudioFile(audio_file_path) as source:
            audio = recognizer.record(source)
        
        print("[TRANSCRIPTION] Audio loaded, transcribing...")
        
        # Use Google Speech Recognition
        try:
            text = recognizer.recognize_google(audio, language='en-US')
            print(f"[TRANSCRIPTION] ✅ Success! Text: {text[:100]}")
            return {
                "text": text.strip(),
                "confidence": 0.85,
                "language": "en",
                "error": None
            }
        except sr.UnknownValueError:
            return {
                "text": "",
                "confidence": 0,
                "language": "en",
                "error": "Could not understand audio. Please speak clearly."
            }
        except sr.RequestError as e:
            return {
                "text": "",
                "confidence": 0,
                "language": "en",
                "error": f"API error: {str(e)}"
            }
    
    except Exception as e:
        print(f"[TRANSCRIPTION] Error loading audio: {str(e)}")
        return {
            "text": "",
            "confidence": 0,
            "language": "en",
            "error": str(e)
        }

def transcribe_audio_from_file(audio_file):
    """
    Transcribe audio from Flask file object
    """
    temp_path = None
    
    try:
        # Read audio data
        audio_data = audio_file.read()
        
        if not audio_data or len(audio_data) < 100:
            return {
                "text": "",
                "confidence": 0,
                "language": "en",
                "error": "Audio data too small. Please record longer."
            }
        
        print(f"[TRANSCRIPTION] Received {len(audio_data)} bytes")
        
        # Determine file extension based on content
        temp_dir = tempfile.gettempdir()
        timestamp = int(time.time() * 1000)
        
        # Check if it's WAV format (WAV starts with RIFF header)
        is_wav = audio_data[:4] == b'RIFF'
        
        if is_wav:
            extension = '.wav'
            print("[TRANSCRIPTION] Detected WAV format")
        else:
            extension = '.webm'
            print("[TRANSCRIPTION] Detected WebM format")
        
        temp_path = os.path.join(temp_dir, f"audio_{timestamp}{extension}")
        
        # Save audio file
        with open(temp_path, 'wb') as f:
            f.write(audio_data)
        
        print(f"[TRANSCRIPTION] Saved audio: {temp_path}")
        
        # Transcribe the audio file
        result = transcribe_audio_google(temp_path)
        return result
    
    except Exception as e:
        print(f"[TRANSCRIPTION] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "text": "",
            "confidence": 0,
            "language": "en",
            "error": f"Error: {str(e)}"
        }
    
    finally:
        # Cleanup temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                print(f"[CLEANUP] Deleted: {temp_path}")
            except Exception as e:
                print(f"[CLEANUP] Error deleting {temp_path}: {e}")


