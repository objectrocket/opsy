var events = {

  statusOptions: [
    {label: 'Critical', title: 'Critical', value: 'Critical'},
    {label: 'Warning', title: 'Warning', value: 'Warning'},
    {label: 'OK', title: 'OK', value: 'OK'},
    {label: 'Unknown', title: 'Unknown', value: 'Unknown'},
  ],

  hideOptions: [
    {label: 'Silenced Checks', title: 'Silenced Checks', value: 'checks'},
    {label: 'Silenced Clients', title: 'Silenced Clients', value: 'clients'},
    {label: 'Below Occurrence Threshold', title: 'Below Occurrence Threshold',
    value: 'occurrences'},
  ],

  getStatusCount: function(state) {
    return document.eventstable.column(0).data().filter(function(value, idx) {
      return value == state ? true : false;
    }).length;
  },

  updateTitle: function() {
    crits = events.getStatusCount('Critical');
    warns = events.getStatusCount('Warning');
    document.title = crits + ' Critical, ' + warns + ' Warning | Events | Opsy';
  },

  zoneOptions: [],

  checkOptions: [],

  multiselectOptions: {
    buttonWidth: '100%',
    enableFiltering: true,
    enableCaseInsensitiveFiltering: true,
    numberDisplayed: 1,
    includeSelectAllOption: true,
    buttonText: function(options, select) {
      if (options.length == 1) {
        return $(options[0]).attr('label');
      } else if (options.length == $(select).children(options).length) {
        return 'All items selected';
      } else if (options.length > 1) {
        return options.length + ' items selected';
      } else {
        return $(select).data('name').replace('-', ' ').capitalize(true);
      }
    },
    buttonTitle: function(options, select) {
      return $(select).data('name').replace('-', ' ').capitalize(true);
    },
    onDropdownHidden: function() {
      events.datatables.updateUrl();
      document.eventstable.ajax.reload(null, false);
    },
  },

  filters: {

    create: function() {
      opsy.addFormGroup('status');
      opsy.addFormGroup('zone');
      opsy.addFormGroup('check');
      opsy.addFormGroup('hide-events', 'hide_silenced');
      $('#zone-filter').multiselect(events.multiselectOptions);
      $('#check-filter').multiselect(events.multiselectOptions);
      $('#status-filter').multiselect(events.multiselectOptions);
      $('#status-filter').multiselect('dataprovider', events.statusOptions);
      $('#hide-events-filter').multiselect(events.multiselectOptions);
      $('#hide-events-filter').multiselect('dataprovider', events.hideOptions);
      events.filters.updateAll(true);
    },

    updateAll: function(init) {
      events.filters.updateZones(init);
      events.filters.updateChecks(init);
    },

    updateZones: function(init) {
      url = opsy.getDashboardUrl('/api/zones');
      $.getJSON(url, function(data) {
        newzones = [];
        $.each(data.zones, function(idx, obj) {
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
      });
    },

    updateChecks: function(init) {
      url = opsy.getDashboardUrl('/api/events?count_checks');
      $.getJSON(url, function(data) {
        newchecks = [];
        $.each(data.events, function(idx, obj) {
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
      });
      return;
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
        document.eventstable.ajax.url('/api/events?' + $.param(params));
      } catch (err) {
      }
      return '/api/events?' + $.param(params);
    },

    init: function() {
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
            json = json.events;
            returnData = new Array();
            for (var i = 0; i < json.length; i++) {
              var row = json[i];
              //jscs:disable requireCamelCaseOrUpperCaseIdentifiers
              uchiwaHref = UCHIWA_URL + '/#/client/' + row.zone_name + '/' +
                row.client_name + '?check=' + row.check_name,
              returnData.push({
                'status': row.status.capitalize(),
                'zone': row.zone_name,
                'source': '<a href="' + uchiwaHref + '"><img src="' +
                  '/static/main/img/backends/sensu.ico"></img></a>' +
                  '<a href="/clients/' + row.zone_name + '/' + row.client_name +
                  '">' + row.client_name + '</a>',
                'check_name': row.check_name,
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
          $('td:first', nRow).addClass(opsy.statusclasses[aData.status]);
        },
        'initComplete': function(foo) {
          events.filters.create();
          opsy.task.register('update-events', 6, function() {
            events.filters.updateAll();
            document.eventstable.ajax.reload(null, false);
          });
        }
      }).on('draw.dt', function() {
        events.updateTitle();
        $('time.timeago').timeago();
      });

    },
  },
};
