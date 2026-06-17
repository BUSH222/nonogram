(function () {
  const MIN_CELL_PX = 18;
  const MAX_CELL_PX = 32;
  const THIN_PX = 1;
  const THICK_PX = 2;
  const MAX_HINT_H_PX = 180;
  const HINT_PAD_PX = 4;

  const elements = {
    nonogram: document.getElementById('nonogram'),
    corner: document.getElementById('corner'),
    colHints: document.getElementById('col-hints'),
    rowHints: document.getElementById('row-hints'),
    grid: document.getElementById('grid'),
    details: document.getElementById('details'),
    statusMsg: document.getElementById('status-msg'),
    errorMsg: document.getElementById('error-msg'),
  };

  const state = {
    gameId: null,
    rows: 0,
    cols: 0,
    board: [],
    hints: null,
    details: null,
    solved: false,
    cellPx: MIN_CELL_PX,
    dragging: false,
    dragValue: 0,
    dragMode: null,
    socket: null,
    socketIntentionalClose: false,
    reloadRequired: false,
    boardReady: false,
    failureAnnounced: false,
    solvedAnnounced: false,
    listenersAttached: false,
  };

  const gameId = new URLSearchParams(window.location.search).get('id');

  if (!gameId) {
    announceFailure('Missing game id in the URL.');
    return;
  }

  state.gameId = gameId;
  attachRecoveryListeners();
  attachBoardListeners();
  connectSocket();

  window.addEventListener('resize', () => {
    if (!state.boardReady) {
      return;
    }

    computeCellSize();
    renderBoard();
  });

  function getSocketUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${window.location.host}/ws/${state.gameId}`;
  }

  function connectSocket() {
    elements.nonogram.classList.add('loading');
    elements.nonogram.setAttribute('aria-busy', 'true');
    setStatusMessage('Connecting to saved game...');
    setErrorMessage('');
    
    const socket = new WebSocket(getSocketUrl());
    state.socket = socket;
    setStatusMessage('');

    socket.addEventListener('open', () => {
      sendMessage({ type: 'get_state' });
    });

    socket.addEventListener('message', handleSocketMessage);
    socket.addEventListener('error', () => {
      announceFailure('Something failed while connecting to the game.');
    });
    socket.addEventListener('close', () => {
      if (state.socketIntentionalClose || state.reloadRequired || state.solvedAnnounced) {
        return;
      }

      announceFailure('The connection to the game was lost.');
    });
  }

  function handleSocketMessage(event) {
    let message;

    try {
      message = JSON.parse(event.data);
    } catch (error) {
      announceFailure('Something failed while reading the game state.');
      return;
    }

    if (!message || typeof message !== 'object') {
      return;
    }

    if (message.received) {
      return;
    }

    if (message.error) {
      announceFailure(message.error);
      return;
    }

    if (message.type === 'state') {
      hydrateFromServer(message.payload || {});
      return;
    }

    if (message.type === 'update') {
      hydrateFromServer(message.payload || {});
      return;
    }

    if (message.type === 'reset') {
      hydrateFromServer({
        state: message.payload?.state,
        height: state.rows,
        width: state.cols,
        hints: state.hints,
        details: state.details,
        solved: false,
      });
      return;
    }

    if (message.type === 'delete') {
      state.socketIntentionalClose = true;
      state.solved = true;
      state.boardReady = false;
      setStatusMessage('Game deleted.', 'solved');
      return;
    }
  }

  function hydrateFromServer(payload) {
    const height = Number(payload.height ?? payload.details?.rows ?? payload.state?.length ?? 0);
    const width = Number(payload.width ?? payload.details?.cols ?? payload.state?.[0]?.length ?? 0);

    if (!height || !width) {
      announceFailure('Something failed while loading the puzzle.');
      return;
    }

    state.rows = height;
    state.cols = width;
    state.hints = payload.hints || state.hints || [[], []];
    state.details = {
      ...(payload.details || {}),
      rows: height,
      cols: width,
    };
    state.solved = Boolean(payload.solved);
    state.board = normalizeBoard(payload.state, height, width);
    state.boardReady = true;

    computeCellSize();
    renderBoard();
    elements.nonogram.classList.remove('loading');
    elements.nonogram.setAttribute('aria-busy', 'false');
    setErrorMessage('');
    if (payload.solved) {
      handleSolved();
    }
  }

  function normalizeBoard(board, height, width) {
    if (!Array.isArray(board)) {
      return Array.from({ length: height }, () => new Array(width).fill(0));
    }

    return Array.from({ length: height }, (_, rowIndex) => {
      const row = Array.isArray(board[rowIndex]) ? board[rowIndex] : [];
      return Array.from({ length: width }, (_, columnIndex) => Number(row[columnIndex] ?? 0));
    });
  }

  function computeCellSize() {
    const availableWidth = window.innerWidth - 64;
    const availableHeight = window.innerHeight - 64;
    const budgetWidth = (availableWidth * 0.7) / state.cols;
    const budgetHeight = (availableHeight * 0.7) / state.rows;
    state.cellPx = Math.min(MAX_CELL_PX, Math.max(MIN_CELL_PX, Math.floor(Math.min(budgetWidth, budgetHeight))));
  }

  function borderWidth(index, total) {
    if (index === 0 || index === total) {
      return THICK_PX;
    }

    if (index % 5 === 0) {
      return THICK_PX;
    }

    return THIN_PX;
  }

  function renderBoard() {
    renderHints();
    renderGrid();
    renderDetails();
  }

  function renderHints() {
    const hints = state.hints || [[], []];
    const rowHints = hints[0] || [];
    const colHints = hints[1] || [];

    elements.colHints.innerHTML = '';
    elements.rowHints.innerHTML = '';

    const maxColumnLength = Math.max(...colHints.map((hint) => hint.length), 1);
    const hintHeight = Math.min(maxColumnLength * state.cellPx, MAX_HINT_H_PX);
    elements.colHints.style.height = `${hintHeight}px`;

    colHints.forEach((numbers, columnIndex) => {
      const hintColumn = document.createElement('div');
      hintColumn.className = 'col-hint';
      hintColumn.style.width = `${state.cellPx}px`;
      hintColumn.style.height = `${hintHeight}px`;
      hintColumn.style.paddingBottom = `${HINT_PAD_PX}px`;
      hintColumn.style.borderLeft = `${borderWidth(columnIndex, state.cols)}px solid #555`;
      if (columnIndex === state.cols - 1) {
        hintColumn.style.borderRight = `${THICK_PX}px solid #555`;
      }

      numbers.forEach((number, hintIndex) => {
        const hintNumber = document.createElement('span');
        hintNumber.className = 'hint-num';
        hintNumber.textContent = number;
        hintNumber.style.lineHeight = `${state.cellPx}px`;
        hintNumber.dataset.axis = 'col';
        hintNumber.dataset.idx = columnIndex;
        hintNumber.dataset.num = hintIndex;
        hintNumber.addEventListener('click', handleHintClick);
        hintColumn.appendChild(hintNumber);
      });

      elements.colHints.appendChild(hintColumn);
    });

    const maxRowLength = Math.max(...rowHints.map((hint) => hint.length), 1);
    const hintWidth = maxRowLength * state.cellPx;

    rowHints.forEach((numbers, rowIndex) => {
      const hintRow = document.createElement('div');
      hintRow.className = 'row-hint';
      hintRow.style.height = `${state.cellPx}px`;
      hintRow.style.width = `${hintWidth}px`;
      hintRow.style.paddingRight = `${HINT_PAD_PX}px`;
      hintRow.style.gap = `${Math.max(2, Math.floor(state.cellPx * 0.15))}px`;
      hintRow.style.borderTop = `${borderWidth(rowIndex, state.rows)}px solid #555`;
      if (rowIndex === state.rows - 1) {
        hintRow.style.borderBottom = `${THICK_PX}px solid #555`;
      }

      numbers.forEach((number, hintIndex) => {
        const hintNumber = document.createElement('span');
        hintNumber.className = 'hint-num';
        hintNumber.textContent = number;
        hintNumber.dataset.axis = 'row';
        hintNumber.dataset.idx = rowIndex;
        hintNumber.dataset.num = hintIndex;
        hintNumber.addEventListener('click', handleHintClick);
        hintRow.appendChild(hintNumber);
      });

      elements.rowHints.appendChild(hintRow);
    });

    elements.corner.style.width = `${hintWidth}px`;
    elements.corner.style.height = `${hintHeight}px`;
    elements.corner.style.flexShrink = '0';
  }

  function renderGrid() {
    elements.grid.innerHTML = '';
    elements.grid.style.gridTemplateColumns = `repeat(${state.cols}, ${state.cellPx}px)`;
    elements.grid.style.gridTemplateRows = `repeat(${state.rows}, ${state.cellPx}px)`;

    const fragment = document.createDocumentFragment();

    for (let rowIndex = 0; rowIndex < state.rows; rowIndex += 1) {
      for (let columnIndex = 0; columnIndex < state.cols; columnIndex += 1) {
        const cell = document.createElement('div');
        cell.className = 'cell';
        cell.dataset.r = rowIndex;
        cell.dataset.c = columnIndex;
        cell.style.width = `${state.cellPx}px`;
        cell.style.height = `${state.cellPx}px`;
        cell.style.borderTop = `${borderWidth(rowIndex, state.rows)}px solid #555`;
        cell.style.borderLeft = `${borderWidth(columnIndex, state.cols)}px solid #555`;

        if (columnIndex === state.cols - 1) {
          cell.style.borderRight = `${THICK_PX}px solid #555`;
        }

        if (rowIndex === state.rows - 1) {
          cell.style.borderBottom = `${THICK_PX}px solid #555`;
        }

        applyCellState(cell, state.board[rowIndex][columnIndex]);
        fragment.appendChild(cell);
      }
    }

    elements.grid.appendChild(fragment);
  }

  function renderDetails() {
    if (!state.details) {
      elements.details.textContent = '';
      return;
    }

    const details = state.details;
    const parts = [
      `${details.rows}×${details.cols}`,
      `seed ${details.seed}`,
      `density ${details.density}`,
      details.random_function,
      `freq ${details.frequency}`,
    ].filter(Boolean);

    elements.details.textContent = parts.join('  ·  ');
  }

  function applyCellState(cell, value) {
    cell.classList.remove('filled', 'marked');

    if (value === 1) {
      cell.classList.add('filled');
      return;
    }

    if (value === -1) {
      cell.classList.add('marked');
    }
  }

  function attachBoardListeners() {
    if (state.listenersAttached) {
      return;
    }

    state.listenersAttached = true;
    elements.grid.addEventListener('mousedown', handleGridMouseDown);
    elements.grid.addEventListener('mouseover', handleGridMouseOver);
    elements.grid.addEventListener('contextmenu', (event) => event.preventDefault());
    window.addEventListener('mouseup', handleGridMouseUp);
  }

  function attachRecoveryListeners() {
    document.addEventListener('pointerdown', handleReloadRecovery, true);
    document.addEventListener('keydown', handleReloadRecovery, true);
  }

  function handleReloadRecovery(event) {
    if (!state.reloadRequired) {
      return;
    }

    event.preventDefault();
    event.stopPropagation();
    window.location.reload();
  }

  function handleGridMouseDown(event) {
    if (!canInteract()) {
      return;
    }

    if (event.button !== 0 && event.button !== 2) {
      return;
    }

    event.preventDefault();

    const hit = getCellHit(event);
    if (!hit) {
      return;
    }

    state.dragging = true;

    const currentValue = state.board[hit.row][hit.column];
    if (event.button === 0) {
      const nextValue = currentValue === 1 ? 0 : 1;
      state.dragMode = nextValue === 1 ? 'fill' : 'erase-fill';
      state.dragValue = nextValue;
    } else {
      const nextValue = currentValue === -1 ? 0 : -1;
      state.dragMode = nextValue === -1 ? 'mark' : 'erase-mark';
      state.dragValue = nextValue;
    }

    applyMove(hit.row, hit.column, hit.element);
  }

  function handleGridMouseOver(event) {
    if (!state.dragging || !canInteract()) {
      return;
    }

    const hit = getCellHit(event);
    if (!hit) {
      return;
    }

    applyMove(hit.row, hit.column, hit.element);
  }

  function handleGridMouseUp() {
    state.dragging = false;
    state.dragMode = null;
  }

  function getCellHit(event) {
    const cell = event.target.closest('.cell');
    if (!cell) {
      return null;
    }

    return {
      row: Number(cell.dataset.r),
      column: Number(cell.dataset.c),
      element: cell,
    };
  }

  function applyMove(rowIndex, columnIndex, element) {
    const currentValue = state.board[rowIndex][columnIndex];

    if (state.dragMode === 'fill' && currentValue !== 0 && currentValue !== 1) {
      return;
    }

    if (state.dragMode === 'erase-fill' && currentValue !== 1 && currentValue !== 0) {
      return;
    }

    if (state.dragMode === 'mark' && currentValue !== 0 && currentValue !== -1) {
      return;
    }

    if (state.dragMode === 'erase-mark' && currentValue !== -1 && currentValue !== 0) {
      return;
    }

    if (currentValue === state.dragValue) {
      return;
    }

    state.board[rowIndex][columnIndex] = state.dragValue;
    applyCellState(element, state.dragValue);

    if (!sendMessage({
      type: 'update',
      payload: {
        x: rowIndex,
        y: columnIndex,
        value: state.dragValue,
      },
    })) {
      return;
    }
  }

  function handleHintClick(event) {
    event.stopPropagation();
    event.target.classList.toggle('highlighted');
  }

  function handleSolved() {
    if (state.solvedAnnounced) {
      return;
    }

    state.solvedAnnounced = true;
    state.solved = true;
    state.dragging = false;
    state.dragMode = null;
    setStatusMessage('The nonogram has been solved.', 'solved');
    alert('The nonogram has been solved.');

    state.socketIntentionalClose = true;
    sendMessage({ type: 'delete' });
  }

  function canInteract() {
    return state.boardReady && !state.reloadRequired && !state.solved;
  }

  function sendMessage(message) {
    if (!state.socket || state.socket.readyState !== WebSocket.OPEN) {
      announceFailure('Something failed while sending a game update.');
      return false;
    }

    try {
      state.socket.send(JSON.stringify(message));
      return true;
    } catch (error) {
      announceFailure('Something failed while sending a game update.');
      return false;
    }
  }

  function announceFailure(message) {
    if (state.failureAnnounced) {
      state.reloadRequired = true;
      state.boardReady = false;
      return;
    }

    state.failureAnnounced = true;
    state.reloadRequired = true;
    state.boardReady = false;
    state.dragging = false;
    state.dragMode = null;
    elements.nonogram.classList.remove('loading');
    setStatusMessage(message, 'error');
    setErrorMessage(message);
    alert(message);
  }

  function setStatusMessage(message, kind = 'normal') {
    elements.statusMsg.textContent = message;
    elements.statusMsg.dataset.state = kind;
  }

  function setErrorMessage(message) {
    elements.errorMsg.textContent = message;
    elements.errorMsg.style.display = message ? 'block' : 'none';
  }
})();
