import os
import sys
import ast
import yaml 
import json


class ApiDocGen(object):
	"""docstring for ApiDocGen"""
	def __init__(self, projectRoot, outfile):
		super(ApiDocGen, self).__init__()
		self.__projectRoot = projectRoot
		self.__outfile = outfile
		self.__spec = ""


	def parseFiles(self):
		for root, dirs, files in os.walk(self.__projectRoot, topdown=True):
			for name in files:
				self.parseFile(os.path.join(root, name))

	def run(self):
		self.parseFiles()
		print(self.__spec)
		self.yamlToHtml(self.__outfile)

	def parseFile(self, filename):
		file_contents = ""
		with open(filename) as fd:
			file_contents = fd.read()
		module = ast.parse(file_contents)
		for node in ast.walk(module):
			try:
				docstring = ast.get_docstring(node)
				if docstring is None:
					docstring = ""
			except Exception as e:
				docstring = ""
			self.parseDocString(docstring)

	def parseDocString(self, docstring):
		if docstring != "":
			if docstring.splitlines()[0] == '@route':
				self.__spec += "\n".join(docstring.splitlines()[1:])

	def yamlToHtml(self, outfile):
		TEMPLATE = """
		<!DOCTYPE html>
		<html lang="en">
		<head>
			<meta charset="UTF-8">
			<title>Swagger UI</title>
			<link href="https://fonts.googleapis.com/css?family=Open+Sans:400,700|Source+Code+Pro:300,600|Titillium+Web:400,600,700" rel="stylesheet">
			<link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.2.2/swagger-ui.css" >
			<style>
				html
				{
					box-sizing: border-box;
					overflow: -moz-scrollbars-vertical;
					overflow-y: scroll;
				}
				*,
				*:before,
				*:after
				{
					box-sizing: inherit;
				}

				body {
					margin:0;
					background: #fafafa;
				}
			</style>
		</head>
		<body>

		<div id="swagger-ui"></div>

		<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.2.2/swagger-ui-bundle.js"> </script>
		<script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/3.2.2/swagger-ui-standalone-preset.js"> </script>
		<script>
		window.onload = function() {

			var spec = %s;

			// Build a system
			const ui = SwaggerUIBundle({
				spec: spec,
				dom_id: '#swagger-ui',
				deepLinking: true,
				presets: [
					SwaggerUIBundle.presets.apis,
					SwaggerUIStandalonePreset
				],
				plugins: [
					SwaggerUIBundle.plugins.DownloadUrl
				],
				layout: "StandaloneLayout"
			})

			window.ui = ui
		}
		</script>
		</body>

		</html>
		"""

		spec = json.loads(self.__spec)
		file = open(outfile,"w") 
		file.write(TEMPLATE % json.dumps(spec))
		file.close()