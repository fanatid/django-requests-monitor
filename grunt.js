var fs         = require("fs");
var path       = require("path");
var browserify = require("browserify");
var shim       = require("browserify-shim");
var UglifyJS   = require("uglify-js");


module.exports = function(grunt) {
  "use strict";
  grunt.initConfig({
    scss: {
      src:  "src/css/app.scss",
      dest: "requests_monitor/static/requests_monitor/css/app.css"
    },
    mincss: {
      files: {
        src:  ["<config:scss.dest>"],
        dest: "<config:scss.dest>"
      }
    },
    coffee: {
      src:       "src/js/app.coffee",
      dest:      "requests_monitor/static/requests_monitor/js/app.js",
      vendorDir: "src/js/vendor"
    },
    watch: {
      coffee: {
        files: "<config:coffee.src>",
        tasks: "coffee:true"
      },
      scss: {
        files: "<config:scss.src>",
        tasks: "scss"
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-mincss');

  grunt.registerTask("default", "scss mincss coffee minjs");

  grunt.registerTask("scss", "Compile SCSS to CSS", function() {
    var done = this.async();
    var scss = grunt.utils.spawn({
      cmd:  "scss",
      args: [
        "--compass",
        path.join(__dirname, grunt.config("scss.src")),
        path.join(__dirname, grunt.config("scss.dest"))
      ]
    }, function(error, result, code) {
      done(!error);
      grunt.log.writeln(code);
    });
    scss.stdout.pipe(process.stdout);
    scss.stderr.pipe(process.stderr);
  });

  grunt.registerTask("coffee", "Compile CoffeeScript to JavaScript with help browserify", function(debug) {
    var bundled  = browserify({ debug: debug===undefined?false:true }),
      vendorDir  = path.join(__dirname, grunt.config("coffee.vendorDir")),
      files    = fs.readdirSync(vendorDir);
    for (var i = 0, len = files.length, alias, exports; i < len; i++) {
      if (!fs.statSync(path.join(vendorDir, files[i])).isFile())
        continue;
      alias = files[i].split(".").slice(0, -1).join("-");
      if (alias === "jquery")
        exports = "$"
      else
        exports = null;
      bundled = bundled.use(shim({
        alias:   alias,
        path:  path.join(vendorDir, files[i]),
        exports: exports
      }));
    }
    bundled = bundled.addEntry(path.join(__dirname, grunt.config("coffee.src")));
    fs.writeFileSync(path.join(__dirname, grunt.config("coffee.dest")),
        bundled.bundle());
  });

  grunt.registerTask("minjs", "Generate minifed JavaScript and SourceMap from file", function() {
    var toplevel = UglifyJS.parse(fs.readFileSync(path.join(__dirname, grunt.config("coffee.dest"))).toString());
    toplevel.figure_out_scope();
    var compressed_ast = toplevel.transform(UglifyJS.Compressor());
    compressed_ast.figure_out_scope();
    compressed_ast.compute_char_frequency();
    compressed_ast.mangle_names();

    var source_map = UglifyJS.SourceMap();
    var stream = UglifyJS.OutputStream({source_map: source_map});
    compressed_ast.print(stream);
    fs.writeFileSync(path.join(__dirname, grunt.config("coffee.dest")), stream.toString());
    //fs.writeFileSync(path.join(__dirname, grunt.config("coffee.dest") + ".map"), source_map.toString());
  });
};
