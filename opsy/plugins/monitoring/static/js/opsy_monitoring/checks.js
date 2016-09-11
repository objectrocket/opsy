var checks = {

  zoneOptions: [],

  checkOptions: [],

  multiselectOptions: opsyMonitoring.multiselectOptions,

  filters: {

    create: function() {
      checks.multiselectOptions.onDropdownHidden = function() {
        checks.datatables.updateUrl();
        document.checkstable.ajax.reload(null, false);
      };
      opsyMonitoring.addFormGroup('zone');
      opsyMonitoring.addFormGroup('check');
      $('#zone-filter').multiselect(checks.multiselectOptions);
      $('#check-filter').multiselect(checks.multiselectOptions);
      checks.filters.updateAll(true);
    },

    updateAll: function(init) {
      checks.filters.updateZones(init);
      checks.filters.updateChecks(init);
    },

    updateZones: function(init) {
      url = opsyMonitoring.getDashboardUrl(Flask.url_for('monitoring_api.zones'));
      $.getJSON(url, function(data) {
        newzones = [];
        $.each(data.zones, function(idx, obj) {
          newzones.push({label: obj.name, title: obj.name, value: obj.name});
        });
        newzones.sort(function(a, b) { return a.value > b.value; });
        checks.zoneOptions = newzones;
      }).success(function() {
        if (init) {
          $('#zone-filter').multiselect('dataprovider', checks.zoneOptions);
        } else {
          selectedOptions = $('#zone-filter option:selected').map(
            function(idx, obj) {
              return obj.value;
            }
          );
          $('#zone-filter option').remove();
          $.each(checks.zoneOptions, function(idx, obj) {
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
      url = opsyMonitoring.getDashboardUrl(Flask.url_for('monitoring_api.checks'));
      $.getJSON(url, function(data) {
        newchecks = [];
        $.each(data.checks, function(idx, obj) {
          newchecks.push({label: obj.name,
            title: obj.name, value: obj.name});
        });
        newchecks.sort(function(a, b) { return a.value > b.value; });
        checks.checkOptions = newchecks;
      }).success(function() {
        if (init) {
          $('#check-filter').multiselect('dataprovider', checks.checkOptions);
        } else {
          selectedOptions = $('#check-filter option:selected')
            .map(function(idx, obj) {
              return obj.value;
            });
          $('#check-filter option').remove();
          $.each(checks.checkOptions, function(idx, obj) {
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
        document.checkstable.ajax.url('/api/monitoring/checks?' + $.param(params));
      } catch (err) {
      }
      return '/api/monitoring/checks?' + $.param(params);
    },

    init: function() {
      document.checkstable = $('#checks').DataTable({
        'lengthMenu': [[25, 50, 100, -1], [25, 50, 100, 'All']],
        'autoWidth': false,
        //'stateSave' : true,
        'ajax': {
          url: checks.datatables.updateUrl(),
          dataSrc: 'checks',
        },
        'dom': '<"row"<"col-sm-2"l><"col-sm-2"<"#zone-filter-div">><"col-sm-2"' +
          '<"#check-filter-div">><"col-sm-4"><"col-sm-2"f>><"row"<"col-sm-12"tr>>' +
          '<"row"<"col-sm-5"i><"col-sm-7"p>>',
        'columns': [
          {data: 'zone_name',
          name: 'zone'},
          {data: 'name',
          name: 'name'},
          {data: 'command',
          name: 'command'},
          {data: 'interval',
          name: 'interval'},
        ],
        'initComplete': function(foo) {
          checks.filters.create();
          opsy.task.register('update-checks', 6, function() {
            //filters.update();
            document.checkstable.ajax.reload(null, false);
          });
        }
      });
    },
  },
};
