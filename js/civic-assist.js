document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('complaintForm');
  if (!form) return;

  const desc = document.getElementById('complaintDescription');
  const title = document.getElementById('complaintTitle');
  const evidence = document.getElementById('complaintEvidence');
  if (!desc) return;

  const box = document.createElement('section');
  box.className = 'civic-ai-assist';
  box.setAttribute('aria-label', 'Smart complaint assistant');
  box.innerHTML = `
    <div class="assist-head">
      <div class="assist-title">
        <div class="assist-badge">✦</div>
        <div><b>Smart Complaint Assistant</b><span>Voice & high-accuracy OCR</span></div>
      </div>
      <span class="assist-live">AI READY</span>
    </div>
    <div class="assist-subtitle">Speak your complaint or extract printed text from an image. OCR automatically improves the image before reading it and lets you review the result.</div>
    <div class="assist-tools">
      <label for="voiceLanguage">Voice language</label>
      <select id="voiceLanguage">
        <option value="en-IN">English (India)</option>
        <option value="hi-IN">Hindi</option>
        <option value="mr-IN">Marathi</option>
      </select>
      <label for="ocrLanguage">OCR language</label>
      <select id="ocrLanguage">
        <option value="eng">English</option>
        <option value="hin">Hindi</option>
        <option value="mar">Marathi</option>
        <option value="eng+hin+mar">Mixed English + Hindi + Marathi</option>
      </select>
    </div>
    <div class="assist-actions">
      <button type="button" class="assist-action assist-voice" id="voiceComplaint">
        <span class="action-icon">🎙</span><span><strong>Speak Complaint</strong><small>Use your voice to fill the complaint description</small></span>
      </button>
      <button type="button" class="assist-action assist-ocr" id="ocrComplaint">
        <span class="action-icon">▣</span><span><strong>Read Text From Image</strong><small>Preprocess + OCR for clearer printed text</small></span>
      </button>
    </div>
    <div id="assistStatus" class="assist-status">Ready — upload a clear text image, select its language, then run OCR.</div>
    <div class="assist-footer"><b>OCR tip:</b> Use a straight, well-lit image with large dark text on a light background. Voice and OCR run in the browser.</div>
  `;

  const anchor = desc.closest('.form-group') || desc.parentElement;
  anchor.parentNode.insertBefore(box, anchor.nextSibling);

  const status = document.getElementById('assistStatus');
  const voiceBtn = document.getElementById('voiceComplaint');
  const ocrBtn = document.getElementById('ocrComplaint');
  const voiceLanguage = document.getElementById('voiceLanguage');
  const ocrLanguage = document.getElementById('ocrLanguage');
  const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;

  function setStatus(message, type = '') {
    status.className = 'assist-status' + (type ? ' ' + type : '');
    status.textContent = message;
  }

  voiceBtn.addEventListener('click', () => {
    if (!Speech) {
      setStatus('Voice input is not supported by this browser. Please use Chrome or Edge.', 'error');
      return;
    }
    try {
      const recognition = new Speech();
      recognition.lang = voiceLanguage.value;
      recognition.interimResults = false;
      recognition.continuous = false;
      recognition.maxAlternatives = 1;
      voiceBtn.classList.add('recording');
      voiceBtn.querySelector('strong').textContent = 'Listening…';
      setStatus('Listening… speak your civic complaint clearly.', 'working');
      recognition.onresult = (event) => {
        const text = event.results?.[0]?.[0]?.transcript?.trim() || '';
        if (!text) { setStatus('No speech was detected. Please try again.', 'error'); return; }
        desc.value = (desc.value ? desc.value.trim() + ' ' : '') + text;
        desc.dispatchEvent(new Event('input', { bubbles: true }));
        if (!title.value.trim()) title.value = text.slice(0, 65);
        setStatus('Voice converted to text successfully. Review the text before submitting.', 'success');
      };
      recognition.onerror = (event) => {
        const messages = { 'not-allowed':'Microphone permission was denied. Allow microphone access in Chrome.', 'no-speech':'No speech detected. Please speak again.', 'audio-capture':'No microphone was found on this device.', 'network':'Browser speech service is unavailable. Check your internet connection.' };
        setStatus(messages[event.error] || ('Voice capture stopped: ' + event.error), 'error');
      };
      recognition.onend = () => {
        voiceBtn.classList.remove('recording');
        voiceBtn.querySelector('strong').textContent = 'Speak Complaint';
      };
      recognition.start();
    } catch (error) {
      console.error(error);
      voiceBtn.classList.remove('recording');
      voiceBtn.querySelector('strong').textContent = 'Speak Complaint';
      setStatus('Could not start voice input. Please check microphone permission and try again.', 'error');
    }
  });

  function loadTesseract() {
    if (window.Tesseract) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-tesseract]');
      if (existing) {
        existing.addEventListener('load', resolve, { once: true });
        existing.addEventListener('error', reject, { once: true });
        return;
      }
      const script = document.createElement('script');
      script.dataset.tesseract = 'true';
      script.src = 'https://cdn.jsdelivr.net/npm/tesseract.js@5/dist/tesseract.min.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function loadImage(file) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(file);
      img.onload = () => { URL.revokeObjectURL(url); resolve(img); };
      img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('The image could not be opened.')); };
      img.src = url;
    });
  }

  // Creates a high-resolution, grayscale/thresholded OCR image. The original evidence file is never changed.
  async function preprocessForOCR(file, variant = 'clean') {
    const img = await loadImage(file);
    const maxSide = 2600;
    const scale = Math.min(3, maxSide / Math.max(img.naturalWidth, img.naturalHeight));
    const width = Math.max(1, Math.round(img.naturalWidth * scale));
    const height = Math.max(1, Math.round(img.naturalHeight * scale));
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, width, height);
    ctx.drawImage(img, 0, 0, width, height);

    const image = ctx.getImageData(0, 0, width, height);
    const data = image.data;
    for (let i = 0; i < data.length; i += 4) {
      // Perceptual luminance removes colored backgrounds while retaining dark text.
      const lum = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      let value = (lum - 128) * 1.45 + 128; // contrast enhancement
      if (variant === 'threshold') value = value > 165 ? 255 : 0;
      value = Math.max(0, Math.min(255, value));
      data[i] = data[i + 1] = data[i + 2] = value;
    }
    ctx.putImageData(image, 0, 0);
    return canvas;
  }

  function normaliseOCRText(text) {
    return text
      .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, '')
      .replace(/\r/g, '')
      .replace(/[ \t]+/g, ' ')
      .replace(/ *\n */g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  function qualityScore(out) {
    const text = normaliseOCRText(out?.data?.text || '');
    const confidence = Number(out?.data?.confidence || 0);
    const usefulChars = (text.match(/[A-Za-z\u0900-\u097F0-9]/g) || []).length;
    const garbage = (text.match(/[|_~`^{}<>]{2,}/g) || []).length;
    return confidence + Math.min(usefulChars, 200) * 0.05 - garbage * 2;
  }

  ocrBtn.addEventListener('click', async () => {
    const file = evidence?.files?.[0];
    if (!file) { setStatus('First upload an evidence image above, then click Read Text From Image.', 'error'); return; }
    if (!/^image\/(jpeg|png|webp|jpg)/i.test(file.type)) { setStatus('OCR supports JPG, PNG and WEBP images.', 'error'); return; }
    if (file.size > 10 * 1024 * 1024) { setStatus('For OCR, please use an image smaller than 10 MB.', 'error'); return; }

    const language = ocrLanguage.value;
    const languageName = ocrLanguage.options[ocrLanguage.selectedIndex].text;
    ocrBtn.disabled = true;
    ocrBtn.classList.add('processing');

    try {
      setStatus('Loading high-accuracy OCR engine…', 'working');
      await loadTesseract();

      setStatus('Preprocessing image: resizing, grayscale and contrast enhancement…', 'working');
      const cleanCanvas = await preprocessForOCR(file, 'clean');

      setStatus(`Reading ${languageName} text… 0%`, 'working');
      const first = await Tesseract.recognize(cleanCanvas, language, {
        logger: m => {
          if (m.status === 'recognizing text') setStatus(`Reading ${languageName} text… ${Math.round((m.progress || 0) * 100)}%`, 'working');
        },
        tessedit_pageseg_mode: '6'
      });

      let best = first;
      // A second binary pass often improves clean printed documents/posters.
      const firstText = normaliseOCRText(first.data?.text || '');
      if (firstText.length < 25 || Number(first.data?.confidence || 0) < 65) {
        setStatus(`Trying a second OCR pass for better accuracy…`, 'working');
        const thresholdCanvas = await preprocessForOCR(file, 'threshold');
        const second = await Tesseract.recognize(thresholdCanvas, language, {
          logger: m => {
            if (m.status === 'recognizing text') setStatus(`Second OCR pass… ${Math.round((m.progress || 0) * 100)}%`, 'working');
          },
          tessedit_pageseg_mode: '6'
        });
        if (qualityScore(second) > qualityScore(first)) best = second;
      }

      const text = normaliseOCRText(best.data?.text || '');
      const confidence = Math.round(Number(best.data?.confidence || 0));
      if (!text || text.replace(/[^A-Za-z\u0900-\u097F0-9]/g, '').length < 5) {
        setStatus('No reliable text found. Use a straight, well-lit image with larger printed text.', 'error');
        return;
      }

      desc.value = (desc.value ? desc.value.trim() + '\n' : '') + text;
      desc.dispatchEvent(new Event('input', { bubbles: true }));
      if (!title.value.trim()) {
        const firstLine = text.split('\n').map(s => s.trim()).find(Boolean) || text;
        title.value = firstLine.replace(/\s+/g, ' ').slice(0, 65);
      }
      setStatus(`Text extracted successfully — OCR confidence ${confidence}%. Please review the text before submitting.`, 'success');
    } catch (error) {
      console.error('OCR error:', error);
      setStatus('OCR could not read this image. Try a clearer image, select the correct language, and try again.', 'error');
    } finally {
      ocrBtn.disabled = false;
      ocrBtn.classList.remove('processing');
    }
  });
});
