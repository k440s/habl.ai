"""
Habl.AI Core Engine
Text translation and text-to-speech generation

Source: English-US → Target: 9 languages (including English)

Requirements: pip install gtts deep-translator pydub

DATA SOURCES:
- Translation: Google Translate API (via deep-translator)
- Text-to-Speech: Google TTS (via gTTS)
- Both services work in the cloud, no need to download models
"""

from gtts import gTTS
from deep_translator import GoogleTranslator
import os
from datetime import datetime

class LocalizationAI:
    def __init__(self):
        # Source language is always English-US
        self.source_language = 'en'
        
        # 9 supported target languages (including English for TTS)
        self.target_languages = {
            'en': 'English (US)',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ja': 'Japanese',
            'zh-CN': 'Chinese',
            'ko': 'Korean'
        }
        
        print("✓ Habl.AI Core initialized")
        print(f"  Source language: English (US)")
        print(f"  Target languages: {len(self.target_languages)}")
        
    def translate_text(self, text, target_lang):
        """
        Translates text from English-US to target language
        If text is too long (>4500 chars), it splits into chunks
        
        Args:
            text (str): English text to translate
            target_lang (str): Target language code (es, fr, de, etc.)
        
        Returns:
            str: Translated text
        """
        MAX_CHUNK_SIZE = 4500  # Google Translate limit
        
        try:
            # If text is short, translate directly
            if len(text) <= MAX_CHUNK_SIZE:
                # If target is same as source (en → en), return original text
                if target_lang == self.source_language:
                    return text
                
                translator = GoogleTranslator(source=self.source_language, target=target_lang)
                return translator.translate(text)
            
            # If text is long, split into chunks
            print(f"  ⚠️  Long text ({len(text)} chars), splitting into chunks...")
            
            # Split by paragraphs first (to maintain context)
            paragraphs = text.split('\n\n')
            chunks = []
            current_chunk = []
            current_length = 0
            
            for paragraph in paragraphs:
                paragraph_length = len(paragraph)
                
                # If a single paragraph is too long, split by sentences
                if paragraph_length > MAX_CHUNK_SIZE:
                    sentences = paragraph.split('. ')
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if not sentence:
                            continue
                        
                        if current_length + len(sentence) + 2 > MAX_CHUNK_SIZE:
                            if current_chunk:
                                chunks.append(' '.join(current_chunk))
                            current_chunk = [sentence]
                            current_length = len(sentence)
                        else:
                            current_chunk.append(sentence)
                            current_length += len(sentence) + 2
                else:
                    # Add complete paragraph if it fits
                    if current_length + paragraph_length + 2 > MAX_CHUNK_SIZE:
                        if current_chunk:
                            chunks.append('\n\n'.join(current_chunk))
                        current_chunk = [paragraph]
                        current_length = paragraph_length
                    else:
                        current_chunk.append(paragraph)
                        current_length += paragraph_length + 2
            
            # Add last chunk
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
            
            print(f"  📦 Split into {len(chunks)} chunks")
            
            # If target is same as source (en → en), return original chunks
            if target_lang == self.source_language:
                print(f"  ℹ️  Target language is same as source, returning original text")
                return text
            
            # Translate each chunk
            translator = GoogleTranslator(source=self.source_language, target=target_lang)
            translated_chunks = []
            
            for i, chunk in enumerate(chunks, 1):
                print(f"  🔄 Translating chunk {i}/{len(chunks)} ({len(chunk)} chars)...")
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            
            # Join all translated chunks
            full_translation = '\n\n'.join(translated_chunks)
            print(f"  ✅ Translation complete: {len(full_translation)} chars")
            
            return full_translation
            
        except Exception as e:
            return f"Translation error: {str(e)}"
    
    def text_to_speech(self, text, lang, output_dir='output_audio'):
        """
        Converts text to MP3 audio using Google TTS
        If text is too long (>4999 chars), it splits into chunks and combines them
        
        Args:
            text (str): Text to convert to audio
            lang (str): Language code for voice
            output_dir (str): Folder where to save audio
        
        Returns:
            str: Path to generated file
        """
        MAX_TTS_SIZE = 4999  # gTTS limit
        
        try:
            # Create folder if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"audio_{lang}_{timestamp}.mp3")
            
            # If text is short, generate directly
            if len(text) <= MAX_TTS_SIZE:
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(filename)
                print(f"  ✓ Audio generated: {filename}")
                return filename
            
            # If text is long, split and combine
            print(f"  ⚠️  Long text for TTS ({len(text)} chars), splitting...")
            
            try:
                from pydub import AudioSegment
            except ImportError:
                print("  ⚠️  pydub not installed. Truncating text to 4999 chars...")
                text = text[:MAX_TTS_SIZE]
                tts = gTTS(text=text, lang=lang, slow=False)
                tts.save(filename)
                print(f"  ✓ Audio generated (truncated): {filename}")
                return filename
            
            # Split by sentences
            sentences = text.replace('.\n', '. ').replace('.\r', '. ').split('. ')
            chunks = []
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                sentence_length = len(sentence)
                
                if current_length + sentence_length + 2 > MAX_TTS_SIZE:
                    if current_chunk:
                        chunks.append('. '.join(current_chunk) + '.')
                    current_chunk = [sentence]
                    current_length = sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length + 2
            
            if current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
            
            print(f"  📦 Split into {len(chunks)} audio chunks")
            
            # Generate audio for each chunk
            combined = AudioSegment.empty()
            
            for i, chunk in enumerate(chunks, 1):
                print(f"  🎵 Generating audio chunk {i}/{len(chunks)}...")
                temp_filename = os.path.join(output_dir, f"temp_{lang}_{timestamp}_{i}.mp3")
                tts = gTTS(text=chunk, lang=lang, slow=False)
                tts.save(temp_filename)
                
                # Load and combine
                audio_chunk = AudioSegment.from_mp3(temp_filename)
                combined += audio_chunk
                
                # Remove temporary file
                os.remove(temp_filename)
            
            # Save combined audio
            combined.export(filename, format="mp3")
            print(f"  ✓ Complete audio generated: {filename}")
            
            return filename
            
        except Exception as e:
            return f"TTS error: {str(e)}"


# Example usage for testing
if __name__ == "__main__":
    # Initialize system
    ai = LocalizationAI()
    
    print("\n" + "="*60)
    print("HABL.AI CORE ENGINE - TEST MODE")
    print("="*60)
    
    # Test 1: Simple translation
    print("\n📌 TEST 1: Simple translation")
    text = "Hello, this is a test of the Habl.AI translation system"
    translated = ai.translate_text(text, 'es')
    print(f"Original: {text}")
    print(f"Spanish: {translated}")
    
    # Test 2: Text-to-speech
    print("\n📌 TEST 2: Text-to-speech generation")
    audio_file = ai.text_to_speech(translated, 'es')
    print(f"Audio saved: {audio_file}")
    
    # Test 3: English to English (TTS only)
    print("\n📌 TEST 3: English TTS (no translation)")
    audio_en = ai.text_to_speech(text, 'en')
    print(f"English audio: {audio_en}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETED")
    print("="*60)