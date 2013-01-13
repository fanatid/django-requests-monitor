var fs         = require('fs'),
    path       = require('path'),
    browserify = require('browserify'),
    shim       = require('browserify-shim'),
    UglifyJS   = require("uglify-js");


function bundle(debug) {
    if (debug === undefined)
        debug = true;
    var builtFile = path.join(__dirname, '../../requests_monitor/static/requests_monitor/js/app.js');
    var vendorDir = path.join(__dirname, 'vendor');
    var entryFile = path.join(__dirname, 'app.coffee');

    var bundled = browserify({ debug: debug })
        .use(shim({
            alias:   'jquery',
            path:    path.join(vendorDir, 'jquery.js'),
            exports: '$'
        }))
        .use(shim({
            alias:   'jquery-strftime',
            path:    path.join(vendorDir, 'jquery.strftime.js'),
            exports: null
        }))
        .use(shim({
            alias:   'jquery-cookie',
            path:    path.join(vendorDir, 'jquery.cookie.js'),
            exports: null
        }))
        .use(shim({
            alias:   'underscore',
            path:    path.join(vendorDir, 'underscore.js'),
            exports: null
        }))
        .use(shim({
            alias:   'backbone',
            path:    path.join(vendorDir, 'backbone.js'),
            exports: null
        }))
        .use(shim({
            alias:   'mustache',
            path:    path.join(vendorDir, 'mustache.js'),
            exports: null
        }))
        .addEntry(entryFile)
        .bundle()
        .shim();

    if (!debug) {
        var ast = UglifyJS.parse(bundled);
        ast.figure_out_scope();
        ast = ast.transform(UglifyJS.Compressor());
        bundled = ast.print_to_string();
    }

    fs.writeFileSync(builtFile, bundled);
}

var debug = false;
var argv = process.argv.slice(2);
if (argv[0] === '-d' || argv[0] == '--debug')
    debug = true;
bundle(debug);
