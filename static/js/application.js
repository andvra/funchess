let running = true;
let show_id=0;
let svgs = []
let socket=null
let possibleSquares = getPossibleSquares();

function getPossibleSquares(){
	const ret=[];
	for(let i=0;i<8;i++){
		for(let j=0;j<8;j++){
			const cur=String.fromCharCode(97+i)+(j+1).toString();
			ret.push(cur);
		}
	}
	return ret;
}
function render(){
	$('#board').html(svgs[show_id]);
	$('#move-count').html('Displayed move: ' + show_id + ' / ' + (svgs.length-1));
	$("#running").html('Running: ' + running);
}

$(document).ready(function(){
    //connect to the socket server.
    socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    //receive details from server
    socket.on('newsvg', function(msg) {
        svgs=msg.svgs;
		if (running===true){
			show_id=svgs.length-1;
		}
		render();
    });

});

$(document).on('click', 'rect', function(event) {
	getSquareFromRect(event.target);
});

function addMoveStep(square){
	const curVal = $("#move-input").val();
	if(curVal.length>=4 || curVal==square){
		$("#move-input").val('');
	}else{
		$("#move-input").val(curVal+square);
	}
	if($("#move-input").val().length===4){
		move();
	}
}

function getSquareFromRect(rect){
	for(let i=0;i<rect.classList.length;i++){
		const idx=possibleSquares.indexOf(rect.classList[i]);
		if(idx>-1){
			addMoveStep(rect.classList[i]);
		}
	}
}

$(document).on('click', 'use', function(event) {
	getSquareFromRect(event.target.previousSibling);
});

function move(){
	current_move = $("#move-input").val();
	socket.emit('move', {data: current_move});
	$("#move-input").val('');
}

function toggle_run(){
	str='';
	if(running===true){
		str = "Continue";
		running=false;
		$('#previous').removeAttr('disabled');
		$('#next').removeAttr('disabled');
	}else{
		str="Pause";
		running=true;
		show_id=svgs.length-1;
		$('#previous').attr('disabled','disabled');
		$('#next').attr('disabled','disabled');
	}
	render();
	$("#toggle-run").html(str); 
	
}


function do_next(){
	if(svgs.length>show_id+1){
		show_id++;
	}
	render();
}

function do_previous(){
	if(show_id>0){
		show_id--;
	}
	render();
}

function restart_game(){
	socket.emit('restart');
}