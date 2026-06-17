(function () {
  /* ── Constants ───────────────────────────────────────────────────────── */
  const MIN_CELL_PX  = 18;   // smallest cell before we scroll instead of shrinking
  const MAX_CELL_PX  = 32;   // largest cell (comfortable for small puzzles)
  const THIN_PX      = 1;    // thin border
  const THICK_PX     = 2;    // thick border (every 5 cells + outer)
  const MAX_HINT_H_PX = 180; // max height of the column-hint area
  const HINT_PAD_PX  = 4;    // padding inside each hint cell

  /* ── State ────────────────────────────────────────────────────────────── */
  let rows, cols, state, hints, details;
  let cellPx;
  let isDragging   = false;
  let dragMode     = null; // 'fill' | 'mark' | 'erase-fill' | 'erase-mark'
  let dragStartVal = null;

  /* ── DOM refs ─────────────────────────────────────────────────────────── */
  const $ng        = document.getElementById('nonogram');
  const $corner    = document.getElementById('corner');
  const $colHints  = document.getElementById('col-hints');
  const $rowHints  = document.getElementById('row-hints');
  const $grid      = document.getElementById('grid');
  const $details   = document.getElementById('details');
  const $errorMsg  = document.getElementById('error-msg');

  /* ── Boot ─────────────────────────────────────────────────────────────── */
  fetchPuzzle();  
  /* ── Get URL parameters ────────────────────────────────────────────── */
  function getUrlParams() {
    const params = new URLSearchParams(window.location.search);
    return {
      rows: params.get('rows') ? parseInt(params.get('rows')) : undefined,
      cols: params.get('cols') ? parseInt(params.get('cols')) : undefined,
      density: params.get('density') ? parseFloat(params.get('density')) : undefined,
      random_function: params.get('random_function') || undefined,
      frequency: params.get('frequency') ? parseInt(params.get('frequency')) : undefined,
      seed: params.get('seed') ? params.get('seed') : undefined
    };
  }
  /* ── Fetch ────────────────────────────────────────────────────────────── */
  async function fetchPuzzle() {
    $ng.classList.add('loading');
    $errorMsg.style.display = 'none';
    try {
      const params = getUrlParams();
      const queryString = new URLSearchParams(params).toString();
      const res  = await fetch(`/new?${queryString}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      initPuzzle(data);
    } catch (e) {
      $errorMsg.textContent = `Failed to load puzzle: ${e.message}`;
      $errorMsg.style.display = 'block';
    } finally {
      $ng.classList.remove('loading');
    }
  }

  /* ── Init ─────────────────────────────────────────────────────────────── */
  function initPuzzle(data) {
    hints   = data.hints;   // [ [row hint arrays], [col hint arrays] ]
    details = data.details;
    rows    = details.rows;
    cols    = details.cols;

    // Build fresh state (all 0)
    state = Array.from({ length: rows }, () => new Array(cols).fill(0));

    computeCellSize();
    renderHints();
    renderGrid();
    renderDetails();
    attachGridEvents();
  }

  /* ── Cell size calculation ────────────────────────────────────────────── */
  function computeCellSize() {
    const availW = window.innerWidth  - 64;   // rough padding budget
    const availH = window.innerHeight - 64;
    // Dedicate ~40% of space to hints; the rest to the grid
    const budgetW = availW * 0.7 / cols;
    const budgetH = availH * 0.7 / rows;
    cellPx = Math.min(MAX_CELL_PX, Math.max(MIN_CELL_PX, Math.floor(Math.min(budgetW, budgetH))));
  }

  /* ── Border helpers ───────────────────────────────────────────────────── */
  // Returns border thickness (px) for a given 0-based index boundary.
  // boundary i = line between cell (i-1) and cell i (i=0 is outer left/top).
  function borderW(i, total) {
    if (i === 0 || i === total) return THICK_PX;   // outer edges
    if (i % 5 === 0)            return THICK_PX;   // every-5 separator
    return THIN_PX;
  }

  /* ── Render hints ─────────────────────────────────────────────────────── */
  function renderHints() {
    $colHints.innerHTML = '';
    $rowHints.innerHTML = '';

    const colHintData = hints[1]; // array of cols → each is array of numbers
    const rowHintData = hints[0]; // array of rows → each is array of numbers

    // ── Column hints ──────────────────────────────────────────────────────
    // Max numbers in any col hint → determines hint area height
    const maxColLen = Math.max(...colHintData.map(h => h.length), 1);
    // Each number gets cellPx height; cap at MAX_HINT_H_PX
    const hintAreaH = Math.min(maxColLen * cellPx, MAX_HINT_H_PX);

    $colHints.style.height = `${hintAreaH}px`;

    colHintData.forEach((nums, ci) => {
      const el = document.createElement('div');
      el.className = 'col-hint';
      el.style.width  = `${cellPx}px`;
      el.style.height = `${hintAreaH}px`;
      el.style.paddingBottom = `${HINT_PAD_PX}px`;
      // left border mirrors the cell grid vertical lines
      el.style.borderLeft = `${borderW(ci, cols)}px solid #555`;
      if (ci === cols - 1) el.style.borderRight = `${THICK_PX}px solid #555`;

      nums.forEach((n, ni) => {
        const span = document.createElement('span');
        span.className   = 'hint-num';
        span.textContent = n;
        span.style.lineHeight = `${cellPx}px`;
        span.dataset.axis = 'col';
        span.dataset.idx  = ci;
        span.dataset.num  = ni;
        span.addEventListener('click', onHintClick);
        el.appendChild(span);
      });
      $colHints.appendChild(el);
    });

    // ── Row hints ─────────────────────────────────────────────────────────
    const maxRowLen = Math.max(...rowHintData.map(h => h.length), 1);
    const hintAreaW = maxRowLen * cellPx;

    rowHintData.forEach((nums, ri) => {
      const el = document.createElement('div');
      el.className = 'row-hint';
      el.style.height     = `${cellPx}px`;
      el.style.width      = `${hintAreaW}px`;
      el.style.paddingRight = `${HINT_PAD_PX}px`;
      el.style.gap        = `${Math.max(2, Math.floor(cellPx * 0.15))}px`;
      // top border mirrors the cell grid horizontal lines
      el.style.borderTop  = `${borderW(ri, rows)}px solid #555`;
      if (ri === rows - 1) el.style.borderBottom = `${THICK_PX}px solid #555`;

      nums.forEach((n, ni) => {
        const span = document.createElement('span');
        span.className   = 'hint-num';
        span.textContent = n;
        span.dataset.axis = 'row';
        span.dataset.idx  = ri;
        span.dataset.num  = ni;
        span.addEventListener('click', onHintClick);
        el.appendChild(span);
      });
      $rowHints.appendChild(el);
    });

    // ── Corner spacer ─────────────────────────────────────────────────────
    const rowHintAreaW = Math.max(...rowHintData.map(h => h.length), 1) * cellPx;
    $corner.style.width  = `${rowHintAreaW}px`;
    $corner.style.height = `${hintAreaH}px`;
    $corner.style.flexShrink = 0;
  }

  /* ── Render grid ──────────────────────────────────────────────────────── */
  function renderGrid() {
    $grid.innerHTML = '';
    $grid.style.gridTemplateColumns = `repeat(${cols}, ${cellPx}px)`;
    $grid.style.gridTemplateRows    = `repeat(${rows}, ${cellPx}px)`;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const cell = document.createElement('div');
        cell.className      = 'cell';
        cell.dataset.r      = r;
        cell.dataset.c      = c;
        cell.style.width    = `${cellPx}px`;
        cell.style.height   = `${cellPx}px`;

        // Borders: each cell owns its top and left border;
        // rightmost col owns right, bottommost row owns bottom.
        cell.style.borderTop    = `${borderW(r, rows)}px solid #555`;
        cell.style.borderLeft   = `${borderW(c, cols)}px solid #555`;
        if (c === cols - 1) cell.style.borderRight  = `${THICK_PX}px solid #555`;
        if (r === rows - 1) cell.style.borderBottom = `${THICK_PX}px solid #555`;

        // Render current state
        applyCellState(cell, state[r][c]);
        $grid.appendChild(cell);
      }
    }
  }

  function applyCellState(cell, val) {
    cell.classList.remove('filled', 'marked');
    if (val === 1)  cell.classList.add('filled');
    if (val === -1) cell.classList.add('marked');
  }

  function cellEl(r, c) {
    return $grid.querySelector(`.cell[data-r="${r}"][data-c="${c}"]`);
  }

  /* ── Drag logic ───────────────────────────────────────────────────────── */
  function cycleStateLeft(current) {
    // left-click: empty→filled→empty
    return current === 1 ? 0 : 1;
  }
  function cycleStateRight(current) {
    // right-click: empty→marked→empty
    return current === -1 ? 0 : -1;
  }

  function attachGridEvents() {
    $grid.addEventListener('mousedown', onMouseDown);
    $grid.addEventListener('mouseover', onMouseOver);
    window.addEventListener('mouseup',  onMouseUp);
    $grid.addEventListener('contextmenu', e => e.preventDefault());
  }

  function getCellCoords(e) {
    const el = e.target.closest('.cell');
    if (!el) return null;
    return { r: +el.dataset.r, c: +el.dataset.c, el };
  }

  function onMouseDown(e) {
    if (e.button !== 0 && e.button !== 2) return;
    e.preventDefault();
    const hit = getCellCoords(e);
    if (!hit) return;

    isDragging   = true;
    const { r, c, el } = hit;
    const current = state[r][c];

    if (e.button === 0) {
      const next = cycleStateLeft(current);
      dragMode     = next === 1  ? 'fill'       : 'erase-fill';
      dragStartVal = next;
    } else {
      const next = cycleStateRight(current);
      dragMode     = next === -1 ? 'mark'       : 'erase-mark';
      dragStartVal = next;
    }

    applyToCell(r, c, el);
  }

  function onMouseOver(e) {
    if (!isDragging) return;
    const hit = getCellCoords(e);
    if (!hit) return;
    applyToCell(hit.r, hit.c, hit.el);
  }

  function onMouseUp() { isDragging = false; dragMode = null; }

  function applyToCell(r, c, el) {
    // Only overwrite cells that are in the correct starting state for this drag
    const current = state[r][c];
    if (dragMode === 'fill'       && current !== 0  && current !== 1)  return;
    if (dragMode === 'erase-fill' && current !== 1  && current !== 0)  return;
    if (dragMode === 'mark'       && current !== 0  && current !== -1) return;
    if (dragMode === 'erase-mark' && current !== -1 && current !== 0)  return;

    state[r][c] = dragStartVal;
    applyCellState(el, dragStartVal);
  }

  /* ── Hint click ───────────────────────────────────────────────────────── */
  function onHintClick(e) {
    e.stopPropagation();
    e.target.classList.toggle('highlighted');
  }

  /* ── Details ──────────────────────────────────────────────────────────── */
  function renderDetails() {
    if (!details) return;
    $details.textContent =
      `${details.rows}×${details.cols}  ·  seed ${details.seed}  ·  ` +
      `density ${details.density}  ·  ${details.random_function}  ·  freq ${details.frequency}`;
  }

})();