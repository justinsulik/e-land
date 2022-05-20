
// Initiate data and then update

var animation_speed = 50;

function cycle(data, iteration){
    // clear old
    svg.selectAll('circle').remove();
    svg.selectAll('path').remove();
    // filter data for this iteration
    points = data[iteration].landscape;
    agents = data[iteration].population;
    // set color for first iteration
    if(iteration==0){
      var yMin = d3.min(points, function(d){ return d.y; });
      var yMax = d3.max(points, function(d){ return d.y; });
      altitude_color.domain([yMin, yMax]);
      visited_color.domain([0, agents.length]);
    }

    // process landscape and agent data
    processLandscape(surface(points));
    processAgents(point3d(agents));
}

function start_animation(data, animation_speed){
    var iteration = 0;
    interval = d3.interval(function(){
      cycle(data, iteration);
      if(iteration<data.length-1){
        iteration += 1;
      }
    }, animation_speed);
}
