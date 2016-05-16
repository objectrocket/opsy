String.prototype.capitalize = function(all) {
    if (all) {
        return this.split(' ').map(function(i) {
            return i.capitalize()
        }).join(' ');
    } else {
        return this.charAt(0).toUpperCase() + this.slice(1);
    }
}

var filters = {

    statusOptions: [
        {label: 'Critical', title: 'Critical', value: 2},
        {label: 'Warning', title: 'Warning', value: 1},
        {label: 'OK', title: 'OK', value: 0},
    ],

    hideOptions: [
        {label: 'Silenced Checks', title: 'Silenced Checks', value: 'checks'},
        {label: 'Silenced Clients', title: 'Silenced Clients', value: 'clients'},
    ],

    datacenterOptions: [],

    checknameOptions: [],

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
                return options.length+' items selected';
            } else {
                return $(select).data('name').replace('-', ' ').capitalize(true);
            }
        },
        buttonTitle: function(options, select) {
            return $(select).data('name').replace('-', ' ').capitalize(true);
        },
        onDropdownHidden: function() {
            filters.setDataTablesUrl();
            document.eventstable.ajax.reload(null, false);
        },
    },

    addFormGroup: function(name, filter=null) {
        var self = this;
        if (filter === null) {
            filter = name;
        }
        formitem = $('<select multiple class="ms" data-name="'+name+'" data-filter="'+filter+'" class="form-control" id="'+name+'-filter"></select>').appendTo( $('#'+name+'-filter-div') );
    },

    create: function() {
        var self = this;
        self.addFormGroup('status');
        $('#status-filter').multiselect(self.multiselectOptions);
        $('#status-filter').multiselect('dataprovider', self.statusOptions);
        self.addFormGroup('datacenter');
        self.updateDatacenters(true);
        self.addFormGroup('checkname');
        self.updateChecknames(true);
        self.addFormGroup('hide-events', 'hide_silenced');
        $('#hide-events-filter').multiselect(self.multiselectOptions);
        $('#hide-events-filter').multiselect('dataprovider', self.hideOptions);
    },

    update: function() {
        this.updateDatacenters();
        this.updateChecknames();
    },

    updateDatacenters: function(init) {
        var self = this;
        $.getJSON('/api/events/datacenters', function(data) {
            newdatacenters = []
            $.each(data.datacenters, function(idx, obj) {
                newdatacenters.push({label: obj, title: obj, value: obj});
            });
            self.datacenterOptions = newdatacenters;
        }).success(function() {
            if (init == true ) {
                $('#datacenter-filter').multiselect(self.multiselectOptions);
                $('#datacenter-filter').multiselect('dataprovider', self.datacenterOptions);
            } else {
                $('#checkname-filter').multiselect('rebuild');
            }
        });
    },

    updateChecknames: function(init) {
        var self = this;
        $.getJSON('/api/events/checks', function(data) {
            newchecknames = []
            $.each(data.checks.sort(), function(idx, obj) {
                newchecknames.push({label: obj, title: obj, value: obj});
            });
            self.checknameOptions = newchecknames;
        }).success(function() {
            if (init == true ) {
                $('#checkname-filter').multiselect(self.multiselectOptions);
                $('#checkname-filter').multiselect('dataprovider', self.checknameOptions);
            } else {
                $('#checkname-filter').multiselect('rebuild');
            }
        });
    },

    setDataTablesUrl: function() {
        params = {}
        $('select.ms').each(function(idx, obj) {
            params[$(obj).data('filter')] = $(obj).children('option:selected').map(function() { return this.value }).get().join(',')
        });
        if ( $.QueryString['dashboard'] ) {
            params['dashboard'] = $.QueryString['dashboard'];
        }
        try {
            document.eventstable.ajax.url('/api/events?'+$.param(params));
        } catch(err) {
        }
        return '/api/events?'+$.param(params);
    }
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
        'autoWidth': false,
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
            url: filters.setDataTablesUrl(),
            dataSrc: 'events',
        },
        //'dom': "<'row'<'col-sm-2'l><'col-sm-8'<'#filters'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'dom': "<'row'<'col-sm-2'l><'col-sm-2'<'#status-filter-div'>><'col-sm-2'<'#datacenter-filter-div'>><'col-sm-2'<'#checkname-filter-div'>><'col-sm-2'<'#hide-events-filter-div'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
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
            var d = new Date(0);
            d.setUTCSeconds(aData['timestamp']);
            $('td:last', nRow).html('<time class="timeago" datetime="'+d.toISOString()+'">'+d+'</time>');
            $('td:first', nRow).addClass(statusclasses[aData['check']['status']]);
            $('td:first', nRow).html(aData['check']['status']);
        },
        'createdRow': function(nRow, aData, iDataIndex) {
            aData['check']['status'] = statusnames[aData['check']['status']];
            aData['href'] = UCHIWA_URL+'/#/client/'+aData['datacenter']+'/'+aData['client']['name']+'?check='+aData['check']['name'];
            $(nRow).data('href', aData['href']);
            $(nRow).click(function(e) {
                window.open($(this).data("href"), '_blank');
                e.stopPropagation();
            });
        },
        'initComplete': function (foo) {
            filters.create();
            setInterval( function() {
                //filters.update();
                document.eventstable.ajax.reload(null, false);
            }, 30000);
        }
    }).on('draw.dt', function() {
        updateTitle();
        $('time.timeago').timeago();
    });
});
