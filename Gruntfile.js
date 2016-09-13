/*global module:false*/
module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    // Metadata.
    pkg: grunt.file.readJSON('package.json'),
    banner: '/*! <%= pkg.title || pkg.name %> - v<%= pkg.version %> - ' +
      '<%= grunt.template.today("yyyy-mm-dd") %>\n' +
      '<%= pkg.homepage ? "* " + pkg.homepage + "\\n" : "" %>' +
      '* Copyright (c) <%= grunt.template.today("yyyy") %> <%= pkg.author.name %>;' +
      ' Licensed <%= _.pluck(pkg.licenses, "type").join(", ") %> */\n',
    // Task configuration.
    jscs: {
      src: [
        "opsy/static/js/opsy/",
        "opsy/plugins/monitoring/static/js/opsy_monitoring/",
      ],
      options: {
        reporter: "inline",
      }
    },
    watch: {
      gruntfile: {
        files: '<%= jshint.gruntfile.src %>',
        tasks: ['jshint:gruntfile']
      },
      lib_test: {
        files: '<%= jshint.lib_test.src %>',
        tasks: ['jshint:lib_test', 'qunit']
      }
    },
    connect: {
      server: {
        options: {
          port: 8000,
          base: '.',
        }
      }
    },
    blanket_qunit: {
      opsy: {
        options: {
          urls: [
            'http://localhost:8000/tests/javascript/opsy/opsy.html?coverage=true&gruntReport',
          ],
          threshold: 85,
        },
      },
      opsy_monitoring: {
        options: {
          urls: [
            'http://localhost:8000/tests/javascript/opsyMonitoring/opsyMonitoring.html?coverage=true&gruntReport',
          ],
          threshold: 85,
        },
      },
    },
  });

  // These plugins provide necessary tasks.
  grunt.loadNpmTasks("grunt-jscs");
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-connect');
  grunt.loadNpmTasks('grunt-blanket-qunit');

  // Default task.
  grunt.registerTask('default', ['connect', 'jscs', 'blanket_qunit']);

};
