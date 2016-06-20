$(document).ready(function() {
    $('#clientdetails').html(function() {
        $.getJSON('/api/clients/'+ZONE+'/'+CLIENT, function(data) {
            client = data['clients'][0];
            $('#clientdetails').html('<h4>'+client['name']+'</h4><pre>'+JSON.stringify(client,null,2)+'</pre>');
        })
    })
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
                    row['check']['status'] = hourglass.statusnames[row['check']['status']];
                    if ( row['check']['status'] === undefined ) {
                        row['check']['status'] = 'Unknown';
                    }
                    var d = new Date(0);
                    d.setUTCSeconds(row['check']['issued']);
                    return_data.push({
                        'status': row['check']['status'],
                        'check_name': row['check']['name'],
                        'check_output': '<a href="/clients/'+row['zone_name']+'/'+row['client']+'/events/'+row['check']['name']+'">'+row['check']['output']+'</a>',
                        'timestamp': '<time class="timeago" datetime="'+d.toISOString()+'">'+d+'</time>',
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
        'columnDefs': [
            { type: 'enum', targets: [0]},
        ],
        'rowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            $('td:first', nRow).addClass(hourglass.statusclasses[aData['status']]);
        },
    }).on('draw.dt', function() {
        $('time.timeago').timeago();
    });
})
