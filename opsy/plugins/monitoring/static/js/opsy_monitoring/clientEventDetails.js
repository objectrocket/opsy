var clientEventDetails = {

  init: function() {
    clientEventDetails.update.all();
    opsy.task.register('update-event-data', 6, function() {
      clientEventDetails.update.eventData();
    });
  },

  update: {

    all: function() {
      clientEventDetails.update.clientData();
      clientEventDetails.update.eventData();
    },

    clientData: function() {
      $.getJSON(Flask.url_for('monitoring_api.client', {'zone_name': ZONE, 'client_name': CLIENT}),
      function(data) {
        client = data.clients[0];
        //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
        $('#clientdetailsname').html('<a href="' +
          Flask.url_for('monitoring_main.client', {'zone': client.zone_name, 'client_name': client.name}) +
          '">' + client.name + '</a>');
        //jscs:enable requireCamelCaseOrUpperCaseIdentifiers
        $('tbody', '#clientdetailstable').html(opsyMonitoring.formatJSONToTable(client));
      });
    },

    eventData: function() {
      $.getJSON(Flask.url_for('monitoring_api.client_event', {'zone_name': ZONE, 'client_name': CLIENT, 'check_name': CHECK}),
      function(data) {
        event = data.events[0];
        $('#eventdetailsname').html(event.check_name); //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
        $('tbody', '#eventdetailstable').html(opsyMonitoring.formatJSONToTable(event));
      })
      .fail(function() {
        $.getJSON(Flask.url_for('monitoring_api.client_result', {'zone_name': ZONE, 'client_name': CLIENT, 'check_name': CHECK}),
        function(data) {
          event = data.results[0];
          $('#eventdetailsname').html(event.check_name); //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
          $('tbody', '#eventdetailstable').html(opsyMonitoring.formatJSONToTable(event));
        });
      });
    },
  },
};
