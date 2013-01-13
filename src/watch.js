var fs   = require('fs'),
    path = require('path'),
    exec = require('child_process').exec;


var files = [
    path.join(__dirname, 'js/app.coffee'),
    path.join(__dirname, 'css/app.scss')
]
for (i = 0, len = files.length; i < len; ++i) {
    fs.watchFile(files[i], {interval: 200}, function() {
        exec('make debug', function(error, stdout, stderr) {
            console.log('stdout: ' + stdout);
            console.log('stderr: ' + stderr);
            if (error !== null) {
              console.log('exec error: ' + error);
            }
        });
    });
}