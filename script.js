(function () {
  'use strict';

  const BOARD_WIDTH = 10;
  const BOARD_HEIGHT = 20;
  const NEXT_SIZE = 4;

  /** @type {HTMLElement} */
  const boardEl = document.getElementById('board');
  /** @type {HTMLElement} */
  const nextEl = document.getElementById('next');
  /** @type {HTMLElement} */
  const scoreEl = document.getElementById('score');
  /** @type {HTMLElement} */
  const linesEl = document.getElementById('lines');
  /** @type {HTMLElement} */
  const levelEl = document.getElementById('level');

  const newGameBtn = document.getElementById('newGameBtn');
  const pauseBtn = document.getElementById('pauseBtn');

  const leftBtn = document.getElementById('leftBtn');
  const rightBtn = document.getElementById('rightBtn');
  const rotateBtn = document.getElementById('rotateBtn');
  const downBtn = document.getElementById('downBtn');
  const pauseSmallBtn = document.getElementById('pauseSmallBtn');

  /** Model state */
  let board = createMatrix(BOARD_HEIGHT, BOARD_WIDTH, 0);
  let rngBag = [];
  let current = null; // {type, rotation, matrix, x, y}
  let next = null;
  let score = 0;
  let linesCleared = 0;
  let level = 1;
  let state = 'gameOver'; // 'playing' | 'paused' | 'gameOver'
  let dropIntervalMs = 800; // adjusted by level
  let dropTimer = 0;
  let lastTime = 0;

  /** Shapes and rotations */
  const TETROMINOES = {
    I: [
      [ [0,0,0,0], [1,1,1,1], [0,0,0,0], [0,0,0,0] ],
      [ [0,0,1,0], [0,0,1,0], [0,0,1,0], [0,0,1,0] ],
      [ [0,0,0,0], [0,0,0,0], [1,1,1,1], [0,0,0,0] ],
      [ [0,1,0,0], [0,1,0,0], [0,1,0,0], [0,1,0,0] ],
    ],
    O: [
      [ [1,1], [1,1] ],
      [ [1,1], [1,1] ],
      [ [1,1], [1,1] ],
      [ [1,1], [1,1] ],
    ],
    T: [
      [ [0,1,0], [1,1,1], [0,0,0] ],
      [ [0,1,0], [0,1,1], [0,1,0] ],
      [ [0,0,0], [1,1,1], [0,1,0] ],
      [ [0,1,0], [1,1,0], [0,1,0] ],
    ],
    S: [
      [ [0,1,1], [1,1,0], [0,0,0] ],
      [ [0,1,0], [0,1,1], [0,0,1] ],
      [ [0,0,0], [0,1,1], [1,1,0] ],
      [ [1,0,0], [1,1,0], [0,1,0] ],
    ],
    Z: [
      [ [1,1,0], [0,1,1], [0,0,0] ],
      [ [0,0,1], [0,1,1], [0,1,0] ],
      [ [0,0,0], [1,1,0], [0,1,1] ],
      [ [0,1,0], [1,1,0], [1,0,0] ],
    ],
    J: [
      [ [1,0,0], [1,1,1], [0,0,0] ],
      [ [0,1,1], [0,1,0], [0,1,0] ],
      [ [0,0,0], [1,1,1], [0,0,1] ],
      [ [0,1,0], [0,1,0], [1,1,0] ],
    ],
    L: [
      [ [0,0,1], [1,1,1], [0,0,0] ],
      [ [0,1,0], [0,1,0], [0,1,1] ],
      [ [0,0,0], [1,1,1], [1,0,0] ],
      [ [1,1,0], [0,1,0], [0,1,0] ],
    ],
  };

  const TYPES = Object.keys(TETROMINOES);

  // Initialize DOM grids
  initBoardDOM();
  initNextDOM();
  updateHUD();

  attachControls();

  // Start new game on load
  newGame();

  /** Functions */
  function createMatrix(h, w, fill = 0) {
    const m = new Array(h);
    for (let i = 0; i < h; i++) m[i] = new Array(w).fill(fill);
    return m;
  }

  function initBoardDOM() {
    boardEl.innerHTML = '';
    const frag = document.createDocumentFragment();
    for (let i = 0; i < BOARD_HEIGHT * BOARD_WIDTH; i++) {
      const div = document.createElement('div');
      div.className = 'cell';
      frag.appendChild(div);
    }
    boardEl.appendChild(frag);
  }

  function initNextDOM() {
    nextEl.innerHTML = '';
    const frag = document.createDocumentFragment();
    for (let i = 0; i < NEXT_SIZE * NEXT_SIZE; i++) {
      const div = document.createElement('div');
      div.className = 'cell';
      frag.appendChild(div);
    }
    nextEl.appendChild(frag);
  }

  function newGame() {
    board = createMatrix(BOARD_HEIGHT, BOARD_WIDTH, 0);
    rngBag = [];
    score = 0;
    linesCleared = 0;
    level = 1;
    dropIntervalMs = levelToDropMs(level);
    current = null;
    next = generateNext();
    state = 'playing';
    lastTime = performance.now();
    dropTimer = 0;
    spawnPiece();
    updateHUD();
    render();
    requestAnimationFrame(loop);
  }

  function updateHUD() {
    scoreEl.textContent = String(score);
    linesEl.textContent = String(linesCleared);
    levelEl.textContent = String(level);
    renderNext();
  }

  function render() {
    const cells = boardEl.children;

    // Base board
    for (let y = 0; y < BOARD_HEIGHT; y++) {
      for (let x = 0; x < BOARD_WIDTH; x++) {
        const idx = y * BOARD_WIDTH + x;
        const cell = cells[idx];
        const v = board[y][x];
        cell.className = 'cell';
        if (v) {
          cell.classList.add('filled', 'type-' + v);
        }
      }
    }

    // Overlay current piece
    if (current) {
      const { matrix, x: px, y: py, type } = current;
      for (let j = 0; j < matrix.length; j++) {
        for (let i = 0; i < matrix[j].length; i++) {
          if (!matrix[j][i]) continue;
          const gx = px + i;
          const gy = py + j;
          if (gy < 0 || gy >= BOARD_HEIGHT || gx < 0 || gx >= BOARD_WIDTH) continue;
          const idx = gy * BOARD_WIDTH + gx;
          const cell = cells[idx];
          cell.classList.add('filled', 'type-' + type);
        }
      }
    }
  }

  function renderNext() {
    const cells = nextEl.children;
    for (let i = 0; i < cells.length; i++) cells[i].className = 'cell';
    if (!next) return;
    const matrix = TETROMINOES[next][0];
    const offset = calcNextOffset(matrix);
    for (let y = 0; y < matrix.length; y++) {
      for (let x = 0; x < matrix[y].length; x++) {
        if (!matrix[y][x]) continue;
        const gx = offset.x + x;
        const gy = offset.y + y;
        if (gx < 0 || gx >= NEXT_SIZE || gy < 0 || gy >= NEXT_SIZE) continue;
        const idx = gy * NEXT_SIZE + gx;
        const cell = cells[idx];
        cell.classList.add('filled', 'type-' + next);
      }
    }
  }

  function calcNextOffset(matrix) {
    // Center the matrix within 4x4 preview
    const w = matrix[0].length;
    const h = matrix.length;
    const x = Math.floor((NEXT_SIZE - w) / 2);
    const y = Math.floor((NEXT_SIZE - h) / 2);
    return { x, y };
  }

  function loop(now) {
    if (state !== 'playing') {
      lastTime = now;
      requestAnimationFrame(loop);
      return;
    }
    const dt = now - lastTime;
    lastTime = now;
    dropTimer += dt;
    if (dropTimer >= dropIntervalMs) {
      dropTimer = 0;
      softDrop();
    }
    requestAnimationFrame(loop);
  }

  function levelToDropMs(lv) {
    // Simple curve: 800 -> 120 ms
    const ms = Math.max(120, 800 - (lv - 1) * 60);
    return ms;
  }

  function spawnPiece() {
    current = createPiece(next);
    next = generateNext();
    // position at top center
    current.x = Math.floor((BOARD_WIDTH - current.matrix[0].length) / 2);
    current.y = -getTopPadding(current.matrix);
    if (collides(board, current.matrix, current.x, current.y)) {
      state = 'gameOver';
      render();
    }
    updateHUD();
  }

  function createPiece(type) {
    return {
      type,
      rotation: 0,
      matrix: cloneMatrix(TETROMINOES[type][0]),
      x: 0,
      y: 0,
    };
  }

  function cloneMatrix(m) { return m.map(row => row.slice()); }

  function getTopPadding(matrix) {
    let top = 0;
    outer: for (let y = 0; y < matrix.length; y++) {
      for (let x = 0; x < matrix[y].length; x++) {
        if (matrix[y][x]) break outer;
      }
      top++;
    }
    return top;
  }

  function generateNext() {
    if (rngBag.length === 0) rngBag = shuffle(TYPES.slice());
    return rngBag.pop();
  }

  function shuffle(arr) {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = (Math.random() * (i + 1)) | 0;
      const t = arr[i]; arr[i] = arr[j]; arr[j] = t;
    }
    return arr;
  }

  function collides(grid, matrix, ox, oy) {
    for (let y = 0; y < matrix.length; y++) {
      for (let x = 0; x < matrix[y].length; x++) {
        if (!matrix[y][x]) continue;
        const gx = ox + x;
        const gy = oy + y;
        if (gx < 0 || gx >= BOARD_WIDTH || gy >= BOARD_HEIGHT) return true;
        if (gy >= 0 && grid[gy][gx]) return true;
      }
    }
    return false;
  }

  function merge(grid, piece) {
    const { matrix, x: ox, y: oy, type } = piece;
    for (let y = 0; y < matrix.length; y++) {
      for (let x = 0; x < matrix[y].length; x++) {
        if (!matrix[y][x]) continue;
        const gx = ox + x;
        const gy = oy + y;
        if (gy >= 0) grid[gy][gx] = type;
      }
    }
  }

  function rotate(matrix) {
    const h = matrix.length; const w = matrix[0].length;
    const res = createMatrix(w, h, 0);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        res[x][h - 1 - y] = matrix[y][x];
      }
    }
    return res;
  }

  function tryRotate(dir = 1) {
    if (!current) return;
    const orig = current.matrix;
    let rotated = orig;
    rotated = dir === 1 ? rotate(rotated) : rotate(rotate(rotate(rotated)));
    // simple wall-kick: try 0, -1, +1
    const kicks = [0, -1, 1, -2, 2];
    for (const dx of kicks) {
      if (!collides(board, rotated, current.x + dx, current.y)) {
        current.matrix = rotated;
        current.x += dx;
        render();
        return;
      }
    }
  }

  function tryMove(dx, dy) {
    if (!current) return false;
    const nx = current.x + dx;
    const ny = current.y + dy;
    if (!collides(board, current.matrix, nx, ny)) {
      current.x = nx; current.y = ny; render();
      return true;
    }
    return false;
  }

  function softDrop() {
    if (!current) return;
    if (!tryMove(0, 1)) {
      // lock
      merge(board, current);
      const cleared = sweepLines();
      if (cleared > 0) {
        const gained = scoreForLines(cleared) * Math.max(1, level);
        score += gained;
        linesCleared += cleared;
        const newLevel = 1 + Math.floor(linesCleared / 10);
        if (newLevel !== level) {
          level = newLevel;
          dropIntervalMs = levelToDropMs(level);
        }
      }
      spawnPiece();
    }
    updateHUD();
    render();
  }

  function scoreForLines(n) {
    if (n === 1) return 100;
    if (n === 2) return 300;
    if (n === 3) return 500;
    if (n === 4) return 800;
    return 0;
  }

  function sweepLines() {
    let removed = 0;
    for (let y = BOARD_HEIGHT - 1; y >= 0; y--) {
      let full = true;
      for (let x = 0; x < BOARD_WIDTH; x++) {
        if (!board[y][x]) { full = false; break; }
      }
      if (full) {
        const row = board.splice(y, 1)[0];
        row.fill(0);
        board.unshift(row);
        removed++;
        y++; // re-check same row index after shift
      }
    }
    return removed;
  }

  function togglePause() {
    if (state === 'playing') state = 'paused';
    else if (state === 'paused') state = 'playing';
  }

  function attachControls() {
    document.addEventListener('keydown', (e) => {
      if (e.code === 'Enter') { e.preventDefault(); newGame(); return; }
      if (e.code === 'KeyP') { e.preventDefault(); togglePause(); return; }
      if (state !== 'playing') return;
      switch (e.code) {
        case 'ArrowLeft':
        case 'KeyA':
          e.preventDefault(); tryMove(-1, 0); break;
        case 'ArrowRight':
        case 'KeyD':
          e.preventDefault(); tryMove(1, 0); break;
        case 'ArrowDown':
        case 'KeyS':
          e.preventDefault(); softDrop(); break;
        case 'ArrowUp':
        case 'Space':
        case 'KeyW':
          e.preventDefault(); tryRotate(1); break;
      }
    });

    newGameBtn && newGameBtn.addEventListener('click', newGame);
    pauseBtn && pauseBtn.addEventListener('click', togglePause);

    leftBtn && leftBtn.addEventListener('click', () => { if (state === 'playing') tryMove(-1, 0); });
    rightBtn && rightBtn.addEventListener('click', () => { if (state === 'playing') tryMove(1, 0); });
    downBtn && downBtn.addEventListener('click', () => { if (state === 'playing') softDrop(); });
    rotateBtn && rotateBtn.addEventListener('click', () => { if (state === 'playing') tryRotate(1); });
    pauseSmallBtn && pauseSmallBtn.addEventListener('click', togglePause);
  }
})();


