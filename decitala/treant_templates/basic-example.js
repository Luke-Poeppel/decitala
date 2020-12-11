// var chart_config = {
//     chart: {
//         container: "#basic-example",
        
//         connectors: {
//             type: 'curve'
//         },
//         node: {
//             HTMLclass: "nodeExample1"
//         }
//     },

//     nodeStructure: {
//         text: {
//             name: "ROOT",
//             value: 1.0,
//         },
//         children: [
//             {
//                 text:{
//                     name: "Pancama",
//                     value: 0.5
//                 },
//                 stackChildren: false,
//             }
//         ]
//     }
// }

var tree = JSON.parse('{"nodeStructure": {"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "D", "parents": ""}, "children": []}]}, {"text": {"value": 3.0, "name": "B", "parents": ""}, "children": []}]}, {"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 2.0, "name": "C", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "Test Overwrite", "parents": ""}, "children": []}]}]}, {"text": {"value": 3.0, "name": "A", "parents": ""}, "children": []}, {"text": {"value": 4.0, "name": "", "parents": ""}, "children": [{"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": [{"text": {"value": 2.0, "name": "Full Path", "parents": ""}, "children": []}]}]}]}]}}')
// var tree = JSON.parse('{"nodeStructure": {"text": {"value": 1.0, "name": "", "parents": ""}, "children": [{"text": {"value": 0.5, "name": "", "parents": ""}, "children": []}]}}')

var chart_config = {
    chart: {
        container: "#basic-example",
        
        connectors: {
            type: 'curve'
        },
        node: {
            HTMLclass: "nodeExample1"
        }
    },
    nodeStructure: tree["nodeStructure"]
}

console.log(tree["nodeStructure"])
    
// }

// 
// removeProps(tree,['parent']);



// var chart_config = tree

// {
//     "nodeStructure": {
//          "text": {
//               "value": 1,
//               "name": "",
//               "parents": ""
//          },
//          "children": [
//               {
//                    "text": {
//                         "value": 0.5,
//                         "name": "",
//                         "parents": ""
//                    },
//                    "children": [
//                         {
//                              "text": {
//                                   "value": 0.5,
//                                   "name": "",
//                                   "parents": ""
//                              },
//                              "children": [
//                                   {
//                                        "text": {
//                                             "value": 1,
//                                             "name": "D",
//                                             "parents": ""
//                                        },
//                                        "children": []
//                                   }
//                              ]
//                         },
//                         {
//                              "text": {
//                                   "value": 3,
//                                   "name": "B",
//                                   "parents": ""
//                              },
//                              "children": []
//                         }
//                    ]
//               },
//               {
//                    "text": {
//                         "value": 1,
//                         "name": "",
//                         "parents": ""
//                    },
//                    "children": [
//                         {
//                              "text": {
//                                   "value": 2,
//                                   "name": "C",
//                                   "parents": ""
//                              },
//                              "children": [
//                                   {
//                                        "text": {
//                                             "value": 1,
//                                             "name": "Test Overwrite",
//                                             "parents": ""
//                                        },
//                                        "children": []
//                                   }
//                              ]
//                         }
//                    ]
//               },
//               {
//                    "text": {
//                         "value": 3,
//                         "name": "A",
//                         "parents": ""
//                    },
//                    "children": []
//               },
//               {
//                    "text": {
//                         "value": 4,
//                         "name": "",
//                         "parents": ""
//                    },
//                    "children": [
//                         {
//                              "text": {
//                                   "value": 1,
//                                   "name": "",
//                                   "parents": ""
//                              },
//                              "children": [
//                                   {
//                                        "text": {
//                                             "value": 0.5,
//                                             "name": "",
//                                             "parents": ""
//                                        },
//                                        "children": [
//                                             {
//                                                  "text": {
//                                                  "value": 2,
//                                                  "name": "Full Path",
//                                                  "parents": ""
//                                                  },
//                                                  "children": []
//                                             }
//                                        ]
//                                   }
//                              ]
//                         }
//                    ]
//               }
//          ]
//     }
// }








