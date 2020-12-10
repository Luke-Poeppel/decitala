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
tree = '{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 1.0, "name": "D", "parent": null, "children": []}]}, {"value": 3.0, "name": "B", "parent": null, "children": []}]}, {"value": 1.0, "name": null, "parent": null, "children": [{"value": 2.0, "name": "C", "parent": null, "children": [{"value": 1.0, "name": "Test Overwrite", "parent": null, "children": []}]}]}, {"value": 3.0, "name": "A", "parent": null, "children": []}, {"value": 4.0, "name": null, "parent": null, "children": [{"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": [{"value": 2.0, "name": "Full Path", "parent": null, "children": []}]}]}]}]}}'

from nested_lookup import nested_delete, nested_lookup, get_occurrence_of_key

def serialize(tree, for_treant=False):
	"""tree=pickled tree will not be needed in the actual tree."""
	if not for_treant:
		x = json.loads(tree)
		return json.dumps(x, indent=4)
	else:
		#tree = tree.replace('null', 'True')
		x = json.loads(tree)
		return json.dumps(x, indent=4)#, indent=4)
		#print(get_occurrence_of_key(x, 'parent'))
		#res = nested_delete(x, 'parent')
		#print(res)
		#tree = tree.replace('"name"', "root")
		#tree = tree.replace('"value"', "value")
		#return x
		#x = json.loads(tree)
		#print(type(x))


serialized = serialize(tree, for_treant=True)
#print(serialized)


simple_tree = '{"root": {"value": 1.0, "name": null, "parent": null, "children": [{"value": 0.5, "name": null, "parent": null, "children": []}]}}'

def add_encapsulation(json_input, lookup_key1, lookup_key2):
	for key, val in json_input.items():
		updated_key = "item"
		subdict = dict()
		if key == lookup_key1:
			vals[key] = json_input["value"]
		elif key == lookup_key2:
			vals[key] = json_input["name"]
			# I can't access the two keys in the same iteration, so you can't add them 
			# to the subdict. Also, where to update the subdict...? 
		else:
			item_generator(v, lookup_key)

print(serialized)


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







