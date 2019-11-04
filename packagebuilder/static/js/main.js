$(document).ready(function() {

	$('.loading').hide();
	$('.logging_out').hide();
});


function showLogout(){
	$('.login_table').hide();
	$('.messages').hide();
	$('.logging_out').show();
}

function hideLogout(){
	$('.login_table').show();
	$('.messages').show();
	$('.logging_out').hide();
}