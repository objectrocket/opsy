var opsy = {

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

  addFormGroup: function(name, filter=null) {
    if (filter === null) {
      filter = name;
    }
    formitem = $('<select multiple class="ms" data-name="' + name +
      '" data-filter="' + filter + '" class="form-control" id="' + name +
      '-filter"><select>').appendTo($('#' + name + '-filter-div'));
  },

  getDashboardUrl: function(url) {
    dash = $.QueryString.dashboard;
    if (dash) {
      var separator = url.indexOf('?') !== -1 ? '&' : '?';
      return url + separator + 'dashboard=' + dash;
    } else {
      return url;
    }
  },

  checkZones: function() {
    $.getJSON('/api/zones', function(json) {
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
    });
  },

  task: {

    list: [],

    register: function(slug, interval, func, runNow=false) {
      console.log('registering task: ' + slug + ' to run every ' + interval +
        ' ticks.');
      opsy.task.list.push(
        {'slug': slug, 'interval': interval, 'callback': func}
      );
      if (runNow) {
        func();
      }
      if (opsy.ticker === undefined) {
        opsy.task.start();
      }
    },

    start: function() {
      if (opsy.ticker !== undefined) {
        return;
      }
      console.log('Starting event loop');
      var tick = new Event('tick');
      var tickcount = 0;
      opsy.ticker = setInterval(function() {
        dispatchEvent(tick);
      }, 5000);
      addEventListener('tick', function(e) {
        tickcount++;
        $.each(opsy.task.list, function(idx, obj) {
          if (tickcount % obj.interval == 0) {
            console.log('running task: ' + obj.slug);
            obj.callback();
          }
        });
      });
    }

  },

  notification: {

    add: function(title, content, level='danger', slug=null, desktop=true) {
      if (slug == null) {
        slug = title.toLowerCase().replace(/ /g, '-');
      }
      if ($('#notification-container').children('#notification-' + slug)
          .length == 0) {
        console.log('adding notification: ' + slug);
        $('#notification-container').append('<div id="notification-' + slug +
          '" class="notification-item alert alert-' + level +
          '"><h4 class="item-title">' + title + '</h4><p class="item-info">' +
          content + '</p></div>');
        $('#notification-' + slug).click(function(e) {
          e.stopPropagation();
          opsy.notification.remove(slug);
        });
        opsy.notification.update();
        opsy.notification.jingle();
        // Don't give desktop notifications within the first 1 second of page load
        if (desktop && (
            (Date.now() - window.performance.timing.loadEventEnd) / 1000 > 1)) {
          if (Notification.permission !== 'granted') {
            Notification.requestPermission();
          } else {
            var desktopNotification = new Notification(title, {
              body: content,
            });
          }
        }
      }
      return;
    },

    remove: function(slug) {
      if ($('#notification-container').children('#notification-' + slug)
          .length > 0) {
        console.log('removing notification: ' + slug);
        $('#notification-container').children('#notification-' + slug).remove();
        opsy.notification.update();
      }
    },

    update: function() {
      container = $('#notification-container');
      $('#notification-count').html($(container).children().length);
      alertClasses = ['alert-success', 'alert-info', 'alert-warning',
        'alert-danger'];
      var notificationColor = '';
      $(alertClasses).each(function(idx, obj) {
        if ($(container).children('.' + obj).length > 0) {
          $('#notification-icon').addClass(obj);
        } else {
          $('#notification-icon').removeClass(obj);
        }
      });
    },

    jingle: function() {
      $('#notification-icon').addClass('animate');
      setTimeout(function() {
        $('#notification-icon').removeClass('animate');
      }, 1100);
    }
  }
};

String.prototype.capitalize = function(all) {
  if (all) {
    return this.split(' ').map(function(i) {
      return i.capitalize();
    }).join(' ');
  } else {
    return this.charAt(0).toUpperCase() + this.slice(1);
  }
};

(function($) {
  $.QueryString = (function(a) {
    if (a == '') { return {}; };
    var b = {};
    for (var i = 0; i < a.length; ++i) {
      var p = a[i].split('=');
      if (p.length != 2) { continue; };
      b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, ' '));
    }
    return b;
  })(window.location.search.substr(1).split('&'));
})(jQuery);
