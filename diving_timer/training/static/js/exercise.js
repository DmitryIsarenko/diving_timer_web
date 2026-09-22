// Breathing exercise logic: 4 phases (last optional), with TTS, pause/resume, and total/phase countdowns
(function () {
  'use strict';

  // Elements
  var el = function (id) { return document.getElementById(id); };
  var inhaleInput = el('inhaleSec');
  var holdInInput = el('holdInSec');
  var exhaleInput = el('exhaleSec');
  var holdOutInput = el('holdOutSec');
  var roundsInput = el('rounds');

  var startBtn = el('startBtn');
  var pauseBtn = el('pauseBtn');
  var resetBtn = el('resetBtn');
  var toStats = el('toStats');

  var currentPhaseEl = el('currentPhase');
  var phaseRemainingEl = el('phaseRemaining');
  var totalRemainingEl = el('totalRemaining');
  var roundInfoEl = el('roundInfo');
  var totalPlannedEl = el('totalPlanned');

  // State
  var timerId = null;
  var running = false;
  var paused = false;
  var currentPhaseIndex = 0;
  var currentRound = 0;
  var phases = [];
  var phaseDeadline = 0; // ms (performance.now reference)
  var totalDeadline = 0; // ms
  var remainingPhaseMs = 0; // used for pause/resume
  var remainingTotalMs = 0; // used for pause/resume

  // TTS
  var voice = null;
  function pickVoice() {
    try {
      var voices = window.speechSynthesis ? window.speechSynthesis.getVoices() : [];
      if (!voices || voices.length === 0) return;
      var ru = voices.find(function (v) { return (v.lang || '').toLowerCase().startsWith('ru'); });
      voice = ru || voices[0];
    } catch (_) { /* noop */ }
  }
  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = function () { pickVoice(); };
    pickVoice();
  }
  function speak(text) {
    try {
      if (!window.speechSynthesis) return;
      var utter = new SpeechSynthesisUtterance(text);
      if (voice) utter.voice = voice;
      utter.lang = voice && voice.lang ? voice.lang : 'ru-RU';
      window.speechSynthesis.cancel(); // ensure no overlap
      window.speechSynthesis.speak(utter);
    } catch (_) { /* noop */ }
  }

  // Utils
  function clampInt(v, min, fallback) {
    var n = parseInt(v, 10);
    if (isNaN(n)) return fallback;
    return Math.max(min, n);
  }
  function formatMMSS(ms) {
    var totalSec = Math.max(0, Math.floor(ms / 1000));
    var m = Math.floor(totalSec / 60);
    var s = totalSec % 60;
    return String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }
  function formatHHMMSS(ms) {
    var totalSec = Math.max(0, Math.floor(ms / 1000));
    var h = Math.floor(totalSec / 3600);
    var remainder = totalSec % 3600;
    var m = Math.floor(remainder / 60);
    var s = remainder % 60;
    return String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0') + ':' + String(s).padStart(2, '0');
  }

  function computePlannedTotalMs(values) {
    var perRound = values.inhale + values.holdIn + values.exhale + (values.holdOutOptional ? values.holdOut : 0);
    return perRound * values.rounds * 1000;
  }

  function readInputs() {
    var inhale = clampInt(inhaleInput.value, 0, 0);
    var holdIn = clampInt(holdInInput.value, 0, 0);
    var exhale = clampInt(exhaleInput.value, 0, 0);
    var holdOut = clampInt(holdOutInput.value, 0, 0);
    var rounds = clampInt(roundsInput.value, 1, 1);
    return {
      inhale: inhale,
      holdIn: holdIn,
      exhale: exhale,
      holdOut: holdOut,
      holdOutOptional: holdOut > 0,
      rounds: rounds
    };
  }

  function validateInputs() {
    var v = readInputs();
    var valid = v.inhale > 0 && v.holdIn > 0 && v.exhale > 0 && v.rounds >= 1;
    startBtn.disabled = !valid || running;
    // Update planned total
    var plannedMs = computePlannedTotalMs(v);
    totalPlannedEl.textContent = formatHHMMSS(plannedMs);
    // Round info pre-start
    roundInfoEl.textContent = '0 / ' + String(v.rounds);
    return valid;
  }

  function buildPhases(values) {
    var p = [
      { key: 'inhale', name: 'Вдох', seconds: values.inhale },
      { key: 'holdIn', name: 'Задержка на вдохе', seconds: values.holdIn },
      { key: 'exhale', name: 'Выдох', seconds: values.exhale }
    ];
    if (values.holdOutOptional) {
      p.push({ key: 'holdOut', name: 'Задержка на выдохе', seconds: values.holdOut });
    }
    return p;
  }

  function setControlsOnStart() {
    running = true; paused = false;
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    resetBtn.disabled = false;
    // lock inputs during run
    inhaleInput.disabled = true;
    holdInInput.disabled = true;
    exhaleInput.disabled = true;
    holdOutInput.disabled = true;
    roundsInput.disabled = true;
    // stats link stays disabled until completion
  }

  function setControlsOnStop() {
    running = false; paused = false;
    startBtn.disabled = !validateInputs();
    pauseBtn.disabled = true;
    pauseBtn.textContent = 'Пауза';
    resetBtn.disabled = true;
    inhaleInput.disabled = false;
    holdInInput.disabled = false;
    exhaleInput.disabled = false;
    holdOutInput.disabled = false;
    roundsInput.disabled = false;
  }

  function enableStatsLink() {
    toStats.classList.remove('disabled-link');
    toStats.removeAttribute('aria-disabled');
    toStats.removeAttribute('tabindex');
  }
  function disableStatsLink() {
    toStats.classList.add('disabled-link');
    toStats.setAttribute('aria-disabled', 'true');
    toStats.setAttribute('tabindex', '-1');
  }

  function startTimerLoop() {
    if (timerId) clearInterval(timerId);
    timerId = setInterval(tick, 250);
  }
  function stopTimerLoop() {
    if (timerId) { clearInterval(timerId); timerId = null; }
  }

  function startPhase(index) {
    currentPhaseIndex = index;
    var phase = phases[currentPhaseIndex];
    currentPhaseEl.textContent = phase.name;
    speak(phase.name);
    var now = performance.now();
    phaseDeadline = now + phase.seconds * 1000;
  }

  function advancePhaseOrRound(values) {
    if (currentPhaseIndex + 1 < phases.length) {
      startPhase(currentPhaseIndex + 1);
      return;
    }
    // round finished
    if (currentRound < values.rounds) {
      currentRound += 1;
      roundInfoEl.textContent = String(currentRound) + ' / ' + String(values.rounds);
    }
    if (currentRound >= values.rounds) {
      // completed all rounds
      complete();
      return;
    }
    // next round, back to first phase
    startPhase(0);
  }

  function tick() {
    var now = performance.now();
    var phaseLeft = Math.max(0, Math.round(phaseDeadline - now));
    var totalLeft = Math.max(0, Math.round(totalDeadline - now));

    phaseRemainingEl.textContent = formatMMSS(phaseLeft);
    totalRemainingEl.textContent = formatHHMMSS(totalLeft);

    if (phaseLeft <= 0) {
      // move to next phase / round
      var values = cachedValues; // use snapshot from start
      advancePhaseOrRound(values);
    }

    if (totalLeft <= 0) {
      complete();
    }
  }

  function complete() {
    stopTimerLoop();
    running = false;
    paused = false;
    enableStatsLink();
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    resetBtn.disabled = false; // allow viewing values after completion, but can reset
  }

  function resetUI() {
    stopTimerLoop();
    currentPhaseEl.textContent = '—';
    phaseRemainingEl.textContent = '00:00';
    totalRemainingEl.textContent = '00:00:00';
    disableStatsLink();
    setControlsOnStop();
  }

  // Keep a snapshot of values used for current run
  var cachedValues = null;

  function handleStart() {
    if (running) return;
    if (!validateInputs()) return;
    disableStatsLink();
    cachedValues = readInputs();
    phases = buildPhases(cachedValues);
    currentRound = 1;
    roundInfoEl.textContent = String(currentRound) + ' / ' + String(cachedValues.rounds);
    setControlsOnStart();

    var now = performance.now();
    // totalDeadline accounts for entire remaining duration from this moment
    var perRoundSec = phases.reduce(function (acc, p) { return acc + p.seconds; }, 0);
    var totalSec = perRoundSec * cachedValues.rounds;
    totalDeadline = now + totalSec * 1000;

    startPhase(0);
    startTimerLoop();
  }

  function handlePause() {
    if (!running) return;
    if (!paused) {
      // pause
      var now = performance.now();
      remainingPhaseMs = Math.max(0, Math.round(phaseDeadline - now));
      remainingTotalMs = Math.max(0, Math.round(totalDeadline - now));
      stopTimerLoop();
      paused = true;
      pauseBtn.textContent = 'Продолжить';
    } else {
      // resume: restart round from inhale
      var now2 = performance.now();
      currentPhaseIndex = 0;
      startPhase(0); // sets phaseDeadline and announces inhale
      var perRoundSec = phases.reduce(function (acc, p) { return acc + p.seconds; }, 0);
      var remainingRounds = Math.max(0, (cachedValues ? cachedValues.rounds : 0) - currentRound + 1);
      totalDeadline = now2 + (remainingRounds * perRoundSec * 1000);
      paused = false;
      pauseBtn.textContent = 'Пауза';
      startTimerLoop();
    }
  }

  function handleReset() {
    cachedValues = null;
    phases = [];
    currentPhaseIndex = 0;
    currentRound = 0;
    resetUI();
    validateInputs();
  }

  // Wire events
  [inhaleInput, holdInInput, exhaleInput, holdOutInput, roundsInput].forEach(function (input) {
    input.addEventListener('input', validateInputs);
    input.addEventListener('change', validateInputs);
  });
  startBtn.addEventListener('click', handleStart);
  pauseBtn.addEventListener('click', handlePause);
  resetBtn.addEventListener('click', handleReset);

  // Initial UI state
  disableStatsLink();
  validateInputs();
})();


