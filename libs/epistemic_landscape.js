// based on https://bl.ocks.org/Niekes/e920c03edd7950578b8a6cded8b5a1a5
var origin = [520, 520];
var j = Math.pow(data[0].landscape.length, 0.5);
var alpha = 0;
var beta = 0;
var hover_offset = 0.1;
var startAngleY = Math.PI/4; // for overhead view: 0
var startAngleX = 3*Math.PI/4; //for overhead view: Math.PI/2
var zoom = 15;

// Set up landscape
var svg = d3.select('svg')
  .call(d3.drag().on('drag', dragged)
  .on('start', dragStart)
  .on('end', dragEnd))
  .append('g');

var points, mx, my, mouseX, mouseY, agents;

var surface = d3._3d()
    .scale(zoom)
    .x(function(d){ return d.x; })
    .y(function(d){ return d.y; })
    .z(function(d){ return d.z; })
    .origin(origin)
    .rotateY(startAngleY)
    .rotateX(startAngleX)
    .shape('SURFACE', j);

var point3d = d3._3d()
   .scale(zoom)
   .x(function(d){ return d.x; })
   .y(function(d){ return d.y+hover_offset; })
   .z(function(d){ return d.z; })
   .origin(origin)
   .rotateY(startAngleY)
   .rotateX(startAngleX);

var altitude_color = d3.scaleLinear();
var visited_color = d3.scaleLinear();

// Updating landscape/agents at each time step

function processLandscape(data){
    var planes = svg.selectAll('path').data(data, function(d){ return d.plane; });
    planes
        .enter()
        .append('path')
        .attr('class', '_3d')
        .attr('stroke-opacity', 0.1)
        .attr('stroke', 'black')
        .attr('opacity', 1)
        .attr('fill', color_landscape)
        .attr('d', surface.draw);
    planes.exit().remove();
    d3.selectAll('._3d').sort(surface.sort);
}

function processAgents(data){
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
        .attr('fill', function(d){return color_agent(d.status)})
        .attr('opacity', 1);
    circles.exit().remove();
    d3.selectAll('._3d').sort(point3d.sort);
}

// Coloring
function color_landscape(d){
  if(color_map=="altitude"){
    return color_landscape_altitude(d);
  } else {
    return color_landscape_visited(d);
  }
}

function color_landscape_altitude(d){
  // var _y = (d[0].y + d[1].y + d[2].y + d[3].y)/4;
  var _y = d3.max([d[0].y + d[1].y + d[2].y + d[3].y]);
  return d3.interpolateViridis(altitude_color(_y));
}

function color_landscape_visited(d){
  var _y = d[1].visited;
  return d3.interpolateViridis(visited_color(_y))
}

function color_agent(status){
  switch(status){
    case 0:
      // exploring-straight line
      return "red";
      break;
    case 1:
      // social learning
      return "black";
      break;
    case 2:
      // leader
      return "white";
      break;
    case 3:
      // completely lost
      return "hotpink";
      break;
    case 4:
      // exploring-local
      return "indianred";
      break;
  }
}

// Interactivity

function dragStart(){
    mx = d3.event.x;
    my = d3.event.y;
}

function dragged(){
    mouseX = mouseX || 0;
    mouseY = mouseY || 0;
    beta   = (d3.event.x - mx + mouseX) * Math.PI / 230 ;
    alpha  = (d3.event.y - my + mouseY) * Math.PI / 230  * (-1);
    processLandscape(surface.rotateY(beta + startAngleY).rotateX(alpha + 3*startAngleX)(points), 0);
    processAgents(point3d.rotateY(beta + startAngleY).rotateX(alpha + 3*startAngleX)(agents), 0);
}

function dragEnd(){
    mouseX = d3.event.x - mx + mouseX;
    mouseY = d3.event.y - my + mouseY;
}
