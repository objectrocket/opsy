var opsy = {

  debug: $.inArray('debug', window.location.search.substr(1).split('&')),

  log: function(msg) {
    opsy.debug > -1 ? console.log('DEBUG: ' + msg) : null;
  },

  task: {

    list: [],

    tickRate: 5000,

    register: function(slug, interval, func, runNow) {
      opsy.log('registering task: ' + slug + ' to run every ' + interval +
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
      return true;
    },

    remove: function(slug) {
      index = -1;
      $.each(opsy.task.list, function(idx, obj) {
        if (obj.slug == slug) {
          index = idx;
        }
      });
      if (index > -1) {
        opsy.task.list.splice(index, 1);
        return true;
      }
      return false;
    },

    start: function() {
      if (opsy.ticker !== undefined) {
        return false;
      }
      opsy.log('Starting event loop');
      var tickcount = 0;
      opsy.ticker = setInterval(function() {
        tickcount++;
        $.each(opsy.task.list, function(idx, obj) {
          if (tickcount % obj.interval == 0) {
            opsy.log('running task: ' + obj.slug);
            obj.callback();
          }
        });
      }, opsy.task.tickRate);
      return true;
    }

  },

  notification: {

    add: function(title, content, level, slug, desktop) {
      level = typeof level !== 'undefined' ? level : 'danger';
      slug = typeof slug !== 'undefined' ? slug : title.toLowerCase().replace(/ /g, '-');
      desktop = typeof desktop !== 'undefined' ? desktop : true;

      if ($('#notification-container').children('#notification-' + slug)
          .length == 0) {
        opsy.log('adding notification: ' + slug);
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
        if (desktop && ((Date.now() - window.performance.timing.loadEventEnd) / 1000 > 1 || typeof(QUnit) === 'object')) {
          if (Notification.permission !== 'granted') {
            Notification.requestPermission();
          } else {
            var desktopNotification = new Notification(title, {
              body: content,
            });
          }
        }
      }
      return true;
    },

    remove: function(slug) {
      if ($('#notification-container').children('#notification-' + slug)
          .length > 0) {
        opsy.log('removing notification: ' + slug);
        $('#notification-container').children('#notification-' + slug).remove();
        opsy.notification.update();
        return true;
      }
      return false;
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
      if (p.length != 2) {
        b[p[0]] = true;
        continue;
      };
      b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, ' '));
    }
    return b;
  })(window.location.search.substr(1).split('&'));
})(jQuery);

$(document).ready(function() {
  opsy.task.tickRate = $.QueryString.tickrate !== undefined ?
    $.QueryString.tickrate : opsy.task.tickRate;
});
