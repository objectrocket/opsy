var clientDetails = {

  init: function() {
    clientDetails.update.all();
    opsy.task.register('update-client-details', 6, function() {
      clientDetails.update.all();
    });
    clientDetails.datatables.init();
  },

  update: {

    all: function() {
      clientDetails.update.clientData();
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
  },

  datatables: {

    init: function() {
      document.clienteventstable = $('#clientevents').DataTable({
        'lengthMenu': [[25, 50, 100, -1], [25, 50, 100, 'All']],
        'autoWidth': false,
        'order': [
          [0, 'asc'],
          [1, 'asc'],
        ],
        'ajax': {
          url: Flask.url_for('monitoring_api.client_results', {'zone_name': ZONE, 'client_name': CLIENT}),
          dataSrc: function(json) {
            json = json.results;
            returnData = new Array();
            for (var i = 0; i < json.length; i++) {
              var row = json[i];
              //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
              uchiwaCheckHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name + '?check=' + row.check_name,
              returnData.push({
                'silences': row.silences,
                'status': row.status.capitalize(),
                'check_name': '<a href="' + uchiwaCheckHref + '"><img src="' +
                  STATICS_URL + 'img/backends/sensu.ico"></img></a>' +
                  '<a href="' + Flask.url_for('monitoring_main.client_event',
                  {'zone': row.zone_name, 'client_name': row.client_name, 'check': row.check_name}) +
                  '">' + row.check_name + '</a>',
                'check_output': row.output,
                'timestamp': '<time class="timeago" datetime="' +
                  row.updated_at + 'Z">' + row.updated_at + 'Z</time>',
                //jscs:enable requireCamelCaseOrUpperCaseIdentifiers
              });
            }
            return returnData;
          }
        },
        'dom': '<"row"<"col-sm-6"l><"col-sm-6"f>><"row"<"col-sm-12"tr>><"row"<"col-sm-5"i><"col-sm-7"p>>',
        'columns': [
          {data: 'status'},
          {data: 'check_name'},
          {data: 'check_output'},
          {data: 'timestamp',
          defaultContent: ''},
        ],
        'rowCallback': function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
          $('td:first', nRow).addClass(opsyMonitoring.statusclasses[aData.status]);
          var d = new Date(0);
          d.setUTCSeconds(aData.timestamp);
          try {
            $('td:last', nRow).html('<time class="timeago" datetime="' +
              d.toISOString() + '">' + d + '</time>');
          } catch (err) {
          }
          if (aData.silences[0] != null) {
            $(nRow).addClass('status-silenced');
          }
        },
        'initComplete': function(foo) {
          opsy.task.register('update-client-results', 6, function() {
            document.clienteventstable.ajax.reload(null, false);
          });
        }
      }).on('draw.dt', function() {
        $('time.timeago').timeago();
      });
    },
  },
};
