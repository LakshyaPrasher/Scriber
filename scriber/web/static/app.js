  var currentResult = null;
  window.currentResult = null;
  var selectedVoiceProfile = null;
  window.selectedVoiceProfile = null;
  var loadedMediaUrl = null;
  var realAudioBuffer = null;
  var audioContext = null;

  const BROWSER_PLAYABLE_EXTS = ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'mp4', 'webm', 'flac', 'opus', 'mov', 'm4v'];

  function loadAudioForPlayback(targetAudioSrc) {
    const audioPlayer = document.getElementById('audio-player');
    if (!audioPlayer) return;
    initAudioPlayerEvents();
    audioPlayer.muted = false;
    const volSlider = document.getElementById('master-volume-slider');
    const targetVol = (volSlider && !isNaN(parseFloat(volSlider.value)) && parseFloat(volSlider.value) > 0)
      ? parseFloat(volSlider.value)
      : (audioPlayer.volume > 0 ? audioPlayer.volume : 1.0);
    audioPlayer.volume = Math.max(0, Math.min(1, targetVol));
    if (volSlider) volSlider.value = audioPlayer.volume;

    if (targetAudioSrc) {
      loadedMediaUrl = targetAudioSrc;
      const curAttr = audioPlayer.getAttribute('src');
      if (curAttr !== targetAudioSrc && audioPlayer.src !== targetAudioSrc) {
        audioPlayer.src = targetAudioSrc;
        audioPlayer.load();
      }
    }
  }
  window.loadAudioForPlayback = loadAudioForPlayback;

  /* Toast Notification System */
  function showToast(message, type) {
    type = type || 'success';
    var cont = document.getElementById('toast-container');
    if (!cont) return;
    var t = document.createElement('div');
    t.className = 'toast toast-' + type;
    var icons = {
      success: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
      error: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
      info: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><line x1="12" y1="11" x2="12" y2="16"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };
    var icon = icons[type] || icons.info;
    t.innerHTML = '<span class="toast-icon" aria-hidden="true">' + icon + '</span><span>' + escapeHtml(message) + '</span>';
    cont.appendChild(t);
    setTimeout(function() { t.classList.add('show'); }, 20);
    setTimeout(function() {
      t.classList.remove('show');
      setTimeout(function() { if (t.parentNode) t.parentNode.removeChild(t); }, 300);
    }, 3000);
  }
  /* Dropzone keyboard activation (Enter/Space) */
  function handleDropzoneKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ' || e.code === 'Space') {
      e.preventDefault();
      openFileDialog(e);
    }
  }
  window.handleDropzoneKeydown = handleDropzoneKeydown;

  /* Roving arrow-key focus for the mode tablist */
  document.querySelectorAll('.nav-pill').forEach(function(tab) {
    tab.addEventListener('keydown', function(e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const tabs = Array.from(document.querySelectorAll('.nav-pill'));
      const idx = tabs.indexOf(tab);
      if (idx === -1) return;
      e.preventDefault();
      const next = e.key === 'ArrowRight'
        ? tabs[(idx + 1) % tabs.length]
        : tabs[(idx - 1 + tabs.length) % tabs.length];
      next.focus();
      next.click();
    });
  });

  /* Mode Switching */
  function switchMode(mode) {
    if (typeof closeAllModelDropdowns === 'function') closeAllModelDropdowns();
    document.querySelectorAll('.nav-pill').forEach(btn => {
      btn.classList.remove('active');
      btn.setAttribute('aria-selected', 'false');
      btn.setAttribute('tabindex', '-1');
    });
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));

    const btn = document.getElementById('btn-mode-' + mode);
    if (btn) {
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      btn.setAttribute('tabindex', '0');
    }

    let viewId = 'transcribe-view';
    if (mode === 'voice') viewId = 'voice-view';
    else if (mode === 'about') viewId = 'about-view';

    const view = document.getElementById(viewId);
    if (view) view.classList.add('active');

    if (mode === 'voice') {
      if (!selectedVoiceProfile && currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
        populateVoiceProfiles(currentResult.voice_profiles);
      }
    } else if (mode === 'transcribe') {
      if (currentResult) {
        const dur = getAccurateDuration();
        const fName = (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
        initModeAudioEditor('m1', dur > 0 ? dur : 10, fName);
      }
      setTimeout(drawWave, 50);
    } else if (mode === 'about') {
      initBentoSpotlight();
    }
  }

  /* Ongoing Process Live Highlighting Indicator for Navigation Pills */
  function setNavProcessingState(mode, isProcessing) {
    const pillMap = {
      'transcribe': document.getElementById('btn-mode-transcribe'),
      'voice': document.getElementById('btn-mode-voice'),
      'about': document.getElementById('btn-mode-about')
    };
    const pill = pillMap[mode];
    if (!pill) return;
    if (isProcessing) {
      pill.classList.add('processing-active');
      pill.setAttribute('data-processing', 'true');
    } else {
      pill.classList.remove('processing-active');
      pill.removeAttribute('data-processing');
    }
  }

  /* Dynamic Name Card Spotlight & Live Diagnostic Audition */
  function initBentoSpotlight() {
    var cards = document.querySelectorAll('.about-card, .social-node-card');
    cards.forEach(function(card) {
      if (card.__hasSpotlight) return;
      card.__hasSpotlight = true;

      card.addEventListener('mousemove', function(e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        card.style.setProperty('--mouse-x', x + 'px');
        card.style.setProperty('--mouse-y', y + 'px');
      });

      card.addEventListener('mouseleave', function() {
        card.style.setProperty('--mouse-x', '-500px');
        card.style.setProperty('--mouse-y', '-500px');
      });
    });
  }

  function copyContactHandle(evt) {
    if (evt && evt.preventDefault) evt.preventDefault();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText('lakshya.prasher@gmail.com').then(function() {
        showToast('Contact email copied: lakshya.prasher@gmail.com', 'success');
      }).catch(function() {
        showToast('Direct contact: lakshya.prasher@gmail.com', 'info');
      });
    } else {
      showToast('Direct contact: lakshya.prasher@gmail.com', 'info');
    }
  }

  function checkUrlMode() {
    try {
      var params = new URLSearchParams(window.location.search);
      var mode = params.get('mode') || (window.location.hash ? window.location.hash.replace('#', '') : null);
      if (mode) switchMode(mode);
    } catch (e) {}
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initBentoSpotlight();
      checkUrlMode();
    });
  } else {
    initBentoSpotlight();
    checkUrlMode();
  }

  /* Reliable, Thread-Safe File Dialog Opening (Guarded against double invocation & COM deadlocks) */
  var isFileDialogOpening = false;
  async function openFileDialog(evt) {
    if (evt) {
      if (typeof evt.preventDefault === 'function') evt.preventDefault();
      if (typeof evt.stopPropagation === 'function') evt.stopPropagation();
    }
    if (isFileDialogOpening) {
      return;
    }
    isFileDialogOpening = true;

    // Direct native desktop file dialog integration (zero upload overhead, instant start)
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_file_dialog === 'function') {
      try {
        const filePath = await window.pywebview.api.open_file_dialog();
        isFileDialogOpening = false;
        if (filePath) {
          startProcessingPath(filePath);
          return;
        }
      } catch (err) {
        console.warn('Native open_file_dialog fallback:', err);
      }
    }

    var releaseLock = function() {
      setTimeout(function() { isFileDialogOpening = false; }, 300);
      window.removeEventListener('focus', releaseLock);
    };
    window.addEventListener('focus', releaseLock);
    setTimeout(releaseLock, 1500);

    const input = document.getElementById('media-file-input');
    if (input) {
      input.value = '';
      input.click();
    }
  }

  /* Drag & Drop Setup */
  const dropzone = document.getElementById('dropzone');
  if (dropzone) {
    ['dragenter', 'dragover'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('drag-active');
      }, false);
    });
    ['dragleave', 'dragend', 'drop'].forEach(name => {
      dropzone.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('drag-active');
      }, false);
    });
    dropzone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        const file = dt.files[0];
        const nativePath = file.path || '';
        if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
          startProcessingPath(nativePath);
        } else {
          startProcessing(file);
        }
      }
    }, false);
  }

  // Prevent browser from navigating away on dropped media files
  window.addEventListener('dragover', (e) => {
    e.preventDefault();
  }, false);

  window.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      const outView = document.getElementById('output-viewport');
      if (!outView || outView.style.display === 'none') {
        const file = dt.files[0];
        const nativePath = file.path || '';
        if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
          startProcessingPath(nativePath);
        } else {
          startProcessing(file);
        }
      }
    }
    e.preventDefault();
  }, false);

  function handleFileSelected(e) {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      const nativePath = file.path || '';
      if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
        startProcessingPath(nativePath);
      } else {
        startProcessing(file);
      }
    }
  }

  /* Precision Real-Time Progress Tracker with Backend Telemetry & Dynamic ETA */
  var progressPollInterval = null;

  function formatDuration(sec) {
    if (!sec || isNaN(sec) || sec < 0) return '00:00';
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  function formatEta(sec) {
    if (!sec || isNaN(sec) || sec <= 0) return 'Calculating remaining time...';
    if (sec < 60) return Math.ceil(sec) + 's remaining';
    var m = Math.floor(sec / 60);
    var s = Math.floor(sec % 60);
    return m + 'm ' + (s > 0 ? s + 's ' : '') + 'remaining';
  }

  function updateProgressUI(data) {
    if (!data) return;
    var pct = Math.max(0, Math.min(100, data.percent || 0));
    var fillEl = document.getElementById('progress-fill');
    var pctBadge = document.getElementById('progress-pct-badge');
    var etaText = document.getElementById('progress-eta-text');
    var speedText = document.getElementById('progress-speed-text');
    var posText = document.getElementById('progress-position-text');
    var elapsedText = document.getElementById('progress-elapsed-text');
    var titleEl = document.getElementById('processing-main-title');
    var subEl = document.getElementById('processing-status-text');

    if (fillEl) {
      fillEl.style.width = pct + '%';
      fillEl.setAttribute('aria-valuenow', String(Math.round(pct)));
    }
    if (pctBadge) pctBadge.innerText = pct + '%';

    if (etaText) {
      if (pct >= 100) {
        etaText.innerText = 'Completed';
      } else if (data.eta_sec && data.eta_sec > 0) {
        etaText.innerText = formatEta(data.eta_sec);
      } else if (pct >= 95) {
        etaText.innerText = 'Finalizing...';
      } else {
        etaText.innerText = 'Estimating time...';
      }
    }

    if (speedText) {
      var speedItem = document.getElementById('progress-speed-item');
      if (data.speed_factor && data.speed_factor > 0) {
        speedText.innerText = data.speed_factor.toFixed(1) + 'x speed';
        if (speedItem) speedItem.style.display = '';
      } else {
        speedText.innerText = '';
        if (speedItem) speedItem.style.display = 'none';
      }
    }

    if (posText) {
      if (data.total_duration_sec && data.total_duration_sec > 0) {
        posText.innerText = formatDuration(data.current_time_sec) + ' / ' + formatDuration(data.total_duration_sec) + ' decoded';
      } else {
        posText.innerText = 'Analyzing audio...';
      }
    }

    if (elapsedText) {
      elapsedText.innerText = 'Elapsed: ' + Math.floor(data.elapsed_sec || 0) + 's';
    }

    if (titleEl && data.title) titleEl.innerText = data.title;
    if (subEl && data.subtitle) subEl.innerText = data.subtitle;
  }

  function startLiveProgressTracker() {
    if (progressPollInterval) clearInterval(progressPollInterval);

    updateProgressUI({
      percent: 4,
      title: "Transcribing & Translating to English",
      subtitle: "Reading the media and preparing the speech track...",
      phase: "Step 1 of 4 · Reading audio",
      speed_factor: 0,
      current_time_sec: 0,
      total_duration_sec: 0,
      elapsed_sec: 0,
      eta_sec: 0
    });

    progressPollInterval = setInterval(async function() {
      try {
        var res = await fetch('/api/progress');
        if (!res.ok) return;
        var p = await res.json();
        if (p && p.active) {
          updateProgressUI(p);
        }
      } catch (e) {
        // Silent retry
      }
    }, 350);
  }

  function stopLiveProgressTracker() {
    if (progressPollInterval) {
      clearInterval(progressPollInterval);
      progressPollInterval = null;
    }
  }

  /* ========================================================= */
  /* ACTIVE JOB CANCELLATION & ABORT CONTROLLERS               */
  /* ========================================================= */
  var activeProcessAbortController = null;
  var activeVoiceAbortController = null;

  async function cancelActiveProcessing(e) {
    if (e && e.preventDefault) e.preventDefault();
    setNavProcessingState('transcribe', false);
    if (activeProcessAbortController) {
      activeProcessAbortController.abort();
      activeProcessAbortController = null;
    }
    try {
      await fetch('/api/cancel', { method: 'POST' });
    } catch (err) {}
    stopLiveProgressTracker();
    stopLiquidOrbAnimation();
    setTranscribeModelLocked(false);
    resetToUpload();
    showToast('Processing cancelled. System idle.', 'info');
  }
  window.cancelActiveProcessing = cancelActiveProcessing;

  async function cancelVoiceSynthesis(e) {
    if (e && e.preventDefault) e.preventDefault();
    setNavProcessingState('voice', false);
    if (activeVoiceAbortController) {
      activeVoiceAbortController.abort();
      activeVoiceAbortController = null;
    }
    try {
      await fetch('/api/cancel', { method: 'POST' });
    } catch (err) {}
    stopAcousticResonanceAnimation();
    setVoiceModelLocked(false);
    var btn = document.getElementById('synthesize-btn');
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> Synthesize Speech';
    }
    showToast('Voice synthesis cancelled.', 'info');
  }
  window.cancelVoiceSynthesis = cancelVoiceSynthesis;

  async function startProcessingPath(filePath, options) {
    if (!filePath) return;
    const fileName = filePath.split(/[\\/]/).pop() || filePath;
    const maxDuration = (options && options.max_duration) || (typeof options === 'number' ? options : null);

    // Transition into Liquid Morphing Orb & Genuine Progress Viewport
    document.getElementById('dropzone').style.display = 'none';
    const procCard = document.getElementById('processing-card');
    procCard.style.display = 'block';
    // The source filename is intentionally kept out of the compact progress view.
    document.getElementById('output-viewport').style.display = 'none';

    // Start minimalist organic liquid light animation and live backend progress polling
    startLiquidOrbAnimation();
    startLiveProgressTracker();
    setTranscribeModelLocked(true);
    setNavProcessingState('transcribe', true);

    if (loadedMediaUrl && loadedMediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(loadedMediaUrl);
    }
    loadedMediaName = fileName;
    const fileExt = (fileName || '').split('.').pop().toLowerCase();
    const isDirectAudio = BROWSER_PLAYABLE_EXTS.includes(fileExt);
    if (isDirectAudio) {
      loadAudioForPlayback('/api/media?path=' + encodeURIComponent(filePath));
    } else {
      loadedMediaUrl = '';
      const audioPlayer = document.getElementById('audio-player');
      if (audioPlayer) {
        audioPlayer.removeAttribute('src');
        audioPlayer.load();
      }
    }

    if (activeProcessAbortController) {
      activeProcessAbortController.abort();
    }
    activeProcessAbortController = new AbortController();

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: activeProcessAbortController.signal,
        body: JSON.stringify({
          file_path: filePath,
          task: 'translate',
          language: 'auto',
          model: selectedTranscribeModel || 'turbo',
          max_duration: maxDuration
        })
      });
      const data = await res.json();
      activeProcessAbortController = null;

      stopLiveProgressTracker();
      stopLiquidOrbAnimation();

      if (data.cancelled) {
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      if (data.error) {
        showToast('Processing error: ' + data.error, 'error');
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      updateProgressUI({
        percent: 100,
        phase: 'Step 4 of 4 · Complete',
        title: 'Transcription & Translation Complete',
        subtitle: 'Transcription segments prepared for review',
        eta_sec: 0
      });

      currentResult = data;
      showToast('Transcription & Translation complete! Ready for review.', 'success');
      renderTranscription(data);
      setTranscribeModelLocked(false);
      setNavProcessingState('transcribe', false);
    } catch (err) {
      activeProcessAbortController = null;
      stopLiveProgressTracker();
      stopLiquidOrbAnimation();
      setNavProcessingState('transcribe', false);
      if (err.name === 'AbortError') {
        return;
      }
      showToast('Processing error: ' + err, 'error');
      resetToUpload();
      setTranscribeModelLocked(false);
    }
  }

  async function startProcessing(file) {
    if (!file) return;

    // Transition into Liquid Morphing Orb & Genuine Progress Viewport
    document.getElementById('dropzone').style.display = 'none';
    const procCard = document.getElementById('processing-card');
    procCard.style.display = 'block';
    // The source filename is intentionally kept out of the compact progress view.
    document.getElementById('output-viewport').style.display = 'none';

    // Start minimalist organic liquid light animation and live backend progress polling
    startLiquidOrbAnimation();
    startLiveProgressTracker();
    setTranscribeModelLocked(true);
    setNavProcessingState('transcribe', true);

    if (loadedMediaUrl && loadedMediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(loadedMediaUrl);
    }
    const uploadExt = (file.name || '').split('.').pop().toLowerCase();
    const isDirectAudio = BROWSER_PLAYABLE_EXTS.includes(uploadExt);
    if (isDirectAudio) {
      loadAudioForPlayback(URL.createObjectURL(file));
      decodeAudioFileForWaveform(file);
    } else {
      loadedMediaUrl = '';
      const audioPlayer = document.getElementById('audio-player');
      if (audioPlayer) {
        audioPlayer.removeAttribute('src');
        audioPlayer.load();
      }
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('task', 'translate');
    formData.append('language', 'auto');
    formData.append('model', selectedTranscribeModel || 'turbo');

    if (activeProcessAbortController) {
      activeProcessAbortController.abort();
    }
    activeProcessAbortController = new AbortController();

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        signal: activeProcessAbortController.signal,
        body: formData
      });
      const data = await res.json();
      activeProcessAbortController = null;

      stopLiveProgressTracker();
      stopLiquidOrbAnimation();

      if (data.cancelled) {
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      if (data.error) {
        showToast('Processing error: ' + data.error, 'error');
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      updateProgressUI({
        percent: 100,
        phase: 'Step 4 of 4 · Complete',
        title: 'Transcription & Translation Complete',
        subtitle: 'Transcription segments prepared for review',
        eta_sec: 0
      });

      currentResult = data;
      showToast('Transcription & Translation complete! Ready for review.', 'success');
      renderTranscription(data);
      setTranscribeModelLocked(false);
      setNavProcessingState('transcribe', false);
    } catch (err) {
      activeProcessAbortController = null;
      stopLiveProgressTracker();
      stopLiquidOrbAnimation();
      setNavProcessingState('transcribe', false);
      if (err.name === 'AbortError') {
        return;
      }
      showToast('Upload or network failed: ' + err, 'error');
      resetToUpload();
      setTranscribeModelLocked(false);
    }
  }

  function resetToUpload() {
    setNavProcessingState('transcribe', false);
    if (activeProcessAbortController) {
      activeProcessAbortController.abort();
      activeProcessAbortController = null;
    }
    setTranscribeModelLocked(false);
    document.getElementById('dropzone').style.display = 'block';
    document.getElementById('processing-card').style.display = 'none';
    document.getElementById('output-viewport').style.display = 'none';
    const syntheticWarning = document.getElementById('synthetic-warning');
    if (syntheticWarning) syntheticWarning.style.display = 'none';
    const player = document.getElementById('audio-player');
    if (player) { player.pause(); player.currentTime = 0; }
    updatePlayPauseIcons(false);
    if (typeof toggleAudioToolsDrawer === 'function') {
      toggleAudioToolsDrawer(false);
    }
  }

  /* Audio Transport Controls & Reliable Native Event Management */
  /* Waveform Animation Loop Scheduler (Prevents duplicate RAF pileups) */
  var waveAnimId = null;
  function scheduleWaveAnimation() {
    if (waveAnimId) cancelAnimationFrame(waveAnimId);
    waveAnimId = requestAnimationFrame(drawWave);
  }
  function stopWaveAnimation() {
    if (waveAnimId) {
      cancelAnimationFrame(waveAnimId);
      waveAnimId = null;
    }
  }

  /* Audio Transport Controls & Reliable Native Event Management */
  function initAudioPlayerEvents() {
    const player = document.getElementById('audio-player');
    if (!player || player.__scriberBound) return;
    player.__scriberBound = true;

    player.addEventListener('play', function() {
      if (typeof initAudioVisualizer === 'function') initAudioVisualizer(player);
      updatePlayPauseIcons(true);
      scheduleWaveAnimation();
    });

    player.addEventListener('playing', function() {
      if (typeof initAudioVisualizer === 'function') initAudioVisualizer(player);
      updatePlayPauseIcons(true);
      scheduleWaveAnimation();
    });

    player.addEventListener('pause', function() {
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      drawWave();
    });

    player.addEventListener('ended', function() {
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      handleAudioEnded();
      drawWave();
    });

    player.addEventListener('timeupdate', function() {
      handleAudioTimeUpdate();
    });

    player.addEventListener('seeking', function() {
      handleAudioTimeUpdate();
    });

    player.addEventListener('seeked', function() {
      handleAudioTimeUpdate();
      drawWave();
    });

    player.addEventListener('loadedmetadata', function() {
      handleAudioTimeUpdate();
      drawWave();
    });

    player.addEventListener('error', function(err) {
      console.warn('Audio player encountered error:', player.error, err);
      updatePlayPauseIcons(false);
      if (currentResult && currentResult.audio_base64 && player.src !== currentResult.audio_base64) {
        console.info('Switching audio player to audio_base64 fallback payload...');
        loadAudioForPlayback(currentResult.audio_base64);
      }
    });
  }

  function togglePlayPause() {
    const player = document.getElementById('audio-player');
    if (!player) return;
    initAudioPlayerEvents();

    if (typeof initAudioVisualizer === 'function') {
      initAudioVisualizer(player);
    }
    if (typeof studioAudioCtx !== 'undefined' && studioAudioCtx && studioAudioCtx.state === 'suspended') {
      studioAudioCtx.resume().catch(() => {});
    }
    if (typeof audioContext !== 'undefined' && audioContext && audioContext.state === 'suspended') {
      audioContext.resume().catch(() => {});
    }

    // Ensure audio element is completely unmuted and audible
    player.muted = false;
    if (player.volume === 0 || isNaN(player.volume)) {
      player.volume = 1.0;
    }
    const volSlider = document.getElementById('master-volume-slider');
    if (volSlider && (!volSlider.value || parseFloat(volSlider.value) === 0)) {
      volSlider.value = player.volume;
    }

    // Fallback: If player has no active source but we have transcribed result with media, assign it
    if ((!player.src || player.src === window.location.href || player.src === '') && currentResult) {
      const src = currentResult.media_url || currentResult.audio_base64 || '';
      if (src) {
        player.src = src;
        player.load();
      }
    }

    // Check if at the end of track, rewind to replay seamlessly
    if (player.ended || (player.duration > 0 && player.currentTime >= player.duration - 0.05)) {
      player.currentTime = 0;
    }

    if (player.paused) {
      updatePlayPauseIcons(true);
      const playPromise = player.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          updatePlayPauseIcons(true);
          scheduleWaveAnimation();
        }).catch((err) => {
          console.warn('Audio playback error:', err);
          updatePlayPauseIcons(false);
          stopWaveAnimation();
          if (err && err.name === 'NotAllowedError') {
            showToast('Click anywhere on the window to enable audio playback', 'info');
          }
        });
      }
    } else {
      player.pause();
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      drawWave();
    }
  }

  function updatePlayPauseIcons(isPlaying) {
    const playIcon = document.getElementById('play-icon');
    const pauseIcon = document.getElementById('pause-icon');
    if (playIcon && pauseIcon) {
      playIcon.style.display = isPlaying ? 'none' : 'block';
      pauseIcon.style.display = isPlaying ? 'block' : 'none';
    }
    const btn = document.getElementById('btn-master-play');
    if (btn) {
      btn.setAttribute('aria-label', isPlaying ? 'Pause audio' : 'Play audio');
      btn.classList.toggle('is-playing', !!isPlaying);
    }
    const waveWrap = document.getElementById('waveform-wrap');
    if (waveWrap) {
      waveWrap.classList.toggle('playing', !!isPlaying);
    }
  }

  function skipAudio(seconds) {
    const player = document.getElementById('audio-player');
    if (!player) return;
    const dur = getAccurateDuration() || player.duration || 0;
    player.currentTime = Math.max(0, Math.min(dur > 0 ? dur : 0, player.currentTime + seconds));
    handleAudioTimeUpdate();
    drawWave();
  }

  function setAudioVolume(vol) {
    const player = document.getElementById('audio-player');
    if (player) {
      const v = parseFloat(vol);
      player.volume = isNaN(v) ? 1.0 : Math.max(0, Math.min(1, v));
      if (player.volume > 0) player.muted = false;
    }
  }

  function setPlaybackRate(rate, btn) {
    const player = document.getElementById('audio-player');
    if (player) player.playbackRate = rate;
    document.querySelectorAll('.btn-speed').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
  }

  function handleAudioEnded() {
    updatePlayPauseIcons(false);
  }

  /* Keyboard Shortcuts */
  window.addEventListener('keydown', function(e) {
    const target = e.target;
    if (target && (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'BUTTON' ||
      target.tagName === 'SELECT' ||
      target.isContentEditable ||
      (target.closest && target.closest('button, select, [role="button"], [contenteditable="true"]'))
    )) {
      return;
    }
    if (e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.code === 'ArrowLeft' || e.code === 'KeyJ') {
      e.preventDefault();
      skipAudio(-5);
    } else if (e.code === 'ArrowRight' || e.code === 'KeyL') {
      e.preventDefault();
      skipAudio(5);
    } else if (e.code === 'Escape') {
      var s = document.getElementById('transcript-search');
      if (s) { s.value = ''; filterTranscript(); }
    }
  });

  /* Web Audio API Real Peak Extraction */
  function decodeAudioFileForWaveform(file) {
    try {
      if (!file) return;
      if (file.size && file.size > 25 * 1024 * 1024) {
        // Prevent browser out-of-memory crash on large files (> 25MB)
        return;
      }
      if (!window.AudioContext && !window.webkitAudioContext) return;
      var AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!audioContext) audioContext = new AudioCtx();
      var reader = new FileReader();
      reader.onload = function(ev) {
        audioContext.decodeAudioData(ev.target.result, function(buffer) {
          realAudioBuffer = buffer;
          computeRealWaveformPeaks(buffer, 64);
        }, function(e) {
          // Fallback to speech cadence envelope
        });
      };
      reader.readAsArrayBuffer(file);
    } catch (e) {}
  }

  function computeRealWaveformPeaks(buffer, numBars) {
    var rawData = buffer.getChannelData(0);
    var totalSamples = rawData.length;
    var blockSize = Math.floor(totalSamples / numBars);
    var peaks = [];
    for (var i = 0; i < numBars; i++) {
      var start = i * blockSize;
      var sum = 0;
      for (var j = 0; j < blockSize; j++) {
        var val = rawData[start + j];
        sum += val * val;
      }
      var rms = Math.sqrt(sum / blockSize);
      peaks.push(Math.max(0.03, Math.min(1, rms * 4.5)));
    }
    waveEnvelope = peaks;
    if (typeof drawWave === 'function') {
      drawWave();
    }
  }

  function updateSyntheticWarning(data) {
    const warning = document.getElementById('synthetic-warning');
    if (!warning) return;
    const textElem = document.getElementById('synthetic-warning-text');
    const transcriptSynthetic = !!(data && data.transcription && data.transcription.is_synthetic);
    const audioSynthetic = !!(data && data.audio_metadata && data.audio_metadata.is_synthetic);

    if (!transcriptSynthetic && !audioSynthetic) {
      warning.style.display = 'none';
      return;
    }

    let message;
    if (transcriptSynthetic && audioSynthetic) {
      message = 'DEMO — synthetic transcript and synthetic audio. No real media was transcribed.';
    } else if (transcriptSynthetic) {
      message = 'DEMO — synthetic transcript. This text was not produced by transcribing the uploaded audio.';
    } else {
      message = 'WARNING — synthetic test audio. The uploaded media could not be decoded, so a placeholder signal was generated.';
    }
    if (textElem) textElem.innerText = message;
    warning.style.display = 'flex';
  }

  /* Render Output Viewport */
  function renderTranscription(data) {
    currentResult = data;
    window.currentResult = data;
    // Real waveform envelope computed server-side from the exact PCM used for playback.
    if (Array.isArray(data.waveform_peaks) && data.waveform_peaks.length) {
      waveEnvelope = data.waveform_peaks.map(function (v) {
        return Math.max(0.03, Math.min(1, Number(v) || 0));
      });
    } else {
      waveEnvelope = null;
    }
    updateSyntheticWarning(data);
    const dropzoneElem = document.getElementById('dropzone');
    if (dropzoneElem) dropzoneElem.style.display = 'none';
    const procCard = document.getElementById('processing-card');
    if (procCard) procCard.style.display = 'none';
    const outputView = document.getElementById('output-viewport');
    if (outputView) outputView.style.display = 'block';

    const segments = (data.transcription && data.transcription.segments) ? data.transcription.segments : [];
    const container = document.getElementById('transcript-container');
    container.innerHTML = '';

    const cleanSegments = segments.map((s, idx) => ({
      id: idx,
      start: s.start,
      end: s.end,
      text: (s.text || '').trim(),
      words: s.words ? [...s.words] : [],
    }));

    window.renderedSegments = cleanSegments;
    let totalWords = 0;

    cleanSegments.forEach((s, idx) => {
      let wordSpans = '';
      if (s.words && s.words.length > 0) {
        totalWords += s.words.length;
        wordSpans = s.words.map(w => {
          const wText = escapeHtml(w.word || '');
          const wStart = (w.start || 0).toFixed(2);
          const wEnd = (w.end || 0).toFixed(2);
          return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${wText}</span> `;
        }).join('');
      } else {
        const words = (s.text || '').trim().split(/\s+/).filter(Boolean);
        totalWords += words.length;
        const segDur = Math.max(0.1, (s.end || 0) - (s.start || 0));
        const wordDur = segDur / Math.max(1, words.length);
        wordSpans = words.map((w, wIdx) => {
          const wStart = ((s.start || 0) + (wIdx * wordDur)).toFixed(2);
          const wEnd = ((s.start || 0) + ((wIdx + 1) * wordDur)).toFixed(2);
          return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${escapeHtml(w)}</span> `;
        }).join('');
      }

      const segCard = document.createElement('div');
      segCard.className = 'segment-card';
      segCard.id = `seg-${idx}`;
      segCard.tabIndex = 0;
      segCard.setAttribute('role', 'region');
      segCard.setAttribute('aria-label', `Transcript segment ${idx + 1}`);
      segCard.onclick = () => seekTo(s.start);
      segCard.onkeydown = (e) => {
        if (e.target === segCard && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          seekTo(s.start);
        }
      };

      segCard.innerHTML = `
        <div class="seg-header">
          <div class="seg-header-left">
            <span class="seg-time" onclick="seekTo(${s.start}); event.stopPropagation();">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              ${formatSec(s.start)} - ${formatSec(s.end)}
            </span>
          </div>
          <div class="seg-actions">
            <button class="btn-seg-icon" onclick="copySegmentText(${idx}, event)" title="Copy segment text">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              Copy
            </button>
          </div>
        </div>
        <div class="seg-text" id="seg-text-${idx}" contenteditable="true" spellcheck="false" onblur="handleSegmentEdit(${idx}, this)" onclick="event.stopPropagation()">
          ${wordSpans}
        </div>
      `;
      container.appendChild(segCard);
    });

    const wordCountBadge = document.getElementById('live-word-count');
    if (wordCountBadge) wordCountBadge.innerText = totalWords;

    // Dynamically populate actual voice profiles into Custom TTS mode
    populateVoiceProfiles(data.voice_profiles || []);

    // Initialize Mode 1 Audio Editor with loaded audio duration & filename
    const durM1 = getAccurateDuration();
    const fileNameM1 = (data && data.video_source) || (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
    initModeAudioEditor('m1', durM1 > 0 ? durM1 : 10, fileNameM1);

    const timecodeElem = document.getElementById('live-timecode');
    if (timecodeElem) {
      timecodeElem.innerText = formatSec(0) + ' / ' + formatSec(durM1 > 0 ? durM1 : 0);
    }

    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
      const targetAudioSrc = (data && (data.media_url || data.audio_base64)) || '';
      const hasValidSource = audioPlayer.src && audioPlayer.src !== window.location.href && !audioPlayer.error;
      if (targetAudioSrc && (!hasValidSource || !loadedMediaUrl)) {
        loadAudioForPlayback(targetAudioSrc);
      }

      function applyLoadedAudioMetadata() {
        const dur = getAccurateDuration();
        if (dur > 0) {
          initModeAudioEditor('m1', dur, fileNameM1);
          if (timecodeElem) {
            timecodeElem.innerText = formatSec(audioPlayer.currentTime || 0) + ' / ' + formatSec(dur);
          }
          handleAudioTimeUpdate();
          resizeWaveform();
          drawWave();
        }
      }

      if (audioPlayer.readyState >= 1) {
        applyLoadedAudioMetadata();
      } else {
        audioPlayer.addEventListener('loadedmetadata', applyLoadedAudioMetadata, { once: true });
        audioPlayer.addEventListener('canplay', applyLoadedAudioMetadata, { once: true });
      }
    }

    // Trigger immediate waveform layout and initial crisp render upon output-viewport reveal
    setTimeout(() => {
      resizeWaveform();
      drawWave();
    }, 25);
  }

  function getSpeakerThemeClass(speaker, idx) {
    var match = /(\d+)\s*$/.exec(String(speaker || ''));
    var n = match ? parseInt(match[1], 10) : (idx + 1);
    if (!isFinite(n) || n < 1) n = 1;
    return 'spk-theme-' + (((n - 1) % 10) + 1);
  }

  /* Clean Text Helpers to Guarantee Proper English Spacing and Formatting */
  function cleanExportText(str) {
    if (!str) return '';
    let t = str.replace(/\u00A0/g, ' ');       // Non-breaking space to regular space
    t = t.replace(/\s+/g, ' ');                // Collapse multiple spaces
    t = t.replace(/\s+([,.:;?!])/g, '$1');     // Remove erroneous spaces before punctuation
    t = t.replace(/([,.:;?!])([A-Za-z0-9])/g, '$1 $2'); // Ensure space after punctuation
    return t.trim();
  }

  function getCleanSegmentText(s, idx) {
    const segElem = document.getElementById('seg-text-' + idx);
    if (segElem) {
      if (segElem.getAttribute('data-edited') === 'true') {
        const domRaw = (segElem.innerText || segElem.textContent || '').trim();
        if (domRaw) {
          return cleanExportText(domRaw);
        }
      }
      const tokens = segElem.querySelectorAll('.word-token');
      if (tokens && tokens.length > 0) {
        const words = [];
        tokens.forEach(tok => {
          const w = (tok.innerText || tok.textContent || '').trim();
          if (w) words.push(w);
        });
        if (words.length > 0) {
          return cleanExportText(words.join(' '));
        }
      } else {
        const domRaw = (segElem.innerText || segElem.textContent || '').trim();
        if (domRaw) {
          return cleanExportText(domRaw);
        }
      }
    }
    return cleanExportText((s && s.text) ? s.text.trim() : '');
  }

  /* One-Click Prominent Full Transcript Copy with Clean Formatting Options */
  function copyFullTranscript() {
    const data = currentResult || window.currentResult;
    if (!data || !data.transcription) {
      showToast('Please upload and transcribe a media file first.', 'info');
      return;
    }
    const format = document.getElementById('copy-format-select') ? document.getElementById('copy-format-select').value : 'standard';
    // The visible transcript is rendered from unified speaker cards. Use those so copied
    // text matches edits and merged turns instead of the original raw segments.
    const segments = (window.renderedSegments && window.renderedSegments.length)
      ? window.renderedSegments
      : (data.transcription.segments || []);
    let formatted = '';

    segments.forEach((s, idx) => {
      const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
      const text = getCleanSegmentText(s, idx);

      if (format === 'dialogue' || format === 'text') {
        formatted += `${text}\n\n`;
      } else if (format === 'markdown') {
        formatted += `### \`[${timeRange}]\`\n\n${text}\n\n`;
      } else {
        formatted += `[${timeRange}]\n${text}\n\n`;
      }
    });

    const btn = document.getElementById('copy-transcript-btn');
    const originalText = btn ? btn.innerHTML : '';

    function showCopied() {
      if (btn) {
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied to Clipboard!`;
        btn.classList.add('btn-copied');
        showToast('Full transcript copied to clipboard!', 'success');
        setTimeout(() => {
          btn.innerHTML = originalText;
          btn.classList.remove('btn-copied');
        }, 2500);
      }
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(formatted.trim()).then(showCopied).catch(() => {
        fallbackCopy(formatted.trim(), showCopied);
      });
    } else {
      fallbackCopy(formatted.trim(), showCopied);
    }
  }

  function copySegmentText(idx, evt) {
    if (evt) evt.stopPropagation();
    const data = currentResult || window.currentResult;
    if (!data || !data.transcription) return;
    const segments = (window.renderedSegments && window.renderedSegments.length)
      ? window.renderedSegments
      : (data.transcription.segments || []);
    const s = segments[idx];
    if (!s) return;
    const textContent = getCleanSegmentText(s, idx);
    const text = `[${formatSec(s.start)} - ${formatSec(s.end)}]\n${textContent}`;

    const btn = evt && evt.currentTarget ? evt.currentTarget : null;
    const origHtml = btn ? btn.innerHTML : '';
    function showCopied() {
      if (btn) {
        btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        btn.style.color = '#10B981';
        showToast('Copied segment text!', 'success');
        setTimeout(() => {
          btn.innerHTML = origHtml;
          btn.style.color = '';
        }, 2000);
      }
    }
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(showCopied).catch(() => {
        fallbackCopy(text, showCopied);
      });
    } else {
      fallbackCopy(text, showCopied);
    }
  }

  function fallbackCopy(text, cb) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand('copy');
    } catch (e) {}
    document.body.removeChild(ta);
    if (cb) cb();
  }

  function handleSegmentEdit(idx, el) {
    el.setAttribute('data-edited', 'true');
    const newText = cleanExportText(el.innerText || el.textContent || '');
    if (window.renderedSegments && window.renderedSegments[idx]) {
      window.renderedSegments[idx].text = newText;
    }
    if (currentResult && currentResult.transcription && currentResult.transcription.segments && currentResult.transcription.segments[idx]) {
      currentResult.transcription.segments[idx].text = newText;
    }
    showToast('Transcript edit saved', 'info');
  }

  // Intercept manual text selection copy within transcript container to guarantee spaces
  document.addEventListener('copy', function(e) {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed) return;
    const cont = document.getElementById('transcript-container');
    if (cont && cont.contains(sel.anchorNode)) {
      const selected = sel.toString();
      if (selected && e.clipboardData) {
        const cleaned = cleanExportText(selected);
        if (cleaned) {
          e.clipboardData.setData('text/plain', cleaned);
          e.preventDefault();
        }
      }
    }
  });

  /* Audio Synchronization & Kinetic Highlights */
  function getAccurateDuration() {
    const player = document.getElementById('audio-player');
    const data = window.currentResult || currentResult;
    let metaDur = 0;
    if (data && data.audio_metadata && data.audio_metadata.duration > 0.05) {
      metaDur = data.audio_metadata.duration;
    } else if (data && data.transcription && data.transcription.duration > 0.05) {
      metaDur = data.transcription.duration;
    } else if (data && data.media_duration_sec > 0.05) {
      metaDur = data.media_duration_sec;
    }
    const playerDur = (player && isFinite(player.duration) && player.duration > 0.05) ? player.duration : 0;
    if (metaDur > 0) {
      // A truncated or mismatched playback track must never shrink a full-length
      // transcript. Trust the source duration unless the player is genuinely longer.
      if (playerDur <= 0 || (playerDur < metaDur * 0.95 && (metaDur - playerDur) > 2.0)) {
        return metaDur;
      }
      return playerDur;
    }
    return playerDur;
  }

  function seekTo(sec) {
    const player = document.getElementById('audio-player');
    if (player) {
      initAudioPlayerEvents();
      if (typeof studioAudioCtx !== 'undefined' && studioAudioCtx && studioAudioCtx.state === 'suspended') {
        studioAudioCtx.resume().catch(() => {});
      }
      if (typeof audioContext !== 'undefined' && audioContext && audioContext.state === 'suspended') {
        audioContext.resume().catch(() => {});
      }
      player.muted = false;
      const dur = getAccurateDuration();
      const clamped = Math.max(0, Math.min(dur > 0 ? dur : sec, sec));
      player.currentTime = clamped;
      handleAudioTimeUpdate();
      drawWave();
      updatePlayPauseIcons(true);
      const playPromise = player.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          updatePlayPauseIcons(true);
          scheduleWaveAnimation();
        }).catch((err) => {
          console.warn('seekTo play() deferred or blocked:', err);
          updatePlayPauseIcons(false);
          stopWaveAnimation();
        });
      }
    }
  }

  function seekToWord(sec, evt) {
    if (evt) evt.stopPropagation();
    seekTo(sec);
  }

  function handleAudioTimeUpdate() {
    const player = document.getElementById('audio-player');
    if (!player) return;
    const ct = (player && isFinite(player.currentTime)) ? player.currentTime : 0;
    const dur = getAccurateDuration() || (player && player.duration) || 1.0;

    const timecodeElem = document.getElementById('live-timecode');
    if (timecodeElem) {
      timecodeElem.innerText = formatSec(ct) + ' / ' + formatSec(dur);
    }

    const segments = window.renderedSegments || (currentResult && currentResult.transcription && currentResult.transcription.segments) || [];
    for (let idx = 0; idx < segments.length; idx++) {
      const s = segments[idx];
      const card = document.getElementById('seg-' + idx);
      if (!card) continue;
      const isCardActive = (ct >= (s.start - 0.05) && ct <= (s.end + 0.1));
      if (isCardActive) {
        if (!card.classList.contains('active-seg')) {
          card.classList.add('active-seg');
          card.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        const wordTokens = card.querySelectorAll('.word-token');
        for (let wIdx = 0; wIdx < wordTokens.length; wIdx++) {
          const w = wordTokens[wIdx];
          const wStart = parseFloat(w.getAttribute('data-start'));
          const wEnd = parseFloat(w.getAttribute('data-end'));
          if (ct >= (wStart - 0.05) && ct <= (wEnd + 0.05)) {
            w.classList.add('active-word');
          } else {
            w.classList.remove('active-word');
          }
        }
      } else {
        if (card.classList.contains('active-seg')) {
          card.classList.remove('active-seg');
          const activeWords = card.querySelectorAll('.word-token.active-word');
          for (let aIdx = 0; aIdx < activeWords.length; aIdx++) {
            activeWords[aIdx].classList.remove('active-word');
          }
        }
      }
    }
  }

  /* Live Keyword Search with Highlights */
  function filterTranscript() {
    const q = document.getElementById('transcript-search').value.toLowerCase().trim();
    const countBadge = document.getElementById('search-count-badge');
    let totalMatches = 0;

    document.querySelectorAll('.segment-card').forEach(card => {
      const segTextElem = card.querySelector('.seg-text');
      if (!segTextElem) return;
      const fullText = card.innerText.toLowerCase();

      if (!q) {
        card.style.display = 'block';
        card.querySelectorAll('.word-token').forEach(w => w.classList.remove('search-match'));
        return;
      }

      const matches = fullText.includes(q);
      card.style.display = matches ? 'block' : 'none';

      card.querySelectorAll('.word-token').forEach(w => {
        const wt = w.innerText.toLowerCase();
        if (wt.includes(q)) {
          w.classList.add('search-match');
          totalMatches++;
        } else {
          w.classList.remove('search-match');
        }
      });
    });

    if (countBadge) {
      if (q) {
        countBadge.style.display = 'block';
        countBadge.innerText = `${totalMatches} match${totalMatches === 1 ? '' : 'es'}`;
      } else {
        countBadge.style.display = 'none';
      }
    }
  }

  /* Client Export Download with Clean English Spacing & Multi-Format Support */
  function downloadArtifact(type) {
    const data = currentResult || window.currentResult;
    if (!data) {
      showToast('Please process an audio file first.', 'info');
      return;
    }
    let content = '';
    let filename = '';
    const baseSource = (data.video_source || 'scriber_transcript').replace(/\.[^/.]+$/, "");
    const rawSegments = (data.transcription && data.transcription.segments) ? data.transcription.segments : [];
    const segments = (window.renderedSegments && window.renderedSegments.length)
      ? window.renderedSegments
      : rawSegments;

    if (type === 'json') {
      filename = `${baseSource}_transcript.json`;
      // Keep exported JSON in sync with any in-place transcript edits the user made.
      const exportPayload = Object.assign({}, data);
      if (exportPayload.transcription && typeof exportPayload.transcription === 'object') {
        const segs = (window.renderedSegments && window.renderedSegments.length)
          ? window.renderedSegments
          : (exportPayload.transcription.segments || []);
        exportPayload.transcription = Object.assign({}, exportPayload.transcription, {
          segments: segs.map(s => {
            const copy = Object.assign({}, s);
            delete copy.speaker;
            return copy;
          })
        });
      }
      content = JSON.stringify(exportPayload, null, 2);
    } else if (type === 'txt') {
      filename = `${baseSource}_transcript.txt`;
      let header = `=================================================================\n`;
      header += `SCRIBER TRANSCRIPT EXPORT: ${data.video_source || 'Audio Recording'}\n`;
      const dur = data.audio_metadata ? data.audio_metadata.duration : 0;
      header += `Duration: ${formatSec(dur)} | Exported: ${new Date().toLocaleString()}\n`;
      header += `=================================================================\n\n`;
      content = header;
      segments.forEach((s, idx) => {
        const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
        const text = getCleanSegmentText(s, idx);
        content += `[${timeRange}]\n${text}\n\n`;
      });
    } else if (type === 'md') {
      filename = `${baseSource}_transcript.md`;
      let md = `# Scriber Transcript: ${data.video_source || 'Audio Recording'}\n\n`;
      const dur = data.audio_metadata ? data.audio_metadata.duration : 0;
      md += `> Duration: ${formatSec(dur)} | Processed by Scriber Autonomous Studio\n\n`;
      segments.forEach((s, idx) => {
        const timeRange = `${formatSec(s.start)} - ${formatSec(s.end)}`;
        const text = getCleanSegmentText(s, idx);
        md += `### \`[${timeRange}]\`\n\n${text}\n\n`;
      });
      content = md;
    } else if (type === 'srt') {
      filename = `${baseSource}.srt`;
      content = formatSrtExport(segments);
    } else if (type === 'vtt') {
      filename = `${baseSource}.vtt`;
      content = formatVttExport(segments);
    }

    if (!filename) {
      filename = `${baseSource}_transcript.txt`;
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Downloaded ${filename}`, 'success');

    // Also persist directly into ./scriber_output for desktop folder view
    fetch('/api/desktop/save-file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename: filename, content: content, dir: './scriber_output' })
    }).catch(function() {});
  }

  /* ========================================================= */
  /* MODE 1 AUDIO TOOLS DRAWER CONTROLLER                      */
  /* ========================================================= */
  var isAudioToolsDrawerOpen = false;

  function toggleAudioToolsDrawer(forceState) {
    var drawer = document.getElementById('audio-tools-drawer');
    var btn = document.getElementById('btn-audio-tools') || document.getElementById('audio-tools-toggle');
    if (!drawer) return;
    isAudioToolsDrawerOpen = (typeof forceState === 'boolean') ? forceState : !isAudioToolsDrawerOpen;
    drawer.style.display = isAudioToolsDrawerOpen ? 'block' : 'none';
    if (btn) btn.classList.toggle('active', isAudioToolsDrawerOpen);
    if (isAudioToolsDrawerOpen && currentResult) {
      var dur = getAccurateDuration();
      var fName = (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
      initModeAudioEditor('m1', dur > 0 ? dur : 10, fName);
    }
  }
  window.toggleAudioToolsDrawer = toggleAudioToolsDrawer;

  /* ========================================================= */
  /* CONSOLIDATED EXPORT DROPDOWN MENU CONTROLLER              */
  /* ========================================================= */
  function toggleExportDropdown(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    var menu = document.getElementById('export-menu');
    var trigger = document.getElementById('export-dropdown-trigger');
    if (!menu) return;
    var isOpen = menu.style.display !== 'none';
    menu.style.display = isOpen ? 'none' : 'block';
    if (trigger) trigger.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
  }

  function handleExportSelect(type) {
    toggleExportDropdown(null);
    if (type === 'folder') {
      revealExportFolder();
    } else {
      downloadArtifact(type);
    }
  }
  window.toggleExportDropdown = toggleExportDropdown;
  window.handleExportSelect = handleExportSelect;

  document.addEventListener('click', function(e) {
    var menu = document.getElementById('export-menu');
    var trigger = document.getElementById('export-dropdown-trigger');
    if (menu && menu.style.display !== 'none') {
      if (!menu.contains(e.target) && (!trigger || !trigger.contains(e.target))) {
        menu.style.display = 'none';
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
      }
    }
  });

  function formatSrtExport(segments) {
    let cues = [];
    let cueIndex = 1;

    segments.forEach((s, segIdx) => {
      if (s.words && s.words.length > 8) {
        const words = s.words;
        const chunkSize = 8;
        for (let i = 0; i < words.length; i += chunkSize) {
          const slice = words.slice(i, i + chunkSize);
          const cStart = slice[0].start !== undefined ? slice[0].start : s.start;
          const cEnd = slice[slice.length - 1].end !== undefined ? slice[slice.length - 1].end : s.end;
          const cText = cleanExportText(slice.map(w => w.word).join(' '));
          cues.push(`${cueIndex++}\n${formatSrtTimestamp(cStart)} --> ${formatSrtTimestamp(cEnd)}\n${cText}\n`);
        }
      } else {
        const cleanText = getCleanSegmentText(s, segIdx);
        cues.push(`${cueIndex++}\n${formatSrtTimestamp(s.start)} --> ${formatSrtTimestamp(s.end)}\n${cleanText}\n`);
      }
    });

    return cues.join(String.fromCharCode(10));
  }

  function formatVttExport(segments) {
    let cues = ['WEBVTT - Scriber Transcript Export' + String.fromCharCode(10)];
    let cueIndex = 1;

    segments.forEach((s, segIdx) => {
      if (s.words && s.words.length > 8) {
        const words = s.words;
        const chunkSize = 8;
        for (let i = 0; i < words.length; i += chunkSize) {
          const slice = words.slice(i, i + chunkSize);
          const cStart = slice[0].start !== undefined ? slice[0].start : s.start;
          const cEnd = slice[slice.length - 1].end !== undefined ? slice[slice.length - 1].end : s.end;
          const cText = cleanExportText(slice.map(w => w.word).join(' '));
          cues.push(`${cueIndex++}\n${formatVttTimestamp(cStart)} --> ${formatVttTimestamp(cEnd)}\n${cText}`);
        }
      } else {
        const cleanText = getCleanSegmentText(s, segIdx);
        cues.push(`${cueIndex++}\n${formatVttTimestamp(s.start)} --> ${formatVttTimestamp(s.end)}\n${cleanText}`);
      }
    });

    return cues.join(String.fromCharCode(10, 10)) + String.fromCharCode(10);
  }

  /* ========================================================= */
  /* MODEL SELECTION DROPDOWNS & DISPATCH                      */
  /* ========================================================= */
  var selectedTranscribeModel = 'turbo';
  var selectedVoiceModel = 'edge-neural';

  function toggleModelDropdown(menuId, event) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    const menu = document.getElementById(menuId);
    if (!menu) return;
    const trigger = menu.closest('.custom-model-dropdown') ? menu.closest('.custom-model-dropdown').querySelector('.model-dropdown-trigger') : null;
    if (trigger && (trigger.disabled || trigger.classList.contains('locked') || trigger.getAttribute('aria-disabled') === 'true')) {
      return;
    }
    const isAlreadyOpen = menu.classList.contains('open');
    closeAllModelDropdowns();
    if (!isAlreadyOpen) {
      menu.classList.add('open');
      if (trigger) {
        trigger.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
      }
    }
  }

  function setTranscribeModelLocked(locked) {
    ['transcribe-dropdown-trigger', 'voice-dropdown-trigger'].forEach(function(id) {
      const el = document.getElementById(id);
      if (!el) return;
      if (locked) {
        el.disabled = true;
        el.classList.add('locked');
        el.setAttribute('aria-disabled', 'true');
      } else {
        el.disabled = false;
        el.classList.remove('locked');
        el.setAttribute('aria-disabled', 'false');
      }
    });
    const copySelect = document.getElementById('copy-format-select');
    if (copySelect) copySelect.disabled = !!locked;
    if (locked) closeAllModelDropdowns();
  }

  function setVoiceModelLocked(locked) {
    setTranscribeModelLocked(locked);
  }

  function closeAllModelDropdowns() {
    document.querySelectorAll('.model-dropdown-menu.open').forEach(function(el) {
      el.classList.remove('open');
    });
    document.querySelectorAll('.model-dropdown-trigger.active').forEach(function(el) {
      el.classList.remove('active');
      el.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.custom-model-dropdown')) {
      closeAllModelDropdowns();
    }
  });

  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
      closeAllModelDropdowns();
    }
  });

  function selectTranscribeModel(modelId) {
    const trigger = document.getElementById('transcribe-dropdown-trigger');
    if (trigger && (trigger.disabled || trigger.classList.contains('locked') || trigger.getAttribute('aria-disabled') === 'true')) {
      return;
    }
    setTranscribeModelLocked(true);
    setTimeout(function() { setTranscribeModelLocked(false); }, 350);

    selectedTranscribeModel = modelId;
    window.selectedTranscribeModel = modelId;
    const names = {
      'turbo': 'Whisper Turbo',
      'distil-large-v3': 'Distil-Whisper Large-v3',
      'base': 'Whisper Base',
      'whisperx': 'WhisperX'
    };
    const badges = {
      'turbo': 'High Accuracy · Recommended',
      'distil-large-v3': 'High Speed',
      'base': 'Lightweight / Low-RAM',
      'whisperx': 'Word-Level Timing'
    };
    const badgeClasses = {
      'turbo': 'tier-recommended',
      'distil-large-v3': 'tier-speed',
      'base': 'tier-lightweight',
      'whisperx': 'tier-aligned'
    };
    const tag = document.getElementById('active-transcribe-tag');
    if (tag) tag.innerText = names[modelId] || modelId;

    const badgeEl = document.getElementById('active-transcribe-badge');
    if (badgeEl) {
      badgeEl.innerText = badges[modelId] || '';
      badgeEl.className = 'model-tier-badge ' + (badgeClasses[modelId] || '');
    }

    ['turbo', 'distil-large-v3', 'base', 'whisperx'].forEach(function(m) {
      const el = document.getElementById('model-opt-' + m);
      if (el) {
        const isActive = (m === modelId);
        el.classList.toggle('active', isActive);
        el.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }
    });

    closeAllModelDropdowns();
    showToast(`Switched transcription engine to ${names[modelId] || modelId}`, 'info');
  }

  function selectVoiceModel(modelId) {
    const trigger = document.getElementById('voice-dropdown-trigger');
    if (trigger && (trigger.disabled || trigger.classList.contains('locked') || trigger.getAttribute('aria-disabled') === 'true')) {
      return;
    }
    setVoiceModelLocked(true);
    setTimeout(function() { setVoiceModelLocked(false); }, 350);

    selectedVoiceModel = modelId;
    window.selectedVoiceModel = modelId;
    const names = {
      'local-gpu': 'Local GPU (F5-TTS companion)',
      'edge-neural': 'Edge Neural TTS',
      'whisperspeech': 'WhisperSpeech (not bundled)',
      'gpt-sovits': 'GPT-SoVITS (not bundled)'
    };
    const badges = {
      'local-gpu': 'Optional · GPU companion',
      'edge-neural': 'Network · Pitch-matched',
      'whisperspeech': 'Unavailable · Fallback',
      'gpt-sovits': 'Unavailable · Fallback'
    };
    const badgeClasses = {
      'local-gpu': 'tier-inversion',
      'edge-neural': 'tier-recommended',
      'whisperspeech': 'tier-inversion',
      'gpt-sovits': 'tier-formant'
    };
    const tag = document.getElementById('active-voice-tag');
    if (tag) tag.innerText = names[modelId] || modelId;

    const badgeEl = document.getElementById('active-voice-badge');
    if (badgeEl) {
      badgeEl.innerText = badges[modelId] || '';
      badgeEl.className = 'model-tier-badge ' + (badgeClasses[modelId] || '');
    }

    ['local-gpu', 'edge-neural', 'whisperspeech', 'gpt-sovits'].forEach(function(m) {
      const el = document.getElementById('voice-opt-' + m);
      if (el) {
        const isActive = (m === modelId);
        el.classList.toggle('active', isActive);
        el.setAttribute('aria-selected', isActive ? 'true' : 'false');
      }
    });

    closeAllModelDropdowns();
    if (modelId === 'whisperspeech' || modelId === 'gpt-sovits') {
      showToast(`${names[modelId]} is unavailable in this build; synthesis will fall back and report the engine used.`, 'info');
    } else if (modelId === 'local-gpu') {
      showToast('Local GPU mode requires the optional F5-TTS companion; otherwise synthesis falls back and reports the engine used.', 'info');
    } else {
      showToast(`Switched voice synthesis engine to ${names[modelId] || modelId}`, 'info');
    }
  }

  /* ========================================================= */
  /* AUDIO STUDIO & MP3 EDITOR STATE MANAGEMENT (REAL-TIME)    */
  /* ========================================================= */
  var audioEditorState = {
    m1: {
      volume: 100,
      pitch: 0,
      trimStart: 0,
      trimEnd: 0,
      totalDuration: 0,
      isPlayingPreview: false,
      previewTimer: null,
      customFileName: null,
    },
    m2: {
      volume: 100,
      pitch: 0,
      trimStart: 0,
      trimEnd: 0,
      totalDuration: 0,
      isPlayingPreview: false,
      previewTimer: null,
      customFileName: null,
      referenceAudioBase64: null,
      audioElement: null,
    }
  };

  /* Web Audio API Realtime Gain & Pitch Node Graph */
  var studioAudioCtx = null;
  var studioGainNodes = { m1: null, m2: null };
  var studioSources = { m1: null, m2: null };

  function getStudioGainNode(mode, player) {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!studioAudioCtx) studioAudioCtx = new AudioCtx();
      if (studioAudioCtx.state === 'suspended') {
        studioAudioCtx.resume().catch(() => {});
      }
      if (!studioGainNodes[mode] && player) {
        const source = studioAudioCtx.createMediaElementSource(player);
        const gainNode = studioAudioCtx.createGain();
        source.connect(gainNode);
        gainNode.connect(studioAudioCtx.destination);
        studioSources[mode] = source;
        studioGainNodes[mode] = gainNode;
      }
      return studioGainNodes[mode];
    } catch (e) {
      return null;
    }
  }

  var liveAuditionDebounce = null;
  function triggerRealtimeAudition(mode, player) {
    if (!player || (!player.src && !player.currentSrc)) return;
    if (studioAudioCtx && studioAudioCtx.state === 'suspended') {
      studioAudioCtx.resume().catch(() => {});
    }
    // If player is already playing, real-time gain/pitch applies immediately without restart
    if (!player.paused) return;

    // If paused, audition a short 1.2s snippet so the user IMMEDIATELY hears the pitch/volume shift
    if (liveAuditionDebounce) clearTimeout(liveAuditionDebounce);
    liveAuditionDebounce = setTimeout(() => {
      const st = audioEditorState[mode];
      const startPos = (st && st.trimStart) ? st.trimStart : (player.currentTime || 0);
      try {
        player.currentTime = startPos;
        player.play().then(() => {
          setTimeout(() => {
            if (!st.isPlayingPreview && player === document.getElementById('audio-player') && !isMasterPlaying()) {
              player.pause();
            } else if (!st.isPlayingPreview && mode === 'm2') {
              player.pause();
            }
          }, 1200);
        }).catch(() => {});
      } catch (e) {}
    }, 90);
  }

  function isMasterPlaying() {
    const pauseIcon = document.getElementById('pause-icon');
    return pauseIcon && pauseIcon.style.display !== 'none';
  }

  function formatSecPrecise(sec) {
    if (!sec || isNaN(sec) || sec < 0) sec = 0;
    const mins = Math.floor(sec / 60);
    const secs = (sec % 60).toFixed(2);
    return String(mins).padStart(2, '0') + ':' + (secs < 10 ? '0' : '') + secs;
  }

  function parseSec(str) {
    if (!str) return 0;
    const parts = String(str).trim().split(':');
    if (parts.length === 2) {
      const m = parseFloat(parts[0]) || 0;
      const s = parseFloat(parts[1]) || 0;
      return m * 60 + s;
    }
    return parseFloat(str) || 0;
  }

  function initModeAudioEditor(mode, duration, filename) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.totalDuration = duration || 10;
    st.trimStart = 0;
    st.trimEnd = st.totalDuration;
    st.customFileName = filename || (mode === 'm1' ? 'scriber_audio.mp3' : 'scriber_voice.mp3');

    const startIn = document.getElementById(mode + '-trim-start');
    const endIn = document.getElementById(mode + '-trim-end');
    const durVal = document.getElementById(mode + '-trim-duration-val');
    const trimPill = document.getElementById(mode + '-trim-pill');

    if (startIn) startIn.value = '00:00.00';
    if (endIn) endIn.value = formatSecPrecise(st.totalDuration);
    if (durVal) durVal.innerText = 'Duration: ' + formatSec(st.totalDuration);
    if (trimPill) trimPill.innerText = 'Trim: 00:00 - ' + formatSec(st.totalDuration);
    syncTrimBarsFromState(mode);
  }

  function handleVolumeInput(mode, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.volume = parseFloat(val);
    const dB = st.volume > 0 ? (20 * Math.log10(st.volume / 100)).toFixed(1) : '-inf';
    const valEl = document.getElementById(mode + '-vol-val');
    if (valEl) valEl.innerText = `${st.volume}% (${dB >= 0 ? '+' : ''}${dB} dB)`;
    const pill = document.getElementById(mode + '-vol-pill');
    if (pill) {
      pill.innerText = `Vol: ${st.volume}%`;
      pill.classList.toggle('active', st.volume !== 100);
    }
    const presets = [50, 100, 130, 160, 200];
    presets.forEach(p => {
      const btn = document.getElementById(mode + '-vol-preset-' + p);
      if (btn) btn.classList.toggle('active', Math.round(st.volume) === p);
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      const gainNode = getStudioGainNode(mode, player);
      if (gainNode) {
        gainNode.gain.setValueAtTime(st.volume / 100.0, studioAudioCtx ? studioAudioCtx.currentTime : 0);
        player.volume = 1.0;
      } else {
        player.volume = Math.max(0.0, Math.min(1.0, st.volume / 100));
      }
      triggerRealtimeAudition(mode, player);
    }
  }

  function setVolumePreset(mode, val) {
    const slider = document.getElementById(mode + '-vol-slider');
    if (slider) {
      slider.value = val;
      handleVolumeInput(mode, val);
    }
  }

  function handlePitchInput(mode, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.pitch = parseInt(val, 10);
    const label = st.pitch === 0 ? 'Natural' : (st.pitch > 0 ? 'Higher' : 'Deeper');
    const valEl = document.getElementById(mode + '-pitch-val');
    if (valEl) valEl.innerText = `${st.pitch > 0 ? '+' : ''}${st.pitch} st (${label})`;
    const pill = document.getElementById(mode + '-pitch-pill');
    if (pill) {
      pill.innerText = `Pitch: ${st.pitch > 0 ? '+' : ''}${st.pitch} st`;
      pill.classList.toggle('active', st.pitch !== 0);
    }
    const presets = [-4, -2, 0, 2, 4];
    presets.forEach(p => {
      const btn = document.getElementById(mode + '-pitch-preset-' + p);
      if (btn) btn.classList.toggle('active', st.pitch === p);
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      player.preservesPitch = false;
      const rate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));
      player.playbackRate = rate;
      triggerRealtimeAudition(mode, player);
    }
  }

  function setPitchPreset(mode, val) {
    const slider = document.getElementById(mode + '-pitch-slider');
    if (slider) {
      slider.value = val;
      handlePitchInput(mode, val);
    }
  }

  function handleTrimBarInput(mode, type, val) {
    const st = audioEditorState[mode];
    if (!st) return;
    const dur = st.totalDuration > 0 ? st.totalDuration : 10.0;
    const targetSec = (parseFloat(val) / 100.0) * dur;

    if (type === 'start') {
      st.trimStart = Math.max(0, Math.min(dur, targetSec));
      if (st.trimStart >= st.trimEnd) {
        st.trimEnd = Math.min(dur, st.trimStart + 0.1);
        const endBar = document.getElementById(mode + '-trim-end-bar');
        if (endBar) endBar.value = (st.trimEnd / dur) * 100;
        const endIn = document.getElementById(mode + '-trim-end');
        if (endIn) endIn.value = formatSecPrecise(st.trimEnd);
      }
      const startIn = document.getElementById(mode + '-trim-start');
      if (startIn) startIn.value = formatSecPrecise(st.trimStart);
    } else {
      st.trimEnd = Math.max(0.1, Math.min(dur, targetSec));
      if (st.trimEnd <= st.trimStart) {
        st.trimStart = Math.max(0, st.trimEnd - 0.1);
        const startBar = document.getElementById(mode + '-trim-start-bar');
        if (startBar) startBar.value = (st.trimStart / dur) * 100;
        const startIn = document.getElementById(mode + '-trim-start');
        if (startIn) startIn.value = formatSecPrecise(st.trimStart);
      }
      const endIn = document.getElementById(mode + '-trim-end');
      if (endIn) endIn.value = formatSecPrecise(st.trimEnd);
    }

    const curTrimDur = Math.max(0, st.trimEnd - st.trimStart);
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (durVal) durVal.innerText = 'Duration: ' + formatSecPrecise(curTrimDur);

    const sliderPill = document.getElementById(mode + '-trim-slider-pill');
    if (sliderPill) sliderPill.innerText = `${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;

    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      player.currentTime = type === 'start' ? st.trimStart : Math.max(0, st.trimEnd - 1.0);
      triggerRealtimeAudition(mode, player);
    }
  }

  function syncTrimBarsFromState(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    const dur = st.totalDuration > 0 ? st.totalDuration : 10.0;
    const sBar = document.getElementById(mode + '-trim-start-bar');
    const eBar = document.getElementById(mode + '-trim-end-bar');
    const pill = document.getElementById(mode + '-trim-slider-pill');
    if (sBar) sBar.value = Math.max(0, Math.min(100, (st.trimStart / dur) * 100));
    if (eBar) eBar.value = Math.max(0, Math.min(100, (st.trimEnd / dur) * 100));
    if (pill) pill.innerText = `${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
  }

  function setTrimToPlayhead(mode, type) {
    const st = audioEditorState[mode];
    if (!st) return;
    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    const ct = (player && isFinite(player.currentTime)) ? player.currentTime : 0;

    if (type === 'start') {
      st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, ct));
      if (st.trimStart >= st.trimEnd && st.totalDuration > 0) {
        st.trimEnd = Math.min(st.totalDuration, st.trimStart + 1.0);
      }
      const el = document.getElementById(mode + '-trim-start');
      if (el) el.value = formatSecPrecise(st.trimStart);
      showToast(`Set Trim Start to ${formatSecPrecise(st.trimStart)}`, 'info');
    } else {
      st.trimEnd = Math.max(st.trimStart + 0.1, Math.min(st.totalDuration || 10, ct));
      const el = document.getElementById(mode + '-trim-end');
      if (el) el.value = formatSecPrecise(st.trimEnd);
      showToast(`Set Trim End to ${formatSecPrecise(st.trimEnd)}`, 'info');
    }

    const dur = Math.max(0, st.trimEnd - st.trimStart);
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (durVal) durVal.innerText = 'Duration: ' + formatSecPrecise(dur);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }
    syncTrimBarsFromState(mode);
  }

  function updateTrimFromText(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    const sVal = parseSec(document.getElementById(mode + '-trim-start').value);
    const eVal = parseSec(document.getElementById(mode + '-trim-end').value);
    st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, sVal));
    st.trimEnd = Math.max(st.trimStart + 0.1, Math.min(st.totalDuration || 10, eVal || st.totalDuration));

    document.getElementById(mode + '-trim-start').value = formatSecPrecise(st.trimStart);
    document.getElementById(mode + '-trim-end').value = formatSecPrecise(st.trimEnd);
    const dur = Math.max(0, st.trimEnd - st.trimStart);
    document.getElementById(mode + '-trim-duration-val').innerText = 'Duration: ' + formatSecPrecise(dur);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }
    syncTrimBarsFromState(mode);
  }

  function resetTrimRange(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.trimStart = 0;
    st.trimEnd = st.totalDuration || 10;
    document.getElementById(mode + '-trim-start').value = '00:00.00';
    document.getElementById(mode + '-trim-end').value = formatSecPrecise(st.totalDuration);
    document.getElementById(mode + '-trim-duration-val').innerText = 'Duration: ' + formatSec(st.totalDuration);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = 'Trim: Full Length';
      trimPill.classList.remove('active');
    }
    syncTrimBarsFromState(mode);
    showToast('Trim range reset to full audio length', 'info');
  }

  function togglePreviewEditedAudio(mode) {
    const st = audioEditorState[mode];
    if (!st) return;

    let player = mode === 'm1' ? document.getElementById('audio-player') : document.getElementById('clone-audio-player');
    if (mode === 'm2' && (!player || !player.src) && st.referenceAudioBase64) {
      if (!st.audioElement) st.audioElement = new Audio();
      st.audioElement.src = st.referenceAudioBase64;
      player = st.audioElement;
    }

    if (!player || (!player.src && !player.currentSrc)) {
      showToast('No audio loaded to preview. Please upload or transcribe media first.', 'info');
      return;
    }

    const btn = document.getElementById(mode + '-preview-btn');
    const statusPill = document.getElementById(mode + '-preview-status');

    function restoreMasterVolume() {
      const volSlider = document.getElementById('master-volume-slider');
      const targetVol = volSlider ? parseFloat(volSlider.value) : 1.0;
      player.volume = (!isNaN(targetVol) && targetVol >= 0) ? Math.min(1.0, targetVol) : 1.0;
      if (typeof getStudioGainNode === 'function') {
        const gn = getStudioGainNode(mode, player);
        if (gn && studioAudioCtx) {
          gn.gain.setValueAtTime(1.0, studioAudioCtx.currentTime);
        }
      }
    }

    if (st.isPlayingPreview) {
      player.pause();
      st.isPlayingPreview = false;
      if (st.previewTimer) clearInterval(st.previewTimer);
      restoreMasterVolume();
      if (btn) {
        btn.classList.remove('playing');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
      }
      if (statusPill) statusPill.style.display = 'none';
      return;
    }

    st.isPlayingPreview = true;
    player.currentTime = st.trimStart || 0;
    player.preservesPitch = false;
    player.playbackRate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));

    // Prevent double-attenuation: let Web Audio GainNode handle gain if available
    const gainNode = (typeof getStudioGainNode === 'function') ? getStudioGainNode(mode, player) : null;
    if (gainNode) {
      gainNode.gain.setValueAtTime(st.volume / 100.0, studioAudioCtx ? studioAudioCtx.currentTime : 0);
      const masterVol = parseFloat(document.getElementById('master-volume-slider')?.value || '1.0');
      player.volume = isNaN(masterVol) ? 1.0 : Math.max(0.0, Math.min(1.0, masterVol));
    } else {
      player.volume = Math.max(0.0, Math.min(1.0, st.volume / 100));
    }
    player.muted = false;

    player.play().catch(e => {
      st.isPlayingPreview = false;
      restoreMasterVolume();
      showToast('Playback error: ' + e, 'error');
    });

    if (btn) {
      btn.classList.add('playing');
      btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect></svg><span>Stop Preview</span>';
    }
    if (statusPill) statusPill.style.display = 'inline-flex';

    if (st.previewTimer) clearInterval(st.previewTimer);
    st.previewTimer = setInterval(() => {
      const cur = player.currentTime;
      const endLimit = (st.trimEnd > st.trimStart) ? st.trimEnd : (st.totalDuration || player.duration || 9999);
      if (cur >= endLimit || player.paused || player.ended) {
        player.pause();
        st.isPlayingPreview = false;
        clearInterval(st.previewTimer);
        restoreMasterVolume();
        if (btn) {
          btn.classList.remove('playing');
          btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
        }
        if (statusPill) statusPill.style.display = 'none';
      }
    }, 50);
  }

  async function exportEditedMP3(mode) {
    const st = audioEditorState[mode];
    if (!st) return;

    const navMode = mode === 'm2' ? 'voice' : 'transcribe';
    setNavProcessingState(navMode, true);

    const btn = document.getElementById(mode + '-export-btn');
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="anim-spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Encoding MP3...';
    btn.disabled = true;

    try {
      const baseName = (st.customFileName || (mode === 'm1' ? 'scriber_transcript' : 'scriber_voice')).replace(/\.[^/.]+$/, "");
      const payload = {
        volume: st.volume / 100,
        pitch_semitones: st.pitch,
        start_sec: st.trimStart || 0,
        end_sec: (st.trimEnd > st.trimStart) ? st.trimEnd : null,
        filename: baseName + '_edited.mp3',
      };

      if (mode === 'm2' && st.referenceAudioBase64) {
        payload.audio_base64 = st.referenceAudioBase64;
      } else if (mode === 'm1') {
        // Use the exact playable track registered for this result. Never rely on a
        // server-wide "last audio" buffer, which could belong to another job.
        const src = (currentResult && (currentResult.media_url || currentResult.audio_base64)) || '';
        if (src && src.indexOf('/api/media') === 0) {
          const query = src.split('path=')[1];
          if (query) {
            try {
              payload.file_path = decodeURIComponent(query);
            } catch (err) {
              payload.file_path = query;
            }
          }
        } else if (currentResult && currentResult.audio_base64) {
          payload.audio_base64 = currentResult.audio_base64;
        }
      }

      const res = await fetch('/api/edit-audio', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      btn.innerHTML = origHtml;
      btn.disabled = false;
      setNavProcessingState(navMode, false);

      if (data.error) {
        showToast('Export error: ' + data.error, 'error');
        return;
      }

      if (data.audio_base64) {
        const link = document.createElement('a');
        link.href = data.audio_base64;
        link.download = data.filename || 'scriber_edited.mp3';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showToast(`✓ Exported ${data.filename} (${formatSec(data.duration)})! Saved to outputs folder.`, 'success');
      }
    } catch (e) {
      btn.innerHTML = origHtml;
      btn.disabled = false;
      setNavProcessingState(navMode, false);
      showToast('Export network error: ' + e, 'error');
    }
  }

  /* Studio Voice Profile Selection */
  function populateVoiceProfiles(profiles) {
    if (!profiles || profiles.length === 0) return;
    window.transcribedVoiceProfiles = profiles;
    selectedVoiceProfile = profiles[0];
    window.selectedVoiceProfile = profiles[0];

    const dur = getAccurateDuration();
    if (dur > 0) {
      initModeAudioEditor('m2', dur, (currentResult && currentResult.video_source) || 'transcribed_voice.mp3');
    }
  }

  async function synthesizeClonedVoice() {
    const text = document.getElementById('clone-text').value.trim();
    if (!text) {
      showToast('Please enter text for the selected voice to speak.', 'info');
      return;
    }
    if (!selectedVoiceProfile) {
      if (currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
        selectedVoiceProfile = currentResult.voice_profiles[0];
        window.selectedVoiceProfile = selectedVoiceProfile;
      } else {
        // No studio voice profile and no transcription profile: send an
        // explicitly unmeasured profile so the server reports pitch similarity
        // as unmeasured instead of comparing against a fabricated 140 Hz /
        // 150 WPM baseline.
        selectedVoiceProfile = {
          speaker_id: "Studio_Voice",
          fundamental_frequency_hz: 0.0,
          estimated_wpm: 0.0,
          gender_estimate: "unmeasured"
        };
      }
    }

    const pitchShift = parseFloat(document.getElementById('pitch-slider').value) || 0;
    const rateShift = parseFloat(document.getElementById('rate-slider').value) || 0;
    const volumeSlider = document.getElementById('volume-slider');
    const volumeGain = volumeSlider ? (parseFloat(volumeSlider.value) / 100.0) : 1.0;
    const targetVoiceId = (selectedStudioVoice && selectedStudioVoice.id) || (selectedVoiceProfile && selectedVoiceProfile.voice_id) || null;

    const btn = document.getElementById('synthesize-btn');
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="anim-spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Synthesizing Speech...';
    btn.disabled = true;

    startAcousticResonanceAnimation();
    setVoiceModelLocked(true);
    setNavProcessingState('voice', true);

    if (activeVoiceAbortController) {
      activeVoiceAbortController.abort();
    }
    activeVoiceAbortController = new AbortController();

    try {
      const res = await fetch('/api/clone-voice', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: activeVoiceAbortController.signal,
        body: JSON.stringify({
          text: text,
          pitch_shift: pitchShift,
          rate_shift: rateShift,
          volume: volumeGain,
          voice_id: targetVoiceId,
          profile: selectedVoiceProfile,
          output_format: 'mp3',
          sample_rate: 48000,
          file_path: (selectedVoiceProfile && selectedVoiceProfile.file_path) || null,
          backend: selectedVoiceModel || 'auto',
        }),
      });
      const data = await res.json();
      activeVoiceAbortController = null;
      btn.innerHTML = origHtml;
      btn.disabled = false;
      stopAcousticResonanceAnimation();
      setVoiceModelLocked(false);
      setNavProcessingState('voice', false);

      if (data.cancelled) {
        showToast('Voice synthesis cancelled.', 'info');
        return;
      }

      if (data.error) {
        showToast('Synthesis error: ' + data.error, 'error');
        return;
      }

      const resBox = document.getElementById('clone-result-box');
      resBox.style.display = 'block';
      const measured = data.similarity_measured === true && typeof data.similarity_score === 'number';
      const scorePct = measured ? (data.similarity_score * 100).toFixed(1) : null;
      const fidelityLabel = measured
        ? `Pitch match: ${scorePct}%`
        : 'Pitch match not measured';
      const badge = document.getElementById('clone-fidelity-badge');
      badge.classList.toggle('unmeasured', !measured);
      const fidelityIcon = measured
        ? '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>'
        : '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><circle cx="12" cy="12" r="9"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>';
      badge.innerHTML = `${fidelityIcon} ${fidelityLabel}`;
      badge.title = measured
        ? 'Compares pitch, tone and energy with the selected preset voice profile. Estimate, not identity verification.'
        : 'The selected engine produced audio, but no comparable pitch profile was available for measurement.';
      if (data.synthesis_backend) {
        badge.title += ' Engine: ' + data.synthesis_backend + '.';
      }
      const player = document.getElementById('clone-audio-player');
      player.src = data.audio_base64;
      player.currentTime = 0;
      player.play().catch(() => {});

      const dlBtn = document.getElementById('clone-download-btn');
      dlBtn.href = data.audio_base64;
      dlBtn.download = `speech_${(selectedVoiceProfile.speaker_id || 'voice').replace(/\s+/g, '_')}.mp3`;

      // Update Mode 2 Audio Editor to point to this synthesized audio
      audioEditorState.m2.referenceAudioBase64 = data.audio_base64;
      initModeAudioEditor('m2', data.duration || 5, 'synthesized_speech.mp3');

      showToast('Speech synthesized successfully!', 'success');
      resBox.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } catch (e) {
      activeVoiceAbortController = null;
      btn.innerHTML = origHtml;
      btn.disabled = false;
      stopAcousticResonanceAnimation();
      setVoiceModelLocked(false);
      setNavProcessingState('voice', false);
      if (e.name === 'AbortError') {
        return;
      }
      showToast('Synthesis network error: ' + e, 'error');
    }
  }

  /* Helpers */
  function formatSec(s) {
    if (!s || !isFinite(s) || s < 0) return '00:00';
    const hrs = Math.floor(s / 3600);
    const mins = Math.floor((s % 3600) / 60);
    const secs = Math.floor(s % 60);
    if (hrs > 0) {
      return String(hrs).padStart(2, '0') + ':' + String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
    }
    return String(mins).padStart(2, '0') + ':' + String(secs).padStart(2, '0');
  }

  function formatSrtTimestamp(sec) {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = Math.floor(sec % 60);
    const millis = Math.floor((sec % 1) * 1000);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')},${String(millis).padStart(3, '0')}`;
  }

  function formatVttTimestamp(sec) {
    const hours = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = Math.floor(sec % 60);
    const millis = Math.floor((sec % 1) * 1000);
    return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(millis).padStart(3, '0')}`;
  }

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /* ========================================================= */
  /* MINIMALIST CLAUDE LIQUID MORPHING LIGHT ORB               */
  /* Ethereal Molten Fluid Light (Zero clutter, Pure Serenity) */
  /* ========================================================= */
  var liquidCanvas, liquidCtx;
  var liquidAnimId = null;
  var liquidTime = 0;

  function startLiquidOrbAnimation() {
    liquidCanvas = document.getElementById('liquid-orb-canvas');
    if (!liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    liquidCanvas.width = 220 * dpr;
    liquidCanvas.height = 220 * dpr;
    // Let the stylesheet scale this fixed logical canvas at each breakpoint.
    // Keeping its 220px drawing space avoids a second rendering path for mobile.
    liquidCanvas.style.width = '';
    liquidCanvas.style.height = '';
    liquidCtx = liquidCanvas.getContext('2d');
    if (!liquidAnimId) {
      renderLiquidLoop();
    }
  }

  function stopLiquidOrbAnimation() {
    if (liquidAnimId) {
      cancelAnimationFrame(liquidAnimId);
      liquidAnimId = null;
    }
  }

  /* Pre-seeded Orbital Stardust Particles (contract compatibility) */
  var orbitalParticles = [];

  /* Molten Fluid Light Orb (72-point Harmonic Spline Deformation with Quadratic Bezier Smoothing) */
  function renderLiquidLoop() {
    if (!liquidCtx || !liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var w = 220;
    var h = 220;
    var cx = w / 2;
    var cy = h / 2;
    liquidTime += 0.016;

    liquidCtx.save();
    liquidCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    liquidCtx.clearRect(0, 0, w, h);

    // 1. Soft Ambient Luminous Halo (Gaussian Falloff into Obsidian)
    var ambientGlow = liquidCtx.createRadialGradient(cx, cy, 14, cx, cy, 104);
    ambientGlow.addColorStop(0, 'rgba(255, 94, 0, 0.20)');
    ambientGlow.addColorStop(0.45, 'rgba(229, 169, 60, 0.06)');
    ambientGlow.addColorStop(1, 'transparent');
    liquidCtx.fillStyle = ambientGlow;
    liquidCtx.fillRect(0, 0, w, h);

    // 2. Subtle Acoustic Pulse Ripple (Concentric sound waves in molten amber)
    var ripplePhase = (liquidTime * 20) % 48;
    var rippleR = 54 + ripplePhase;
    var rippleAlpha = Math.max(0, 0.16 * (1 - ripplePhase / 48));
    liquidCtx.beginPath();
    liquidCtx.arc(cx, cy, rippleR, 0, Math.PI * 2);
    liquidCtx.strokeStyle = 'rgba(255, 122, 26, ' + rippleAlpha + ')';
    liquidCtx.lineWidth = 1.2;
    liquidCtx.stroke();

    // 3. Primary Liquid Mantle (72-point Harmonic Spline Deformation)
    var numPoints = 72;
    var baseR = 50 + Math.sin(liquidTime * 1.5) * 3.2;
    var points = [];

    for (var i = 0; i < numPoints; i++) {
      var theta = (i / numPoints) * Math.PI * 2;
      var h1 = Math.sin(theta * 2 + liquidTime * 1.3) * 6.5;
      var h2 = Math.cos(theta * 3 - liquidTime * 0.95) * 4.0;
      var h3 = Math.sin(theta * 5 + liquidTime * 0.75) * 2.2;
      var r = baseR + h1 + h2 + h3;
      points.push({
        x: cx + Math.cos(theta) * r,
        y: cy + Math.sin(theta) * r
      });
    }

    // Draw smooth closed fluid contour using quadratic bezier smoothing
    liquidCtx.beginPath();
    liquidCtx.moveTo((points[0].x + points[numPoints - 1].x) / 2, (points[0].y + points[numPoints - 1].y) / 2);
    for (var j = 0; j < numPoints; j++) {
      var next = points[(j + 1) % numPoints];
      var midX = (points[j].x + next.x) / 2;
      var midY = (points[j].y + next.y) / 2;
      liquidCtx.quadraticCurveTo(points[j].x, points[j].y, midX, midY);
    }
    liquidCtx.closePath();

    // Internal Molten Radial Gradient
    var mantleGrad = liquidCtx.createRadialGradient(cx - 8, cy - 8, 6, cx, cy, baseR + 12);
    mantleGrad.addColorStop(0, '#FFA826');
    mantleGrad.addColorStop(0.48, '#FF5E00');
    mantleGrad.addColorStop(0.88, '#D94F00');
    mantleGrad.addColorStop(1, 'rgba(180, 50, 0, 0.85)');
    liquidCtx.fillStyle = mantleGrad;
    liquidCtx.shadowColor = 'rgba(255, 94, 0, 0.42)';
    liquidCtx.shadowBlur = 20;
    liquidCtx.fill();
    liquidCtx.shadowBlur = 0;

    // 4. Inner Luminous Liquid Caustic (Secondary harmonic phase for organic depth)
    var innerR = baseR * 0.58;
    var innerPoints = [];
    for (var k = 0; k < numPoints; k++) {
      var itheta = (k / numPoints) * Math.PI * 2;
      var ih1 = Math.sin(itheta * 2 + liquidTime * 1.5 + 0.8) * 3.6;
      var ih2 = Math.cos(itheta * 3 - liquidTime * 1.1 + 0.5) * 2.2;
      var ir = innerR + ih1 + ih2;
      innerPoints.push({
        x: (cx - 4) + Math.cos(itheta) * ir,
        y: (cy - 4) + Math.sin(itheta) * ir
      });
    }

    liquidCtx.beginPath();
    liquidCtx.moveTo((innerPoints[0].x + innerPoints[numPoints - 1].x) / 2, (innerPoints[0].y + innerPoints[numPoints - 1].y) / 2);
    for (var m = 0; m < numPoints; m++) {
      var inext = innerPoints[(m + 1) % numPoints];
      var imidX = (innerPoints[m].x + inext.x) / 2;
      var imidY = (innerPoints[m].y + inext.y) / 2;
      liquidCtx.quadraticCurveTo(innerPoints[m].x, innerPoints[m].y, imidX, imidY);
    }
    liquidCtx.closePath();

    var innerGrad = liquidCtx.createRadialGradient(cx - 6, cy - 6, 2, cx - 2, cy - 2, innerR + 6);
    innerGrad.addColorStop(0, '#FFF5EB');
    innerGrad.addColorStop(0.45, '#FFA826');
    innerGrad.addColorStop(1, 'rgba(255, 94, 0, 0.15)');
    liquidCtx.fillStyle = innerGrad;
    liquidCtx.fill();

    liquidCtx.restore();
    liquidAnimId = requestAnimationFrame(renderLiquidLoop);
  }

  /* ========================================================= */
  /* MINIMAL ACOUSTIC RESONANCE OSCILLOSCOPE (CUSTOM TTS)      */
  /* ========================================================= */
  var resCanvas, resCtx;
  var voiceOrbCanvas, voiceOrbCtx;
  var resAnimId = null;
  var resTime = 0;
  var voiceOrbTime = 0;

  function startAcousticResonanceAnimation() {
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) stage.style.display = 'block';
    
    var dpr = window.devicePixelRatio || 1;

    // 1. Resonant Voice Morphing Orb
    voiceOrbCanvas = document.getElementById('voice-orb-canvas');
    if (voiceOrbCanvas) {
      voiceOrbCanvas.width = 160 * dpr;
      voiceOrbCanvas.height = 160 * dpr;
      voiceOrbCanvas.style.width = '160px';
      voiceOrbCanvas.style.height = '160px';
      voiceOrbCtx = voiceOrbCanvas.getContext('2d');
    }

    // 2. Multi-Harmonic Resonant Oscilloscope Waveforms
    resCanvas = document.getElementById('resonance-canvas');
    if (resCanvas) {
      var w = resCanvas.parentElement.clientWidth || 500;
      var h = 60;
      resCanvas.width = w * dpr;
      resCanvas.height = h * dpr;
      resCanvas.style.width = '100%';
      resCanvas.style.height = '60px';
      resCtx = resCanvas.getContext('2d');
    }

    if (!resAnimId) {
      renderResonanceLoop();
    }
  }

  function stopAcousticResonanceAnimation() {
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) stage.style.display = 'none';
    if (resAnimId) {
      cancelAnimationFrame(resAnimId);
      resAnimId = null;
    }
  }

  function renderResonanceLoop() {
    var dpr = window.devicePixelRatio || 1;

    // Calculate effective vocal pitch from active profile and pitch slider
    var baseF0 = (selectedVoiceProfile && selectedVoiceProfile.fundamental_frequency_hz) ? selectedVoiceProfile.fundamental_frequency_hz : 145;
    var pitchSlider = document.getElementById('pitch-slider');
    var pitchShift = pitchSlider ? (parseFloat(pitchSlider.value) || 0) : 0;
    var effectiveF0 = Math.max(60, baseF0 + pitchShift);
    var pitchScale = effectiveF0 / 140.0;

    // Smooth harmonic phase synthesis for organic fluidity
    voiceOrbTime += 0.018 * Math.sqrt(pitchScale);
    resTime += 0.024 * Math.sqrt(pitchScale);

    // 1. Render Fluid Liquid Voice Morphing Orb
    if (voiceOrbCtx && voiceOrbCanvas) {
      var ow = 160;
      var oh = 160;
      var ocx = ow / 2;
      var ocy = oh / 2;

      voiceOrbCtx.save();
      voiceOrbCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      voiceOrbCtx.clearRect(0, 0, ow, oh);

      // Acoustic Halo Glow with Warm Obsidian & Tangerine Falloff
      var orbGlow = voiceOrbCtx.createRadialGradient(ocx, ocy, 8, ocx, ocy, 74);
      orbGlow.addColorStop(0, 'rgba(255, 94, 0, 0.22)');
      orbGlow.addColorStop(0.45, 'rgba(229, 169, 60, 0.07)');
      orbGlow.addColorStop(1, 'transparent');
      voiceOrbCtx.fillStyle = orbGlow;
      voiceOrbCtx.fillRect(0, 0, ow, oh);

      // Smooth acoustic pulse ripple matching voice harmonics
      var orbRipple = (voiceOrbTime * 18) % 36;
      var rippleR = 40 + orbRipple;
      var rippleAlpha = Math.max(0, 0.18 * (1 - orbRipple / 36));
      voiceOrbCtx.beginPath();
      voiceOrbCtx.arc(ocx, ocy, rippleR, 0, Math.PI * 2);
      voiceOrbCtx.strokeStyle = 'rgba(255, 122, 26, ' + rippleAlpha + ')';
      voiceOrbCtx.lineWidth = 1.2;
      voiceOrbCtx.stroke();

      // 72-point Harmonic Spline Deformation for Voice Orb
      var numPoints = 72;
      var baseR = 38 + Math.sin(voiceOrbTime * 1.6) * 2.5;
      var orbPoints = [];

      for (var pIdx = 0; pIdx < numPoints; pIdx++) {
        var theta = (pIdx / numPoints) * Math.PI * 2;
        var h1 = Math.sin(theta * 2 + voiceOrbTime * 1.8) * 4.6;
        var h2 = Math.cos(theta * 3 - voiceOrbTime * 1.3) * 3.0;
        var h3 = Math.sin(theta * 5 + voiceOrbTime * 1.0) * 1.8;
        var r = baseR + (h1 + h2 + h3) * (0.8 + pitchScale * 0.2);
        orbPoints.push({
          x: ocx + Math.cos(theta) * r,
          y: ocy + Math.sin(theta) * r
        });
      }

      voiceOrbCtx.beginPath();
      voiceOrbCtx.moveTo((orbPoints[0].x + orbPoints[numPoints - 1].x) / 2, (orbPoints[0].y + orbPoints[numPoints - 1].y) / 2);
      for (var j = 0; j < numPoints; j++) {
        var next = orbPoints[(j + 1) % numPoints];
        var midX = (orbPoints[j].x + next.x) / 2;
        var midY = (orbPoints[j].y + next.y) / 2;
        voiceOrbCtx.quadraticCurveTo(orbPoints[j].x, orbPoints[j].y, midX, midY);
      }
      voiceOrbCtx.closePath();

      var orbGrad = voiceOrbCtx.createRadialGradient(ocx - 6, ocy - 6, 4, ocx, ocy, baseR + 10);
      orbGrad.addColorStop(0, '#FFA826');
      orbGrad.addColorStop(0.48, '#FF5E00');
      orbGrad.addColorStop(0.88, '#D94F00');
      orbGrad.addColorStop(1, 'rgba(180, 50, 0, 0.85)');
      voiceOrbCtx.fillStyle = orbGrad;
      voiceOrbCtx.shadowColor = 'rgba(255, 94, 0, 0.40)';
      voiceOrbCtx.shadowBlur = 16;
      voiceOrbCtx.fill();
      voiceOrbCtx.shadowBlur = 0;

      // Inner Luminous Caustic
      var innerR = baseR * 0.56;
      var innerPoints = [];
      for (var k = 0; k < numPoints; k++) {
        var itheta = (k / numPoints) * Math.PI * 2;
        var ih1 = Math.sin(itheta * 2 + voiceOrbTime * 1.9 + 0.8) * 2.8;
        var ih2 = Math.cos(itheta * 3 - voiceOrbTime * 1.4 + 0.4) * 1.8;
        var ir = innerR + ih1 + ih2;
        innerPoints.push({
          x: (ocx - 3) + Math.cos(itheta) * ir,
          y: (ocy - 3) + Math.sin(itheta) * ir
        });
      }

      voiceOrbCtx.beginPath();
      voiceOrbCtx.moveTo((innerPoints[0].x + innerPoints[numPoints - 1].x) / 2, (innerPoints[0].y + innerPoints[numPoints - 1].y) / 2);
      for (var m = 0; m < numPoints; m++) {
        var inext = innerPoints[(m + 1) % numPoints];
        var imidX = (innerPoints[m].x + inext.x) / 2;
        var imidY = (innerPoints[m].y + inext.y) / 2;
        voiceOrbCtx.quadraticCurveTo(innerPoints[m].x, innerPoints[m].y, imidX, imidY);
      }
      voiceOrbCtx.closePath();

      var innerGrad = voiceOrbCtx.createRadialGradient(ocx - 5, ocy - 5, 2, ocx - 2, ocy - 2, innerR + 5);
      innerGrad.addColorStop(0, '#FFF5EB');
      innerGrad.addColorStop(0.45, '#FFA826');
      innerGrad.addColorStop(1, 'rgba(255, 94, 0, 0.15)');
      voiceOrbCtx.fillStyle = innerGrad;
      voiceOrbCtx.fill();

      voiceOrbCtx.restore();
    }

    // 2. Render Butter-Smooth Acoustic Oscilloscope Ribbon Waveforms
    if (resCtx && resCanvas) {
      var rw = resCanvas.clientWidth || (resCanvas.width / dpr);
      var rh = 60;

      resCtx.save();
      resCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      resCtx.clearRect(0, 0, rw, rh);

      // Smooth flowing harmonic ribbons in Tangerine, Gold, Coral
      var waves = [
        { freq: 0.045 * pitchScale, amp: 14, color: 'rgba(255, 94, 0, 0.90)', width: 1.8 },
        { freq: 0.085 * pitchScale, amp: 9, color: 'rgba(229, 169, 60, 0.85)', width: 1.4 },
        { freq: 0.145 * pitchScale, amp: 6, color: 'rgba(255, 138, 122, 0.75)', width: 1.1 },
        { freq: 0.220 * pitchScale, amp: 3.5, color: 'rgba(255, 216, 138, 0.65)', width: 0.8 }
      ];

      waves.forEach(function(wv, wi) {
        resCtx.beginPath();
        for (var x = 0; x < rw; x += 1) {
          var t = resTime * (1.6 + wi * 0.7);
          var envelope = Math.sin((x / rw) * Math.PI);
          var y = (rh / 2) + Math.sin(x * wv.freq + t) * (wv.amp * envelope) + Math.cos(x * 0.025 + t * 0.6) * (2.5 * envelope);
          if (x === 0) resCtx.moveTo(x, y);
          else resCtx.lineTo(x, y);
        }
        resCtx.strokeStyle = wv.color;
        resCtx.lineWidth = wv.width;
        resCtx.stroke();
      });

      resCtx.restore();
    }

    // 3. Update dynamic pitch status text
    var statusText = document.getElementById('resonance-status-text');
    if (statusText) {
      statusText.innerText = 'Matching the selected voice · Pitch: ' + effectiveF0.toFixed(1) + ' Hz';
    }

    resAnimId = requestAnimationFrame(renderResonanceLoop);
  }

  /* ========================================================= */
  /* MINIMALIST AUDIO WAVEFORM: 64 BARS & SLEEK SCRUBBER        */
  /* ========================================================= */
  var waveCanvas, waveCtx;
  var waveEnvelope = null;
  var isScrubbing = false;

  /* Web Audio API AnalyserNode Realtime Frequency Visualizer */
  var visualizerAnalyser = null;
  var visualizerDataArray = null;
  var visualizerConnected = false;

  function initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return null;
      if (!studioAudioCtx) studioAudioCtx = new AudioCtx();
      if (studioAudioCtx.state === 'suspended') {
        studioAudioCtx.resume().catch(() => {});
      }
      return studioAudioCtx;
    } catch (e) {
      return null;
    }
  }

  function initAudioVisualizer(player) {
    if (!player) player = document.getElementById('audio-player');
    const ctx = initAudioContext();
    if (!ctx) return null;
    try {
      if (!visualizerAnalyser) {
        visualizerAnalyser = ctx.createAnalyser();
        visualizerAnalyser.fftSize = 128; // 64 frequency bins
        visualizerAnalyser.smoothingTimeConstant = 0.8;
        visualizerDataArray = new Uint8Array(visualizerAnalyser.frequencyBinCount);
      }
      if (player && typeof getStudioGainNode === 'function' && !visualizerConnected) {
        const gainNode = getStudioGainNode('m1', player);
        if (gainNode) {
          try {
            gainNode.connect(visualizerAnalyser);
            visualizerConnected = true;
          } catch (e) {}
        }
      }
      return visualizerAnalyser;
    } catch (e) {
      return null;
    }
  }

  function getWaveformClickProgress(e) {
    const canvas = document.getElementById('waveform-canvas');
    const wrap = document.getElementById('waveform-wrap');
    const target = canvas || wrap;
    if (!target) return 0;
    const rect = target.getBoundingClientRect();
    const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : (e.clientX || 0);
    const clickX = clientX - rect.left;
    return Math.max(0, Math.min(1, clickX / Math.max(1, rect.width)));
  }

  function initWaveform() {
    waveCanvas = document.getElementById('waveform-canvas');
    if (!waveCanvas) return;
    waveCtx = waveCanvas.getContext('2d');
    resizeWaveform();
    window.addEventListener('resize', resizeWaveform);

    const wrap = document.getElementById('waveform-wrap');
    const tooltip = document.getElementById('waveform-tooltip');

    function updateTooltip(e) {
      if (!tooltip || !wrap) return;
      const pct = getWaveformClickProgress(e);
      const totalDur = getAccurateDuration();
      const canvas = document.getElementById('waveform-canvas');
      const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : (e.clientX || 0);
      const refLeft = (canvas ? canvas.getBoundingClientRect().left : wrap.getBoundingClientRect().left);
      const clickX = clientX - refLeft;
      tooltip.style.display = 'block';
      tooltip.style.left = Math.max(10, Math.min(wrap.clientWidth - 50, clickX)) + 'px';
      tooltip.innerText = formatSec(pct * totalDur);
    }

    function handleSeekFromEvent(e) {
      const pct = getWaveformClickProgress(e);
      const totalDur = getAccurateDuration();
      const player = document.getElementById('audio-player');
      if (player && totalDur > 0) {
        player.muted = false;
        player.currentTime = pct * totalDur;
        handleAudioTimeUpdate();
        drawWave();
      }
    }

    wrap.addEventListener('mousemove', function(e) {
      updateTooltip(e);
      if (isScrubbing) {
        handleSeekFromEvent(e);
      }
    });

    wrap.addEventListener('mouseleave', function() {
      if (tooltip && !isScrubbing) tooltip.style.display = 'none';
    });

    wrap.addEventListener('mousedown', function(e) {
      isScrubbing = true;
      initAudioPlayerEvents();
      initAudioContext();
      const player = document.getElementById('audio-player');
      if (player) {
        initAudioVisualizer(player);
      }
      if (typeof audioContext !== 'undefined' && audioContext && audioContext.state === 'suspended') {
        audioContext.resume().catch(() => {});
      }
      handleSeekFromEvent(e);
      if (player) {
        updatePlayPauseIcons(true);
        const playPromise = player.play();
        if (playPromise !== undefined) {
          playPromise.then(() => {
            updatePlayPauseIcons(true);
            scheduleWaveAnimation();
          }).catch((err) => {
            console.warn('Waveform mousedown play() deferred or blocked:', err);
            updatePlayPauseIcons(false);
          });
        }
      }
    });

    // Touch event support for tablet / touch screens
    wrap.addEventListener('touchstart', function(e) {
      isScrubbing = true;
      initAudioPlayerEvents();
      initAudioContext();
      const player = document.getElementById('audio-player');
      if (player) initAudioVisualizer(player);
      updateTooltip(e);
      handleSeekFromEvent(e);
      if (player) {
        const playPromise = player.play();
        if (playPromise !== undefined) {
          playPromise.then(() => {
            updatePlayPauseIcons(true);
            scheduleWaveAnimation();
          }).catch(() => {});
        }
      }
    }, { passive: true });

    wrap.addEventListener('touchmove', function(e) {
      if (isScrubbing) {
        updateTooltip(e);
        handleSeekFromEvent(e);
      }
    }, { passive: true });

    wrap.addEventListener('touchend', function() {
      if (isScrubbing) {
        isScrubbing = false;
        if (tooltip) tooltip.style.display = 'none';
        drawWave();
      }
    });

    window.addEventListener('mousemove', function(e) {
      if (isScrubbing) {
        updateTooltip(e);
        handleSeekFromEvent(e);
      }
    });

    window.addEventListener('mouseup', function() {
      if (isScrubbing) {
        isScrubbing = false;
        if (tooltip) tooltip.style.display = 'none';
        drawWave();
      }
    });

    initAudioPlayerEvents();
    drawWave();
  }

  function resizeWaveform() {
    if (!waveCanvas) waveCanvas = document.getElementById('waveform-canvas');
    if (!waveCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var parentRect = waveCanvas.parentElement ? waveCanvas.parentElement.getBoundingClientRect() : null;
    var w = parentRect ? Math.max(100, Math.floor(parentRect.width - 24)) : (waveCanvas.clientWidth || 600);
    var h = 40;
    waveCanvas.width = Math.round(w * dpr);
    waveCanvas.height = Math.round(h * dpr);
    waveCanvas.style.width = '100%';
    waveCanvas.style.height = '40px';
  }

  function resampleEnvelope(envelope, count) {
    if (!envelope || !envelope.length) return null;
    if (envelope.length === count) return envelope;
    if (envelope.length === 1) return new Array(count).fill(envelope[0]);
    const out = [];
    for (let i = 0; i < count; i++) {
      const pos = (i / (count - 1)) * (envelope.length - 1);
      const lo = Math.floor(pos);
      const hi = Math.min(envelope.length - 1, lo + 1);
      const frac = pos - lo;
      out.push(envelope[lo] * (1 - frac) + envelope[hi] * frac);
    }
    return out;
  }

  function drawBars(ctx, w, h, envelope, progress, isPlaying, duration, hasTrim, trimStartProg, trimEndProg) {
    const bars = 64;
    const gap = Math.max(1, Math.min(3, Math.floor(w / 180)));
    const totalGap = (bars - 1) * gap;
    const barWidth = Math.max(1.5, (w - totalGap) / bars);
    const step = barWidth + gap;

    let liveLevel = 0;
    let hasLiveFrequency = false;
    if (visualizerAnalyser && visualizerDataArray && isPlaying) {
      try {
        visualizerAnalyser.getByteFrequencyData(visualizerDataArray);
        // Measure active human speech frequencies (first 24 bins cover up to ~9kHz)
        let sum = 0;
        let count = 0;
        for (let j = 0; j < Math.min(24, visualizerDataArray.length); j++) {
          sum += visualizerDataArray[j];
          count++;
        }
        if (sum > 0) {
          hasLiveFrequency = true;
          liveLevel = sum / (count * 255.0);
        }
      } catch (e) {}
    }

    const now = performance.now() * 0.0035;
    if (!hasLiveFrequency && isPlaying) {
      // Dynamic harmonic voice cadence modulation fallback
      liveLevel = 0.42 + 0.38 * (0.6 * Math.sin(now * 5.2) + 0.4 * Math.cos(now * 3.1));
    }

    const closestBar = Math.round(progress * (bars - 1));

    for (let i = 0; i < bars; i++) {
      const barProg = i / (bars - 1);
      const isPast = barProg <= progress;
      const isPlayhead = (i === closestBar);
      const isInsideTrim = !hasTrim || (barProg >= trimStartProg - (0.5 / bars) && barProg <= trimEndProg + (0.5 / bars));

      // Determine base height ratio (0.0 to 1.0)
      let baseVal = 0.22;
      if (envelope && envelope.length) {
        baseVal = Math.max(0.04, envelope[i]);
      } else {
        // Aesthetic resting wave profile when no precomputed envelope is present
        baseVal = 0.22 + 0.16 * Math.sin(i * 0.22) * Math.cos(i * 0.11 + 0.3);
      }

      // Dynamic animation modulation during active playback
      let dynamicFactor = 1.0;
      if (isPlaying) {
        const distToPlayhead = Math.abs(barProg - progress);
        // Focused acoustic energy dancing wave centered directly around the active playhead
        const playheadRipple = Math.max(0, 1.0 - distToPlayhead * 5.5);
        const playheadBounce = playheadRipple * (liveLevel * 0.95 + 0.35 * Math.sin(now * 7.5 + i * 0.4));

        // Traveling acoustic wave across the entire waveform
        const travelingWave = 0.12 * Math.sin(i * 0.36 - now * 3.8) + 0.08 * Math.cos(i * 0.22 + now * 2.4);

        // Played portion carries live energy pulse
        const pastPulse = isPast ? (0.09 * Math.sin(now * 3.2 + i * 0.28)) : 0;

        dynamicFactor = Math.max(0.32, 1.0 + playheadBounce + travelingWave + pastPulse);
      }

      const barHeight = Math.max(4, Math.min(h - 4, baseVal * dynamicFactor * (h * 0.86)));
      const x = i * step;
      const y = (h - barHeight) / 2;

      if (!isInsideTrim) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.07)';
        ctx.shadowBlur = 0;
      } else if (isPlayhead) {
        ctx.fillStyle = '#FFE4B5';
        ctx.shadowColor = '#FF5E00';
        ctx.shadowBlur = isPlaying ? 10 : 3;
      } else if (isPast) {
        const grad = ctx.createLinearGradient(0, y, 0, y + barHeight);
        grad.addColorStop(0, '#FF8A33');
        grad.addColorStop(0.5, '#FF5E00');
        grad.addColorStop(1, '#E5A93C');
        ctx.fillStyle = grad;
        ctx.shadowColor = 'rgba(255, 94, 0, 0.35)';
        ctx.shadowBlur = isPlaying ? 4 : 0;
      } else {
        ctx.fillStyle = 'rgba(229, 169, 60, 0.32)';
        ctx.shadowBlur = 0;
      }

      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(x, y, barWidth, barHeight, 2.5);
      } else {
        ctx.rect(x, y, barWidth, barHeight);
      }
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  function drawWave() {
    if (!waveCanvas) waveCanvas = document.getElementById('waveform-canvas');
    if (!waveCtx && waveCanvas) waveCtx = waveCanvas.getContext('2d');
    if (!waveCtx || !waveCanvas) return;
    if (waveCanvas.offsetParent === null) {
      return;
    }
    var dpr = window.devicePixelRatio || 1;
    var parentRect = waveCanvas.parentElement ? waveCanvas.parentElement.getBoundingClientRect() : null;
    var w = parentRect ? Math.max(100, Math.floor(parentRect.width - 24)) : (waveCanvas.clientWidth || 600);
    var h = 40;

    // Automatically sync internal bitmap resolution if container resized while hidden
    var expectedW = Math.round(w * dpr);
    var expectedH = Math.round(h * dpr);
    if (waveCanvas.width !== expectedW || waveCanvas.height !== expectedH) {
      waveCanvas.width = expectedW;
      waveCanvas.height = expectedH;
    }

    waveCtx.save();
    waveCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    waveCtx.clearRect(0, 0, w, h);

    const player = document.getElementById('audio-player');
    const isPlaying = player && !player.paused;
    if (isPlaying) {
      handleAudioTimeUpdate();
    }
    const duration = getAccurateDuration() || 10;
    const currentTime = (player && isFinite(player.currentTime)) ? player.currentTime : 0;
    const progress = Math.max(0, Math.min(1, currentTime / duration));

    const bars = 64;
    const envelope = resampleEnvelope(waveEnvelope, bars);

    const m1State = audioEditorState && audioEditorState.m1;
    const hasTrim = m1State && (m1State.trimStart > 0 || (m1State.trimEnd && m1State.trimEnd < (m1State.totalDuration - 0.05)));
    const trimStartProg = hasTrim && duration > 0 ? (m1State.trimStart / duration) : 0;
    const trimEndProg = hasTrim && duration > 0 ? (m1State.trimEnd / duration) : 1;

    drawBars(waveCtx, w, h, envelope, progress, isPlaying, duration, hasTrim, trimStartProg, trimEndProg);

    if (hasTrim) {
      const inX = Math.max(0, Math.min(w - 1, trimStartProg * w));
      const outX = Math.max(0, Math.min(w - 1, trimEndProg * w));

      waveCtx.strokeStyle = '#E5A93C';
      waveCtx.lineWidth = 1.5;
      waveCtx.beginPath();
      waveCtx.moveTo(inX, 2);
      waveCtx.lineTo(inX, h - 2);
      waveCtx.stroke();

      waveCtx.strokeStyle = '#FF5E00';
      waveCtx.lineWidth = 1.5;
      waveCtx.beginPath();
      waveCtx.moveTo(outX, 2);
      waveCtx.lineTo(outX, h - 2);
      waveCtx.stroke();
    }

    waveCtx.restore();
    if (isPlaying || isScrubbing) {
      scheduleWaveAnimation();
    } else {
      stopWaveAnimation();
    }
  }

  function revealExportFolder() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.reveal_in_explorer) {
      window.pywebview.api.reveal_in_explorer('./scriber_output');
      showToast('Opened Scriber output folder in Explorer', 'info');
      return;
    }
    fetch('/api/desktop/reveal', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: './scriber_output' })
    }).then(r => r.json()).then(d => {
      showToast('Opened Scriber output folder in Explorer', 'info');
    }).catch(err => {
      showToast('Could not open folder: ' + err.message, 'error');
    });
  }

  function checkDesktopRuntime() {
    fetch('/api/desktop/info')
      .then(r => r.ok ? r.json() : null)
      .catch(() => {});
  }

  window.addEventListener('DOMContentLoaded', checkDesktopRuntime);
  setTimeout(checkDesktopRuntime, 300);

  initWaveform();

  /* ==========================================================================
     Studio Voice Suite & Hardware Performance Telemetry
     ========================================================================== */
  var studioVoicesList = [];
  var selectedStudioVoice = null;
  var currentRegionFilter = 'all';
  var currentGenderFilter = 'all';

  async function loadStudioVoices() {
    const grid = document.getElementById('voice-suite-grid');
    try {
      const res = await fetch('/api/voices');
      if (!res.ok) {
        throw new Error('Voice API returned HTTP ' + res.status);
      }
      const data = await res.json();
      studioVoicesList = data.voices || [];
      if (studioVoicesList.length > 0 && !selectedStudioVoice) {
        selectedStudioVoice = studioVoicesList[0]; // Jenny (US)
        updateActiveVoiceBanner(selectedStudioVoice);
      }
      renderStudioVoices();
    } catch (e) {
      console.warn('Failed to load studio voices:', e);
      if (grid) {
        grid.innerHTML = `
          <div class="voice-load-error" role="alert">
            <strong>Voice suite could not load.</strong>
            <span>${escapeHtml(e && e.message ? e.message : 'Network error')}</span>
            <button type="button" class="btn-secondary" onclick="loadStudioVoices()">Retry</button>
          </div>`;
      }
    }
  }

  function renderStudioVoices() {
    const grid = document.getElementById('voice-suite-grid');
    if (!grid) return;
    const filtered = studioVoicesList.filter(function(v) {
      var matchRegion = (currentRegionFilter === 'all') || 
                        (v.region === currentRegionFilter) ||
                        (currentRegionFilter === 'Africa' && (v.region === 'South Africa' || v.region === 'Nigeria' || v.region.indexOf('Africa') !== -1));
      var matchGender = (currentGenderFilter === 'all') || (v.gender === currentGenderFilter);
      return matchRegion && matchGender;
    });

    if (filtered.length === 0) {
      grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 24px; color: var(--text-muted); font-size:12px;">No voices found for selected filters.</div>';
      return;
    }

    grid.innerHTML = filtered.map(function(v) {
      var isSel = selectedStudioVoice && (selectedStudioVoice.id === v.id);
      var genderClass = v.gender === 'feminine' ? 'female' : 'male';
      var genderInit = v.gender === 'feminine' ? 'F' : 'M';
      const safeId = escapeHtml(v.id);
      return `
        <div class="voice-suite-card ${isSel ? 'selected' : ''}" role="button" tabindex="0"
             onclick="selectStudioVoice('${safeId}')"
             onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();selectStudioVoice('${safeId}');}">
          <div class="voice-card-header-row">
            <div class="voice-card-name-wrap">
              <span class="voice-avatar-badge ${genderClass}">${genderInit}</span>
              <span class="voice-card-name">${escapeHtml(v.name)}</span>
            </div>
            <span class="voice-locale-badge">${escapeHtml(v.locale)}</span>
          </div>
          <div class="voice-card-style">
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            <span>${escapeHtml(v.style || 'Natural')}</span>
          </div>
          <div class="voice-card-desc">${escapeHtml(v.description || '')}</div>
          <div class="voice-card-footer">
            <button type="button" class="btn-audition-card" onclick="event.stopPropagation(); auditionVoiceCard('${safeId}')" title="Audition this voice preview">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              <span>Preview Script</span>
            </button>
            <div class="voice-select-radio"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  function filterStudioVoices(type, value, btnElem) {
    if (type === 'region') {
      currentRegionFilter = value;
    } else if (type === 'gender') {
      currentGenderFilter = value;
    }
    if (btnElem && btnElem.parentNode) {
      btnElem.parentNode.querySelectorAll('.suite-filter-pill').forEach(function(p) {
        p.classList.remove('active');
        p.setAttribute('aria-pressed', 'false');
      });
      btnElem.classList.add('active');
      btnElem.setAttribute('aria-pressed', 'true');
    }
    renderStudioVoices();
  }

  function selectStudioVoice(voiceId) {
    var voice = studioVoicesList.find(function(v) { return v.id === voiceId; });
    if (!voice) return;
    selectedStudioVoice = voice;
    updateActiveVoiceBanner(voice);

    selectedVoiceProfile = {
      speaker_id: voice.id,
      voice_id: voice.id,
      fundamental_frequency_hz: voice.base_f0 || 160.0,
      gender_estimate: voice.gender || "feminine",
      spectral_centroid_hz: voice.centroid || 1600.0,
      recommended_voice: voice.id,
    };
    window.selectedVoiceProfile = selectedVoiceProfile;

    renderStudioVoices();
  }

  function updateActiveVoiceBanner(voice) {
    var titleEl = document.getElementById('banner-voice-title');
    var subEl = document.getElementById('banner-voice-sub');
    if (titleEl && voice) {
      titleEl.innerText = voice.name + ' — ' + (voice.style || 'Studio Quality');
    }
    if (subEl && voice) {
      subEl.innerText = voice.locale + ' · ' + (voice.description || '');
    }
  }

  function auditionVoiceCard(voiceId) {
    var voice = studioVoicesList.find(function(v) { return v.id === voiceId; });
    if (!voice) return;
    selectStudioVoice(voiceId);
    if (voice.preview_text) {
      var txtArea = document.getElementById('clone-text');
      if (txtArea) txtArea.value = voice.preview_text;
    }
    showToast(`Loaded preview script for ${voice.name}. Ready to synthesize!`, 'info');
  }

  function auditionSelectedVoice() {
    if (selectedStudioVoice) {
      auditionVoiceCard(selectedStudioVoice.id);
    }
  }

  // Initialize studio voices on startup
  setTimeout(loadStudioVoices, 100);

  // Export functions to window
  window.loadStudioVoices = loadStudioVoices;
  window.filterStudioVoices = filterStudioVoices;
  window.selectStudioVoice = selectStudioVoice;
  window.auditionVoiceCard = auditionVoiceCard;
  window.auditionSelectedVoice = auditionSelectedVoice;
  window.renderTranscription = renderTranscription;
  window.copyFullTranscript = copyFullTranscript;
  window.switchMode = switchMode;
  window.openFileDialog = openFileDialog;
  window.synthesizeClonedVoice = synthesizeClonedVoice;
  window.downloadArtifact = downloadArtifact;
  window.revealExportFolder = revealExportFolder;
  window.startProcessing = startProcessing;
  window.togglePlayPause = togglePlayPause;
  window.updatePlayPauseIcons = updatePlayPauseIcons;
  window.handleAudioTimeUpdate = handleAudioTimeUpdate;
  window.handleAudioEnded = handleAudioEnded;
  window.seekTo = seekTo;
  window.seekToWord = seekToWord;
  window.skipAudio = skipAudio;
  window.setAudioVolume = setAudioVolume;
  window.setPlaybackRate = setPlaybackRate;
  window.showToast = showToast;
  window.setTranscribeModelLocked = setTranscribeModelLocked;
  window.setVoiceModelLocked = setVoiceModelLocked;
  window.startProcessingPath = startProcessingPath;
  window.initModeAudioEditor = initModeAudioEditor;
  window.exportEditedMP3 = exportEditedMP3;
  window.audioEditorState = audioEditorState;
  window.handleVolumeInput = handleVolumeInput;
  window.handlePitchInput = handlePitchInput;
  window.handleTrimBarInput = handleTrimBarInput;
  window.toggleAudioToolsDrawer = toggleAudioToolsDrawer;
  window.toggleExportDropdown = toggleExportDropdown;
  window.handleExportSelect = handleExportSelect;
  window.cancelActiveProcessing = cancelActiveProcessing;
  window.cancelVoiceSynthesis = cancelVoiceSynthesis;
  window.drawWave = drawWave;
  window.drawBars = drawBars;
  window.initAudioContext = initAudioContext;
  window.initAudioVisualizer = initAudioVisualizer;
  window.setNavProcessingState = setNavProcessingState;
  window.audioVisualizer = {
    init: initAudioVisualizer,
    getAnalyser: () => visualizerAnalyser,
    getData: () => visualizerDataArray,
    drawWave: drawWave,
    drawBars: drawBars,
    schedule: scheduleWaveAnimation,
    stop: stopWaveAnimation
  };
