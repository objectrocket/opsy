$(document).ready(function() {
    $('#clientdetails').html(function() {
        $.getJSON('/api/clients/'+ZONE+'/'+CLIENT+'/events/'+CHECK, function(data) {
            event = data['events'][0];
            $('#clientdetails').html('<h4>'+event['client']['name']+'</h4><pre>'+JSON.stringify(event['client'],null,2)+'</pre>');
            $('#eventdetails').html('<h4>'+event['check']['name']+'</h4><pre>'+JSON.stringify(event['check'],null,2)+'</pre>');
        })
    })
})
