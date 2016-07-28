var checksfilters = {

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
            checksfilters.setDataTablesUrl();
            document.checkstable.ajax.reload(null, false);
        },
    },

    create: function() {
        hourglass.addFormGroup('zone');
        this.updateZones(true);
        hourglass.addFormGroup('check');
        this.updateChecks(true);
    },

    update: function() {
        this.updateZones();
        this.updateChecks();
    },

    updateZones: function(init) {
        var self = this;
        $.getJSON('/api/zones', function(data) {
            newzones = []
            $.each(data.zones, function(idx, obj) {
                newzones.push({label: obj.name, title: obj.name, value: obj.name});
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
        $.getJSON('/api/checks', function(data) {
            newchecks = []
            $.each(data.checks.sort(), function(idx, obj) {
                newchecks.push({label: obj.name, title: obj.name, value: obj.name});
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
            document.checkstable.ajax.url('/api/checks?'+$.param(params));
        } catch(err) {
        }
        return '/api/checks?'+$.param(params);
    }
}

$(document).ready(function() {

    document.checkstable = $('#checks').DataTable({
        'lengthMenu': [ [25, 50, 100, -1], [25, 50, 100, "All"] ],
        'autoWidth': false,
        //'stateSave' : true,
        'ajax': {
            url: checksfilters.setDataTablesUrl(),
            dataSrc: 'checks',
        },
        'dom': "<'row'<'col-sm-2'l><'col-sm-2'<'#zone-filter-div'>><'col-sm-2'<'#check-filter-div'>><'col-sm-4'><'col-sm-2'f>><'row'<'col-sm-12'tr>><'row'<'col-sm-5'i><'col-sm-7'p>>",
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
        'initComplete': function (foo) {
            checksfilters.create();
            hourglass.registerTask('update-checks', 6, function() {
                //filters.update();
                document.checkstable.ajax.reload(null, false);
            });
        }
    })
});
