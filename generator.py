import os
import sys
import ast
import yaml 
import json
import requests
import tempfile
import shutil
import config
import re


class ApiDocGen(object):
	"""docstring for ApiDocGen"""
	def __init__(self, argv):
		super(ApiDocGen, self).__init__()
		self.__projectRoot = config.INPUT_ROOT
		self.__parseVersion(argv)
		self.__outfile = ""
		self.__spec = ""
		self.__outPath = ""
		self.__info = ""
		self.__path = ""
		self.__server = ""
		self.__swaggerDependencyUrl = 'https://api.cdnjs.com/libraries?search=swagger-ui&fields=version'
		self.__swaggerDependencyfilenames = ['/swagger-ui.css', '/swagger-ui-bundle.js',\
			'/swagger-ui-standalone-preset.js']

	def __updateVersionFile(self, value):
		file = open('versions',"w")
		file.write(value)
		file.close()

	def __readVersionFile(self):
		versions = ''
		with open('versions', 'r') as inputFile:
			versions = inputFile.read()
		inputFile.close()
		return versions

	def __autoVersion(self):
		versions = self.__readVersionFile()
		if versions == '':
			self.__version = config.FIRST_VERSION
			self.__updateVersionFile(self.__incrementVersion())
		else:
			self.__version = versions
			self.__updateVersionFile(self.__incrementVersion())

	def __incrementVersion(self):
		temp = self.__version.split(".")
		print(temp)
		temp[0] = str(int(temp[0]) + 1)
		return '.'.join(temp)


	def __parseVersion(self, argv):
		if len(argv) > 1:
			temp = argv[1].split('=')
			print(temp)
			lastVersion = self.__readVersionFile()
			if len(temp) > 0 and temp[0] == '--version' and temp[1] > lastVersion:
				self.__version = temp[1]
				self.__updateVersionFile(temp[1])
			elif not (temp[1] > lastVersion):
				raise Exception('last version is ' + lastVersion + ', please check your version number.')
			else:
				self.__autoVersion()
		else:
			self.__autoVersion()

	def __createVersionDir(self):
		self.__outPath = 'docs/' + self.__version
		try:
			os.mkdir(self.__outPath)
		except OSError:
			print ("Creation of the directory %s failed" % self.__outPath)
		else:
			print ("Successfully created the directory %s " % self.__outPath)


	def __handleDependenciesOffline(self):
		for item in self.__swaggerDependencyfilenames:
			shutil.copy('template' + item, self.__outPath + item)

	def __handleDependenciesOnline(self, baseUrl):
		for item in self.__swaggerDependencyfilenames:
			myfile = requests.get(baseUrl + item)
			tf = tempfile.TemporaryFile()
			tf.write(myfile.text.encode())
			tf.seek(0)
			if len(tf.read()) > 0:
				tf.seek(0)
				open(self.__outPath + item, 'w').write(tf.read().decode())
				shutil.copy(self.__outPath + item, 'template' + item)
			else:
				shutil.copy('template' + item, self.__outPath + item)
			tf.close()

	def __updateDependencies(self):
		try:
			if config.ONLINE:
				response = requests.get(self.__swaggerDependencyUrl)
				print(response.text)
				jsonFormat = json.loads(response.text)
				print(jsonFormat['results'][0]['version'])
				baseUrl = 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/' + jsonFormat['results'][0]['version']
				self.__handleDependenciesOnline(baseUrl)
			else:
				self.__handleDependenciesOffline()
		except:
			print("connection error!")
			self.__handleDependenciesOffline()


	def __prepareOutputDirectory(self):
		self.__createVersionDir()
		self.__outfile = self.__outPath + '/index.html'
		self.__updateDependencies()

	def __parseFiles(self):
		for root, dirs, files in os.walk(self.__projectRoot, topdown=True):
			if not config.FROM_FILE:
				for name in files:
					if name.endswith('.py'):
						self.__parsePythonFile(os.path.join(root, name))
			else:
				for name in files:
					if name.endswith(config.EXTENSION):
						self.__parseJsonFile(os.path.join(root, name))

	def run(self):
		self.__prepareOutputDirectory()
		self.__parseFiles()
		print(self.__spec)
		self.__toHtml()

	def __parseJsonFile(self, filename):
		print(filename)
		file_contents = ""
		with open(filename) as fd:
			file_contents = fd.read()
		self.__parseDocString(file_contents)

	def __parsePythonFile(self, filename):
		print(filename)
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
			self.__parseDocString(docstring)

	def __parseDocString(self, docstring):
		if docstring != "":
			lines = docstring.splitlines()
			start = 0
			for i in range(0,len(lines)): 
				if lines[i].strip() == config.KEYWORD:
					end = lambda a, b, start: [i+1 for i in range(start, len(a)) if a[i].strip() == b][0]-1
					j = end(lines,'@end', start)
					start = j+2
					if lines[i+1].strip() == '@path':
						self.__path += "\n".join(lines[i+2:j])
					elif lines[i+1].strip() == '@server':
						self.__server += "\n".join(lines[i+2:j])
					elif lines[i+1].strip() == '@info':
						self.__info += "\n".join(lines[i+2:j])

	def __toHtml(self):
		template = ''
		specTemplate = ''
		with open('template/index.html', 'r') as inputFile:
			template = inputFile.read()
		with open('template/api.json', 'r') as inputFile:
			specTemplate = inputFile.read()
		self.__path = re.sub('\,$', '', self.__path)
		spec = json.loads(specTemplate % (self.__info, self.__server, self.__path))
		self.__writeDocumentJson(json.dumps(spec, indent=4, sort_keys=True))
		print(json.dumps(spec, indent=4, sort_keys=True))
		file = open(self.__outfile,"w")
		file.write(template % json.dumps(spec, indent=4, sort_keys=True))
		file.close()

	def __writeDocumentJson(self, jsonString):
		file = open(self.__outPath + '/doc.json',"w")
		file.write(jsonString)
		file.close()		

adg = ApiDocGen(sys.argv)
adg.run()