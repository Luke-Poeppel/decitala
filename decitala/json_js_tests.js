// a = s.replace("'", '"')
// can't deal with NONE –– has to be null; or maybe 0? Make names blank and set parents to 0
// var tree = JSON.parse('{"ROOT": {"value": 1.0, "name": "", "parent": 0, "children": [{"value": 0.5, "name": "", "parent": 0, "children": []}]}}')

// var tree = JSON.parse('{"root": {"value": 1.0, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 1.0, "name": "D", "parent": "", "children": []}]}, {"value": 3.0, "name": "B", "parent": "", "children": []}]}, {"value": 1.0, "name": "", "parent": "", "children": [{"value": 2.0, "name": "C", "parent": "", "children": [{"value": 1.0, "name": "Test Overwrite", "parent": "", "children": []}]}]}, {"value": 3.0, "name": "A", "parent": "", "children": []}, {"value": 4.0, "name": "", "parent": "", "children": [{"value": 1.0, "name": "", "parent": "", "children": [{"value": 0.5, "name": "", "parent": "", "children": [{"value": 2.0, "name": "Full Path", "parent": "", "children": []}]}]}]}]}}')
var tree = JSON.parse('{"nodeStructure": {"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "D", "parents": ""}, "children": []}]}, {"text": {"value": 3.0, "name": "B", "parents": ""}, "children": []}]}, {"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 2.0, "name": "C", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "Test Overwrite", "parents": ""}, "children": []}]}]}, {"text": {"value": 3.0, "name": "A", "parents": ""}, "children": []}, {"text": {"value": 4.0, "name": "", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 2.0, "name": "Full Path", "parents": ""}, "children": []}]}]}]}]}}')

removeProps(tree,['parent']);

// parseObjectProperties(tree, function(key="value") {
//   console.log(function(key="value")
// })
// console.log(tree)

// console.log(tree["root"])
// console.log(tree)
  
// console.log(JSON.stringify(tree, null, ' \t'))



