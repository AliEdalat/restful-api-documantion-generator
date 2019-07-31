import os
import sys
import ast
import yaml 
import json
import requests
import tempfile
import shutil
import config


class ApiDocGen(object):
	"""docstring for ApiDocGen"""
	def __init__(self, argv):
		super(ApiDocGen, self).__init__()
		self.__projectRoot = config.INPUT_ROOT
		self.parseVersion(argv)
		self.__outfile = ""
		self.__spec = ""
		self.__outPath = ""

	def updateVersionFile(self, value):
		file = open('versions',"w")
		file.write(value)
		file.close()

	def readVersionFile(self):
		versions = ''
		with open('versions', 'r') as inputFile:
			versions = inputFile.read()
		inputFile.close()
		return versions

	def autoVersion(self):
		versions = self.readVersionFile()
		if versions == '':
			self.__version = '0.0.1'
			self.updateVersionFile('0.0.1')
		else:
			self.__version = versions
			self.updateVersionFile(self.incrementVersion())

	def incrementVersion(self):
		temp = self.__version.split(".")
		print(temp)
		temp[0] = str(int(temp[0]) + 1)
		return '.'.join(temp)


	def parseVersion(self, argv):
		if len(argv) > 1:
			temp = argv[1].split('=')
			print(temp)
			lastVersion = self.readVersionFile()
			if len(temp) > 0 and temp[0] == '--version' and temp[1] > lastVersion:
				self.__version = temp[1]
				self.updateVersionFile(temp[1])
			elif not (temp[1] > lastVersion):
				raise Exception('last version is ' + lastVersion + ', please check your version number.')
			else:
				self.autoVersion()
		else:
			self.autoVersion()

	def createVersionDir(self):
		self.__outPath = 'docs/' + self.__version
		try:
			os.mkdir(self.__outPath)
		except OSError:
			print ("Creation of the directory %s failed" % self.__outPath)
		else:
			print ("Successfully created the directory %s " % self.__outPath)


	def updateDependencies(self):
		url = 'https://api.cdnjs.com/libraries?search=swagger-ui&fields=version'
		try:
			response = requests.get(url)
			print(response.text)
			jsonFormat = json.loads(response.text)
			print(jsonFormat['results'][0]['version'])
			baseUrl = 'https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/' + jsonFormat['results'][0]['version']
			filenames = ['/swagger-ui.css', '/swagger-ui-bundle.js', '/swagger-ui-standalone-preset.js']
			for item in filenames:
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
		except:
			print("connection error!")
			for item in filenames:
				shutil.copy('template' + item, self.__outPath + item)


	def prepareOutputDirectory(self):
		self.createVersionDir()
		self.__outfile = self.__outPath + '/index.html'
		self.updateDependencies()

	def parseFiles(self):
		for root, dirs, files in os.walk(self.__projectRoot, topdown=True):
			for name in files:
				if name.endswith('.py'):
					self.parseFile(os.path.join(root, name))

	def run(self):
		self.prepareOutputDirectory()
		self.parseFiles()
		print(self.__spec)
		self.toHtml()

	def parseFile(self, filename):
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
			self.parseDocString(docstring)

	def parseDocString(self, docstring):
		if docstring != "":
			if docstring.splitlines()[0] == config.KEYWORD:
				self.__spec += "\n".join(docstring.splitlines()[1:])

	def toHtml(self):
		template = ''
		with open('template/index.html', 'r') as inputFile:
			template = inputFile.read()
		spec = json.loads(self.__spec)
		file = open(self.__outfile,"w")
		file.write(template % json.dumps(spec))
		file.close()

adg = ApiDocGen(sys.argv)
adg.run()