console.log("HI!!!");

// HELPER: https://stackoverflow.com/questions/31728988/using-javascript-whats-the-quickest-way-to-recursively-remove-properties-and-va
function removeProps(obj,keys){
  if(obj instanceof Array){
    obj.forEach(function(item){
      removeProps(item,keys)
    });
  }
  else if(typeof obj === 'object'){
    Object.getOwnPropertyNames(obj).forEach(function(key){
      if(keys.indexOf(key) !== -1)delete obj[key];
      else removeProps(obj[key],keys);
    });
  }
}

// Helper: https://stackoverflow.com/questions/2549320/looping-through-an-object-tree-recursively
function parseObjectProperties (obj, parse) {
  for (var k in obj) {
    if (typeof obj[k] === 'object' && obj[k] !== null) {
      parseObjectProperties(obj[k], parse)
    } else if (obj.hasOwnProperty(k)) {
      parse(obj[k])
    }
  }
}

// a = s.replace("'", '"')
// can't deal with NONE –– has to be null; or maybe 0? Make names blank and set parents to 0
// var tree = JSON.parse('{"ROOT": {"value": 1.0, "name": "", "parent": 0, "children": [{"value": 0.5, "name": "", "parent": 0, "children": []}]}}')

var tree = JSON.parse('{"root": {"value": 1.0, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 1.0, "name": "D", "parent": "", "children": []}]}, {"value": 3.0, "name": "B", "parent": "", "children": []}]}, {"value": 1.0, "name": "", "parent": "", "children": [{"value": 2.0, "name": "C", "parent": "", "children": [{"value": 1.0, "name": "Test Overwrite", "parent": "", "children": []}]}]}, {"value": 3.0, "name": "A", "parent": "", "children": []}, {"value": 4.0, "name": "", "parent": "", "children": [{"value": 1.0, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 2.0, "name": "Full Path", "parent": "", "children": []}]}]}]}]}}')

removeProps(tree,['parent']);


// parseObjectProperties(tree, function(key="value") {
//   console.log(function(key="value")
// })
console.log(tree)

// console.log(tree["root"])
// console.log(JSON.stringify(tree)) // ,null,' \t'))



