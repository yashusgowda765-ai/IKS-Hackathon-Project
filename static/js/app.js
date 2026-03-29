document.addEventListener('DOMContentLoaded', () => {
    const chantBtn = document.getElementById('chant-btn');
    const inputArea = document.getElementById('sanskrit-input');
    const loadingState = document.getElementById('loading');
    const playerSection = document.getElementById('player-section');
    const audioPlayer = document.getElementById('audio-player');
    const formattedText = document.getElementById('formatted-text');
    const errorMessage = document.getElementById('error-message');


    inputArea.addEventListener('input', () => {
        if (!inputArea.value.trim()) {
            playerSection.classList.add('hidden');
            audioPlayer.pause();
            audioPlayer.src = '';
            formattedText.innerHTML = '';
        }
        hideError();
    });

    chantBtn.addEventListener('click', async () => {
        const text = inputArea.value.trim();
        const modeInput = document.querySelector('input[name="chant-mode"]:checked');
        const mode = modeInput ? modeInput.value : 'rhythmic';
        const chandaSelect = document.getElementById('chanda-select');
        const chanda = chandaSelect ? chandaSelect.value : 'anushtubh';

        if (!text) {
            showError('Please enter some Sanskrit text to generate chanting.');
            return;
        }


        hideError();
        playerSection.classList.add('hidden');


        audioPlayer.pause();
        audioPlayer.src = '';

        loadingState.classList.remove('hidden');
        chantBtn.disabled = true;
        chantBtn.style.opacity = '0.7';

        try {
            const response = await fetch('/api/chant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, mode, chanda })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to generate audio');
            }

            loadingState.classList.add('hidden');


            audioPlayer.src = data.audio_url + '?t=' + new Date().getTime();
            audioPlayer.load();

            const rhythmHtml = data.formatted_text.replace(/,/g, '<span style="color: var(--primary-color)">,</span>');
            formattedText.innerHTML = rhythmHtml;

            playerSection.classList.remove('hidden');

            audioPlayer.play().catch(e => console.log('Auto-play prevented by browser:', e));

        } catch (error) {
            loadingState.classList.add('hidden');
            showError(error.message || 'An error occurred while generating audio. Please try again.');
        } finally {
            chantBtn.disabled = false;
            chantBtn.style.opacity = '1';
        }
    });

    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
        errorMessage.textContent = '';
    }
});