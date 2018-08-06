#!/usr/bin/env python3
from os import listdir
from os.path import isfile, join
import xml.etree.ElementTree as ET
import xmlschema
import os.path
from os import path
from colorama import init, Fore, Back, Style
import shutil
import subprocess
init()

#global variables
inputDir ="./input"
outputDir= "./output"
workDir  = "./working"
errDir  = "./error"
inputs = []

class Video:
	def __init__(self, file: str, size: int):
		self.file= file
		self.size = size

class Audio:
	def __init__(self, file: str, size: int, fmt: str, lang: str, chans: int):
		self.file= file
		self.size = size
		self.format= fmt
		self.lang = lang
		self.channels = chans

class Input:
	def __init__(self, audios: "list of Audios", video: Video, xmlFile: str):
		print("initing video " +video.file)
		self.video= video
		self.audios = audios
		self.xmlFile = xmlFile

	def GetAudio(self):
		if self.HasMuxedAudio():
			return self.video.file
		else:
			for audio in self.audios:
				if audio.channels ==2:
			 		return audio.file
		return ""

	def HasMuxedAudio(self):
		for audio in self.audios:
			if audio.file == self.video.file:
				print("The audio of " + self.video.file + " is muxed, no need to get another file")
				return True
		return False

	def Process(self):
		print("Processing " + self.xmlFile+"...")
		self.output = os.path.splitext(os.path.basename(self.video.file))[0]+"-low.mp4"
		shutil.move(inputDir+"/"+self.xmlFile, workDir+"/"+self.xmlFile)
		shutil.move(inputDir+"/"+self.video.file, workDir+"/"+self.video.file)
		args = ["ffmpeg", "-y", "-i", workDir+"/"+self.video.file]
		if self.GetAudio() != "":
			args = args + ["-i", workDir+"/" +self.GetAudio(), "-c:a", "aac"]
		args = args +['-vf', 'scale=-2:720', "-c:v", 
			"libx264", "-bf", "0", "-crf", "22", workDir+"/" + self.output]
		print(args)
		ret = subprocess.call(args)
		return ret

	def MoveToDone(self):
		shutil.move(workDir+"/"+self.video.file, outputDir+"/"+self.video.file)
		shutil.move(workDir+"/"+self.xmlFile, outputDir+"/"+self.xmlFile)
		for audio in self.audios:
			if audio.file != self.video.file:
				shutil.move(workDir+"/"+audio.file, outputDir+"/"+audio.file)

		shutil.move(workDir+"/"+self.output, outputDir+"/"+self.output)

	def MoveToError(self):
		if path.exists(inputDir+"/"+self.video.file):
			shutil.move(inputDir+"/"+self.video.file, errDir+"/"+self.video.file)
		if path.exists(inputDir+"/"+self.xmlFile):
			shutil.move(inputDir+"/"+self.xmlFile, errDir+"/"+self.xmlFile)
		for audio in self.audios:
			if path.exists(inputDir+"/"+audio.file):
				shutil.move(inputDir+"/"+audio.file, errDir+"/"+audio.file)
		print(Fore.RED + "Files are missing, moving to error")
		print(Style.RESET_ALL)

	def MoveFiles(self):
		return

	def Check(self) -> bool:
		print("Checking that the files listed in " + self.xmlFile+ " are present")
		if path.exists(inputDir + "/" + self.video.file) and (os.path.getsize(inputDir + "/" + self.video.file) == self.video.size):
			print(self.video.file + " is present on the disk")
		else:			
			print(Fore.RED + self.video.file + " is NOT present on the disk or has the wrong size")
			print(Style.RESET_ALL)
			return False
		for audio in self.audios:
			if path.exists(inputDir + "/" + audio.file) and (os.path.getsize(inputDir + "/" + audio.file) == audio.size or audio.size == 0):
				print(Fore.RED + audio.file + " is present on the disk")
				print(Style.RESET_ALL)
			else:			
				print(Fore.RED + audio.file + " is NOT present on the disk or has the wrong size")
				print(Style.RESET_ALL)
				return False	
		self.HasMuxedAudio()
		return True	



def validateXML(xmlFile: str) -> Input:
	filePath = inputDir + "/" + xmlFile 
	print("Validating " + filePath)
	try:
		tree = ET.parse(filePath)
		root = tree.getroot()
		my_schema = xmlschema.XMLSchema('imac.xsd')
		if my_schema.is_valid(filePath):
			print(filePath + " is a valid ACM XML")
		else:
			print(Fore.RED + filePath + " is not a valid ACM XML")
			print(Style.RESET_ALL)
			return None

		inputs = root.find('inputs')
		video = inputs.find('video')
		audios = inputs.findall('audio')
		audioItemList = []
		videoItem  = Video(file=video.find('file').text, size=int(video.find('size').text))

		for audio in audios:
			audioName = file = audio.find('file').text
			size = 0
			if audioName != videoItem.file:
				size = int(audio.find('size').text)
			audioItemList += [Audio(file = audio.find('file').text, 
				size = size,
				lang = audio.find('lang').text,
				fmt = audio.find('format').text,
				chans=int(audio.find('channels').text))]
		return Input(audioItemList,videoItem,xmlFile)
	except ET.ParseError:
		return None

def printSeparator():
	print("#"*80)

printSeparator()
print("Starting Imakron")
printSeparator()


print("Listing xml files in " + inputDir  +":")

onlyfiles = [f for f in listdir(inputDir) if isfile(join(inputDir, f)) and f.endswith(".xml")]
for s in onlyfiles:   
	print("") 
	work = validateXML(s)     
	if work == None:
		print(Fore.RED + "Error " + s + " is not valid")
		print(Style.RESET_ALL)
		shutil.move(inputDir+"/"+s, errDir+"/"+s)
		continue

	if not work.Check():
		work.MoveToError()
		continue
	if work.Process() == 0:
		work.MoveToDone()
		print(Fore.GREEN + s + " has been processed successfully")
		print(Style.RESET_ALL)


print(Fore.GREEN)
printSeparator()
print("Processing finished")
printSeparator()