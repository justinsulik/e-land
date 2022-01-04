const express = require('express');

const app = express();
const PORT = process.env.PORT || 5000;
app.use(express.static(__dirname + '/public'));
app.set('views', __dirname + '/public/views');
app.use('/python', express.static(__dirname + "/python"));
app.use('/libs', express.static(__dirname + "/libs"));
app.engine('html', require('ejs').renderFile);

app.get('/', (req, res, next) => {
    // Call a child process to run the python script
    let runPy = new Promise(function(resolve, reject) {
        console.log("Node: python starting...");
        const { spawn } = require('child_process');
        // 'browser' tells the pythons script that this is the source of the call
        // 'all' tells the simulation to report every time step
        const pyprog = spawn('python3', ['python/run_simulations.py', 'browser', 'time']);
        let python_out = '';
        // add data to string for eventual passing to the front end
        pyprog.stdout.on('data', function(data) {
            python_out += data.toString();
        });
        pyprog.stdout.on('message', function(data) {
            console.log(data);
        });

        // handle errors
        pyprog.stderr.on('data', (data) => {
            console.log("Python error!", data.toString());
            reject(data.toString());
        });

        // at the end of the data stream, split the data into messages (--> console) and data (--> browser)
        pyprog.stdout.on('end', () => {
            console.log('Node: python end...');
            var data = [];
            python_out.split('\n').forEach(function(d,i){
              if(d.length>0){
                d = JSON.parse(d);
                if(d.type=="message"){
                  console.log(d.data);
                } else if (d.type=="data") {
                  data.push(JSON.parse(d.data));
                }
              }
            });
            resolve(data);
        });

    }).catch((err)=>{
      console.log("Python error! catch");
    });

    runPy.then((data) => {
        console.log('Node: python script success!');
        res.render('index.html', {data: JSON.stringify(data)});
    })
    .catch((err)=>{
      res.end(err);
    });
});

app.listen(PORT, () => console.log('Application listening on port '+PORT+'!'));
