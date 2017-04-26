var opsyMonitoring = {

  linkedFields: [
    'output',
  ],

  statusclasses: {
    'Ok': 'success',
    'Warning': 'warning',
    'Critical': 'danger'
  },

  statusnames: {
    0: 'OK',
    1: 'Warning',
    2: 'Critical'
  },

  addFormGroup: function(name, filter) {
    if (filter === undefined) {
      filter = name;
    }
    formitem = $('<select multiple class="ms" data-name="' + name +
      '" data-filter="' + filter + '" class="form-control" id="' + name +
      '-filter"><select>').appendTo($('#' + name + '-filter-div'));
  },

  getDashboardUrl: function(url, dash) {
    if (dash === undefined) {
      dash = $.QueryString.dashboard;
    }
    if (dash) {
      var separator = url.indexOf('?') !== -1 ? '&' : '?';
      return url + separator + 'dashboard=' + dash;
    } else {
      return url;
    }
  },

  formatJSONToTable: function(data) {
    html = [];
    $.each(data, function(item, value) {
      if (opsyMonitoring.linkedFields.indexOf(item) >= 0) {
        opsy.log('autolinking ' + item);
        value = autolinker.link(value);
      }
      if(typeof(value) === 'object'){
          value = JSON.stringify(value,null,2);
      };
      html.push('<tr><td>' + item + '</td><td>' + value + '</td></tr>');
    });
    return html.join('\n');
  },

  checkZones: function(url, cb) {
    if (url === undefined) {
      url = Flask.url_for('monitoring_api.zones');
    }
    $.getJSON(url, function(json, status) {
      zones = json.zones;
      for (var i = 0; i < zones.length; i++) {
        zone = zones[i];
        if (zone.status != 'ok') {
          opsy.notification.add(zone.name + ' Poller Failure', 'Datacenter ' +
            zone.name + ' is not responding!', 'danger', zone.name +
            '-offline');
        } else {
          opsy.notification.remove(zone.name + '-offline');
        }
      }
    }).done(function() {
      if (typeof(cb) === 'function') {
        cb();
      }
    });
  },

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
  }
};
