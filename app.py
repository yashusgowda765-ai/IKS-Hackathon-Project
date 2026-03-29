import os
import re
import uuid
import logging
import subprocess
import sys
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)


AUDIO_DIR = os.path.join(app.root_path, 'static', 'audio')
os.makedirs(AUDIO_DIR, exist_ok=True)


INDEPENDENT_VOWELS = r'[\u0904-\u0914\u0960-\u0961]'
DEPENDENT_VOWELS = r'[\u093E-\u094C\u0962-\u0963]'
CONSONANTS = r'[\u0915-\u0939\u0958-\u095F]'
HALANT = '\u094D'

def syllabify_and_format(text, pause_char=',', chanda='anushtubh'):
   
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split(' ')
    
    chanda_syllables = {
        'gayatri': 8,
        'anushtubh': 8,
        'pankti': 10,
        'trishtubh': 11,
        'jagati': 12,
        'shikharini': 17
    }
    pada_length = chanda_syllables.get(chanda.lower(), 8)
    
    formatted_words = []
    syllable_count = 0
    
    for word in words:
        chars = list(word)
        word_syllables = 0
        for i, char in enumerate(chars):
            if re.match(INDEPENDENT_VOWELS, char) or re.match(DEPENDENT_VOWELS, char):
                word_syllables += 1
            elif re.match(CONSONANTS, char):
                
                has_inherent_a = True
                if i + 1 < len(chars):
                    next_char = chars[i+1]
                    if re.match(DEPENDENT_VOWELS, next_char) or next_char == HALANT:
                        has_inherent_a = False
                if has_inherent_a:
                    word_syllables += 1
                    
        syllable_count += word_syllables
        
        
        if syllable_count >= pada_length:
            
            if not word.endswith((',', '।', '॥', '.', '?', '!')):
                word += pause_char
            syllable_count = syllable_count % pada_length
            
        formatted_words.append(word)

    result = ' '.join(formatted_words)
    
    if pause_char and not result.endswith(('.', '।', '॥', '?', '!')):
        result += (pause_char if pause_char != ',' else '.')
        
    return result

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chant', methods=['POST'])
def chant():
    data = request.json
    text = data.get('text', '')
    mode = data.get('mode', 'rhythmic')
    chanda = data.get('chanda', 'anushtubh')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    
    mode_configs = {
        'vedic': {'rate': '-35%', 'pitch': '-15Hz', 'pause_char': ' ॥'},
        'rhythmic': {'rate': '-5%', 'pitch': '+5Hz', 'pause_char': ','},
        'normal': {'rate': '+0%', 'pitch': '+0Hz', 'pause_char': ''}
    }
    
    config = mode_configs.get(mode, mode_configs['rhythmic'])
    
    
    rhythmic_text = syllabify_and_format(text, config['pause_char'], chanda)
    app.logger.info(f"Original Text: {text}")
    app.logger.info(f"Rhythmic Text: {rhythmic_text}")
    
    try:
        
        filename = f"chant_{uuid.uuid4().hex[:8]}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        
        voice = "hi-IN-MadhurNeural"
        
        command = [
            sys.executable, "-m", "edge_tts",
            "--text", rhythmic_text,
            "--voice", voice,
            f"--rate={config['rate']}",
            f"--pitch={config['pitch']}",
            "--write-media", filepath
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            app.logger.error(f"edge-tts failed: {result.stderr}")
            return jsonify({'error': 'Failed to generate audio using Edge-TTS'}), 500
                
        return jsonify({
            'success': True,
            'audio_url': f"/static/audio/{filename}",
            'formatted_text': rhythmic_text
        })
    except Exception as e:
        app.logger.error(f"Error generating TTS: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
