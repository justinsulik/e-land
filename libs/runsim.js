// Call a child process to run the python script
const { spawn } = require('child_process');

exports.run_py = function(params={}){
  let run = new Promise(function(resolve, reject) {

      console.log("Node: python starting...");

      // arg 'browser' tells the pythons script that this is the source of the call
      // arg 'time' tells the simulation to report every time step
      const pyprog = spawn('python3', ['python/run_simulations.py', 'browser', 'time', JSON.stringify(params)]);

      // add data to string for eventual passing to the front end
      let python_out = '';
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
    console.log("runsim error!", err);
  });

  return run
}
