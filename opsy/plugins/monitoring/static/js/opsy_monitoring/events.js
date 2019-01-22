var events = {

  statusOptions: [
    {label: 'Critical', title: 'Critical', value: 'Critical'},
    {label: 'Warning', title: 'Warning', value: 'Warning'},
    {label: 'OK', title: 'OK', value: 'OK'},
    {label: 'Unknown', title: 'Unknown', value: 'Unknown'},
  ],

  hideOptions: [
    {label: 'Silenced', title: 'Silenced', value: 'silenced'},
    {label: 'Below Occurrence Threshold', title: 'Below Occurrence Threshold',
    value: 'below_occurrences'},
  ],

  multiselectOptions: opsyMonitoring.multiselectOptions,

  getStatusCount: function(state) {
    return document.eventstable.column(0).data().filter(function(value, idx) {
      return value == state ? true : false;
    }).length;
  },

  updateTitle: function(crits, warns) {
    crits = typeof crits !== 'undefined' ? crits : events.getStatusCount('Critical');
    warns = typeof warns !== 'undefined' ? warns : events.getStatusCount('Warning');
    document.title = crits + ' Critical, ' + warns + ' Warning | Events | Opsy';
  },

  zoneOptions: [],

  checkOptions: [],

  filters: {

    create: function(update, cb) {
      update = typeof update !== 'undefined' ? update : true;
      events.multiselectOptions.onDropdownHidden = function() {
        events.datatables.updateUrl();
        document.eventstable.ajax.reload(null, false);
      };
      opsyMonitoring.addFormGroup('status');
      opsyMonitoring.addFormGroup('zone');
      opsyMonitoring.addFormGroup('check');
      opsyMonitoring.addFormGroup('hide-events', 'hide');
      $('#zone-filter').multiselect(events.multiselectOptions);
      $('#check-filter').multiselect(events.multiselectOptions);
      $('#status-filter').multiselect(events.multiselectOptions);
      $('#status-filter').multiselect('dataprovider', events.statusOptions);
      $('#hide-events-filter').multiselect(events.multiselectOptions);
      $('#hide-events-filter').multiselect('dataprovider', events.hideOptions);
      if (update) {
        events.filters.updateAll(true, cb);
      }
    },

    updateAll: function(init, cb) {
      events.filters.updateZones(init, cb);
      events.filters.updateChecks(init, cb);
    },

    updateZones: function(init, cb) {
      url = opsyMonitoring.getDashboardUrl(Flask.url_for('monitoring_api.zones'));
      $.getJSON(url, function(json) {
        zones = json;
        newzones = [];
        $.each(zones, function(idx, obj) {
          newzones.push({label: obj.name, title: obj.name, value: obj.name});
        });
        newzones.sort(function(a, b) { return a.value > b.value; });
        events.zoneOptions = newzones;
      }).success(function() {
        if (init) {
          $('#zone-filter').multiselect('dataprovider', events.zoneOptions);
        } else {
          selectedOptions = $('#zone-filter option:selected').map(
            function(idx, obj) {
              return obj.value;
            }
          );
          $('#zone-filter option').remove();
          $.each(events.zoneOptions, function(idx, obj) {
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
        if (typeof(cb) === 'function') {
          cb();
        }
      });
    },

    updateChecks: function(init, cb) {
      url = opsyMonitoring.getDashboardUrl(Flask.url_for('monitoring_api.events') +
      '?count_checks=true');
      $.getJSON(url, function(data) {
        newchecks = [];
        $.each(data, function(idx, obj) {
          newchecks.push({label: obj.name + ' (' + obj.count + ')',
            title: obj.name, value: obj.name});
        });
        newchecks.sort(function(a, b) { return a.value > b.value; });
        events.checkOptions = newchecks;
      }).success(function() {
        if (init) {
          $('#check-filter').multiselect('dataprovider', events.checkOptions);
        } else {
          selectedOptions = $('#check-filter option:selected')
            .map(function(idx, obj) {
              return obj.value;
            });
          $('#check-filter option').remove();
          $.each(events.checkOptions, function(idx, obj) {
            $('#check-filter')
              .append('<option value="' + obj.value + '" label="' + obj.label +
              '" title="' + obj.title + '"></option>');
            if ($.inArray(obj.value, selectedOptions) !== -1) {
              $('#check-filter option[value="' + obj.value + '"')
                .prop('selected', true);
            }
          });
        }
        $('#check-filter').multiselect('rebuild');
        if (typeof(cb) === 'function') {
          cb();
        }
      });
    },
  },

  datatables: {

    updateUrl: function(url) {
      url = typeof url !== 'undefined' ? url : Flask.url_for('monitoring_api.events');
      params = {'truncate': true};
      $('select.ms').each(function(idx, obj) {
        params[$(obj).data('filter')] = $(obj).children('option:selected').map(
          function() { return this.value; }
        ).get().join(',');
      });
      if ($.QueryString.dashboard) {
        params.dashboard = $.QueryString.dashboard;
      }
      try {
        document.eventstable.ajax.url(url + '?' + $.param(params));
      } catch (err) {
      }
      return url + '?' + $.param(params);
    },

    init: function(cb) {
      $.fn.dataTable.enum(['Critical', 'Warning','Ok', 'Unknown']);
      document.eventstable = $('#events').DataTable({
        'lengthMenu': [[25, 50, 100, -1], [25, 50, 100, 'All']],
        'autoWidth': false,
        //'stateSave' : true,
        'order': [
          [0, 'asc'],
          [5, 'desc'],
        ],
        'ajax': {
          url: events.datatables.updateUrl(),
          dataSrc: function(json) {
            json = json;
            returnData = new Array();
            for (var i = 0; i < json.length; i++) {
              var row = json[i];
              //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
              uchiwaClientHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name,
              uchiwaCheckHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name + '?check=' + row.check_name,
              returnData.push({
                'silences': row.silences,
                'status': row.status.capitalize(),
                'zone': row.zone_name,
                'source': '<a href="' + uchiwaClientHref + '"><img src="' +
                  STATICS_URL + 'img/backends/sensu.ico"></img></a>' +
                  '<a href="' + Flask.url_for('monitoring_main.client', {'zone': row.zone_name, 'client_name': row.client_name}) +
                  '">' + row.client_name + '</a>',
                'check_name': '<a href="' + uchiwaCheckHref + '"><img src="' +
                  STATICS_URL + 'img/backends/sensu.ico"></img></a>' +
                  '<a href="' + Flask.url_for('monitoring_main.client_event',
                  {'zone': row.zone_name, 'client_name': row.client_name, 'check': row.check_name}) +
                  '">' + row.check_name + '</a>',
                'check_output': row.output,
                'count': row.occurrences,
                'timestamp': '<time class="timeago" datetime="' +
                  row.updated_at + 'Z">' + row.updated_at + 'Z</time>',
                //jscs:enable requireCamelCaseOrUpperCaseIdentifiers
              });
            }
            return returnData;
          },
        },
        'dom': '<"row"<"col-sm-2"l><"col-sm-2"<"#status-filter-div">>' +
          '<"col-sm-2"<"#zone-filter-div">><"col-sm-2"<"#check-filter-div">>' +
          '<"col-sm-2"<"#hide-events-filter-div">><"col-sm-2"f>><"row"' +
          '<"col-sm-12"tr>><"row"<"col-sm-5"i><"col-sm-7"p>>',
        'columns': [
          {data: 'status'},
          {data: 'zone'},
          {data: 'source'},
          {data: 'check_name'},
          {data: 'check_output'},
          {data: 'count'},
          {data: 'timestamp'},
        ],
        'rowCallback': function(nRow, aData, iDisplayIndex, iDisplayIndexFull) {
          $('td:first', nRow).addClass(opsyMonitoring.statusclasses[aData.status]);
          if (aData.silences[0] != null) {
            $(nRow).addClass('status-silenced');
          }
        },
        'initComplete': function() {
          events.filters.create();
          opsy.task.register('update-events', 6, function() {
            events.filters.updateAll();
            document.eventstable.ajax.reload(null, false);
          });
          if (typeof(cb) === 'function') {
            cb();
          }
        }
      }).on('draw.dt', function() {
        events.updateTitle();
        $('time.timeago').timeago();
      });

    },
  },
};
