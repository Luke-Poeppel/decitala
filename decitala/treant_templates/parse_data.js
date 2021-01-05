console.log("Parsing JSON data & Creating Tree...")

// HELPER: https://stackoverflow.com/questions/31728988/using-javascript-whats-the-quickest-way-to-recursively-remove-properties-and-va
function removeProps(obj,keys){
    if(obj instanceof Array){
      obj.forEach(function(item){
        removeProps(item, keys)
      });
    }
    else if(typeof obj === 'object'){
      Object.getOwnPropertyNames(obj).forEach(function(key){
        if(keys.indexOf(key) !== -1)delete obj[key];
        else removeProps(obj[key], keys);
      });
    }
  }

require("./Treant.min.js"); 
const html2canvas = require("./html2canvas.min.js");
const saveAs = require("./FileSaver.min.js");

// import html2canvas from "html2canvas";
// require("./jquery.min.js");

var tree_data = require("./tree.json");
var tree = JSON.parse(tree_data);

removeProps(tree,['parents']);

var chart_config = {
    chart: {
        container: "#mytree",
        
        connectors: {
            type: 'curve'
        },
        node: {
            HTMLclass: "nodeExample1"
        }
    },
    nodeStructure: tree["nodeStructure"]
}

new Treant(chart_config);

html2canvas(document.body).then(function(canvas) {
  // document.body.appendChild(canvas);
  saveAs(canvas.toDataURL(), 'tree-diagram.png');
});