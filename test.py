# read JSON file and parse contents
import json


with open('sample_data.json', encoding='utf-8') as fh:
    data = json.load(fh)

print(data)

li = list(filter(lambda x: x["name"] == "Minh", data))
member = li[0]

messages = member["messages"]

messages = [x for x in messages if x["type"] != "newyear"]
messages = [x for x in messages if x["type"] != "christmas"]
data[data.index(member)]["messages"] = messages
print(data)