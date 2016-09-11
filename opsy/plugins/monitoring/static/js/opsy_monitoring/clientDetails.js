var clientDetails = {

  datatables: {

    init: function() {
      $('#clientdetails').html(function() {
        $.getJSON('/api/monitoring/clients/' + ZONE + '/' + CLIENT, function(data) {
          client = data.clients[0];
          $('#clientdetails').html('<h4>' + client.name + '</h4><pre>' +
            JSON.stringify(client, null, 2) + '</pre>');
        });
      });
      $.fn.dataTable.enum(['Critical', 'Warning', 'OK']);
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
              returnData.push({
                'status': row.status.capitalize(),
                //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
                'check_name': row.check_name,
                'check_output': '<a href="' + Flask.url_for('monitoring_main.clients') + '/' + row.zone_name + '/' +
                  row.client_name + '/events/' + row.check_name + '">' +
                  row.output + '</a>',
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
