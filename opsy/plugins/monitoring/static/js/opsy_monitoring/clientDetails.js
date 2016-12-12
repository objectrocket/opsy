var clientDetails = {

  datatables: {

    init: function() {
      $('#clientdetails').html(function() {
        $.getJSON(Flask.url_for('monitoring_api.clients') + '/' + ZONE + '/' + CLIENT, function(data) {
          client = data.clients[0];
          $('#clientdetailsname').html(client.name);
          $('#clientdetailstable').html(opsyMonitoring.formatJSONToTable(client));
        });
      });
      $.fn.dataTable.enum(['Critical', 'Warning','Ok', 'Unknown']);
      document.clientevents = $('#clientevents').DataTable({
        'lengthMenu': [[25, 50, 100, -1], [25, 50, 100, 'All']],
        'order': [
          [0, 'asc'],
          [1, 'desc'],
        ],
        'ajax': {
          'url': Flask.url_for('monitoring_api.clients') + '/' + ZONE + '/' + CLIENT + '/results',
          'dataSrc': function(json) {
            json = json.results;
            returnData = new Array();
            for (var i = 0; i < json.length; i++) {
              var row = json[i];
              console.log(row);
              //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
              uchiwaClientHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name,
              uchiwaCheckHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name + '?check=' + row.check_name,
              returnData.push({
                'silenced': row.silenced,
                'status': row.status.capitalize(),
                'check_name': '<a href="' + uchiwaCheckHref + '"><img src="' +
                  STATICS_URL + 'img/backends/sensu.ico"></img></a>' +
                  '<a href="' + Flask.url_for('monitoring_main.client_event',
                  {'zone': row.zone_name, 'client_name': row.client_name, 'check': row.check_name}) +
                  '">' + row.check_name + '</a>',
                'check_output': row.output,
                'timestamp': '<time class="timeago" datetime="' +
                  row.last_poll_time + 'Z">' + row.last_poll_time + 'Z</time>',
                //jscs:enable requireCamelCaseOrUpperCaseIdentifiers
              });
            }
            return returnData;
          }
        },
        'columns': [
          {data: 'status'},
          {data: 'check_name'},
          {data: 'check_output'},
          {data: 'timestamp'},
        ],
        'rowCallback': function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
          $('td:first', nRow).addClass(opsyMonitoring.statusclasses[aData.status]);
          if (aData.silenced) {
            $(nRow).addClass('status-silenced');
          }
        },
        'initComplete': function(foo) {
          opsy.task.register('update-client-details', 6, function() {
            document.clientevents.ajax.reload(null, false);
          });
        }
      }).on('draw.dt', function() {
        $('time.timeago').timeago();
      });
    },
  },
};

//$(document).ready(function() {
//});
