let running = true;
let show_id = 0;
let svgs = [];
let socket = null;
let possibleSquares = getPossibleSquares();

function getPossibleSquares() {
  const ret = [];
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      const cur = String.fromCharCode(97 + i) + (j + 1).toString();
      ret.push(cur);
    }
  }
  return ret;
}

function render() {
  $('#board').html(svgs[show_id]);
  $('#move-count').html(
    'Displayed move: ' + show_id + ' / ' + (svgs.length - 1)
  );
  $('#running').html('Running: ' + running);
}

$(document).ready(function() {
  // Connect to the socket server
  socket = io.connect(
    'http://' + document.domain + ':' + location.port + '/chessgame'
  );

  //  Subscribe to messages from server
  socket.on('newsvg', function(msg) {
    svgs = msg.svgs;
    if (running === true) {
      update_show_id(svgs.length - 1 - show_id);
    }
    render();
  });
});

$(document).on('click', 'rect', function(event) {
  getSquareFromRect(event.target);
});

function addMoveStep(square) {
  // Don't perform move if we're reviewing the board
  if (running === false) {
    return;
  }
  const curVal = $('#move-input').val();
  if (curVal.length >= 4 || curVal == square) {
    clearMoveStep();
  } else {
    $('#move-input').val(curVal + square);
  }
  if ($('#move-input').val().length === 4) {
    move();
  }
}

function clearMoveStep() {
  $('#move-input').val('');
}

function getSquareFromRect(rect) {
  for (let i = 0; i < rect.classList.length; i++) {
    const idx = possibleSquares.indexOf(rect.classList[i]);
    if (idx > -1) {
      addMoveStep(rect.classList[i]);
    }
  }
}

$(document).on('click', 'use', function(event) {
  getSquareFromRect(event.target.previousSibling);
});

function move() {
  current_move = $('#move-input').val();
  socket.emit('human_move', { data: current_move });
  clearMoveStep();
}

function do_continue() {
  running = true;
  update_show_id(svgs.length - 1 - show_id);
  $('#continue').prop('disabled', true);
  render();
}

function pause() {
  running = false;
  clearMoveStep();
  $('#continue').prop('disabled', false);
}

function do_next() {
  update_show_id(1);
  render();
}

function do_previous() {
  // Pause auto-change image
  pause();
  update_show_id(-1);
  render();
}

function restart_game() {
  socket.emit('restart');
}

function update_show_id(diff) {
  const new_show_id = show_id + diff;
  $('#previous').prop('disabled', false);
  $('#next').prop('disabled', false);

  if (new_show_id < 0 || new_show_id >= svgs.length) {
    console.log('Invalid ID');
    return;
  } else if (new_show_id === 0) {
    $('#previous').prop('disabled', true);
  } else if (new_show_id === svgs.length - 1) {
    $('#next').prop('disabled', true);
  }

  show_id = new_show_id;
}
