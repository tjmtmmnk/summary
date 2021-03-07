import json

filename = ""
title = """"""
body = """"""

data = {}
data["title"] = title
data["body"] = body

with open(filename, 'w') as outfile:
    json.dump(data, outfile)