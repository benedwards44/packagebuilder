$(document).ready(function() {

    $('.loading').hide();
    $('.logging_out').hide();
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