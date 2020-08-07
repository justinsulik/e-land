const express = require('express');

const app = express();
const PORT = process.env.PORT || 5000;
app.use(express.static(__dirname + '/public'));
app.set('views', __dirname + '/public/views');
app.use('/python', express.static(__dirname + "/python"));
app.use('/libs', express.static(__dirname + "/libs"));
app.engine('html', require('ejs').renderFile);

app.get('/', (req, res, next) => {

    let runPy = new Promise(function(resolve, reject) {
        console.log("Node: python starting...");
        const { spawn } = require('child_process');
        const pyprog = spawn('python3', ['python/sim.py', 'browser']);
        let python_out = '';

        pyprog.stdout.on('data', function(data) {
            python_out += data.toString();
        });

        pyprog.stderr.on('data', (data) => {
            console.log("Python error!", data.toString())
            reject(data.toString());
        });

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
        // res.end(fromRunpy.toString());
    })
    .catch((err)=>{
      res.end(err);
    });
});


app.listen(PORT, () => console.log('Application listening on port '+PORT+'!'));
