$(document).ready(function() {
    $('table.dt').DataTable({
        'lengthMenu': [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
        'stateSave' : true,
    });
    $('.link-row').click(function() {
        window.document.location = $(this).data("href");
    });
});
