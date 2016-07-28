$(document).ready(function() {
    $('#clientdetails').html(function() {
        $.getJSON('/api/clients/'+ZONE+'/'+CLIENT, function(data) {
            client = data['clients'][0];
            $('#clientdetails').html('<h4>'+client['name']+'</h4><pre>'+JSON.stringify(client,null,2)+'</pre>');
        })
    })
    $.fn.dataTable.enum( [ 'Critical', 'Warning', 'OK' ] );
    document.clientevents = $('#clientevents').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        'order': [
            [ 0, 'asc' ],
            [ 1, 'desc' ],
        ],
        'ajax': {
            'url': '/api/clients/'+ZONE+'/'+CLIENT+'/results',
            'dataSrc': function(json) {
                json = json['results'];
                return_data = new Array();
                for (var i=0; i<json.length; i++) {
                    var row = json[i];
                    return_data.push({
                        'status': row['status'].capitalize(),
                        'check_name': row['check_name'],
                        'check_output': '<a href="/clients/'+row['zone_name']+'/'+row['client_name']+'/events/'+row['check_name']+'">'+row['output']+'</a>',
                        'timestamp': '<time class="timeago" datetime="'+row['last_poll_time']+'Z">'+row['last_poll_time']+'Z</time>',
                    })
                }
                return return_data;
            }
        },
        'columns': [
            {data: 'status'},
            {data: 'check_name'},
            {data: 'check_output'},
            {data: 'timestamp'},
        ],
        'rowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            $('td:first', nRow).addClass(hourglass.statusclasses[aData['status']]);
        },
    }).on('draw.dt', function() {
        $('time.timeago').timeago();
    });
})
