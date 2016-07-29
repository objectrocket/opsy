var hourglass = {

    tasks: [],

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
        formitem = $('<select multiple class="ms" data-name="'+name+'" data-filter="'+filter+'" class="form-control" id="'+name+'-filter"><select>').appendTo( $('#'+name+'-filter-div') );
    },

    get_dashboard_url: function(url) {
        dash = $.QueryString['dashboard'];
        if (dash) {
            return url+'?dashboard='+dash;
        } else {
            return url;
        }
    },

    check_zones: function() {
        $.getJSON('/api/zones', function(json) {
            zones = json['zones'];
            for (var i=0; i<zones.length; i++) {
                zone = zones[i];
                if (zone.status != 'ok') {
                    hourglass.notification.add(zone.name+' Poller Failure', '<strong>Failure!</strong> datacenter '+zone.name+' is not responding!', 'danger', true, zone.name+'-offline');
                } else {
                    hourglass.notification.remove(zone.name+'-offline');
                }
            }
        })
    },

    registerTask: function(slug, interval, func, run_now=false) {
        console.log('registering task: '+slug+' to run every '+interval+' ticks.');
        hourglass.tasks.push({'slug': slug, 'interval': interval, 'callback': func});
        if (run_now) {
            func();
        }
    },

    notification: {

        add: function(title, content, level='danger', dismissable=true, slug=null) {
            if (slug == null) {
                slug = title.toLowerCase().replace(/ /g,'-');
            }
            if ($('#notification-container').children('#notification-'+slug).length == 0) {
                console.log('adding notification: '+slug);
                $('#notification-container').append("<div id='notification-"+slug+"' class='notification-item alert alert-"+level+"'><h4 class='item-title'>"+title+"</h4><p class='item-info'>"+content+"</p></div>");
                if (dismissable) {
                    $('#notification-'+slug).click(function(e) {
                        e.stopPropagation();
                        hourglass.notification.remove(slug)
                    });
                }
                hourglass.notification.update();
                hourglass.notification.jingle();
            }
            return;
        },

        remove: function(slug) {
            if ($('#notification-container').children('#notification-'+slug).length > 0) {
                console.log('removing notification: '+slug);
                $('#notification-container').children('#notification-'+slug).remove();
                hourglass.notification.update();
            }
        },

        update: function() {
            container = $('#notification-container')
            $('#notification-count').html($(container).children().length);
            alertClasses = ['alert-success', 'alert-info', 'alert-warning', 'alert-danger'];
            var notificationColor = '';
            $(alertClasses).each(function(idx, obj) {
                if ($(container).children('.'+obj).length > 0) {
                    $('#notification-icon').addClass(obj);
                } else {
                    $('#notification-icon').removeClass(obj);
                }
            });
        },

        jingle: function() {
            $('#notification-icon').addClass('animate')
            setTimeout(function() {
                $('#notification-icon').removeClass('animate')
            }, 1100);
        }

    }

}

String.prototype.capitalize = function(all) {
    if (all) {
        return this.split(' ').map(function(i) {
            return i.capitalize()
        }).join(' ');
    } else {
        return this.charAt(0).toUpperCase() + this.slice(1);
    }
}

$(document).ready(function() {
    hourglass.registerTask('zone-check', 5, hourglass.check_zones, true);
    (function($) {
        $.QueryString = (function(a) {
            if (a == "") return {};
            var b = {};
            for (var i = 0; i < a.length; ++i)
            {
                var p=a[i].split('=');
                if (p.length != 2) continue;
                b[p[0]] = decodeURIComponent(p[1].replace(/\+/g, " "));
            }
            return b;
        })(window.location.search.substr(1).split('&'))
    })(jQuery);
    var tick = new Event('tick');
    var tickcount=0;
    ticker = setInterval( function() {
        dispatchEvent(tick);
    }, 5000);
    addEventListener('tick', function tickHandler(e) {
        tickcount++;
        $.each(hourglass.tasks, function(idx, obj) {
            if (tickcount % obj.interval == 0) {
                console.log('running task: '+obj.slug);
                obj.callback();
            }
        })
    });
    
});
