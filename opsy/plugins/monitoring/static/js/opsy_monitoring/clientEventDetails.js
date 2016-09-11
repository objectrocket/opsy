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
      $.getJSON(Flask.url_for('monitoring_api.clients') + '/' + ZONE + '/' + CLIENT, function(data) {
        client = data.clients[0];
        $('#clientdetailsname').html(client.name);
        $('#clientdetailstable').html(opsyMonitoring.formatJSONToTable(client));
      });
    },

    eventData: function() {
      $.getJSON(Flask.url_for('monitoring_api.clients') + '/' + ZONE + '/' + CLIENT + '/events/' + CHECK,
      function(data) {
        event = data.events[0];
        $('#eventdetailsname').html(event.check_name); //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
        $('#eventdetailstable').html(opsyMonitoring.formatJSONToTable(event));
      })
      .fail(function() {
        $.getJSON(Flask.url_for('monitoring_api.clients') + '/' + ZONE + '/' + CLIENT + '/results/' + CHECK,
        function(data) {
          event = data.results[0];
          $('#eventdetailsname').html(event.check_name); //jscs:ignore requireCamelCaseOrUpperCaseIdentifiers
          $('#eventdetailstable').html(opsyMonitoring.formatJSONToTable(event));
        });
      });
    },
  },
};
