  var currentResult = null;
  window.currentResult = null;
  var selectedVoiceProfile = null;
  window.selectedVoiceProfile = null;
  var loadedMediaUrl = null;
  var loadedMediaName = '';
  var realAudioBuffer = null;
  var audioContext = null;
  var activeWaveformJobId = 0;
  var activeTranscribeJobToken = 0;
  var selectedPlaybackRate = 1;
  var savedSpeedRate = 1;
  var currentActiveMode = 'transcribe';
  var activeTranscribeStage = 'dropzone';
  var currentProcessingProgress = 0;

  const BROWSER_PLAYABLE_EXTS = ['mp3', 'wav', 'ogg', 'm4a', 'aac', 'mp4', 'webm', 'flac', 'opus', 'mov', 'm4v'];
  const VALID_MEDIA_EXTS = ['mp4', 'mp3', 'wav', 'm4a', 'mov', 'webm', 'flac', 'ogg', 'aac', 'mkv', 'avi', 'flv', 'wmv', 'opus', 'wma', '3gp', 'ts', 'm4v', 'mpeg', 'mpg', 'aiff', 'aif', 'm4b'];

  /* Reduced Motion Helper */
  var reducedMotionQuery = (typeof window.matchMedia === 'function')
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null;

  function prefersReducedMotion() {
    return !!(reducedMotionQuery && reducedMotionQuery.matches);
  }

  /* Safe JSON Response Parser */
  async function parseJsonResponse(res) {
    let payload = null;
    try {
      const raw = await res.text();
      payload = raw ? JSON.parse(raw) : {};
    } catch (e) {
      if (!res.ok) {
        throw new Error('HTTP ' + res.status + (res.statusText ? ' ' + res.statusText : ''));
      }
      throw new Error('Invalid JSON response from server');
    }
    if (!res.ok) {
      const msg = (payload && (payload.error || payload.detail || payload.message)) || ('HTTP ' + res.status);
      throw new Error(msg);
    }
    return payload;
  }

  /* Bidirectional Panel Open / Close Helpers */
  function openAnimatedPanel(el, openClass, displayValue) {
    if (!el) return;
    if (el._closeCleanup) {
      el._closeCleanup();
      el._closeCleanup = null;
    }
    el._animGen = (el._animGen || 0) + 1;
    const gen = el._animGen;
    el.style.display = (displayValue !== undefined) ? displayValue : '';
    if (displayValue === '' && window.getComputedStyle(el).display === 'none') {
      el.style.display = 'grid';
    }
    if (prefersReducedMotion()) {
      el.classList.add(openClass);
      return;
    }
    el.classList.remove(openClass);
    void el.offsetWidth;
    requestAnimationFrame(function() {
      if (el._animGen !== gen) return;
      requestAnimationFrame(function() {
        if (el._animGen !== gen) return;
        el.classList.add(openClass);
      });
    });
  }

  function closeAnimatedPanel(el, openClass, fallbackMs) {
    if (!el) return;
    if (el._closeCleanup) {
      el._closeCleanup();
      el._closeCleanup = null;
    }
    el._animGen = (el._animGen || 0) + 1;
    const gen = el._animGen;
    const alreadyHidden = !el.classList.contains(openClass) && el.style.display === 'none';
    el.classList.remove(openClass);
    if (alreadyHidden || prefersReducedMotion()) {
      el.style.display = 'none';
      return;
    }
    let finished = false;
    function finish() {
      if (finished) return;
      finished = true;
      el.removeEventListener('transitionend', onEnd);
      if (el._closeTimeout) {
        clearTimeout(el._closeTimeout);
        el._closeTimeout = null;
      }
      el._closeCleanup = null;
      if (el._animGen === gen && !el.classList.contains(openClass)) {
        el.style.display = 'none';
      }
    }
    function onEnd(evt) {
      if (evt.target === el) finish();
    }
    el._closeCleanup = finish;
    el.addEventListener('transitionend', onEnd);
    el._closeTimeout = setTimeout(finish, fallbackMs || 360);
  }

  function loadAudioForPlayback(targetAudioSrc) {
    const audioPlayer = document.getElementById('audio-player');
    if (!audioPlayer) return;
    initAudioPlayerEvents();
    audioPlayer.muted = false;
    const volSlider = document.getElementById('master-volume-slider');
    const sliderVal = volSlider ? parseFloat(volSlider.value) : NaN;
    const targetVol = !isNaN(sliderVal)
      ? sliderVal
      : (isFinite(audioPlayer.volume) ? audioPlayer.volume : 1.0);
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
      success: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>',
      error: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>',
      info: '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"></circle><line x1="12" y1="11" x2="12" y2="16"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>'
    };
    var icon = icons[type] || icons.info;
    t.innerHTML = '<span class="toast-icon" aria-hidden="true">' + icon + '</span><span>' + escapeHtml(message) + '</span>';
    cont.appendChild(t);

    var remaining = 3200;
    var startedAt = 0;
    var dismissTimer = null;

    function dismissToast() {
      if (t._leaving) return;
      t._leaving = true;
      if (dismissTimer) {
        clearTimeout(dismissTimer);
        dismissTimer = null;
      }
      t.classList.remove('show');
      if (prefersReducedMotion()) {
        if (t.parentNode) t.parentNode.removeChild(t);
        return;
      }
      t.classList.add('toast-leaving');
      var removed = false;
      function removeNode() {
        if (removed) return;
        removed = true;
        t.removeEventListener('transitionend', removeNode);
        if (t.parentNode) t.parentNode.removeChild(t);
      }
      t.addEventListener('transitionend', removeNode);
      setTimeout(removeNode, 320);
    }

    function scheduleDismiss(delay) {
      if (dismissTimer) clearTimeout(dismissTimer);
      startedAt = Date.now();
      remaining = delay;
      dismissTimer = setTimeout(dismissToast, delay);
    }

    function pauseDismiss() {
      if (dismissTimer && !t._leaving) {
        clearTimeout(dismissTimer);
        dismissTimer = null;
        remaining = Math.max(500, remaining - (Date.now() - startedAt));
      }
    }

    function resumeDismiss() {
      if (!dismissTimer && !t._leaving) {
        scheduleDismiss(remaining);
      }
    }

    t.addEventListener('mouseenter', pauseDismiss);
    t.addEventListener('focusin', pauseDismiss);
    t.addEventListener('mouseleave', resumeDismiss);
    t.addEventListener('focusout', resumeDismiss);

    if (prefersReducedMotion()) {
      t.classList.add('show');
    } else {
      requestAnimationFrame(function() {
        requestAnimationFrame(function() {
          if (!t._leaving) t.classList.add('show');
        });
      });
    }
    scheduleDismiss(3200);
  }

  /* Dropzone keyboard activation (Enter/Space) */
  function handleDropzoneKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ' || e.code === 'Space') {
      e.preventDefault();
      openFileDialog(e);
    }
  }
  window.handleDropzoneKeydown = handleDropzoneKeydown;

  /* Sliding Nav Active Indicator */
  function updateNavActiveIndicator() {
    const nav = document.querySelector('.nav-pills');
    const ind = document.getElementById('nav-active-indicator');
    if (!nav || !ind) return;
    const activePill = nav.querySelector('.nav-pill.active');
    if (!activePill) return;
    const x = activePill.offsetLeft;
    const w = activePill.offsetWidth;
    if (w <= 0) return;
    nav.style.setProperty('--ind-x', x + 'px');
    nav.style.setProperty('--ind-w', w + 'px');
    ind.style.setProperty('--ind-x', x + 'px');
    ind.style.setProperty('--ind-w', w + 'px');
  }

  function initNavIndicatorObserver() {
    const nav = document.querySelector('.nav-pills[role="tablist"]') || document.querySelector('.nav-pills');
    if (!nav) return;
    updateNavActiveIndicator();
    if (typeof ResizeObserver === 'function' && !nav.__indObserver) {
      nav.__indObserver = new ResizeObserver(function() {
        updateNavActiveIndicator();
      });
      nav.__indObserver.observe(nav);
    }
    if (document.fonts && document.fonts.ready) {
      document.fonts.ready.then(updateNavActiveIndicator).catch(function() {});
    }
  }

  /* Roving arrow-key / Home / End focus for the mode tablist */
  document.querySelectorAll('[role="tablist"] .nav-pill').forEach(function(tab) {
    tab.addEventListener('keydown', function(e) {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight' && e.key !== 'Home' && e.key !== 'End') return;
      const tablist = tab.closest('[role="tablist"]') || document;
      const tabs = Array.from(tablist.querySelectorAll('.nav-pill'));
      const idx = tabs.indexOf(tab);
      if (idx === -1) return;
      e.preventDefault();
      let next = tab;
      if (e.key === 'ArrowRight') next = tabs[(idx + 1) % tabs.length];
      else if (e.key === 'ArrowLeft') next = tabs[(idx - 1 + tabs.length) % tabs.length];
      else if (e.key === 'Home') next = tabs[0];
      else if (e.key === 'End') next = tabs[tabs.length - 1];
      next.focus();
      next.click();
    });
  });

  /* Mode Switching */
  function switchMode(mode) {
    const prevMode = currentActiveMode;
    currentActiveMode = mode;

    if (typeof closeAllModelDropdowns === 'function') closeAllModelDropdowns(false);
    if (typeof closeExportDropdown === 'function') closeExportDropdown(false);

    // Pause inactive mode's audio & preview timers cleanly
    if (mode !== 'transcribe') {
      const m1Player = document.getElementById('audio-player');
      if (m1Player && !m1Player.paused) m1Player.pause();
      if (typeof stopModePreview === 'function') stopModePreview('m1');
      if (typeof stopWaveAnimation === 'function') stopWaveAnimation();
      if (typeof stopTranscriptTracking === 'function') stopTranscriptTracking();
    }
    if (mode !== 'voice') {
      const m2Player = document.getElementById('clone-audio-player');
      if (m2Player && !m2Player.paused) m2Player.pause();
      if (typeof audioEditorState !== 'undefined' && audioEditorState.m2 && audioEditorState.m2.audioElement && !audioEditorState.m2.audioElement.paused) {
        audioEditorState.m2.audioElement.pause();
      }
      if (typeof stopModePreview === 'function') stopModePreview('m2');
    }

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
    updateNavActiveIndicator();

    let viewId = 'transcribe-view';
    if (mode === 'voice') viewId = 'voice-view';
    else if (mode === 'about') viewId = 'about-view';

    const view = document.getElementById(viewId);
    if (view) view.classList.add('active');

    if (mode === 'voice') {
      if (!selectedVoiceProfile && currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
        populateVoiceProfiles(currentResult.voice_profiles);
      }
      if (typeof resumeActiveCanvasLoops === 'function') resumeActiveCanvasLoops();
    } else if (mode === 'transcribe') {
      if (currentResult) {
        const dur = getAccurateDuration();
        const fName = (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
        const mediaKey = getTranscribeMediaKey(currentResult, fName);
        initModeAudioEditor('m1', dur > 0 ? dur : 10, fName, mediaKey);
      }
      if (typeof resumeActiveCanvasLoops === 'function') resumeActiveCanvasLoops();
      setTimeout(drawWave, 50);
    } else if (mode === 'about') {
      initBentoSpotlight();
    }
    if (prevMode !== mode && typeof updatePlayPauseIcons === 'function') {
      const m1p = document.getElementById('audio-player');
      if (mode === 'transcribe' && m1p) updatePlayPauseIcons(!m1p.paused);
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

  /* Dynamic Name Card Spotlight (rAF-throttled with cached mouseenter rect) */
  function initBentoSpotlight() {
    var cards = document.querySelectorAll('.about-card, .social-node-card');
    cards.forEach(function(card) {
      if (card.__hasSpotlight) return;
      card.__hasSpotlight = true;
      var cachedRect = null;
      var rafId = null;
      var pendingX = 0;
      var pendingY = 0;

      card.addEventListener('mouseenter', function() {
        cachedRect = card.getBoundingClientRect();
      });

      card.addEventListener('mousemove', function(e) {
        if (!cachedRect) cachedRect = card.getBoundingClientRect();
        pendingX = e.clientX - cachedRect.left;
        pendingY = e.clientY - cachedRect.top;
        if (rafId !== null) return;
        rafId = requestAnimationFrame(function() {
          rafId = null;
          card.style.setProperty('--mouse-x', Math.round(pendingX) + 'px');
          card.style.setProperty('--mouse-y', Math.round(pendingY) + 'px');
        });
      });

      card.addEventListener('mouseleave', function() {
        cachedRect = null;
        if (rafId !== null) {
          cancelAnimationFrame(rafId);
          rafId = null;
        }
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
      initNavIndicatorObserver();
      initBentoSpotlight();
      checkUrlMode();
    });
  } else {
    initNavIndicatorObserver();
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
        }
        return;
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

  /* Drag & Drop Setup with Child-Safe Depth & Media Validation */
  function hasDragFiles(e) {
    return !!(e && e.dataTransfer && Array.from(e.dataTransfer.types || []).includes('Files'));
  }

  function canAcceptDropOnUploadScreen() {
    const tv = document.getElementById('transcribe-view');
    const dz = document.getElementById('dropzone');
    const proc = document.getElementById('processing-card');
    const out = document.getElementById('output-viewport');
    if (!tv || !tv.classList.contains('active')) return false;
    if (!dz || dz.style.display === 'none' || dz.offsetParent === null) return false;
    if (proc && proc.style.display !== 'none' && proc.offsetParent !== null) return false;
    if (out && out.style.display !== 'none' && out.offsetParent !== null) return false;
    return true;
  }

  function validateSelectedMediaFile(file) {
    if (!file) return false;
    if (typeof file.size === 'number' && file.size <= 0) {
      showToast('Selected file is empty (0 bytes). Please choose a valid audio or video file.', 'error');
      return false;
    }
    const name = file.name || '';
    const dotIdx = name.lastIndexOf('.');
    const ext = dotIdx !== -1 ? name.slice(dotIdx + 1).toLowerCase() : '';
    const mime = (file.type || '').toLowerCase();
    const isMediaMime = mime.startsWith('audio/') || mime.startsWith('video/');
    const isMediaExt = ext && VALID_MEDIA_EXTS.includes(ext);
    if (!isMediaMime && !isMediaExt) {
      showToast('Unsupported file type. Please choose an audio or video file.', 'error');
      return false;
    }
    return true;
  }

  function dispatchMediaFile(file) {
    if (!validateSelectedMediaFile(file)) return;
    const nativePath = file.path || '';
    if (nativePath && (nativePath.indexOf('\\') !== -1 || nativePath.indexOf('/') !== -1)) {
      startProcessingPath(nativePath);
    } else {
      startProcessing(file);
    }
  }

  const dropzone = document.getElementById('dropzone');
  var dropzoneDragDepth = 0;
  if (dropzone) {
    dropzone.classList.add('stage-visible');
    dropzone.addEventListener('dragenter', (e) => {
      if (!hasDragFiles(e)) return;
      e.preventDefault();
      e.stopPropagation();
      dropzoneDragDepth++;
      if (canAcceptDropOnUploadScreen()) {
        dropzone.classList.add('drag-active');
      }
    }, false);

    dropzone.addEventListener('dragover', (e) => {
      if (!hasDragFiles(e)) return;
      e.preventDefault();
      e.stopPropagation();
      if (e.dataTransfer) {
        e.dataTransfer.dropEffect = canAcceptDropOnUploadScreen() ? 'copy' : 'none';
      }
      if (canAcceptDropOnUploadScreen()) {
        dropzone.classList.add('drag-active');
      }
    }, false);

    dropzone.addEventListener('dragleave', (e) => {
      if (!hasDragFiles(e)) return;
      e.preventDefault();
      e.stopPropagation();
      dropzoneDragDepth = Math.max(0, dropzoneDragDepth - 1);
      if (dropzoneDragDepth === 0) {
        dropzone.classList.remove('drag-active');
      }
    }, false);

    dropzone.addEventListener('dragend', () => {
      dropzoneDragDepth = 0;
      dropzone.classList.remove('drag-active');
    }, false);

    dropzone.addEventListener('drop', (e) => {
      if (!hasDragFiles(e)) return;
      e.preventDefault();
      e.stopPropagation();
      dropzoneDragDepth = 0;
      dropzone.classList.remove('drag-active');
      if (!canAcceptDropOnUploadScreen()) return;
      const dt = e.dataTransfer;
      if (dt && dt.files && dt.files.length > 0) {
        dispatchMediaFile(dt.files[0]);
      }
    }, false);
  }

  // Prevent browser from navigating away on dropped files; only accept drops on active upload screen
  window.addEventListener('dragover', (e) => {
    if (!hasDragFiles(e)) return;
    e.preventDefault();
    if (e.dataTransfer) {
      e.dataTransfer.dropEffect = canAcceptDropOnUploadScreen() ? 'copy' : 'none';
    }
  }, false);

  window.addEventListener('drop', (e) => {
    if (!hasDragFiles(e)) return;
    e.preventDefault();
    dropzoneDragDepth = 0;
    if (dropzone) dropzone.classList.remove('drag-active');
    if (!canAcceptDropOnUploadScreen()) return;
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      dispatchMediaFile(dt.files[0]);
    }
  }, false);

  function handleFileSelected(e) {
    if (e && e.target && e.target.files && e.target.files.length > 0) {
      dispatchMediaFile(e.target.files[0]);
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
    currentProcessingProgress = pct / 100;
    var fillEl = document.getElementById('progress-fill');
    var pctBadge = document.getElementById('progress-pct-badge');
    var etaText = document.getElementById('progress-eta-text');
    var speedText = document.getElementById('progress-speed-text');
    var posText = document.getElementById('progress-position-text');
    var elapsedText = document.getElementById('progress-elapsed-text');
    var titleEl = document.getElementById('processing-main-title');
    var subEl = document.getElementById('processing-status-text');

    if (fillEl) {
      fillEl.style.setProperty('--progress-ratio', String(pct / 100));
      fillEl.setAttribute('aria-valuenow', String(Math.round(pct)));
    }
    if (pctBadge) pctBadge.innerText = Math.round(pct) + '%';

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
        if (speedItem) speedItem.classList.remove('is-empty');
      } else {
        speedText.innerText = '';
        if (speedItem) speedItem.classList.add('is-empty');
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
  /* TRANSCRIBE STAGE CROSSFADE CONTROLLER                     */
  /* ========================================================= */
  function showTranscribeStage(stage) {
    const dropzoneEl = document.getElementById('dropzone');
    const procEl = document.getElementById('processing-card');
    const outEl = document.getElementById('output-viewport');
    const map = { dropzone: dropzoneEl, processing: procEl, output: outEl };
    activeTranscribeStage = stage;

    Object.keys(map).forEach(function(key) {
      const el = map[key];
      if (!el || key === stage) return;
      el.classList.remove('stage-entering', 'stage-visible');
      el.style.display = 'none';
    });

    const target = map[stage];
    if (!target) return;
    // Keep #dropzone's 2-column CSS grid intact by clearing inline display rather than 'block'
    target.style.display = (stage === 'dropzone') ? '' : 'block';
    if (prefersReducedMotion()) {
      target.classList.remove('stage-entering');
      target.classList.add('stage-visible');
      return;
    }
    target.classList.remove('stage-visible');
    target.classList.add('stage-entering');
    void target.offsetWidth;
    requestAnimationFrame(function() {
      if (activeTranscribeStage !== stage) return;
      requestAnimationFrame(function() {
        if (activeTranscribeStage !== stage) return;
        target.classList.remove('stage-entering');
        target.classList.add('stage-visible');
      });
    });
  }

  /* ========================================================= */
  /* ACTIVE JOB CANCELLATION & ABORT CONTROLLERS               */
  /* ========================================================= */
  var activeProcessAbortController = null;
  var activeVoiceAbortController = null;

  async function cancelActiveProcessing(e) {
    if (e && e.preventDefault) e.preventDefault();
    activeTranscribeJobToken++;
    activeWaveformJobId++;
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

  async function executeTranscribeJob(opts) {
    activeWaveformJobId++;
    activeTranscribeJobToken++;
    const jobId = activeWaveformJobId;
    const jobToken = activeTranscribeJobToken;

    currentResult = null;
    window.currentResult = null;
    window.renderedSegments = [];
    currentProcessingProgress = 0;

    showTranscribeStage('processing');
    startLiquidOrbAnimation();
    startLiveProgressTracker();
    setTranscribeModelLocked(true);
    setNavProcessingState('transcribe', true);

    if (loadedMediaUrl && loadedMediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(loadedMediaUrl);
    }
    loadedMediaName = opts.fileName || '';
    const fileExt = (opts.fileName || '').split('.').pop().toLowerCase();
    const isDirectAudio = BROWSER_PLAYABLE_EXTS.includes(fileExt);
    if (isDirectAudio && opts.mediaSrc) {
      loadAudioForPlayback(opts.mediaSrc);
      if (opts.rawFile) {
        decodeAudioFileForWaveform(opts.rawFile, jobId);
      }
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
      const res = await fetch('/api/process', opts.buildFetchInit(activeProcessAbortController.signal));
      const data = await parseJsonResponse(res);
      activeProcessAbortController = null;
      stopLiveProgressTracker();

      if (jobToken !== activeTranscribeJobToken) {
        stopLiquidOrbAnimation();
        return;
      }

      if (data.cancelled) {
        stopLiquidOrbAnimation();
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      if (data.error) {
        stopLiquidOrbAnimation();
        showToast('Processing error: ' + data.error, 'error');
        setNavProcessingState('transcribe', false);
        resetToUpload();
        setTranscribeModelLocked(false);
        return;
      }

      currentProcessingProgress = 1;
      updateProgressUI({
        percent: 100,
        phase: 'Step 4 of 4 · Complete',
        title: 'Transcription & Translation Complete',
        subtitle: 'Transcription segments prepared for review',
        eta_sec: 0
      });

      const beatMs = prefersReducedMotion() ? 0 : 260;
      if (beatMs > 0) {
        await new Promise(function(resolve) { setTimeout(resolve, beatMs); });
      }
      if (jobToken !== activeTranscribeJobToken) {
        stopLiquidOrbAnimation();
        return;
      }

      stopLiquidOrbAnimation();
      currentResult = data;
      window.currentResult = data;
      showToast('Transcription & Translation complete! Ready for review.', 'success');
      renderTranscription(data);
      setTranscribeModelLocked(false);
      setNavProcessingState('transcribe', false);
    } catch (err) {
      activeProcessAbortController = null;
      stopLiveProgressTracker();
      stopLiquidOrbAnimation();
      setNavProcessingState('transcribe', false);
      if (err && err.name === 'AbortError') {
        return;
      }
      showToast('Processing error: ' + (err && err.message ? err.message : err), 'error');
      resetToUpload();
      setTranscribeModelLocked(false);
    }
  }

  async function startProcessingPath(filePath, options) {
    if (!filePath) return;
    const fileName = filePath.split(/[\\/]/).pop() || filePath;
    const maxDuration = (options && options.max_duration) || (typeof options === 'number' ? options : null);
    await executeTranscribeJob({
      fileName: fileName,
      mediaSrc: '/api/media?path=' + encodeURIComponent(filePath),
      rawFile: null,
      buildFetchInit: function(signal) {
        return {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: signal,
          body: JSON.stringify({
            file_path: filePath,
            task: 'translate',
            language: 'auto',
            model: selectedTranscribeModel || 'turbo',
            max_duration: maxDuration
          })
        };
      }
    });
  }

  async function startProcessing(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('task', 'translate');
    formData.append('language', 'auto');
    formData.append('model', selectedTranscribeModel || 'turbo');
    await executeTranscribeJob({
      fileName: file.name || '',
      mediaSrc: URL.createObjectURL(file),
      rawFile: file,
      buildFetchInit: function(signal) {
        return {
          method: 'POST',
          signal: signal,
          body: formData
        };
      }
    });
  }

  function resetToUpload() {
    activeTranscribeJobToken++;
    activeWaveformJobId++;
    setNavProcessingState('transcribe', false);
    if (activeProcessAbortController) {
      activeProcessAbortController.abort();
      activeProcessAbortController = null;
    }
    stopLiveProgressTracker();
    stopLiquidOrbAnimation();
    stopWaveAnimation();
    if (typeof stopTranscriptTracking === 'function') stopTranscriptTracking();
    if (typeof stopModePreview === 'function') stopModePreview('m1');
    if (typeof liveAuditionDebounce !== 'undefined' && liveAuditionDebounce) {
      clearTimeout(liveAuditionDebounce);
      liveAuditionDebounce = null;
    }
    if (typeof auditionStopTimer !== 'undefined' && auditionStopTimer) {
      clearTimeout(auditionStopTimer);
      auditionStopTimer = null;
    }
    setTranscribeModelLocked(false);

    if (loadedMediaUrl && loadedMediaUrl.startsWith('blob:')) {
      URL.revokeObjectURL(loadedMediaUrl);
    }
    loadedMediaUrl = null;
    loadedMediaName = '';
    currentResult = null;
    window.currentResult = null;
    window.renderedSegments = [];
    waveEnvelope = null;
    realAudioBuffer = null;
    currentProcessingProgress = 0;

    if (typeof cachedActiveSegIdx !== 'undefined') cachedActiveSegIdx = -1;
    if (typeof cachedActiveWordEl !== 'undefined') cachedActiveWordEl = null;
    if (typeof cachedTimecodeStr !== 'undefined') cachedTimecodeStr = '';
    if (typeof cachedWaveProgressPct !== 'undefined') cachedWaveProgressPct = -1;

    const syntheticWarning = document.getElementById('synthetic-warning');
    if (syntheticWarning) syntheticWarning.style.display = 'none';

    const player = document.getElementById('audio-player');
    if (player) {
      player.pause();
      player.currentTime = 0;
      player.removeAttribute('src');
      player.load();
      player.playbackRate = 1;
      player.preservesPitch = true;
    }
    savedSpeedRate = 1;
    selectedPlaybackRate = 1;
    document.querySelectorAll('.btn-speed').forEach(function(b) {
      const isDefault = (b.textContent || '').trim() === '1x';
      b.classList.toggle('active', isDefault);
      b.setAttribute('aria-pressed', isDefault ? 'true' : 'false');
    });

    if (typeof studioGainNodes !== 'undefined' && studioGainNodes.m1) {
      try {
        if (typeof studioAudioCtx !== 'undefined' && studioAudioCtx) {
          studioGainNodes.m1.gain.setValueAtTime(1.0, studioAudioCtx.currentTime);
        } else {
          studioGainNodes.m1.gain.value = 1.0;
        }
      } catch (e) {}
    }

    if (typeof resetModeEditorState === 'function') {
      resetModeEditorState('m1');
    }

    const searchInput = document.getElementById('transcript-search');
    if (searchInput) searchInput.value = '';
    const searchBadge = document.getElementById('search-count-badge');
    if (searchBadge) {
      searchBadge.style.display = 'none';
      searchBadge.innerText = '0';
    }
    const transcriptCont = document.getElementById('transcript-container');
    if (transcriptCont) transcriptCont.innerHTML = '';
    const tcEl = document.getElementById('live-timecode');
    if (tcEl) tcEl.innerText = '00:00 / 00:00';
    const wcEl = document.getElementById('live-word-count');
    if (wcEl) wcEl.innerText = '0';
    const mediaInput = document.getElementById('media-file-input');
    if (mediaInput) mediaInput.value = '';

    updatePlayPauseIcons(false);
    if (typeof closeExportDropdown === 'function') closeExportDropdown(false);
    if (typeof toggleAudioToolsDrawer === 'function') {
      toggleAudioToolsDrawer(false, false);
    }

    showTranscribeStage('dropzone');
  }

  /* Audio Transport Controls & Reliable Native Event Management */
  /* Waveform Animation Loop Scheduler (Prevents duplicate RAF pileups) */
  var waveAnimId = null;
  var transcriptTrackInterval = null;
  var cachedActiveSegIdx = -1;
  var cachedActiveWordEl = null;
  var cachedTimecodeStr = '';
  var cachedWaveProgressPct = -1;

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

  function startTranscriptTracking() {
    if (transcriptTrackInterval) return;
    transcriptTrackInterval = setInterval(function() {
      const player = document.getElementById('audio-player');
      if (!player || player.paused || document.hidden) return;
      handleAudioTimeUpdate();
    }, 90);
  }

  function stopTranscriptTracking() {
    if (transcriptTrackInterval) {
      clearInterval(transcriptTrackInterval);
      transcriptTrackInterval = null;
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
      startTranscriptTracking();
    });

    player.addEventListener('playing', function() {
      if (typeof initAudioVisualizer === 'function') initAudioVisualizer(player);
      updatePlayPauseIcons(true);
      scheduleWaveAnimation();
      startTranscriptTracking();
    });

    player.addEventListener('pause', function() {
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      stopTranscriptTracking();
      drawWave();
    });

    player.addEventListener('ended', function() {
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      stopTranscriptTracking();
      handleAudioEnded();
      drawWave();
    });

    player.addEventListener('timeupdate', function() {
      handleAudioTimeUpdate();
      if (prefersReducedMotion()) drawWave();
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
      stopWaveAnimation();
      stopTranscriptTracking();
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

    if (typeof auditionStopTimer !== 'undefined' && auditionStopTimer) {
      clearTimeout(auditionStopTimer);
      auditionStopTimer = null;
    }
    if (typeof audioEditorState !== 'undefined' && audioEditorState.m1) {
      audioEditorState.m1.isAuditioning = false;
    }

    if (typeof initAudioVisualizer === 'function') {
      initAudioVisualizer(player);
    }
    if (typeof studioAudioCtx !== 'undefined' && studioAudioCtx && studioAudioCtx.state === 'suspended') {
      studioAudioCtx.resume().catch(() => {});
    }
    if (typeof audioContext !== 'undefined' && audioContext && audioContext.state === 'suspended') {
      audioContext.resume().catch(() => {});
    }

    // Preserve intentional volume (including 0); only normalize NaN
    player.muted = false;
    if (isNaN(player.volume)) {
      player.volume = 1.0;
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
          startTranscriptTracking();
        }).catch((err) => {
          console.warn('Audio playback error:', err);
          updatePlayPauseIcons(false);
          stopWaveAnimation();
          stopTranscriptTracking();
          if (err && err.name === 'NotAllowedError') {
            showToast('Click anywhere on the window to enable audio playback', 'info');
          }
        });
      }
    } else {
      player.pause();
      updatePlayPauseIcons(false);
      stopWaveAnimation();
      stopTranscriptTracking();
      drawWave();
    }
  }

  function updatePlayPauseIcons(isPlaying) {
    const btn = document.getElementById('btn-master-play');
    if (btn) {
      btn.setAttribute('aria-label', isPlaying ? 'Pause audio' : 'Play audio');
      btn.setAttribute('aria-pressed', isPlaying ? 'true' : 'false');
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
    savedSpeedRate = rate;
    selectedPlaybackRate = rate;
    const player = document.getElementById('audio-player');
    if (player && (!audioEditorState.m1 || audioEditorState.m1.pitch === 0)) {
      player.preservesPitch = true;
      player.playbackRate = rate;
    }
    document.querySelectorAll('.btn-speed').forEach(function(b) {
      const isMatch = (b === btn);
      b.classList.toggle('active', isMatch);
      b.setAttribute('aria-pressed', isMatch ? 'true' : 'false');
    });
  }

  function handleAudioEnded() {
    updatePlayPauseIcons(false);
    stopTranscriptTracking();
  }

  /* Gated Keyboard Shortcuts & Escape Choreography */
  function isTranscribeOutputActive() {
    const tv = document.getElementById('transcribe-view');
    const out = document.getElementById('output-viewport');
    return !!(tv && tv.classList.contains('active') && out && out.style.display !== 'none' && out.offsetParent !== null);
  }

  function isTranscribeProcessingActive() {
    const tv = document.getElementById('transcribe-view');
    const proc = document.getElementById('processing-card');
    return !!(tv && tv.classList.contains('active') && proc && proc.style.display !== 'none' && proc.offsetParent !== null);
  }

  window.addEventListener('keydown', function(e) {
    const target = e.target;

    if (e.key === 'Escape') {
      const openModelMenus = document.querySelectorAll('.model-dropdown-menu.open');
      if (openModelMenus.length > 0) {
        e.preventDefault();
        closeAllModelDropdowns(true);
        return;
      }
      const exportMenu = document.getElementById('export-menu');
      if (exportMenu && exportMenu.classList.contains('open')) {
        e.preventDefault();
        closeExportDropdown(true);
        return;
      }
      if (isAudioToolsDrawerOpen) {
        e.preventDefault();
        toggleAudioToolsDrawer(false, true);
        return;
      }
      const searchInput = document.getElementById('transcript-search');
      if (searchInput && searchInput.value.trim() !== '' && (target === searchInput || isTranscribeOutputActive())) {
        e.preventDefault();
        clearTranscriptSearch(target === searchInput);
        return;
      }
      if (isTranscribeProcessingActive()) {
        e.preventDefault();
        cancelActiveProcessing();
        return;
      }
      return;
    }

    if (!isTranscribeOutputActive()) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    const blockedTag = target && (
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.tagName === 'SELECT' ||
      target.tagName === 'BUTTON' ||
      target.tagName === 'SUMMARY' ||
      target.tagName === 'A' ||
      target.tagName === 'AUDIO' ||
      target.isContentEditable ||
      (target.getAttribute && ['option', 'menuitem', 'slider'].includes(target.getAttribute('role'))) ||
      (target.classList && target.classList.contains('segment-card'))
    );
    if (blockedTag || (target && target.closest && target.closest('input, textarea, select, button, summary, a, audio, [role="option"], [role="menuitem"], [role="button"], [role="slider"], .segment-card, [contenteditable="true"]'))) {
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
    }
  });

  /* Web Audio API Real Peak Extraction */
  function decodeAudioFileForWaveform(file, jobId) {
    try {
      if (!file) return;
      if (typeof jobId !== 'number') jobId = activeWaveformJobId;
      if (file.size && file.size > 25 * 1024 * 1024) {
        // Prevent browser out-of-memory crash on large files (> 25MB)
        return;
      }
      if (!window.AudioContext && !window.webkitAudioContext) return;
      var AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!audioContext) audioContext = new AudioCtx();
      var reader = new FileReader();
      reader.onload = function(ev) {
        if (jobId !== activeWaveformJobId) return;
        audioContext.decodeAudioData(ev.target.result, function(buffer) {
          if (jobId !== activeWaveformJobId) return;
          realAudioBuffer = buffer;
          computeRealWaveformPeaks(buffer, 64);
        }, function() {
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

  function getTranscribeMediaKey(data, fallbackName) {
    return (data && (data.session_id || data.media_url || data.video_source)) || fallbackName || ('job-' + activeTranscribeJobToken);
  }

  function buildWordSpansHtml(wordsArr, fallbackText, segStart, segEnd) {
    if (wordsArr && wordsArr.length > 0) {
      return wordsArr.map(function(w) {
        const wText = escapeHtml(w.word || '');
        const wStart = (Number(w.start) || 0).toFixed(2);
        const wEnd = (Number(w.end) || 0).toFixed(2);
        return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${wText}</span> `;
      }).join('');
    }
    const words = (fallbackText || '').trim().split(/\s+/).filter(Boolean);
    const sStart = Number(segStart) || 0;
    const segDur = Math.max(0.1, (Number(segEnd) || sStart) - sStart);
    const wordDur = segDur / Math.max(1, words.length);
    return words.map(function(w, wIdx) {
      const wStart = (sStart + (wIdx * wordDur)).toFixed(2);
      const wEnd = (sStart + ((wIdx + 1) * wordDur)).toFixed(2);
      return `<span class="word-token" data-start="${wStart}" data-end="${wEnd}" onclick="seekToWord(${wStart}, event)">${escapeHtml(w)}</span> `;
    }).join('');
  }

  /* Render Output Viewport */
  function renderTranscription(data) {
    currentResult = data;
    window.currentResult = data;
    cachedActiveSegIdx = -1;
    cachedActiveWordEl = null;
    cachedTimecodeStr = '';
    cachedWaveProgressPct = -1;

    // Real waveform envelope computed server-side from the exact PCM used for playback.
    if (Array.isArray(data.waveform_peaks) && data.waveform_peaks.length) {
      activeWaveformJobId++;
      waveEnvelope = data.waveform_peaks.map(function (v) {
        return Math.max(0.03, Math.min(1, Number(v) || 0));
      });
    } else {
      waveEnvelope = null;
    }
    updateSyntheticWarning(data);
    showTranscribeStage('output');

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

    if (cleanSegments.length === 0) {
      const emptyCard = document.createElement('div');
      emptyCard.className = 'empty-state-card';
      emptyCard.setAttribute('role', 'status');
      emptyCard.innerHTML = '<p>No speech segments were detected in this media file.</p>';
      container.appendChild(emptyCard);
    }

    cleanSegments.forEach((s, idx) => {
      let wordSpans = '';
      if (s.words && s.words.length > 0) {
        totalWords += s.words.length;
        wordSpans = buildWordSpansHtml(s.words, s.text, s.start, s.end);
      } else {
        const words = (s.text || '').trim().split(/\s+/).filter(Boolean);
        totalWords += words.length;
        wordSpans = buildWordSpansHtml([], s.text, s.start, s.end);
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
            <button type="button" class="btn-seg-icon" onclick="copySegmentText(${idx}, event)" title="Copy segment text">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              Copy
            </button>
          </div>
        </div>
        <div class="seg-text" id="seg-text-${idx}" contenteditable="true" spellcheck="false" onmousedown="this.dataset.wasFocused=(document.activeElement===this)?'1':'0'" onblur="handleSegmentEdit(${idx}, this)" onclick="event.stopPropagation()">
          ${wordSpans}
        </div>
      `;
      container.appendChild(segCard);
      const segTextEl = segCard.querySelector('.seg-text');
      if (segTextEl) {
        segTextEl.dataset.origText = cleanExportText(segTextEl.innerText || segTextEl.textContent || s.text || '');
      }
    });

    if (cleanSegments.length > 0) {
      const emptySearch = document.createElement('div');
      emptySearch.id = 'transcript-empty-search';
      emptySearch.className = 'empty-state-card';
      emptySearch.style.display = 'none';
      emptySearch.setAttribute('role', 'status');
      emptySearch.innerHTML = '<p>No transcript segments match your search.</p><button type="button" class="btn-secondary" onclick="clearTranscriptSearch()">Clear Search</button>';
      container.appendChild(emptySearch);
    }

    const searchInput = document.getElementById('transcript-search');
    if (searchInput) {
      searchInput.value = '';
      filterTranscript();
    }

    const wordCountBadge = document.getElementById('live-word-count');
    if (wordCountBadge) wordCountBadge.innerText = totalWords;

    // Store transcribed profiles without clobbering Mode 2's active studio selection
    populateVoiceProfiles(data.voice_profiles || []);

    // Initialize Mode 1 Audio Editor with loaded audio duration & filename
    const durM1 = getAccurateDuration();
    const fileNameM1 = (data && data.video_source) || (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
    const mediaKeyM1 = getTranscribeMediaKey(data, fileNameM1);
    initModeAudioEditor('m1', durM1 > 0 ? durM1 : 10, fileNameM1, mediaKeyM1);

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
          initModeAudioEditor('m1', dur, fileNameM1, mediaKeyM1);
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
    var n = match ? parseInt(match[1], 10) : ((idx || 0) + 1);
    if (!isFinite(n) || n < 1) n = 1;
    return 'spk-theme-' + (((n - 1) % 4) + 1);
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
    if (btn && !btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }

    function showCopied() {
      if (btn) {
        if (btn._copyResetTimer) clearTimeout(btn._copyResetTimer);
        btn.innerHTML = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied to Clipboard!`;
        btn.classList.add('btn-copied');
        showToast('Full transcript copied to clipboard!', 'success');
        btn._copyResetTimer = setTimeout(() => {
          btn.innerHTML = btn.dataset.origHtml || '';
          btn.classList.remove('btn-copied');
          btn._copyResetTimer = null;
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
    if (btn && !btn.dataset.origHtml) {
      btn.dataset.origHtml = btn.innerHTML;
    }
    function showCopied() {
      if (btn) {
        if (btn._copyResetTimer) clearTimeout(btn._copyResetTimer);
        btn.innerHTML = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="#10B981" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!`;
        btn.style.color = '#10B981';
        showToast('Copied segment text!', 'success');
        btn._copyResetTimer = setTimeout(() => {
          btn.innerHTML = btn.dataset.origHtml || '';
          btn.style.color = '';
          btn._copyResetTimer = null;
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
    if (!el) return;
    const newText = cleanExportText(el.innerText || el.textContent || '');
    const origText = (el.dataset.origText !== undefined) ? el.dataset.origText : '';
    if (newText === origText) return;

    el.setAttribute('data-edited', 'true');
    el.dataset.origText = newText;

    const segObj = (window.renderedSegments && window.renderedSegments[idx]) ||
      (currentResult && currentResult.transcription && currentResult.transcription.segments && currentResult.transcription.segments[idx]);
    const sStart = segObj ? (Number(segObj.start) || 0) : 0;
    const sEnd = segObj ? Math.max(sStart + 0.1, Number(segObj.end) || sStart + 0.1) : 0.1;
    const wordsArr = newText ? newText.split(/\s+/).filter(Boolean) : [];
    const wordDur = (sEnd - sStart) / Math.max(1, wordsArr.length);
    const resyncedWords = wordsArr.map(function(w, wIdx) {
      return {
        word: w,
        start: Number((sStart + wIdx * wordDur).toFixed(2)),
        end: Number((sStart + (wIdx + 1) * wordDur).toFixed(2))
      };
    });

    if (window.renderedSegments && window.renderedSegments[idx]) {
      window.renderedSegments[idx].text = newText;
      window.renderedSegments[idx].words = resyncedWords;
    }
    if (currentResult && currentResult.transcription && currentResult.transcription.segments && currentResult.transcription.segments[idx]) {
      currentResult.transcription.segments[idx].text = newText;
      currentResult.transcription.segments[idx].words = resyncedWords;
      if (window.renderedSegments) {
        currentResult.transcription.text = window.renderedSegments.map(function(s, i) {
          return s.id === idx ? newText : getCleanSegmentText(s, i);
        }).filter(Boolean).join(' ');
      }
    }

    // Never rewrite DOM or steal caret while this .seg-text is focused
    if (document.activeElement !== el) {
      el.innerHTML = buildWordSpansHtml(resyncedWords, newText, sStart, sEnd);
      const card = el.closest('.segment-card');
      if (card) card._wordTokens = null;
      cachedActiveWordEl = null;
    }

    // Recalculate live word count across all rendered segments
    if (window.renderedSegments) {
      let totalWords = 0;
      window.renderedSegments.forEach(function(seg) {
        if (seg.words && seg.words.length > 0) {
          totalWords += seg.words.length;
        } else if (seg.text) {
          totalWords += seg.text.trim().split(/\s+/).filter(Boolean).length;
        }
      });
      const wordCountBadge = document.getElementById('live-word-count');
      if (wordCountBadge) wordCountBadge.innerText = totalWords;
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
          startTranscriptTracking();
        }).catch((err) => {
          console.warn('seekTo play() deferred or blocked:', err);
          updatePlayPauseIcons(false);
          stopWaveAnimation();
          stopTranscriptTracking();
        });
      }
    }
  }

  function seekToWord(sec, evt) {
    if (evt) {
      evt.stopPropagation();
      const target = evt.target;
      const segText = target && target.closest ? target.closest('.seg-text') : null;
      const sel = window.getSelection ? window.getSelection() : null;
      if (sel && !sel.isCollapsed) return;
      if (segText && segText.dataset.wasFocused === '1') return;
    }
    seekTo(sec);
  }

  function handleAudioTimeUpdate() {
    const player = document.getElementById('audio-player');
    if (!player) return;
    const ct = (player && isFinite(player.currentTime)) ? player.currentTime : 0;
    const dur = getAccurateDuration() || (player && player.duration) || 1.0;

    const nextTc = formatSec(ct) + ' / ' + formatSec(dur);
    if (nextTc !== cachedTimecodeStr) {
      cachedTimecodeStr = nextTc;
      const timecodeElem = document.getElementById('live-timecode');
      if (timecodeElem) timecodeElem.innerText = nextTc;
    }

    const pct = dur > 0 ? Math.max(0, Math.min(100, Math.round((ct / dur) * 100))) : 0;
    if (pct !== cachedWaveProgressPct) {
      cachedWaveProgressPct = pct;
      const wrap = document.getElementById('waveform-wrap');
      if (wrap) {
        wrap.setAttribute('aria-valuenow', String(pct));
        wrap.setAttribute('aria-valuetext', nextTc);
      }
    }

    const segments = window.renderedSegments || (currentResult && currentResult.transcription && currentResult.transcription.segments) || [];
    if (!segments.length) return;

    let nextSegIdx = -1;
    if (cachedActiveSegIdx >= 0 && cachedActiveSegIdx < segments.length) {
      const cs = segments[cachedActiveSegIdx];
      if (ct >= (cs.start - 0.05) && ct <= (cs.end + 0.1)) {
        nextSegIdx = cachedActiveSegIdx;
      }
    }
    if (nextSegIdx === -1) {
      for (let idx = 0; idx < segments.length; idx++) {
        const s = segments[idx];
        if (ct >= (s.start - 0.05) && ct <= (s.end + 0.1)) {
          nextSegIdx = idx;
          break;
        }
      }
    }

    if (nextSegIdx !== cachedActiveSegIdx) {
      if (cachedActiveSegIdx >= 0) {
        const prevCard = document.getElementById('seg-' + cachedActiveSegIdx);
        if (prevCard) prevCard.classList.remove('active-seg');
      }
      if (cachedActiveWordEl) {
        cachedActiveWordEl.classList.remove('active-word');
        cachedActiveWordEl = null;
      }
      cachedActiveSegIdx = nextSegIdx;
      if (nextSegIdx >= 0) {
        const nextCard = document.getElementById('seg-' + nextSegIdx);
        if (nextCard) {
          nextCard.classList.add('active-seg');
          const activeEl = document.activeElement;
          const isEditingSeg = !!(activeEl && activeEl.classList && activeEl.classList.contains('seg-text'));
          const drawerEl = document.getElementById('audio-tools-drawer');
          const isDrawerOpen = !!(isAudioToolsDrawerOpen || (drawerEl && drawerEl.classList.contains('is-open')));
          if (!isEditingSeg && !isDrawerOpen) {
            nextCard.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'nearest' });
          }
        }
      }
    }

    if (nextSegIdx >= 0) {
      const activeCard = document.getElementById('seg-' + nextSegIdx);
      if (activeCard) {
        const wordTokens = activeCard._wordTokens || (activeCard._wordTokens = activeCard.querySelectorAll('.word-token'));
        let nextWordEl = null;
        for (let wIdx = 0; wIdx < wordTokens.length; wIdx++) {
          const w = wordTokens[wIdx];
          const wStart = parseFloat(w.getAttribute('data-start'));
          const wEnd = parseFloat(w.getAttribute('data-end'));
          if (ct >= (wStart - 0.05) && ct <= (wEnd + 0.05)) {
            nextWordEl = w;
            break;
          }
        }
        if (nextWordEl !== cachedActiveWordEl) {
          if (cachedActiveWordEl) cachedActiveWordEl.classList.remove('active-word');
          if (nextWordEl) nextWordEl.classList.add('active-word');
          cachedActiveWordEl = nextWordEl;
        }
      }
    }
  }

  /* Live Keyword Search with Highlights */
  function filterTranscript() {
    const searchInput = document.getElementById('transcript-search');
    const q = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const countBadge = document.getElementById('search-count-badge');
    const cards = document.querySelectorAll('.segment-card');
    let totalMatches = 0;
    let visibleCards = 0;

    cards.forEach(card => {
      const segTextElem = card.querySelector('.seg-text');
      if (!segTextElem) return;
      const fullText = (segTextElem.innerText || segTextElem.textContent || '').toLowerCase();

      if (!q) {
        card.style.display = 'block';
        visibleCards++;
        card.querySelectorAll('.word-token').forEach(w => w.classList.remove('search-match'));
        return;
      }

      const matches = fullText.includes(q);
      card.style.display = matches ? 'block' : 'none';
      if (matches) visibleCards++;

      const tokens = card.querySelectorAll('.word-token');
      if (tokens.length > 0) {
        tokens.forEach(w => {
          const wt = (w.innerText || w.textContent || '').toLowerCase();
          if (wt.includes(q)) {
            w.classList.add('search-match');
            totalMatches++;
          } else {
            w.classList.remove('search-match');
          }
        });
      } else if (matches) {
        totalMatches++;
      }
    });

    const emptySearchEl = document.getElementById('transcript-empty-search');
    if (emptySearchEl) {
      emptySearchEl.style.display = (cards.length > 0 && q && visibleCards === 0) ? 'block' : 'none';
    }

    if (countBadge) {
      if (q) {
        countBadge.style.display = 'block';
        countBadge.innerText = `${totalMatches} match${totalMatches === 1 ? '' : 'es'}`;
      } else {
        countBadge.style.display = 'none';
      }
    }
  }

  function clearTranscriptSearch(keepFocus) {
    const s = document.getElementById('transcript-search');
    if (s) {
      s.value = '';
      filterTranscript();
      if (keepFocus) s.focus();
    }
  }
  window.clearTranscriptSearch = clearTranscriptSearch;

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
      md += `> Duration: ${formatSec(dur)} | Processed by Scriber Local Studio\n\n`;
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

  function toggleAudioToolsDrawer(forceState, restoreFocus) {
    var drawer = document.getElementById('audio-tools-drawer');
    var btn = document.getElementById('btn-audio-tools') || document.getElementById('audio-tools-toggle');
    if (!drawer) return;
    var nextOpen = (typeof forceState === 'boolean') ? forceState : !isAudioToolsDrawerOpen;
    var wasOpen = isAudioToolsDrawerOpen || drawer.classList.contains('is-open');
    var wasFocusInside = !nextOpen && drawer.contains(document.activeElement);
    isAudioToolsDrawerOpen = nextOpen;

    if (btn) {
      btn.classList.toggle('active', nextOpen);
      btn.setAttribute('aria-expanded', nextOpen ? 'true' : 'false');
    }

    if (nextOpen) {
      openAnimatedPanel(drawer, 'is-open', '');
      if (currentResult) {
        var dur = getAccurateDuration();
        var fName = (currentResult && currentResult.video_source) || 'transcribed_media.mp3';
        var mediaKey = getTranscribeMediaKey(currentResult, fName);
        initModeAudioEditor('m1', dur > 0 ? dur : 10, fName, mediaKey);
      }
    } else {
      if (wasOpen || drawer.style.display !== 'none') {
        closeAnimatedPanel(drawer, 'is-open', 360);
      } else {
        drawer.classList.remove('is-open');
        drawer.style.display = 'none';
      }
      if (restoreFocus !== false && wasFocusInside && btn) {
        btn.focus();
      }
    }
  }
  window.toggleAudioToolsDrawer = toggleAudioToolsDrawer;

  /* ========================================================= */
  /* CONSOLIDATED EXPORT DROPDOWN MENU CONTROLLER              */
  /* ========================================================= */
  function openExportDropdown(focusFirst) {
    var menu = document.getElementById('export-menu');
    var trigger = document.getElementById('export-dropdown-trigger');
    var wrapper = document.getElementById('export-dropdown-wrapper');
    if (!menu) return;
    openAnimatedPanel(menu, 'open', 'block');
    if (wrapper) wrapper.classList.add('open');
    if (trigger) trigger.setAttribute('aria-expanded', 'true');
    if (focusFirst) {
      var firstItem = menu.querySelector('.export-menu-item[role="menuitem"]');
      if (firstItem) {
        requestAnimationFrame(function() { firstItem.focus(); });
      }
    }
  }

  function closeExportDropdown(restoreFocus) {
    var menu = document.getElementById('export-menu');
    var trigger = document.getElementById('export-dropdown-trigger');
    var wrapper = document.getElementById('export-dropdown-wrapper');
    if (!menu) return;
    var wasFocusInside = menu.contains(document.activeElement);
    var wasOpen = menu.classList.contains('open') || menu.style.display !== 'none';
    if (wrapper) wrapper.classList.remove('open');
    if (trigger) trigger.setAttribute('aria-expanded', 'false');
    if (wasOpen) {
      closeAnimatedPanel(menu, 'open', 260);
    } else {
      menu.classList.remove('open');
      menu.style.display = 'none';
    }
    if (restoreFocus && wasFocusInside && trigger) {
      trigger.focus();
    }
  }

  function toggleExportDropdown(e) {
    if (e && e.stopPropagation) e.stopPropagation();
    var menu = document.getElementById('export-menu');
    if (!menu) return;
    var isOpen = menu.classList.contains('open');
    if (isOpen) {
      closeExportDropdown(false);
    } else {
      closeAllModelDropdowns(false);
      var isKeyboardOpen = !!(e && e.detail === 0);
      openExportDropdown(isKeyboardOpen);
    }
  }

  function handleExportSelect(type) {
    var menu = document.getElementById('export-menu');
    var viaKeyboard = !!(menu && menu.contains(document.activeElement));
    closeExportDropdown(viaKeyboard);
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
    if (menu && menu.classList.contains('open')) {
      if (!menu.contains(e.target) && (!trigger || !trigger.contains(e.target))) {
        closeExportDropdown(false);
      }
    }
  });

  function initDropdownKeyboardNavigation() {
    var exportTrigger = document.getElementById('export-dropdown-trigger');
    var exportMenu = document.getElementById('export-menu');
    if (exportTrigger && !exportTrigger.__keyNavBound) {
      exportTrigger.__keyNavBound = true;
      exportTrigger.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          closeAllModelDropdowns(false);
          openExportDropdown(true);
        }
      });
    }
    if (exportMenu && !exportMenu.__keyNavBound) {
      exportMenu.__keyNavBound = true;
      exportMenu.addEventListener('keydown', function(e) {
        var items = Array.from(exportMenu.querySelectorAll('.export-menu-item[role="menuitem"]'));
        if (!items.length) return;
        var idx = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          items[(idx + 1) % items.length].focus();
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          items[(idx - 1 + items.length) % items.length].focus();
        } else if (e.key === 'Home') {
          e.preventDefault();
          items[0].focus();
        } else if (e.key === 'End') {
          e.preventDefault();
          items[items.length - 1].focus();
        } else if (e.key === 'Tab') {
          closeExportDropdown(false);
        }
      });
    }

    document.querySelectorAll('.custom-model-dropdown').forEach(function(dropdown) {
      var trigger = dropdown.querySelector('.model-dropdown-trigger');
      var menu = dropdown.querySelector('.model-dropdown-menu');
      if (!trigger || !menu || menu.__keyNavBound) return;
      menu.__keyNavBound = true;

      trigger.addEventListener('keydown', function(e) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
          e.preventDefault();
          if (!menu.classList.contains('open')) {
            toggleModelDropdown(menu.id, e);
          } else {
            var active = menu.querySelector('.dropdown-item.active[role="option"]') || menu.querySelector('.dropdown-item[role="option"]');
            if (active) active.focus();
          }
        }
      });

      menu.addEventListener('keydown', function(e) {
        var items = Array.from(menu.querySelectorAll('.dropdown-item[role="option"]'));
        if (!items.length) return;
        var idx = items.indexOf(document.activeElement);
        var nextItem = null;
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          nextItem = items[(idx + 1) % items.length];
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          nextItem = items[(idx - 1 + items.length) % items.length];
        } else if (e.key === 'Home') {
          e.preventDefault();
          nextItem = items[0];
        } else if (e.key === 'End') {
          e.preventDefault();
          nextItem = items[items.length - 1];
        } else if (e.key === 'Tab') {
          closeAllModelDropdowns(false);
          return;
        }
        if (nextItem) {
          nextItem.focus();
          if (nextItem.id) menu.setAttribute('aria-activedescendant', nextItem.id);
        }
      });
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDropdownKeyboardNavigation);
  } else {
    initDropdownKeyboardNavigation();
  }

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
  var isTranscribeRunning = false;
  var isVoiceSynthesizing = false;
  var lastModelSelectAt = 0;

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
    closeAllModelDropdowns(false);
    if (!isAlreadyOpen) {
      menu.classList.add('open');
      if (trigger) {
        trigger.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
      }
      const focusItem = menu.querySelector('.dropdown-item.active[role="option"]') || menu.querySelector('.dropdown-item[role="option"]');
      if (focusItem) {
        if (focusItem.id) menu.setAttribute('aria-activedescendant', focusItem.id);
        if (event && (event.type === 'keydown' || event.detail === 0)) {
          requestAnimationFrame(function() { focusItem.focus(); });
        }
      }
    }
  }

  function setDropdownTriggerLocked(triggerId, locked) {
    const el = document.getElementById(triggerId);
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
  }

  function setTranscribeModelLocked(locked) {
    isTranscribeRunning = !!locked;
    setDropdownTriggerLocked('transcribe-dropdown-trigger', isTranscribeRunning);
    const copySelect = document.getElementById('copy-format-select');
    if (copySelect) copySelect.disabled = isTranscribeRunning;
    if (isTranscribeRunning) closeAllModelDropdowns(false);
  }

  function setVoiceModelLocked(locked) {
    isVoiceSynthesizing = !!locked;
    setDropdownTriggerLocked('voice-dropdown-trigger', isVoiceSynthesizing);
    if (isVoiceSynthesizing) closeAllModelDropdowns(false);
  }

  function closeAllModelDropdowns(restoreFocus) {
    let focusTargetTrigger = null;
    document.querySelectorAll('.model-dropdown-menu.open').forEach(function(el) {
      if (restoreFocus && el.contains(document.activeElement)) {
        const dropdown = el.closest('.custom-model-dropdown');
        focusTargetTrigger = dropdown ? dropdown.querySelector('.model-dropdown-trigger') : null;
      }
      el.classList.remove('open');
    });
    document.querySelectorAll('.model-dropdown-trigger.active').forEach(function(el) {
      el.classList.remove('active');
      el.setAttribute('aria-expanded', 'false');
    });
    if (focusTargetTrigger && !focusTargetTrigger.disabled) {
      focusTargetTrigger.focus();
    }
  }

  document.addEventListener('click', function(e) {
    if (!e.target.closest('.custom-model-dropdown')) {
      closeAllModelDropdowns(false);
    }
  });

  function selectTranscribeModel(modelId) {
    const trigger = document.getElementById('transcribe-dropdown-trigger');
    if (trigger && (trigger.disabled || trigger.classList.contains('locked') || trigger.getAttribute('aria-disabled') === 'true')) {
      return;
    }
    const now = Date.now();
    if (now - lastModelSelectAt < 200) return;
    lastModelSelectAt = now;

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

    const menu = document.getElementById('transcribe-dropdown-menu');
    const viaKeyboard = !!(menu && menu.contains(document.activeElement));
    closeAllModelDropdowns(viaKeyboard);
    showToast(`Switched transcription engine to ${names[modelId] || modelId}`, 'info');
  }

  function selectVoiceModel(modelId) {
    const trigger = document.getElementById('voice-dropdown-trigger');
    if (trigger && (trigger.disabled || trigger.classList.contains('locked') || trigger.getAttribute('aria-disabled') === 'true')) {
      return;
    }
    const now = Date.now();
    if (now - lastModelSelectAt < 200) return;
    lastModelSelectAt = now;

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

    const menu = document.getElementById('voice-dropdown-menu');
    const viaKeyboard = !!(menu && menu.contains(document.activeElement));
    closeAllModelDropdowns(viaKeyboard);
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
      isAuditioning: false,
      previewTimer: null,
      customFileName: null,
      mediaKey: null,
      userTrimmed: false,
    },
    m2: {
      volume: 100,
      pitch: 0,
      trimStart: 0,
      trimEnd: 0,
      totalDuration: 0,
      isPlayingPreview: false,
      isAuditioning: false,
      previewTimer: null,
      customFileName: null,
      mediaKey: null,
      userTrimmed: false,
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
  var auditionStopTimer = null;

  function triggerRealtimeAudition(mode, player) {
    if (!player || (!player.src && !player.currentSrc)) return;
    if (studioAudioCtx && studioAudioCtx.state === 'suspended') {
      studioAudioCtx.resume().catch(() => {});
    }
    const st = audioEditorState[mode];
    if (!st) return;

    const wasAlreadyPlaying = (mode === 'm1')
      ? isMasterPlaying()
      : !!(player && !player.paused && !player.ended);

    if (liveAuditionDebounce) {
      clearTimeout(liveAuditionDebounce);
      liveAuditionDebounce = null;
    }
    if (auditionStopTimer) {
      clearTimeout(auditionStopTimer);
      auditionStopTimer = null;
    }

    // If user is actively playing normally (not inside a transient 1.2s audition), DSP updates live
    if (wasAlreadyPlaying && !st.isAuditioning) return;

    liveAuditionDebounce = setTimeout(() => {
      liveAuditionDebounce = null;
      const startPos = (st && st.trimStart) ? st.trimStart : (player.currentTime || 0);
      try {
        if (!wasAlreadyPlaying && !st.isAuditioning) {
          player.currentTime = startPos;
        }
        st.isAuditioning = true;
        player.play().then(() => {
          if (auditionStopTimer) clearTimeout(auditionStopTimer);
          auditionStopTimer = setTimeout(() => {
            auditionStopTimer = null;
            st.isAuditioning = false;
            if (!st.isPlayingPreview) {
              player.pause();
            }
          }, 1200);
        }).catch(() => {
          st.isAuditioning = false;
        });
      } catch (e) {
        st.isAuditioning = false;
      }
    }, 90);
  }

  function isMasterPlaying() {
    const player = document.getElementById('audio-player');
    return !!(player && !player.paused && !player.ended);
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

  function syncEditorTrimDisplay(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    const startIn = document.getElementById(mode + '-trim-start');
    const endIn = document.getElementById(mode + '-trim-end');
    const durVal = document.getElementById(mode + '-trim-duration-val');
    const trimPill = document.getElementById(mode + '-trim-pill');

    if (startIn) startIn.value = formatSecPrecise(st.trimStart);
    if (endIn) endIn.value = formatSecPrecise(st.trimEnd);
    const curTrimDur = Math.max(0, st.trimEnd - st.trimStart);
    if (durVal) {
      durVal.innerText = st.userTrimmed
        ? ('Duration: ' + formatSecPrecise(curTrimDur))
        : ('Duration: ' + formatSec(st.totalDuration));
    }
    if (trimPill) {
      trimPill.innerText = st.userTrimmed
        ? (`Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`)
        : ('Trim: 00:00 - ' + formatSec(st.totalDuration));
      trimPill.classList.toggle('active', !!st.userTrimmed);
    }
    syncTrimBarsFromState(mode);
  }

  function resetModeEditorState(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.volume = 100;
    st.pitch = 0;
    st.trimStart = 0;
    st.trimEnd = 0;
    st.totalDuration = 0;
    st.isPlayingPreview = false;
    st.isAuditioning = false;
    st.customFileName = null;
    st.mediaKey = null;
    st.userTrimmed = false;
    if (st.previewTimer) {
      clearInterval(st.previewTimer);
      st.previewTimer = null;
    }

    const volSlider = document.getElementById(mode + '-vol-slider');
    if (volSlider) volSlider.value = 100;
    const volVal = document.getElementById(mode + '-vol-val');
    if (volVal) volVal.innerText = '100% (0.0 dB)';
    [50, 100, 130, 160, 200].forEach(p => {
      const btn = document.getElementById(mode + '-vol-preset-' + p);
      if (btn) {
        const isDef = (p === 100);
        btn.classList.toggle('active', isDef);
        btn.setAttribute('aria-pressed', isDef ? 'true' : 'false');
      }
    });

    const pitchSlider = document.getElementById(mode + '-pitch-slider');
    if (pitchSlider) pitchSlider.value = 0;
    const pitchVal = document.getElementById(mode + '-pitch-val');
    if (pitchVal) pitchVal.innerText = '0 st (Natural)';
    [-4, -2, 0, 2, 4].forEach(p => {
      const btn = document.getElementById(mode + '-pitch-preset-' + p);
      if (btn) {
        const isDef = (p === 0);
        btn.classList.toggle('active', isDef);
        btn.setAttribute('aria-pressed', isDef ? 'true' : 'false');
      }
    });

    const startIn = document.getElementById(mode + '-trim-start');
    const endIn = document.getElementById(mode + '-trim-end');
    const durVal = document.getElementById(mode + '-trim-duration-val');
    const sliderPill = document.getElementById(mode + '-trim-slider-pill');
    const sBar = document.getElementById(mode + '-trim-start-bar');
    const eBar = document.getElementById(mode + '-trim-end-bar');
    if (startIn) startIn.value = '00:00.00';
    if (endIn) endIn.value = '00:00.00';
    if (durVal) durVal.innerText = 'Full File';
    if (sliderPill) sliderPill.innerText = '00:00 - 00:00';
    if (sBar) sBar.value = 0;
    if (eBar) eBar.value = 100;
  }

  function initModeAudioEditor(mode, duration, filename, mediaKey) {
    const st = audioEditorState[mode];
    if (!st) return;
    const hasRealDuration = !!(duration && isFinite(duration) && duration > 0);
    const nextDur = hasRealDuration ? duration : 10;
    const nextKey = mediaKey || filename || (mode + ':default');

    if (st.mediaKey !== nextKey) {
      st.mediaKey = nextKey;
      st.totalDuration = nextDur;
      st.trimStart = 0;
      st.trimEnd = nextDur;
      st.userTrimmed = false;
      st.customFileName = filename || (mode === 'm1' ? 'scriber_audio.mp3' : 'scriber_voice.mp3');
    } else {
      if (filename) st.customFileName = filename;
      if (hasRealDuration && Math.abs(nextDur - st.totalDuration) > 0.05) {
        const prevDur = st.totalDuration;
        st.totalDuration = nextDur;
        if (!st.userTrimmed && st.trimStart === 0 && Math.abs(st.trimEnd - prevDur) < 0.25) {
          st.trimEnd = nextDur;
        } else {
          st.trimEnd = Math.min(nextDur, Math.max(0.1, st.trimEnd));
          st.trimStart = Math.min(st.trimStart, Math.max(0, st.trimEnd - 0.1));
        }
      }
    }

    syncEditorTrimDisplay(mode);
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
      if (btn) {
        const isMatch = (Math.round(st.volume) === p);
        btn.classList.toggle('active', isMatch);
        btn.setAttribute('aria-pressed', isMatch ? 'true' : 'false');
      }
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      const gainNode = getStudioGainNode(mode, player);
      if (gainNode) {
        gainNode.gain.setValueAtTime(st.volume / 100.0, studioAudioCtx ? studioAudioCtx.currentTime : 0);
        if (mode === 'm2') {
          player.volume = 1.0;
        }
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
      if (btn) {
        const isMatch = (st.pitch === p);
        btn.classList.toggle('active', isMatch);
        btn.setAttribute('aria-pressed', isMatch ? 'true' : 'false');
      }
    });

    const player = mode === 'm1' ? document.getElementById('audio-player') : (document.getElementById('clone-audio-player') || st.audioElement);
    if (player) {
      if (st.pitch === 0) {
        player.preservesPitch = true;
        player.playbackRate = (mode === 'm1') ? savedSpeedRate : 1.0;
      } else {
        player.preservesPitch = false;
        const rate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));
        player.playbackRate = rate;
      }
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
    st.userTrimmed = true;

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

    if (mode === 'm1' && typeof drawWave === 'function') {
      drawWave();
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
    st.userTrimmed = true;

    if (type === 'start') {
      st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, ct));
      if (st.trimStart >= st.trimEnd && st.totalDuration > 0) {
        st.trimEnd = Math.min(st.totalDuration, st.trimStart + 1.0);
        const endEl = document.getElementById(mode + '-trim-end');
        if (endEl) endEl.value = formatSecPrecise(st.trimEnd);
      }
      const el = document.getElementById(mode + '-trim-start');
      if (el) el.value = formatSecPrecise(st.trimStart);
      showToast(`Set Trim Start to ${formatSecPrecise(st.trimStart)}`, 'info');
    } else {
      st.trimEnd = Math.max(0.1, Math.min(st.totalDuration || 10, ct));
      if (st.trimEnd <= st.trimStart) {
        st.trimStart = Math.max(0, st.trimEnd - 0.1);
        const startEl = document.getElementById(mode + '-trim-start');
        if (startEl) startEl.value = formatSecPrecise(st.trimStart);
      }
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
    if (mode === 'm1' && typeof drawWave === 'function') {
      drawWave();
    }
  }

  function updateTrimFromText(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.userTrimmed = true;
    const startInput = document.getElementById(mode + '-trim-start');
    const endInput = document.getElementById(mode + '-trim-end');
    const sVal = parseSec(startInput ? startInput.value : 0);
    const eVal = parseSec(endInput ? endInput.value : st.totalDuration);
    st.trimStart = Math.max(0, Math.min(st.totalDuration || 10, sVal));
    st.trimEnd = Math.max(st.trimStart + 0.1, Math.min(st.totalDuration || 10, eVal || st.totalDuration));

    if (startInput) startInput.value = formatSecPrecise(st.trimStart);
    if (endInput) endInput.value = formatSecPrecise(st.trimEnd);
    const dur = Math.max(0, st.trimEnd - st.trimStart);
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (durVal) durVal.innerText = 'Duration: ' + formatSecPrecise(dur);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = `Trim: ${formatSec(st.trimStart)} - ${formatSec(st.trimEnd)}`;
      trimPill.classList.add('active');
    }
    syncTrimBarsFromState(mode);
    if (mode === 'm1' && typeof drawWave === 'function') {
      drawWave();
    }
  }

  function resetTrimRange(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    st.trimStart = 0;
    st.trimEnd = st.totalDuration || 10;
    st.userTrimmed = false;
    const startInput = document.getElementById(mode + '-trim-start');
    const endInput = document.getElementById(mode + '-trim-end');
    const durVal = document.getElementById(mode + '-trim-duration-val');
    if (startInput) startInput.value = '00:00.00';
    if (endInput) endInput.value = formatSecPrecise(st.totalDuration);
    if (durVal) durVal.innerText = 'Duration: ' + formatSec(st.totalDuration);
    const trimPill = document.getElementById(mode + '-trim-pill');
    if (trimPill) {
      trimPill.innerText = 'Trim: Full Length';
      trimPill.classList.remove('active');
    }
    syncTrimBarsFromState(mode);
    if (mode === 'm1' && typeof drawWave === 'function') {
      drawWave();
    }
    showToast('Trim range reset to full audio length', 'info');
  }

  function restoreEditorPlaybackSettings(mode, player) {
    if (!player) return;
    if (mode === 'm1') {
      const volSlider = document.getElementById('master-volume-slider');
      const targetVol = volSlider ? parseFloat(volSlider.value) : 1.0;
      player.volume = (!isNaN(targetVol) && targetVol >= 0) ? Math.min(1.0, targetVol) : 1.0;
      player.preservesPitch = true;
      player.playbackRate = savedSpeedRate;
    } else {
      player.volume = 1.0;
      player.preservesPitch = true;
      player.playbackRate = 1.0;
    }
    if (studioGainNodes[mode] && studioAudioCtx) {
      try {
        studioGainNodes[mode].gain.setValueAtTime(1.0, studioAudioCtx.currentTime);
      } catch (e) {}
    }
  }

  function stopModePreview(mode) {
    const st = audioEditorState[mode];
    if (!st) return;
    if (st.previewTimer) {
      clearInterval(st.previewTimer);
      st.previewTimer = null;
    }
    if (st.isPlayingPreview) {
      st.isPlayingPreview = false;
      const player = mode === 'm1'
        ? document.getElementById('audio-player')
        : (document.getElementById('clone-audio-player') || st.audioElement);
      if (player) {
        player.pause();
        restoreEditorPlaybackSettings(mode, player);
      }
      const btn = document.getElementById(mode + '-preview-btn');
      const statusPill = document.getElementById(mode + '-preview-status');
      if (btn) {
        btn.classList.remove('playing');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
      }
      if (statusPill) statusPill.style.display = 'none';
    }
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
      const msg = mode === 'm2'
        ? 'No synthesized audio yet. Click Synthesize Speech first.'
        : 'No audio loaded to preview. Please upload or transcribe media first.';
      showToast(msg, 'info');
      return;
    }

    const btn = document.getElementById(mode + '-preview-btn');
    const statusPill = document.getElementById(mode + '-preview-status');

    function finishPreview() {
      player.pause();
      st.isPlayingPreview = false;
      if (st.previewTimer) {
        clearInterval(st.previewTimer);
        st.previewTimer = null;
      }
      restoreEditorPlaybackSettings(mode, player);
      if (btn) {
        btn.classList.remove('playing');
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg><span>Preview Edited Audio</span>';
      }
      if (statusPill) statusPill.style.display = 'none';
    }

    if (st.isPlayingPreview) {
      finishPreview();
      return;
    }

    if (auditionStopTimer) {
      clearTimeout(auditionStopTimer);
      auditionStopTimer = null;
    }
    st.isAuditioning = false;
    st.isPlayingPreview = true;
    player.currentTime = st.trimStart || 0;
    if (st.pitch === 0) {
      player.preservesPitch = true;
      player.playbackRate = (mode === 'm1') ? savedSpeedRate : 1.0;
    } else {
      player.preservesPitch = false;
      player.playbackRate = Math.max(0.3, Math.min(3.0, Math.pow(2, st.pitch / 12)));
    }

    // Prevent double-attenuation: let Web Audio GainNode handle gain if available
    const gainNode = (typeof getStudioGainNode === 'function') ? getStudioGainNode(mode, player) : null;
    if (gainNode) {
      gainNode.gain.setValueAtTime(st.volume / 100.0, studioAudioCtx ? studioAudioCtx.currentTime : 0);
      if (mode === 'm1') {
        const masterVol = parseFloat(document.getElementById('master-volume-slider')?.value || '1.0');
        player.volume = isNaN(masterVol) ? 1.0 : Math.max(0.0, Math.min(1.0, masterVol));
      } else {
        player.volume = 1.0;
      }
    } else {
      player.volume = Math.max(0.0, Math.min(1.0, st.volume / 100));
    }
    player.muted = false;

    player.play().catch(e => {
      finishPreview();
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
        finishPreview();
      }
    }, 50);
  }

  async function exportEditedMP3(mode) {
    const st = audioEditorState[mode];
    if (!st) return;

    if (mode === 'm2' && !st.referenceAudioBase64) {
      showToast('Synthesize speech before exporting an edited MP3.', 'info');
      return;
    }

    const navMode = mode === 'm2' ? 'voice' : 'transcribe';
    setNavProcessingState(navMode, true);

    const btn = document.getElementById(mode + '-export-btn');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
      btn.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" class="anim-spin"><circle cx="12" cy="12" r="10"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg> Encoding MP3...';
      btn.disabled = true;
    }

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
      const data = await parseJsonResponse(res);
      if (btn) {
        btn.innerHTML = origHtml;
        btn.disabled = (mode === 'm2' && !st.referenceAudioBase64);
      }
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

        showToast(`Exported ${data.filename} (${formatSec(data.duration)}). Saved to outputs folder.`, 'success');
      }
    } catch (e) {
      if (btn) {
        btn.innerHTML = origHtml;
        btn.disabled = (mode === 'm2' && !st.referenceAudioBase64);
      }
      setNavProcessingState(navMode, false);
      showToast('Export error: ' + (e && e.message ? e.message : e), 'error');
    }
  }

  /* Studio Voice Profile Selection */
  function populateVoiceProfiles(profiles) {
    if (!profiles || profiles.length === 0) return;
    window.transcribedVoiceProfiles = profiles;
    if (!selectedStudioVoice && !selectedVoiceProfile) {
      selectedVoiceProfile = profiles[0];
      window.selectedVoiceProfile = profiles[0];
    }
  }

  /* Mode 2 Mini Audio Player Controller */
  var isSeekingCloneAudio = false;

  function updateCloneMiniPlayerUI() {
    const player = document.getElementById('clone-audio-player');
    const playBtn = document.getElementById('btn-clone-play');
    const seekSlider = document.getElementById('clone-seek-slider');
    const timecodeEl = document.getElementById('clone-timecode');
    if (!player) return;

    const isPlaying = !player.paused && !player.ended;
    if (playBtn) {
      playBtn.classList.toggle('is-playing', isPlaying);
      playBtn.setAttribute('aria-label', isPlaying ? 'Pause synthesized audio' : 'Play synthesized audio');
      playBtn.setAttribute('aria-pressed', isPlaying ? 'true' : 'false');
    }

    const dur = (isFinite(player.duration) && player.duration > 0)
      ? player.duration
      : ((audioEditorState.m2 && audioEditorState.m2.totalDuration) || 0);
    const ct = isFinite(player.currentTime) ? player.currentTime : 0;

    if (seekSlider && !isSeekingCloneAudio) {
      seekSlider.value = dur > 0 ? String(Math.max(0, Math.min(100, (ct / dur) * 100))) : '0';
    }
    if (timecodeEl) {
      timecodeEl.innerText = formatSec(ct) + ' / ' + formatSec(dur);
    }
  }

  function initCloneMiniPlayer() {
    const player = document.getElementById('clone-audio-player');
    const playBtn = document.getElementById('btn-clone-play');
    const seekSlider = document.getElementById('clone-seek-slider');
    if (!player || player.__cloneBound) return;
    player.__cloneBound = true;

    if (playBtn) {
      playBtn.addEventListener('click', function() {
        if (!player.src && !player.currentSrc) return;
        if (studioAudioCtx && studioAudioCtx.state === 'suspended') {
          studioAudioCtx.resume().catch(() => {});
        }
        if (player.paused) {
          if (player.ended || (player.duration > 0 && player.currentTime >= player.duration - 0.05)) {
            player.currentTime = 0;
          }
          player.play().catch(function() {});
        } else {
          player.pause();
        }
      });
    }

    if (seekSlider) {
      seekSlider.addEventListener('pointerdown', function() { isSeekingCloneAudio = true; });
      seekSlider.addEventListener('mousedown', function() { isSeekingCloneAudio = true; });
      seekSlider.addEventListener('touchstart', function() { isSeekingCloneAudio = true; }, { passive: true });
      seekSlider.addEventListener('input', function() {
        const dur = (isFinite(player.duration) && player.duration > 0)
          ? player.duration
          : ((audioEditorState.m2 && audioEditorState.m2.totalDuration) || 0);
        if (dur > 0) {
          player.currentTime = (parseFloat(seekSlider.value) / 100) * dur;
          updateCloneMiniPlayerUI();
        }
      });
      const finishSeek = function() {
        isSeekingCloneAudio = false;
        updateCloneMiniPlayerUI();
      };
      seekSlider.addEventListener('change', finishSeek);
      seekSlider.addEventListener('mouseup', finishSeek);
      seekSlider.addEventListener('touchend', finishSeek);
    }

    ['play', 'playing', 'pause', 'ended', 'timeupdate', 'loadedmetadata', 'durationchange', 'seeked'].forEach(function(evtName) {
      player.addEventListener(evtName, updateCloneMiniPlayerUI);
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCloneMiniPlayer);
  } else {
    initCloneMiniPlayer();
  }

  async function synthesizeClonedVoice() {
    const text = document.getElementById('clone-text').value.trim();
    if (!text) {
      showToast('Please enter text for the selected voice to speak.', 'info');
      return;
    }
    if (!selectedVoiceProfile) {
      if (selectedStudioVoice) {
        selectedVoiceProfile = {
          speaker_id: selectedStudioVoice.id,
          voice_id: selectedStudioVoice.id,
          fundamental_frequency_hz: selectedStudioVoice.base_f0 || 160.0,
          gender_estimate: selectedStudioVoice.gender || 'feminine',
          spectral_centroid_hz: selectedStudioVoice.centroid || 1600.0,
          recommended_voice: selectedStudioVoice.id,
        };
        window.selectedVoiceProfile = selectedVoiceProfile;
      } else if (currentResult && currentResult.voice_profiles && currentResult.voice_profiles.length > 0) {
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
      const data = await parseJsonResponse(res);
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

      initCloneMiniPlayer();
      const resBox = document.getElementById('clone-result-box');
      if (resBox) openAnimatedPanel(resBox, 'is-open', 'block');

      const measured = data.similarity_measured === true && typeof data.similarity_score === 'number';
      const scorePct = measured ? (data.similarity_score * 100).toFixed(1) : null;
      const fidelityLabel = measured
        ? `Pitch match: ${scorePct}%`
        : 'Pitch match not measured';
      const badge = document.getElementById('clone-fidelity-badge');
      if (badge) {
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
      }

      const actualBackend = data.synthesis_backend || '';
      const expectedBackends = {
        'edge-neural': ['edge-tts-neural', 'edge-tts'],
        'local-gpu': ['f5-tts-flow-matching', 'local-gpu'],
      };
      const requested = selectedVoiceModel || 'edge-neural';
      const expected = expectedBackends[requested] || [];
      const isFallback = !!actualBackend && (!expected.length || !expected.includes(actualBackend));

      const backendPill = document.getElementById('clone-backend-pill');
      if (backendPill) {
        if (actualBackend) {
          backendPill.style.display = 'inline-flex';
          backendPill.classList.toggle('is-fallback', isFallback);
          backendPill.innerText = isFallback ? ('Fallback: ' + actualBackend) : ('Engine: ' + actualBackend);
        } else {
          backendPill.style.display = 'none';
        }
      }

      const player = document.getElementById('clone-audio-player');
      if (player) {
        player.src = data.audio_base64;
        player.currentTime = 0;
        player.playbackRate = 1.0;
        player.preservesPitch = true;
        updateCloneMiniPlayerUI();
        player.play().catch(() => {});
      }

      const dlBtn = document.getElementById('clone-download-btn');
      if (dlBtn) {
        dlBtn.href = data.audio_base64;
        dlBtn.download = `speech_${(selectedVoiceProfile.speaker_id || 'voice').replace(/\s+/g, '_')}.mp3`;
      }

      // Update Mode 2 Audio Editor to point to this synthesized audio & unlock export
      audioEditorState.m2.referenceAudioBase64 = data.audio_base64;
      initModeAudioEditor('m2', data.duration || 5, 'synthesized_speech.mp3', 'synth-' + Date.now());
      const m2ExportBtn = document.getElementById('m2-export-btn');
      if (m2ExportBtn) m2ExportBtn.disabled = false;

      if (isFallback) {
        showToast('Speech synthesized using fallback engine: ' + actualBackend, 'info');
      } else {
        showToast('Speech synthesized successfully!', 'success');
      }
      if (resBox) {
        resBox.scrollIntoView({ behavior: prefersReducedMotion() ? 'auto' : 'smooth', block: 'nearest' });
      }
    } catch (e) {
      activeVoiceAbortController = null;
      btn.innerHTML = origHtml;
      btn.disabled = false;
      stopAcousticResonanceAnimation();
      setVoiceModelLocked(false);
      setNavProcessingState('voice', false);
      if (e && e.name === 'AbortError') {
        return;
      }
      showToast('Synthesis error: ' + (e && e.message ? e.message : e), 'error');
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
  var isLiquidOrbActive = false;
  var liquidTime = 0;
  var liquidStartTs = 0;
  var lastLiquidTs = 0;
  var liquidLogicalSize = 72;
  var liquidResizeObserver = null;

  function sizeLiquidCanvas() {
    if (!liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var rect = liquidCanvas.getBoundingClientRect();
    var size = (rect && rect.width > 0) ? Math.round(rect.width) : (liquidCanvas.clientWidth || 72);
    liquidLogicalSize = Math.max(40, size);
    var targetPx = Math.round(liquidLogicalSize * dpr);
    if (liquidCanvas.width !== targetPx || liquidCanvas.height !== targetPx) {
      liquidCanvas.width = targetPx;
      liquidCanvas.height = targetPx;
    }
    liquidCanvas.style.width = '';
    liquidCanvas.style.height = '';
  }

  function ensureLiquidResizeObserver() {
    if (!liquidCanvas || liquidResizeObserver || typeof ResizeObserver !== 'function') return;
    liquidResizeObserver = new ResizeObserver(function() {
      sizeLiquidCanvas();
      if (isLiquidOrbActive && prefersReducedMotion()) {
        drawLiquidOrbFrame(0.35);
      }
    });
    liquidResizeObserver.observe(liquidCanvas);
  }

  function startLiquidOrbAnimation() {
    liquidCanvas = document.getElementById('liquid-orb-canvas');
    if (!liquidCanvas) return;
    isLiquidOrbActive = true;
    liquidStartTs = performance.now();
    lastLiquidTs = 0;
    sizeLiquidCanvas();
    ensureLiquidResizeObserver();
    liquidCtx = liquidCanvas.getContext('2d');
    if (prefersReducedMotion()) {
      if (liquidAnimId) {
        cancelAnimationFrame(liquidAnimId);
        liquidAnimId = null;
      }
      drawLiquidOrbFrame(0.35);
      return;
    }
    if (!liquidAnimId) {
      liquidAnimId = requestAnimationFrame(renderLiquidLoop);
    }
  }

  function stopLiquidOrbAnimation() {
    isLiquidOrbActive = false;
    lastLiquidTs = 0;
    if (liquidAnimId) {
      cancelAnimationFrame(liquidAnimId);
      liquidAnimId = null;
    }
  }

  /* Pre-seeded Orbital Stardust Particles (contract compatibility) */
  var orbitalParticles = [];

  function drawLiquidOrbFrame(ampFactor) {
    if (!liquidCtx || !liquidCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var w = liquidLogicalSize || 72;
    var h = liquidLogicalSize || 72;
    var scale = w / 220;
    var cx = w / 2;
    var cy = h / 2;
    var expectedPx = Math.round(w * dpr);
    if (liquidCanvas.width !== expectedPx || liquidCanvas.height !== expectedPx) {
      liquidCanvas.width = expectedPx;
      liquidCanvas.height = expectedPx;
    }

    liquidCtx.save();
    liquidCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    liquidCtx.clearRect(0, 0, w, h);

    // 1. Soft Ambient Luminous Halo (Layered glow without software shadowBlur)
    var ambientGlow = liquidCtx.createRadialGradient(cx, cy, 14 * scale, cx, cy, 102 * scale);
    ambientGlow.addColorStop(0, 'rgba(255, 94, 0, 0.24)');
    ambientGlow.addColorStop(0.5, 'rgba(229, 169, 60, 0.08)');
    ambientGlow.addColorStop(1, 'transparent');
    liquidCtx.fillStyle = ambientGlow;
    liquidCtx.fillRect(0, 0, w, h);

    // 2. Subtle Acoustic Pulse Ripple (Bounded cleanly inside circular canvas)
    if (!prefersReducedMotion()) {
      var ripplePhase = (liquidTime * 18) % 42;
      var rippleR = (52 + ripplePhase) * scale;
      var rippleAlpha = Math.max(0, 0.16 * ampFactor * (1 - ripplePhase / 42));
      liquidCtx.beginPath();
      liquidCtx.arc(cx, cy, rippleR, 0, Math.PI * 2);
      liquidCtx.strokeStyle = 'rgba(255, 122, 26, ' + rippleAlpha.toFixed(3) + ')';
      liquidCtx.lineWidth = Math.max(0.9, 1.2 * scale);
      liquidCtx.stroke();
    }

    // 3. Primary Liquid Mantle (72-point Harmonic Spline Deformation)
    var numPoints = 72;
    var baseR = (50 + Math.sin(liquidTime * 1.5) * 3.0 * ampFactor) * scale;
    var points = [];

    for (var i = 0; i < numPoints; i++) {
      var theta = (i / numPoints) * Math.PI * 2;
      var h1 = Math.sin(theta * 2 + liquidTime * 1.3) * 6.5;
      var h2 = Math.cos(theta * 3 - liquidTime * 0.95) * 4.0;
      var h3 = Math.sin(theta * 5 + liquidTime * 0.75) * 2.2;
      var r = baseR + (h1 + h2 + h3) * scale * ampFactor;
      points.push({
        x: cx + Math.cos(theta) * r,
        y: cy + Math.sin(theta) * r
      });
    }

    liquidCtx.beginPath();
    liquidCtx.moveTo((points[0].x + points[numPoints - 1].x) / 2, (points[0].y + points[numPoints - 1].y) / 2);
    for (var j = 0; j < numPoints; j++) {
      var next = points[(j + 1) % numPoints];
      var midX = (points[j].x + next.x) / 2;
      var midY = (points[j].y + next.y) / 2;
      liquidCtx.quadraticCurveTo(points[j].x, points[j].y, midX, midY);
    }
    liquidCtx.closePath();

    var mantleGrad = liquidCtx.createRadialGradient(cx - 8 * scale, cy - 8 * scale, 6 * scale, cx, cy, baseR + 12 * scale);
    mantleGrad.addColorStop(0, '#FFA826');
    mantleGrad.addColorStop(0.48, '#FF5E00');
    mantleGrad.addColorStop(0.88, '#D94F00');
    mantleGrad.addColorStop(1, 'rgba(180, 50, 0, 0.85)');
    liquidCtx.fillStyle = mantleGrad;
    liquidCtx.fill();

    // 4. Inner Luminous Liquid Caustic
    var innerR = baseR * 0.58;
    var innerPoints = [];
    for (var k = 0; k < numPoints; k++) {
      var itheta = (k / numPoints) * Math.PI * 2;
      var ih1 = Math.sin(itheta * 2 + liquidTime * 1.5 + 0.8) * 3.6;
      var ih2 = Math.cos(itheta * 3 - liquidTime * 1.1 + 0.5) * 2.2;
      var ir = innerR + (ih1 + ih2) * scale * ampFactor;
      innerPoints.push({
        x: (cx - 4 * scale) + Math.cos(itheta) * ir,
        y: (cy - 4 * scale) + Math.sin(itheta) * ir
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

    var innerGrad = liquidCtx.createRadialGradient(cx - 6 * scale, cy - 6 * scale, 2 * scale, cx - 2 * scale, cy - 2 * scale, innerR + 6 * scale);
    innerGrad.addColorStop(0, '#FFF5EB');
    innerGrad.addColorStop(0.45, '#FFA826');
    innerGrad.addColorStop(1, 'rgba(255, 94, 0, 0.15)');
    liquidCtx.fillStyle = innerGrad;
    liquidCtx.fill();

    liquidCtx.restore();
  }

  /* Molten Fluid Light Orb (72-point Harmonic Spline Deformation with Delta-Time Physics) */
  function renderLiquidLoop(ts) {
    if (!isLiquidOrbActive || !liquidCtx || !liquidCanvas) {
      liquidAnimId = null;
      return;
    }
    if (document.hidden || liquidCanvas.offsetParent === null) {
      liquidAnimId = null;
      lastLiquidTs = 0;
      return;
    }
    if (prefersReducedMotion()) {
      liquidAnimId = null;
      drawLiquidOrbFrame(0.35);
      return;
    }

    var nowTs = (typeof ts === 'number') ? ts : performance.now();
    var dt = lastLiquidTs ? Math.min(0.05, Math.max(0, (nowTs - lastLiquidTs) / 1000)) : 0.016;
    lastLiquidTs = nowTs;
    liquidTime += dt * 0.96;

    var rawRamp = Math.min(1, Math.max(0, (nowTs - liquidStartTs) / 350));
    var rampIn = rawRamp * rawRamp * (3 - 2 * rawRamp);
    var calmSettle = 1 - 0.65 * Math.max(0, Math.min(1, (currentProcessingProgress - 0.85) / 0.15));

    drawLiquidOrbFrame(rampIn * calmSettle);
    liquidAnimId = requestAnimationFrame(renderLiquidLoop);
  }

  /* ========================================================= */
  /* MINIMAL ACOUSTIC RESONANCE OSCILLOSCOPE (CUSTOM TTS)      */
  /* ========================================================= */
  var resCanvas, resCtx;
  var voiceOrbCanvas, voiceOrbCtx;
  var resAnimId = null;
  var isResonanceActive = false;
  var resTime = 0;
  var voiceOrbTime = 0;
  var lastResTs = 0;
  var resLogicalWidth = 500;
  var resResizeObserver = null;
  var cachedResStatusEl = null;
  var cachedPitchSliderEl = null;
  var lastResStatusText = '';

  function sizeResonanceCanvas() {
    if (!resCanvas) return;
    var dpr = window.devicePixelRatio || 1;
    var parentW = resCanvas.parentElement ? resCanvas.parentElement.clientWidth : 0;
    var w = Math.max(120, parentW || resCanvas.clientWidth || 500);
    var h = 60;
    resLogicalWidth = w;
    var targetW = Math.round(w * dpr);
    var targetH = Math.round(h * dpr);
    if (resCanvas.width !== targetW || resCanvas.height !== targetH) {
      resCanvas.width = targetW;
      resCanvas.height = targetH;
    }
    resCanvas.style.width = '100%';
    resCanvas.style.height = '60px';
  }

  function ensureResonanceResizeObserver() {
    if (!resCanvas || !resCanvas.parentElement || resResizeObserver || typeof ResizeObserver !== 'function') return;
    resResizeObserver = new ResizeObserver(function() {
      sizeResonanceCanvas();
      if (isResonanceActive && prefersReducedMotion()) {
        drawResonanceFrame(0.35);
      }
    });
    resResizeObserver.observe(resCanvas.parentElement);
  }

  function startAcousticResonanceAnimation() {
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) openAnimatedPanel(stage, 'is-open', '');

    cachedResStatusEl = document.getElementById('resonance-status-text');
    cachedPitchSliderEl = document.getElementById('pitch-slider');
    lastResStatusText = '';

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
      sizeResonanceCanvas();
      ensureResonanceResizeObserver();
      resCtx = resCanvas.getContext('2d');
    }

    isResonanceActive = true;
    lastResTs = 0;

    if (prefersReducedMotion()) {
      if (resAnimId) {
        cancelAnimationFrame(resAnimId);
        resAnimId = null;
      }
      drawResonanceFrame(0.35);
      return;
    }

    if (!resAnimId) {
      resAnimId = requestAnimationFrame(renderResonanceLoop);
    }
  }

  function stopAcousticResonanceAnimation() {
    isResonanceActive = false;
    lastResTs = 0;
    var stage = document.getElementById('synthesis-resonance-stage');
    if (stage) closeAnimatedPanel(stage, 'is-open', 360);
    if (resAnimId) {
      cancelAnimationFrame(resAnimId);
      resAnimId = null;
    }
  }

  function drawResonanceFrame(ampScale) {
    var dpr = window.devicePixelRatio || 1;
    var baseF0 = (selectedVoiceProfile && selectedVoiceProfile.fundamental_frequency_hz) ? selectedVoiceProfile.fundamental_frequency_hz : 145;
    var pitchShift = cachedPitchSliderEl ? (parseFloat(cachedPitchSliderEl.value) || 0) : 0;
    var effectiveF0 = Math.max(60, baseF0 + pitchShift);
    var pitchScale = effectiveF0 / 140.0;

    // 1. Render Fluid Liquid Voice Morphing Orb
    if (voiceOrbCtx && voiceOrbCanvas) {
      var ow = 160;
      var oh = 160;
      var ocx = ow / 2;
      var ocy = oh / 2;

      voiceOrbCtx.save();
      voiceOrbCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      voiceOrbCtx.clearRect(0, 0, ow, oh);

      var orbGlow = voiceOrbCtx.createRadialGradient(ocx, ocy, 8, ocx, ocy, 74);
      orbGlow.addColorStop(0, 'rgba(255, 94, 0, 0.24)');
      orbGlow.addColorStop(0.45, 'rgba(229, 169, 60, 0.08)');
      orbGlow.addColorStop(1, 'transparent');
      voiceOrbCtx.fillStyle = orbGlow;
      voiceOrbCtx.fillRect(0, 0, ow, oh);

      if (!prefersReducedMotion()) {
        var orbRipple = (voiceOrbTime * 18) % 36;
        var rippleR = 40 + orbRipple;
        var rippleAlpha = Math.max(0, 0.18 * (1 - orbRipple / 36));
        voiceOrbCtx.beginPath();
        voiceOrbCtx.arc(ocx, ocy, rippleR, 0, Math.PI * 2);
        voiceOrbCtx.strokeStyle = 'rgba(255, 122, 26, ' + rippleAlpha.toFixed(3) + ')';
        voiceOrbCtx.lineWidth = 1.2;
        voiceOrbCtx.stroke();
      }

      var numPoints = 72;
      var baseR = 38 + Math.sin(voiceOrbTime * 1.6) * 2.5 * ampScale;
      var orbPoints = [];

      for (var pIdx = 0; pIdx < numPoints; pIdx++) {
        var theta = (pIdx / numPoints) * Math.PI * 2;
        var h1 = Math.sin(theta * 2 + voiceOrbTime * 1.8) * 4.6;
        var h2 = Math.cos(theta * 3 - voiceOrbTime * 1.3) * 3.0;
        var h3 = Math.sin(theta * 5 + voiceOrbTime * 1.0) * 1.8;
        var r = baseR + (h1 + h2 + h3) * (0.8 + pitchScale * 0.2) * ampScale;
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
      voiceOrbCtx.fill();

      var innerR = baseR * 0.56;
      var innerPoints = [];
      for (var k = 0; k < numPoints; k++) {
        var itheta = (k / numPoints) * Math.PI * 2;
        var ih1 = Math.sin(itheta * 2 + voiceOrbTime * 1.9 + 0.8) * 2.8;
        var ih2 = Math.cos(itheta * 3 - voiceOrbTime * 1.4 + 0.4) * 1.8;
        var ir = innerR + (ih1 + ih2) * ampScale;
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

    // 2. Render Smooth Acoustic Oscilloscope Ribbon Waveforms (x += 3 with quadratic smoothing)
    if (resCtx && resCanvas) {
      var rw = resCanvas.clientWidth || resLogicalWidth || (resCanvas.width / dpr);
      var rh = 60;
      if (rw > 0 && Math.abs(rw - resLogicalWidth) > 1) {
        sizeResonanceCanvas();
      }

      resCtx.save();
      resCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
      resCtx.clearRect(0, 0, rw, rh);

      var waves = [
        { freq: 0.045 * pitchScale, amp: 14, color: 'rgba(255, 94, 0, 0.90)', width: 1.8 },
        { freq: 0.085 * pitchScale, amp: 9, color: 'rgba(229, 169, 60, 0.85)', width: 1.4 },
        { freq: 0.145 * pitchScale, amp: 6, color: 'rgba(255, 138, 122, 0.75)', width: 1.1 },
        { freq: 0.220 * pitchScale, amp: 3.5, color: 'rgba(255, 216, 138, 0.65)', width: 0.8 }
      ];

      waves.forEach(function(wv, wi) {
        var pts = [];
        var t = resTime * (1.6 + wi * 0.7);
        for (var x = 0; x <= rw + 3; x += 3) {
          var sx = Math.min(rw, x);
          var envelope = Math.sin((sx / Math.max(1, rw)) * Math.PI);
          var y = (rh / 2) + (Math.sin(sx * wv.freq + t) * (wv.amp * envelope) + Math.cos(sx * 0.025 + t * 0.6) * (2.5 * envelope)) * ampScale;
          pts.push({ x: sx, y: y });
        }
        if (pts.length > 0) {
          resCtx.beginPath();
          resCtx.moveTo(pts[0].x, pts[0].y);
          for (var pi = 1; pi < pts.length - 1; pi++) {
            var midX = (pts[pi].x + pts[pi + 1].x) / 2;
            var midY = (pts[pi].y + pts[pi + 1].y) / 2;
            resCtx.quadraticCurveTo(pts[pi].x, pts[pi].y, midX, midY);
          }
          resCtx.lineTo(pts[pts.length - 1].x, pts[pts.length - 1].y);
          resCtx.strokeStyle = wv.color;
          resCtx.lineWidth = wv.width;
          resCtx.stroke();
        }
      });

      resCtx.restore();
    }

    // 3. Cache status node & mutate only when formatted F0 changes
    if (cachedResStatusEl) {
      var nextStatus = 'Matching the selected voice · Pitch: ' + effectiveF0.toFixed(1) + ' Hz';
      if (nextStatus !== lastResStatusText) {
        cachedResStatusEl.innerText = nextStatus;
        lastResStatusText = nextStatus;
      }
    }
  }

  function renderResonanceLoop(ts) {
    if (!isResonanceActive) {
      resAnimId = null;
      return;
    }
    if (document.hidden || (resCanvas && resCanvas.offsetParent === null)) {
      resAnimId = null;
      lastResTs = 0;
      return;
    }
    if (prefersReducedMotion()) {
      resAnimId = null;
      drawResonanceFrame(0.35);
      return;
    }

    var nowTs = (typeof ts === 'number') ? ts : performance.now();
    var dt = lastResTs ? Math.min(0.05, Math.max(0, (nowTs - lastResTs) / 1000)) : 0.016;
    lastResTs = nowTs;

    var baseF0 = (selectedVoiceProfile && selectedVoiceProfile.fundamental_frequency_hz) ? selectedVoiceProfile.fundamental_frequency_hz : 145;
    var pitchShift = cachedPitchSliderEl ? (parseFloat(cachedPitchSliderEl.value) || 0) : 0;
    var effectiveF0 = Math.max(60, baseF0 + pitchShift);
    var pitchScale = effectiveF0 / 140.0;

    voiceOrbTime += dt * 1.08 * Math.sqrt(pitchScale);
    resTime += dt * 1.44 * Math.sqrt(pitchScale);

    drawResonanceFrame(1.0);
    resAnimId = requestAnimationFrame(renderResonanceLoop);
  }

  function resumeActiveCanvasLoops() {
    if (document.hidden) return;
    if (isLiquidOrbActive && liquidCanvas && liquidCanvas.offsetParent !== null && !liquidAnimId) {
      if (prefersReducedMotion()) {
        drawLiquidOrbFrame(0.35);
      } else {
        lastLiquidTs = 0;
        liquidAnimId = requestAnimationFrame(renderLiquidLoop);
      }
    }
    if (isResonanceActive && resCanvas && resCanvas.offsetParent !== null && !resAnimId) {
      if (prefersReducedMotion()) {
        drawResonanceFrame(0.35);
      } else {
        lastResTs = 0;
        resAnimId = requestAnimationFrame(renderResonanceLoop);
      }
    }
    var m1Player = document.getElementById('audio-player');
    if (m1Player && !m1Player.paused && waveCanvas && waveCanvas.offsetParent !== null) {
      scheduleWaveAnimation();
      startTranscriptTracking();
    }
  }

  document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
      if (liquidAnimId) { cancelAnimationFrame(liquidAnimId); liquidAnimId = null; }
      if (resAnimId) { cancelAnimationFrame(resAnimId); resAnimId = null; }
      lastLiquidTs = 0;
      lastResTs = 0;
      stopWaveAnimation();
    } else {
      resumeActiveCanvasLoops();
    }
  });

  if (reducedMotionQuery) {
    const onMotionPreferenceChange = function() {
      if (prefersReducedMotion()) {
        if (liquidAnimId) { cancelAnimationFrame(liquidAnimId); liquidAnimId = null; }
        if (resAnimId) { cancelAnimationFrame(resAnimId); resAnimId = null; }
        if (isLiquidOrbActive) drawLiquidOrbFrame(0.35);
        if (isResonanceActive) drawResonanceFrame(0.35);
        stopWaveAnimation();
      } else {
        resumeActiveCanvasLoops();
      }
      if (typeof drawWave === 'function') drawWave();
    };
    if (typeof reducedMotionQuery.addEventListener === 'function') {
      reducedMotionQuery.addEventListener('change', onMotionPreferenceChange);
    } else if (typeof reducedMotionQuery.addListener === 'function') {
      reducedMotionQuery.addListener(onMotionPreferenceChange);
    }
  }

  /* ========================================================= */
  /* MINIMALIST AUDIO WAVEFORM: 64 BARS & SLEEK SCRUBBER        */
  /* ========================================================= */
  var waveCanvas, waveCtx;
  var waveEnvelope = null;
  var isScrubbing = false;
  var cachedWavePastGrad = null;
  var cachedWaveGradH = 0;

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
      const wrapRect = wrap.getBoundingClientRect();
      const clientX = (e.touches && e.touches.length > 0) ? e.touches[0].clientX : (e.clientX || 0);
      const clickX = clientX - wrapRect.left;
      tooltip.innerText = formatSec(pct * totalDur);
      const tipHalf = Math.max(20, (tooltip.offsetWidth || 44) / 2);
      const clampedX = Math.max(tipHalf + 4, Math.min(Math.max(tipHalf + 4, wrap.clientWidth - tipHalf - 4), clickX));
      tooltip.style.setProperty('--tip-x', Math.round(clampedX) + 'px');
      tooltip.classList.add('visible');
    }

    function hideTooltip() {
      if (tooltip) tooltip.classList.remove('visible');
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

    if (wrap) {
      wrap.addEventListener('keydown', function(e) {
        const player = document.getElementById('audio-player');
        const dur = getAccurateDuration() || (player && player.duration) || 0;
        if (e.key === 'ArrowLeft') {
          e.preventDefault();
          e.stopPropagation();
          skipAudio(-5);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          e.stopPropagation();
          skipAudio(5);
        } else if (e.key === 'Home') {
          e.preventDefault();
          e.stopPropagation();
          if (player) {
            player.currentTime = 0;
            handleAudioTimeUpdate();
            drawWave();
          }
        } else if (e.key === 'End') {
          e.preventDefault();
          e.stopPropagation();
          if (player && dur > 0) {
            player.currentTime = dur;
            handleAudioTimeUpdate();
            drawWave();
          }
        } else if (e.code === 'Space' || e.key === 'Enter') {
          e.preventDefault();
          e.stopPropagation();
          togglePlayPause();
        }
      });

      wrap.addEventListener('mousemove', function(e) {
        updateTooltip(e);
        if (isScrubbing) {
          handleSeekFromEvent(e);
        }
      });

      wrap.addEventListener('mouseleave', function() {
        if (!isScrubbing) hideTooltip();
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
              startTranscriptTracking();
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
              startTranscriptTracking();
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
          hideTooltip();
          drawWave();
        }
      });
    }

    window.addEventListener('mousemove', function(e) {
      if (isScrubbing) {
        updateTooltip(e);
        handleSeekFromEvent(e);
      }
    });

    window.addEventListener('mouseup', function() {
      if (isScrubbing) {
        isScrubbing = false;
        hideTooltip();
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
    if (typeof drawWave === 'function') {
      drawWave();
    }
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
    const reduceMotion = prefersReducedMotion();

    let liveLevel = 0;
    let hasLiveFrequency = false;
    if (visualizerAnalyser && visualizerDataArray && isPlaying && !reduceMotion) {
      try {
        visualizerAnalyser.getByteFrequencyData(visualizerDataArray);
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
    if (!hasLiveFrequency && isPlaying && !reduceMotion) {
      liveLevel = 0.36 + 0.28 * (0.6 * Math.sin(now * 4.5) + 0.4 * Math.cos(now * 2.8));
    }

    if (!cachedWavePastGrad || cachedWaveGradH !== h) {
      cachedWavePastGrad = ctx.createLinearGradient(0, 0, 0, h);
      cachedWavePastGrad.addColorStop(0, '#FF8A33');
      cachedWavePastGrad.addColorStop(0.5, '#FF5E00');
      cachedWavePastGrad.addColorStop(1, '#E5A93C');
      cachedWaveGradH = h;
    }

    const closestBar = Math.round(progress * (bars - 1));

    for (let i = 0; i < bars; i++) {
      const barProg = i / (bars - 1);
      const isPast = barProg <= progress;
      const isPlayhead = (i === closestBar);
      const isInsideTrim = !hasTrim || (barProg >= trimStartProg - (0.5 / bars) && barProg <= trimEndProg + (0.5 / bars));

      let baseVal = 0.22;
      if (envelope && envelope.length) {
        baseVal = Math.max(0.04, envelope[i]);
      } else {
        baseVal = 0.22 + 0.16 * Math.sin(i * 0.22) * Math.cos(i * 0.11 + 0.3);
      }

      let dynamicFactor = 1.0;
      if (isPlaying && !reduceMotion) {
        const distToPlayhead = Math.abs(barProg - progress);
        const playheadRipple = Math.max(0, 1.0 - distToPlayhead * 6.0);
        const playheadBounce = playheadRipple * (liveLevel * 0.85 + 0.24 * Math.sin(now * 6.5 + i * 0.4));
        dynamicFactor = Math.max(0.45, 1.0 + playheadBounce);
      }

      const barHeight = Math.max(4, Math.min(h - 4, baseVal * dynamicFactor * (h * 0.86)));
      const x = i * step;
      const y = (h - barHeight) / 2;

      if (!isInsideTrim) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.07)';
      } else if (isPlayhead) {
        ctx.fillStyle = '#FFE4B5';
      } else if (isPast) {
        ctx.fillStyle = cachedWavePastGrad;
      } else {
        ctx.fillStyle = 'rgba(229, 169, 60, 0.32)';
      }

      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(x, y, barWidth, barHeight, 2.5);
      } else {
        ctx.rect(x, y, barWidth, barHeight);
      }
      ctx.fill();
    }

    // Crisp sub-pixel playhead hairline
    const playheadX = Math.max(0.75, Math.min(w - 0.75, progress * w));
    ctx.save();
    ctx.strokeStyle = 'rgba(255, 228, 181, 0.88)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(playheadX, 1);
    ctx.lineTo(playheadX, h - 1);
    ctx.stroke();
    ctx.restore();
  }

  function drawWave() {
    if (!waveCanvas) waveCanvas = document.getElementById('waveform-canvas');
    if (!waveCtx && waveCanvas) waveCtx = waveCanvas.getContext('2d');
    if (!waveCtx || !waveCanvas) return;
    if (document.hidden || waveCanvas.offsetParent === null) {
      stopWaveAnimation();
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
    const isPlaying = !!(player && !player.paused);
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
    if ((isPlaying && !prefersReducedMotion()) || isScrubbing) {
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
    }).then(parseJsonResponse).then(function() {
      showToast('Opened Scriber output folder in Explorer', 'info');
    }).catch(err => {
      showToast('Could not open folder: ' + (err && err.message ? err.message : err), 'error');
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
     Studio Voice Suite & Presets
     ========================================================================== */
  var studioVoicesList = [];
  var selectedStudioVoice = null;
  var currentRegionFilter = 'all';
  var currentGenderFilter = 'all';
  var userEditedCloneText = false;
  var defaultCloneText = '';
  var lastLoadedSampleText = '';

  function initCloneTextEditTracking() {
    const txtArea = document.getElementById('clone-text');
    if (!txtArea || txtArea.__editTracked) return;
    txtArea.__editTracked = true;
    defaultCloneText = txtArea.value || '';
    txtArea.addEventListener('input', function() {
      const cur = txtArea.value.trim();
      if (!cur || cur === defaultCloneText.trim() || (lastLoadedSampleText && cur === lastLoadedSampleText.trim())) {
        userEditedCloneText = false;
      } else {
        userEditedCloneText = true;
      }
    });
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCloneTextEditTracking);
  } else {
    initCloneTextEditTracking();
  }

  async function loadStudioVoices() {
    const grid = document.getElementById('voice-suite-grid');
    try {
      const res = await fetch('/api/voices');
      const data = await parseJsonResponse(res);
      studioVoicesList = data.voices || [];
      if (studioVoicesList.length > 0 && !selectedStudioVoice) {
        selectedStudioVoice = studioVoicesList[0]; // Jenny (US)
        updateActiveVoiceBanner(selectedStudioVoice);
        selectedVoiceProfile = {
          speaker_id: selectedStudioVoice.id,
          voice_id: selectedStudioVoice.id,
          fundamental_frequency_hz: selectedStudioVoice.base_f0 || 160.0,
          gender_estimate: selectedStudioVoice.gender || 'feminine',
          spectral_centroid_hz: selectedStudioVoice.centroid || 1600.0,
          recommended_voice: selectedStudioVoice.id,
        };
        window.selectedVoiceProfile = selectedVoiceProfile;
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
      grid.innerHTML = '<div class="empty-state-card voice-suite-loading" role="status">No voices match the selected filters.</div>';
      return;
    }

    grid.innerHTML = filtered.map(function(v) {
      var isSel = selectedStudioVoice && (selectedStudioVoice.id === v.id);
      var genderClass = v.gender === 'feminine' ? 'female' : 'male';
      var genderInit = v.gender === 'feminine' ? 'F' : 'M';
      const safeId = escapeHtml(v.id);
      return `
        <div class="voice-suite-card ${isSel ? 'selected' : ''}" data-voice-id="${safeId}" role="button" tabindex="0" aria-pressed="${isSel ? 'true' : 'false'}"
             onclick="selectStudioVoice('${safeId}')"
             onkeydown="if(event.target===event.currentTarget&&(event.key==='Enter'||event.key===' ')){event.preventDefault();selectStudioVoice('${safeId}');}">
          <div class="voice-card-header-row">
            <div class="voice-card-name-wrap">
              <span class="voice-avatar-badge ${genderClass}">${genderInit}</span>
              <span class="voice-card-name">${escapeHtml(v.name)}</span>
            </div>
            <span class="voice-locale-badge">${escapeHtml(v.locale)}</span>
          </div>
          <div class="voice-card-style">
            <span>${escapeHtml(v.style || 'Natural')}</span>
          </div>
          <div class="voice-card-desc">${escapeHtml(v.description || '')}</div>
          <div class="voice-card-footer">
            <button type="button" class="btn-audition-card" onclick="event.stopPropagation(); auditionVoiceCard('${safeId}')" title="Load sample text for this voice">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
              <span>Load Sample Text</span>
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

    const grid = document.getElementById('voice-suite-grid');
    if (grid) {
      const cards = grid.querySelectorAll('.voice-suite-card[data-voice-id]');
      if (cards.length > 0) {
        cards.forEach(function(card) {
          const isMatch = card.getAttribute('data-voice-id') === voiceId;
          card.classList.toggle('selected', isMatch);
          card.setAttribute('aria-pressed', isMatch ? 'true' : 'false');
        });
        return;
      }
    }
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
    initCloneTextEditTracking();
    if (voice.preview_text) {
      var txtArea = document.getElementById('clone-text');
      if (txtArea) {
        var cur = txtArea.value.trim();
        var canOverwrite = !userEditedCloneText || !cur || cur === defaultCloneText.trim() || (lastLoadedSampleText && cur === lastLoadedSampleText.trim());
        if (!canOverwrite) {
          showToast('Clear or reset text to load sample script', 'info');
          return;
        }
        txtArea.value = voice.preview_text;
        lastLoadedSampleText = voice.preview_text;
        userEditedCloneText = false;
      }
    }
    showToast(`Loaded sample text for ${voice.name}. Ready to synthesize!`, 'info');
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
