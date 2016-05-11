String.prototype.capitalize = function() {
    return this.charAt(0).toUpperCase() + this.slice(1);
}

var addFormGroup = function(name) {
    filterdiv = $('<div class="form-group"></div>').appendTo( $('#filters') );
    labeldiv = $('<label for="'+name+'-filter">'+name.capitalize()+'</label>').appendTo( $(filterdiv) );
    formitem = $('<select data-filter="'+name+'" class="form-control" id="'+name+'-filter"><option value="">All</option></select>').appendTo($(labeldiv));
    formitem.on('change', function() {
        updateDataTablesUrl();
    });
}

var addFilters = function() {
    $('#filters').addClass('form-inline');
    addFormGroup('status');
    addFormGroup('datacenter');
    addFormGroup('checkname');
}

var addOption = function(selectID, option, value=null) {
    if (value === null) {
        value = option;
    }
    if ( $('#'+selectID+':has(option[value='+value+'])').length == 0) {
        $('#'+selectID).append('<option value="'+value+'">'+option+'</option>');
    }
}

var updateFilters = function() {

    $.getJSON('/api/events/checks', function(data) {
        $.each(data.checks.sort(), function(idx, obj) {
            addOption('checkname-filter', obj);
        });
    });
    $.getJSON('/api/events/datacenters', function(data) {
        $.each(data.datacenters, function(idx, obj) {
            addOption('datacenter-filter', obj);
        });
    });
}

var setDataTablesUrl = function() {
    params = {}
    $('#filters select').each(function(idx, obj) {
        params[$(obj).data('filter')] = $(obj).children('option:selected').val()
    });
    if ( $.QueryString['dashboard'] ) {
        params['dashboard'] = $.QueryString['dashboard'];
    }
    return '/api/events?'+$.param(params);
}

var updateDataTablesUrl = function() {
    params = {}
    $('#filters select').each(function(idx, obj) {
        params[$(obj).data('filter')] = $(obj).children('option:selected').val()
    });
    if ( $.QueryString['dashboard'] ) {
        params['dashboard'] = $.QueryString['dashboard'];
    }
    document.eventstable.ajax.url('/api/events?'+$.param(params));
    document.eventstable.ajax.reload(null, false);
}

var getStatusCount = function(state) {
    return document.eventstable.column(0).data().filter( function(value, idx){
          return value == state ? true : false;
    }).length
}

var updateTitle = function() {
    crits = getStatusCount("Critical");
    warns = getStatusCount("Warning");
    document.title = crits+' Critical, '+warns+' Warning | Events | Hourglass';
}

$(document).ready(function() {
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
    statusclasses = {
        'OK': 'success',
        'Warning': 'warning',
        'Critical': 'danger'
    }
    statusnames = {
        0: 'OK',
        1: 'Warning',
        2: 'Critical'
    }
    document.eventstable = $('#events').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        //'stateSave' : true,
        'columnDefs': [
            {
                "targets": [ 0 ],
                "visible": true,
                "searchable": true
            },
        ],
        'order': [
            [ 0, 'asc' ],
            [ 5, 'desc' ],
        ],
        'ajax': {
            url: setDataTablesUrl(),
            dataSrc: 'events',
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-8'<'#filters'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'columns': [
            {data: 'check.status',
             name: 'status'},
            {data: 'datacenter',
             name: 'datacenter'},
            {data: 'client.name',
             name: 'source'},
            {data: 'check.name',
             name: 'check-name'},
            {data: 'check.output',
             name: 'check-output'},
            {data: 'occurrences',
             name: 'occurrences'},
            {data: 'timestamp',
             name: 'timestamp'},
        ],
        'rowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            //$(nRow).addClass(statusclasses[aData['check']['status']]);
            var d = new Date(0);
            d.setUTCSeconds(aData['timestamp']);
            $('td:last', nRow).html('<time class="timeago" datetime="'+d.toISOString()+'">'+d+'</time>');
            $('td:first', nRow).html($('<span class="fa fa-flag '+aData['check']['status']+'"></span>'));
        },
        'createdRow': function(nRow, aData, iDataIndex) {
            aData['check']['status'] = statusnames[aData['check']['status']];
            $(nRow).data('href', aData['href']);
            $(nRow).click(function() {
                window.open($(this).data("href"), '_blank');
            });
        },
        'initComplete': function (foo) {
            addFilters();
            updateFilters();
            $([['Critical', 2],['Warning', 1],['OK', 0]]).each( function(idx, obj) {
                addOption('status-filter', obj[0], obj[1])
            });
            setInterval( function() {
                updateFilters();
                document.eventstable.ajax.reload(null, false);
            }, 30000);
        }
    }).on('draw.dt', function() {
        updateTitle();
        $('time.timeago').timeago();
    });
});
