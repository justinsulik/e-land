const express = require('express');
const runsim = require('./libs/runsim.js');
const body_parser = require('body-parser')

const app = express();
const PORT = process.env.PORT || 5000;

app.use(express.static(__dirname + '/public'));
app.use(body_parser.json());
app.set('views', __dirname + '/public/views');
app.use('/python', express.static(__dirname + "/python"));
app.use('/libs', express.static(__dirname + "/libs"));
app.engine('html', require('ejs').renderFile);

app.get('/', (req, res, next) => {

    runsim.run_py().then((data) => {
        console.log('Node: python script success!');
        res.render('index.html', {data: JSON.stringify(data)});
    })
    .catch((err)=>{
      res.end(err);
    });

});

app.post('/runsim', (req, res, next) => {
  var params = req.body;
  runsim.run_py(params).then((data) => {
      console.log('Node: python script success!');
      res.send(JSON.stringify(data)).end();
  })
  .catch((err)=>{
    res.end(err);
  });

})

app.listen(PORT, () => console.log('Application listening on port '+PORT+'!'));
