$(document).ready(function() {
    $('#clientdetails').html(function() {
        var jqxhr = $.getJSON('/api/clients/'+ZONE+'/'+CLIENT+'/events/'+CHECK, function(data) {
            event = data['events'][0];
            $('#clientdetails').html('<h4>'+event['client']['name']+'</h4><pre>'+JSON.stringify(event['client'],null,2)+'</pre>');
            $('#eventdetails').html('<h4>'+event['check']['name']+'</h4><pre>'+JSON.stringify(event['check'],null,2)+'</pre>');
        })
        .fail(function() {
            $.getJSON('/api/clients/'+ZONE+'/'+CLIENT, function(data) {
                client = data['clients'][0];
                $('#clientdetails').html('<h4>'+client['name']+'</h4><pre>'+JSON.stringify(client,null,2)+'</pre>');
            })
            $.getJSON('/api/clients/'+ZONE+'/'+CLIENT+'/results/'+CHECK, function(data) {
                event = data['results'][0];
                $('#eventdetails').html('<h4>'+event['check']['name']+'</h4><pre>'+JSON.stringify(event['check'],null,2)+'</pre>');
            })
        })
    })
})
