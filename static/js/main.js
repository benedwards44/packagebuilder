$(document).ready(function() {
    $('.loading').hide();
    $('.logging_out').hide();

    $('#id_environment').change(function() {
		if ( $(this).val() == 'Custom' ) {
			$('.custom-domain').show();
            $("#id_domain").prop('required', true);
		}
		else {
			$('.custom-domain').hide();
            $("#id_domain").prop('required', false);
		}
	});
});

function hideTable(){
    $('.login_table').hide();
    $('.messages').hide();
    $('.loading').show();
}
function showTable(){
    $('.login_table').show();
    $('.messages').show();
    $('.loading').hide();
}

function showLogout(){
    $('.login_table').hide();
    $('#select_components').hide();
    $('.messages').hide();
    $('.logging_out').show();
}

function hideLogout(){
    $('.login_table').show();
    $('#select_components').show();
    $('.messages').show();
    $('.logging_out').hide();
}