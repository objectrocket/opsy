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
        url = hourglass.get_dashboard_url('/api/zones');
        $.getJSON(url, function updateZonesJSONCB(data) {
            newzones = []
            $.each(data.zones, function updateZonesEachCB(idx, obj) {
                newzones.push({label: obj.name, title: obj.name, value: obj.name});
            });
            self.zoneOptions = newzones;
        }).success(function updateZonesSuccessCB() {
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
        url = hourglass.get_dashboard_url('/api/checks');
        $.getJSON(url, function updateChecksJSONCB(data) {
            newchecks = []
            $.each(data.checks.sort(), function updateChecksEachCB(idx, obj) {
                newchecks.push({label: obj.name, title: obj.name, value: obj.name});
            });
            self.checkOptions = newchecks;
        }).success(function updateChecksSuccessCB() {
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
        $('select.ms').each(function setDTUrlEachCB(idx, obj) {
            params[$(obj).data('filter')] = $(obj).children('option:selected').map(function setDTUrlMapCB() { return this.value }).get().join(',')
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
    return document.eventstable.column(0).data().filter( function getStatusCountFilterCB(value, idx){
          return value == state ? true : false;
    }).length
}

var updateTitle = function() {
    crits = getStatusCount("Critical");
    warns = getStatusCount("Warning");
    document.title = crits+' Critical, '+warns+' Warning | Events | Hourglass';
}

$(document).ready(function documentReadyCB() {
    $.fn.dataTable.enum( [ 'Critical', 'Warning', 'OK' ] );
    document.eventstable = $('#events').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        'autoWidth': false,
        //'stateSave' : true,
        'order': [
            [ 0, 'asc' ],
            [ 5, 'desc' ],
        ],
        'ajax': {
            url: eventsfilters.setDataTablesUrl(),
            dataSrc: function(json) {
                json = json['events'];
                return_data = new Array();
                for (var i=0; i<json.length; i++) {
                    var row = json[i];
                    uchiwaHref = UCHIWA_URL+'/#/client/'+row['zone_name']+'/'+row['client_name']+'?check='+row['check_name'],
                    return_data.push({
                        'status': row['status'].capitalize(),
                        'zone': row['zone_name'],
                        'source': "<a href='"+uchiwaHref+"'><img src='/static/main/img/backends/sensu.ico'></img></a> <a href='/clients/"+row['zone_name']+"/"+row['client_name']+"'>"+row['client_name']+"</a>",
                        'check_name': row['check_name'],
                        'check_output': row['output'],
                        'count': row['occurrences'],
                        'timestamp': '<time class="timeago" datetime="'+row['updated_at']+'Z">'+row['updated_at']+'Z</time>',
                    })
                }
                return return_data;
            },
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-2'<'#status-filter-div'>><'col-sm-2'<'#zone-filter-div'>><'col-sm-2'<'#check-filter-div'>><'col-sm-2'<'#hide-events-filter-div'>><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'columns': [
            {data: 'status'},
            {data: 'zone'},
            {data: 'source'},
            {data: 'check_name'},
            {data: 'check_output'},
            {data: 'count'},
            {data: 'timestamp'},
        ],
        'rowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            $('td:first', nRow).addClass(hourglass.statusclasses[aData['status']]);
        },
        'initComplete': function (foo) {
            eventsfilters.create();
            hourglass.registerTask('update-events', 6, function() {
                //filters.update();
                document.eventstable.ajax.reload(null, false);
            });
        }
    }).on('draw.dt', function onDrawDTCB() {
        updateTitle();
        $('time.timeago').timeago();
    });
});
