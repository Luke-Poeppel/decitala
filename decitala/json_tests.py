import json
import jsonpickle

"""
TREANT TARGET:
nodeStructure: {
	text: {
		name: "ROOT",
		value: 1.0,
	},
	children: [
		{
			text:{
				name: "Pancama",
				value: 0.5
			},
			stackChildren: false,
		}
	]
}
"""

from nested_lookup import nested_delete, nested_lookup, get_occurrence_of_key

tree = '{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 1.0, "name": "D", "parent": null, "children": []}]}, {"value": 3.0, "name": "B", "parent": null, "children": []}]}, {"value": 1.0, "name": null, "parent": null, "children": [{"value": 2.0, "name": "C", "parent": null, "children": [{"value": 1.0, "name": "Test Overwrite", "parent": null, "children": []}]}]}, {"value": 3.0, "name": "A", "parent": null, "children": []}, {"value": 4.0, "name": null, "parent": null, "children": [{"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 2.0, "name": "Full Path", "parent": null, "children": []}]}]}]}]}}'
simple_tree = '{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": []}]}}'



def serialize(tree, for_treant=False):
	"""tree=pickled tree will not be needed in the actual tree."""
	def encapsulate(d):
		rv = {}
		value, name, parents, children = d.values()
		if name == None:
			name = ""
		if parents == None:
			parents = ""
		rv['text'] = {'value': value, 'name': name, 'parents': parents}
		rv['children'] = [encapsulate(c) for c in children]
		return rv

	if not for_treant:
		x = json.loads(tree)
		return json.dumps(x)
	else:
		loaded = json.loads(tree)
		w_text_field = {"nodeStructure" : encapsulate(loaded["root"])}
		return json.dumps(w_text_field)

# SO close! Just need to turn all the nulls into empty quotes or something. 
serialized = serialize(tree, for_treant=True)
loaded = json.loads(serialized)
print(serialized)
# print(type(serialized)) #{"nodeStructure" : encapsulate(json.loads(tree))})# ["root"])})


#print({'root': encapsulate(data['root'])})

# don't need to do a check: simply add the subdict to EVERY level. 



# OMG: JSON.parse in javascript :-) 

"""
Pipeline:
1. get the serialization in python
2. json load 
3. remove and add stuff
4. json dump
5. send dumped json to js
5. literal_eval...? 
"""

# we want to: 
# (some of this should be done in javascript).
# 1. remove the "root" (name of root) at the beginning
# 2. put the name / value info in ANOTHER dict called "text"
# 3. "text" and "children" cannot be strings.


#tree2 = '{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children":[]}]}}'


#print(tree2)







