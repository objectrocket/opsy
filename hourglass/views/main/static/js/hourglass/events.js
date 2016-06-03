var eventsfilters = {

    statusOptions: [
        {label: 'Critical', title: 'Critical', value: 2},
        {label: 'Warning', title: 'Warning', value: 1},
        {label: 'OK', title: 'OK', value: 0},
    ],

    hideOptions: [
        {label: 'Silenced Checks', title: 'Silenced Checks', value: 'checks'},
        {label: 'Silenced Clients', title: 'Silenced Clients', value: 'clients'},
        {label: 'Below Occurrence Threshold', title: 'Below Occurrence Threshold', value: 'occurrences'},
    ],

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
                return options.length+' items selected';
            } else {
                return $(select).data('name').replace('-', ' ').capitalize(true);
            }
        },
        buttonTitle: function(options, select) {
            return $(select).data('name').replace('-', ' ').capitalize(true);
        },
        onDropdownHidden: function() {
            eventsfilters.setDataTablesUrl();
            document.eventstable.ajax.reload(null, false);
        },
    },

    create: function() {
        hourglass.addFormGroup('status');
        $('#status-filter').multiselect(this.multiselectOptions);
        $('#status-filter').multiselect('dataprovider', this.statusOptions);
        hourglass.addFormGroup('zone');
        this.updateZones(true);
        hourglass.addFormGroup('check');
        this.updateChecks(true);
        hourglass.addFormGroup('hide-events', 'hide_silenced');
        $('#hide-events-filter').multiselect(this.multiselectOptions);
        $('#hide-events-filter').multiselect('dataprovider', this.hideOptions);
    },

    update: function() {
        this.updateZones();
        this.updateChecks();
    },

    updateZones: function(init) {
        var self = this;
        url = hourglass.get_dashboard_url('/api/list/zones');
        $.getJSON(url, function(data) {
            newzones = []
            $.each(data.zones, function(idx, obj) {
                newzones.push({label: obj, title: obj, value: obj});
            });
            self.zoneOptions = newzones;
        }).success(function() {
            if (init == true ) {
                $('#zone-filter').multiselect(self.multiselectOptions);
                $('#zone-filter').multiselect('dataprovider', self.zoneOptions);
            } else {
                $('#zone-filter').multiselect('rebuild');
            }
        });
    },

    updateChecks: function(init) {
        var self = this;
        url = hourglass.get_dashboard_url('/api/list/checks');
        $.getJSON(url, function(data) {
            newchecks = []
            $.each(data.checks.sort(), function(idx, obj) {
                newchecks.push({label: obj, title: obj, value: obj});
            });
            self.checkOptions = newchecks;
        }).success(function() {
            if (init == true ) {
                $('#check-filter').multiselect(self.multiselectOptions);
                $('#check-filter').multiselect('dataprovider', self.checkOptions);
            } else {
                $('#check-filter').multiselect('rebuild');
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
            url: eventsfilters.setDataTablesUrl(),
            dataSrc: 'events',
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-2'<'#status-filter-div'>><'col-sm-2'<'#zone-filter-div'>><'col-sm-2'<'#check-filter-div'>><'col-sm-2'<'#hide-events-filter-div'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'columns': [
            {data: 'check.status',
             name: 'status'},
            {data: 'zone_name',
             name: 'zone'},
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
            $('td:first', nRow).addClass(hourglass.statusclasses[aData['check']['status']]);
            $('td:first', nRow).html(aData['check']['status']);
        },
        'createdRow': function(nRow, aData, iDataIndex) {
            aData['check']['status'] = hourglass.statusnames[aData['check']['status']];
            if ( aData['check']['status'] === undefined ) {
                aData['check']['status'] = 'Unknown';
            }
            aData['href'] = UCHIWA_URL+'/#/client/'+aData['zone_name']+'/'+aData['client']['name']+'?check='+aData['check']['name'];
            $(nRow).data('href', aData['href']);
            $(nRow).click(function(e) {
                window.open($(this).data("href"), '_blank');
                e.stopPropagation();
            });
        },
        'initComplete': function (foo) {
            eventsfilters.create();
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
