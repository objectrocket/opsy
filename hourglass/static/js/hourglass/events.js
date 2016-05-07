String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

$(document).ready(function() {
    statusclasses = {
        'OK': 'success',
        'Warning': 'warning',
        'Critical': 'danger'
    }
    statusnames = {
        0: 'OK',
        1: 'Warning',
        2: 'Critical'
    }
    document.dt = $('table.dt').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        //'stateSave' : true,
        'columnDefs': [
            {
                "targets": [ 0 ],
                "visible": false,
                "searchable": true
            },
        ],
        'order': [
            [ 0, 'asc' ],
            [ 5, 'desc' ],
        ],
        'ajax': {
            url: '/api/events',
            dataSrc: 'events'
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-8'<'#filters'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'columns': [
            {data: 'check.status',
             name: 'status'},
            {data: 'datacenter',
             name: 'datacenter'},
            {data: 'client.name',
             name: 'source'},
            {data: 'check.name',
             name: 'check-name'},
            {data: 'check.output',
             name: 'check-output'},
            {data: 'occurrences',
             name: 'occurrences'},
            {data: 'timestamp',
             name: 'timestamp'},
        ],
        'fnRowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            $(nRow).addClass(statusclasses[aData['check']['status']]);
            var d = new Date(0);
            d.setUTCSeconds(aData['timestamp']);
            $('td:last', nRow).html('<time class="timeago" datetime="'+d.toISOString()+'">'+d+'</time>');
        },
        'fnDrawCallback': function(oSettings){
            $('time.timeago').timeago();
        },
        'createdRow': function(nRow, aData, iDataIndex) {
            aData['check']['status'] = statusnames[aData['check']['status']];
            $(nRow).data('href', aData['href']);
            $(nRow).click(function() {
                window.open($(this).data("href"), '_blank');
            });
        },
        'initComplete': function () {
            filteredColumns = [
                'status:name',
                'datacenter:name',
                'check-name:name'
            ]
            var columns = this.api().settings().init().columns;
            $('#filters').addClass('form-inline');
            this.api().columns(filteredColumns).every(function(index) {
                var name = columns[index].name;
                var column = this;
                var filterdiv = $('<div class="form-group"></div>').appendTo( $('#filters') );
                var filterlabel = $('<label for="'+name+'-filter">'+name.capitalize()+'</label>').appendTo( $(filterdiv) );
                var select = $('<select class="form-control" id="'+name+'-filter"><option value=""></option></select>')
                    .appendTo( $(filterdiv) )
                    .on( 'change', function () {
                        var val = $.fn.dataTable.util.escapeRegex(
                            $(this).val()
                        );
 
                        column
                            .search( val ? '^'+val+'$' : '', true, false )
                            .draw();
                    } );
 
                column.data().unique().sort().each( function ( d, j ) {
                    select.append( '<option value="'+d+'">'+d+'</option>' )
                } );
            });
            setInterval( function() {
                document.dt.ajax.reload(null, false);
            }, 30000);
        }
    });
});
