$(document).ready(function() {

	$('.loading').hide();

	$('.logging_out').hide();

	$('#selection_tree').tree();

	$('#selectAll').prop('checked', true);

	$('#selection_tree input[type="checkbox"]').prop('checked', true);

	$('#id_component_option').val('all');

	$('#selection_tree').hide();

	$('input[name="select"]').change(function() {
		if ($(this).val() == 'partial') {
			$('#selection_tree').slideDown('slow');
			$('#id_component_option').val('partial');
		} else {
			$('#selection_tree').slideUp('slow');
			$('#id_component_option').val('all');
		}
	});		

	$('.component_type_display').change(function() {

		var component_id = $(this).attr('name');

		if( $(this).prop('checked') ){
			$('#id_component_type-' + component_id + '-include_all').prop('checked', true);
		} else {
			$('#id_component_type-' + component_id + '-include_all').prop('checked', false);
		}

	});

	$('.component_display').change(function() {

		var component_id = $(this).attr('name');
		var checkbox_id = $('input[value="' + component_id + '"]').attr('id');
		
		checkbox_id = checkbox_id.replace('-id','-include');

		if( $(this).prop('checked') ){
			$('#'+checkbox_id).prop('checked', true);
		} else {
			$('#'+checkbox_id).prop('checked', false);
		}

	});
});

function hideTable(){
	$('.login_table').hide();
	$('#select_components').hide();
	$('.messages').hide();
	$('.loading').show();
}
function showTable(){
	$('.login_table').show();
	$('#select_components').show();
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