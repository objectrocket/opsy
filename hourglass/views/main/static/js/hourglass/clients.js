var clientsfilters = {

    zoneOptions: [],

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
            clientsfilters.setDataTablesUrl();
            document.eventstable.ajax.reload(null, false);
        },
    },

    create: function() {
        hourglass.addFormGroup('zone');
        this.updateZones(true);
    },

    update: function() {
        this.updateZones();
        this.updateChecks();
    },

    updateZones: function(init) {
        var self = this;
        $.getJSON('/api/list/zones', function(data) {
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

    setDataTablesUrl: function() {
        params = {}
        $('select.ms').each(function(idx, obj) {
            params[$(obj).data('filter')] = $(obj).children('option:selected').map(function() { return this.value }).get().join(',')
        });
        if ( $.QueryString['dashboard'] ) {
            params['dashboard'] = $.QueryString['dashboard'];
        }
        try {
            document.eventstable.ajax.url('/api/clients?'+$.param(params));
        } catch(err) {
        }
        return '/api/clients?'+$.param(params);
    }
}

$(document).ready(function() {

    document.eventstable = $('#clients').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        'autoWidth': false,
        //'stateSave' : true,
        'order': [
            [ 0, 'asc' ],
            [ 1, 'asc' ],
        ],
        'ajax': {
            url: clientsfilters.setDataTablesUrl(),
            dataSrc: 'clients',
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-2'<'#zone-filter-div'>><'col-sm-6'><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
        'columns': [
            {data: 'zone_name',
             name: 'zone'},
            {data: 'name',
             name: 'name'},
            {data: 'address',
             name: 'ip'},
            {data: 'version',
             name: 'version'},
            {data: 'timestamp',
             name: 'timestamp',
             defaultContent: ''},
        ],
        'rowCallback': function( nRow, aData, iDisplayIndex, iDisplayIndexFull ) {
            var d = new Date(0);
            d.setUTCSeconds(aData['timestamp']);
            try {
                $('td:last', nRow).html('<time class="timeago" datetime="'+d.toISOString()+'">'+d+'</time>');
            } catch(err){
            }
        },
        'initComplete': function (foo) {
            clientsfilters.create();
            setInterval( function() {
                //filters.update();
                document.eventstable.ajax.reload(null, false);
            }, 30000);
        }
    }).on('draw.dt', function() {
        $('time.timeago').timeago();
    });
});
