// based on https://bl.ocks.org/Niekes/e920c03edd7950578b8a6cded8b5a1a5
var origin = [480, 480];
var j = Math.pow(data[0].landscape.length, 0.5);
var alpha = 0;
var beta = 0;
var hover_offset = 0.6;
var startAngle = Math.PI/4;
var svg = d3.select('svg')
  .call(d3.drag().on('drag', dragged)
  .on('start', dragStart)
  .on('end', dragEnd))
  .append('g');

var points, mx, my, mouseX, mouseY, agents;

var surface = d3._3d()
    .scale(10)
    .x(function(d){ return d.x; })
    .y(function(d){ return d.y; })
    .z(function(d){ return d.z; })
    .origin(origin)
    .rotateY(startAngle)
    .rotateX(3*startAngle)
    .shape('SURFACE', j);

var point3d = d3._3d()
   .scale(10)
   .x(function(d){ return d.x; })
   .y(function(d){ return d.y+hover_offset; })
   .z(function(d){ return d.z; })
   .origin(origin)
   .rotateY(startAngle)
   .rotateX(3*startAngle);

var color = d3.scaleLinear();

function processLandscape(data, tt){
    var planes = svg.selectAll('path').data(data, function(d){ return d.plane; });
    planes
        .enter()
        .append('path')
        .attr('class', '_3d')
        .attr('fill', colorize)
        .attr('opacity', 0)
        .attr('stroke-opacity', 0.1)
        .merge(planes)
        .attr('stroke', 'black')
        .transition().duration(tt)
        .attr('opacity', 1)
        .attr('fill', colorize)
        .attr('d', surface.draw);
    planes.exit().remove();
    d3.selectAll('._3d').sort(surface.sort);
}

function processAgents(data, tt){
    var circles = svg.selectAll('circle').data(data);
    circles
        .enter()
        .append('circle')
        .attr('class', '_3d')
        .attr('opacity', 0)
        .attr('cx', function(d){return(d.projected.x);})
        .attr('cy', function(d){return(d.projected.y);})
        .attr('r', 4)
        .attr('stroke', function(d){ return "black"; })
        .attr('fill', function(d){
          if(d.status==0){
            return "red";
          } else {
            return "black";
          }
        })
        .attr('opacity', 1);
    circles.exit().remove();
    d3.selectAll('._3d').sort(point3d.sort);
}

function colorize(d){
    var _y = (d[0].y + d[1].y + d[2].y + d[3].y)/4;
    return d.ccw ? d3.interpolateViridis(color(_y)) : d3.color(d3.interpolateViridis(color(_y))).darker(2.5);
}

function dragStart(){
    mx = d3.event.x;
    my = d3.event.y;
}

function dragged(){
    mouseX = mouseX || 0;
    mouseY = mouseY || 0;
    beta   = (d3.event.x - mx + mouseX) * Math.PI / 230 ;
    alpha  = (d3.event.y - my + mouseY) * Math.PI / 230  * (-1);
    processLandscape(surface.rotateY(beta + startAngle).rotateX(alpha + 3*startAngle)(points), 0);
    processAgents(point3d.rotateY(beta + startAngle).rotateX(alpha + 3*startAngle)(agents), 0);
}

function dragEnd(){
    mouseX = d3.event.x - mx + mouseX;
    mouseY = d3.event.y - my + mouseY;
}

function init(data){
    // clear old
    svg.selectAll('circle').remove();
    svg.selectAll('path').remove();
    //landscape
    points = data.landscape;
    var yMin = d3.min(points, function(d){ return d.y; });
    var yMax = d3.max(points, function(d){ return d.y; });
    color.domain([yMin, yMax]);
    processLandscape(surface(points), 0);
    //agents
    // todo: necessary to double up on code like this? cf. above poitns
    agents = data.population;
    processAgents(point3d(agents), 1000);
}

function change(data){
    var iteration = 0;
    d3.interval(function(){
      init(data[iteration]);
      if(iteration<data.length-1){
        iteration += 1;
      }
    }, 100);
}

// d3.selectAll('button').on('click', ()=>{
//   console.log(i)
//   i += 1
//   change(data, i)
// });
