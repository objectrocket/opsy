var clientEventDetails = {

  datatables: {

    init: function() {
      $('#clientdetails').html(function() {
        $.getJSON('/api/monitoring/clients/' + ZONE + '/' + CLIENT, function(data) {
          client = data.clients[0];
          $('#clientdetails').html('<h4>' + client.name + '</h4><pre>' +
            JSON.stringify(client, null, 2) + '</pre>');
        });
        $.getJSON('/api/monitoring/clients/' + ZONE + '/' + CLIENT + '/events/' + CHECK,
        function(data) {
          event = data.events[0];
          $('#eventdetails').html('<h4>' + event.check_name + '</h4><pre>' + //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
            JSON.stringify(event, null, 2) + '</pre>');
        })
        .fail(function() {
          $.getJSON('/api/monitoring/clients/' + ZONE + '/' + CLIENT + '/results/' + CHECK,
          function(data) {
            event = data.results[0];
            $('#eventdetails').html('<h4>' + event.check_name + '</h4><pre>' + //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
              JSON.stringify(event, null, 2) + '</pre>');
          });
        });
      });
    }
  }
};
