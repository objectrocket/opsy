var clients = {

  zoneOptions: [],

  multiselectOptions: opsyMonitoring.multiselectOptions,

  filters: {

    create: function() {
      clients.multiselectOptions.onDropdownHidden = function() {
        clients.datatables.updateUrl();
        document.clientstable.ajax.reload(null, false);
      };
      opsyMonitoring.addFormGroup('zone');
      $('#zone-filter').multiselect(opsyMonitoring.multiselectOptions);
      clients.filters.updateAll(true);
    },

    updateAll: function(init) {
      clients.filters.updateZones(init);
    },

    updateZones: function(init) {
      url = opsyMonitoring.getDashboardUrl(Flask.url_for('monitoring_api.zones'));
      $.getJSON(url, function(data) {
        newzones = [];
        $.each(data.zones, function(idx, obj) {
          newzones.push({label: obj.name, title: obj.name, value: obj.name});
        });
        newzones.sort(function(a, b) { return a.value > b.value; });
        clients.zoneOptions = newzones;
      }).success(function() {
        if (init) {
          $('#zone-filter').multiselect('dataprovider', clients.zoneOptions);
        } else {
          selectedOptions = $('#zone-filter option:selected').map(
            function(idx, obj) {
              return obj.value;
            }
          );
          $('#zone-filter option').remove();
          $.each(clients.zoneOptions, function(idx, obj) {
            $('#zone-filter')
              .append('<option value="' + obj.value + '" label="' + obj.label +
                '" title="' + obj.title + '"></option>'
            );
            if ($.inArray(obj.value, selectedOptions) !== -1) {
              $('#zone-filter option[value="' + obj.value + '"')
                .prop('selected', true);
            }
          });
        }
        $('#zone-filter').multiselect('rebuild');
      });
    },

  },

  datatables: {

    updateUrl: function() {
      params = {};
      $('select.ms').each(function(idx, obj) {
        params[$(obj).data('filter')] = $(obj).children('option:selected').map(
          function() { return this.value; }
        ).get().join(',');
      });
      if ($.QueryString.dashboard) {
        params.dashboard = $.QueryString.dashboard;
      }
      try {
        document.clientstable.ajax.url(Flask.url_for('monitoring_api.clients') + '?' + $.param(params));
      } catch (err) {
      }
      return Flask.url_for('monitoring_api.clients') + '?' + $.param(params);
    },

    init: function() {
      document.clientstable = $('#clients').DataTable({
        'lengthMenu': [[25, 50, 100, -1], [25, 50, 100, 'All']],
        'autoWidth': false,
        //'stateSave' : true,
        'order': [
          [0, 'asc'],
          [1, 'asc'],
        ],
        'ajax': {
          url: clients.datatables.updateUrl(),
          //dataSrc: 'clients',
          dataSrc: function(json) {
            json = json.clients;
            returnData = new Array();
            for (var i = 0; i < json.length; i++) {
              var row = json[i];
              //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
              uchiwaHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name,
              returnData.push({
                'silences': row.silences,
                'zone': row.zone_name,
                'name': '<a href="' + uchiwaHref + '"><img src="' +
                  STATICS_URL + 'img/backends/sensu.ico"></img></a> ' +
                  '<a href="/monitoring/clients/' + row.zone_name + '/' + row.name + '">' +
                  row.name + '</a>',
                'backend': row.backend,
                'subscriptions': row.subscriptions,
                'timestamp': '<time class="timeago" datetime="' +
                  row.last_poll_time + 'Z">' + row.last_poll_time + 'Z</time>',
                //jscs:enable requireCamelCaseOrUpperCaseIdentifiers
              });
            }
            return returnData;
          }
        },
        'dom': '<"row"<"col-sm-2"l><"col-sm-2"<"#zone-filter-div">><"col-sm-6">' +
          '<"col-sm-2"f>><"row"<"col-sm-12"tr>><"row"<"col-sm-5"i><"col-sm-7"p>>',
        'columns': [
          {data: 'zone'},
          {data: 'backend'},
          {data: 'name'},
          {data: 'subscriptions'},
          {data: 'timestamp',
          defaultContent: ''},
        ],
        'rowCallback': function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
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
          clients.filters.create();
          opsy.task.register('update-clients', 6, function() {
            //filters.update();
            document.clientstable.ajax.reload(null, false);
          });
        }
      }).on('draw.dt', function() {
        $('time.timeago').timeago();
      });
    },
  },
};
