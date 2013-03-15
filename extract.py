# coding: utf-8
from __future__ import division


from pdfminer.pdfparser import PDFParser, PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer.layout import LAParams, LTChar
from pdfminer.converter import PDFPageAggregator

import sys, re, operator, math, json, string, random, nltk, requests, os, os.path
from numpy import median
from collections import Counter
from collections import defaultdict

mode = ""


class cit:

	def  __init__(self, filename = ''):
		
		# Open a PDF file.
		fp = open(filename, 'rb')
		# Create a PDF parser object associated with the file object.
		parser = PDFParser(fp)
		# Create a PDF document object that stores the document structure.
		doc = PDFDocument()
		# Connect the parser and document objects.
		parser.set_document(doc)
		doc.set_parser(parser)
		# Supply the password for initialization.
		# (If no password is set, give an empty string.)
		doc.initialize('')
		# Check if the document allows text extraction. If not, abort.
		if not doc.is_extractable:
			raise PDFTextExtractionNotAllowed
		# Create a PDF resource manager object that stores shared resources.
		rsrcmgr = PDFResourceManager()

		# Set parameters for analysis.
		laparams = LAParams()

		# Create a PDF device object.
		self.device = PDFPageAggregator(rsrcmgr, laparams=laparams)

		# Create a PDF interpreter object.
		self.interpreter = PDFPageInterpreter(rsrcmgr, self.device)



		#quirks mode PMLA is nessisary for the short term until we can find a better source
		#the PMLA pdfs we are using have broken wods throughout it.
		#TODO: Figure out the fractured text or get different PMLA source
		self.quirksModePMLA = False
		if filename.find("pmla_") != -1:
			self.quirksModePMLA = True

				
		self.calaisName = 'ausename'
		self.calaisKey =  'akey'
		
				
		"""		
		for xref in doc.xrefs:	
			info_ref = xref.trailer.get('Info')
			if info_ref:
				#info = resolve1(info_ref)
				print info_ref
		"""
		 
	 
		report = {}
		
				
		#load the pages
		self.pages = doc.get_pages()
		self.storeLayouts()

		#figureout the font sizes used
		self.storeFontSizes()

		#figure out if the doc is multi column
		self.analyzePages()

		
		#process the text
		self.returnText()
		
		
		
		#try to extract the bib if it is there
		self.extractBib()
		
				
		#work on the the text itself.
		self.analyzeText()
		
		
		if self.fontDetectionError:
			print "Error: Unifont size, TODO: Fix this :("
			print self.fontSizes
			print self.fontSizeBody, self.fontSizeFoot 	
			sys.exit()

		
		
		

		
		

		#fromat and store some text
		self.prepareText()
		
		#self.NERText()
		 
		if self.citationTypeInline:		
			
				
			self.analyzeBib()
			
			#self.checkForInlineCitation()
			
			report['data'] = self.notesWeb
			report['authors'] = self.webAuthorCount
			report['docLen'] = len(self.tokenizedBodySentences)
			
			
		else:
			self.extractNotes()
			self.analyzeNotes()
			
			report['data'] = self.notesWeb
			report['authors'] = self.webAuthorCount
			report['docLen'] = self.bodyTextLength
		 
		 
		 
		report['fontSizes'] = str(self.fontSizes)
		 
		if self.citationTypeNote:
			if self.isFootNote:
				report['style'] = 'Footnotes'
			else:
				report['style'] = 'Endnotes'
		else:
			report['style'] = 'Inline'
			
		if self.layoutColumnOne:
			report['format'] = 'One Column'
		else:
			report['format'] = 'Two Columns'

		print json.dumps(report)
		
		
		#------------------------------------------------------------------Bach output mode-------------------------------------------------------
		bachMode = False
		
		
		
		if (mode == "batch"):
			bachMode = True
			bachModeOutputFile = sys.argv[1] + '.txt'
		
		
		
		
		
		
		filename = filename.split("/")[len(filename.split("/"))-1]
		
		if (bachMode):
			
			bachReport = []
			
			citCount = {}
			
			#build a lookup of all the citations count
			
			if self.citationTypeNote:
				for x in report['data']:
					if 'authors' in report['data'][x]:
						for aAuthor in report['data'][x]['authors']:
							if aAuthor[1] in citCount:
								citCount[aAuthor[1]] = citCount[aAuthor[1]] + 1
							else:
								citCount[aAuthor[1]] = 1
							
				
			
			
			#if inline we want a differnt type of author lookup and cit lookup
			if self.citationTypeInline:
				
				
				for x in report['data']:
					if report['data'][x]['note'] in citCount:
						citCount[report['data'][x]['note']] = citCount[report['data'][x]['note']] + 1
					else:
						citCount[report['data'][x]['note']] = 1				
		
				
				#-------
				
				
				
				
				
				oldAuthorLookup = report['authors']
				report['authors'] = {}
				
				#loop through and build a compiled list of authors per entry
				for x in report['data']:
					if 'authors' in report['data'][x]:
						
						authors = ""
						#Todo? Add in counts for single authors occuring among other multi author publications?
						for y in report['data'][x]['authors']:
							
							authors = authors + " & " + y
							
						
						authors = authors.strip()[1:].strip()
						
						if authors in report['authors']:
							report['authors'][authors] = report['authors'][authors] + 1
						else:
							report['authors'][authors] = 1
						
						
			
			for x in report['data']:
				
				
				
				#print report['data'][x]
				#print "\n"
				
				#first see if this citation has it for any other 
				
				#it has to have citation data to add it
				if 'authors' in report['data'][x]:
					
					if self.citationTypeInline:
						
						aItem = {}
						
						aItem['citation'] = report['data'][x]['note']
						aItem['page'] = 'n/a'
						aItem['noteId'] = "n/a" 
						aItem['context'] = report['data'][x]['body']
						aItem['note'] = "n/a"
						
						aItem['docLen'] = report['docLen']
						
						aItem['posRaw'] =  report['data'][x]['pos']						
						aItem['posRel'] =  report['data'][x]['pos'] / report['docLen'] * 100
					
						aItem['doc'] = filename 		
						
						aItem['citFreqRaw'] = citCount[aItem['citation']] 
						
						authors = ""
						
						if self.quirksModePMLA:
							
							
							authors = report['data'][x]['authors']
							
							
						else:
						
						
							for aAuthor in report['data'][x]['authors']:
								authors = authors + " & " + aAuthor
							
							authors = authors.strip()[1:].strip()		
							
						if authors in report['authors']:
							aItem['authorFreqRaw'] = report['authors'][authors]
						else:
							aItem['authorFreqRaw'] = 0						
							
						aItem['citFreqRaw'] = citCount[aItem['citation']]
						
						
						aItem['author'] = authors
						
						aItem['polarity'] = aClassify.judge(aItem['context'])
						
						
						bachReport.append(aItem)
						
						
						
								
					if self.citationTypeNote:
					
						
						#there are multiple citations per note in foot/end notes
						for aAuthor in report['data'][x]['authors']:
						
							aItem = {}
							
							
							aItem['context'] = report['data'][x]['body']
						
						
							aItem['note'] = report['data'][x]['note']
							aItem['author'] = aAuthor[0]
							aItem['citation'] = aAuthor[1]							
							aItem['page'] =  report['data'][x]['page']
								
							
							if 'id' in report['data'][x]:
								aItem['noteId'] = report['data'][x]['id']
							else:
								aItem['noteId'] = "n/a" 
								
							
							
							#if self.isFootNote:	
							aItem['polarity'] = aClassify.judge(aItem['context'] + aItem['note'])
							#else:
							#	aItem['polarity'] = aClassify.judge(aItem['note'])
							
							aItem['docLen'] = report['docLen']
							
							aItem['posRaw'] =  report['data'][x]['pos']						
							aItem['posRel'] =  report['data'][x]['pos'] / report['docLen'] * 100
						
							aItem['doc'] = filename 
							
							
						
							if aItem['author'] in report['authors']:
								aItem['authorFreqRaw'] = report['authors'][aItem['author']]
							else:
								aItem['authorFreqRaw'] = 0
						
							
						
							
							aItem['citFreqRaw'] = citCount[aItem['citation']] 
				  
						
						
							bachReport.append(aItem)
						
						
						#print aItem
			
			
			
			
			
			for x in bachReport:
				
				
				#print x
				
				#print report['data'][x]
				citPos = []
				autPos = []
				citPolPos = []
				autPolPos = []
				citPolNeg = []
				autPolNeg = []	
				
							
				#loop through and gather some stats for similar citations
				for y in bachReport:
					
					#same cit?
					if x['citation'] == y['citation']:
						
						citPos.append(y['posRel'])
						citPolPos.append(y['polarity']['positive'])
						citPolNeg.append(y['polarity']['negative'])
					
					#same Author?
					if x['author'] == y['author']:
						
						
						autPos.append(y['posRel'])
						autPolPos.append(y['polarity']['positive'])
						autPolNeg.append(y['polarity']['negative'])		
					
		
		
				citMean = 0
				citMedian = 0
				citMode = 0
				citRounded = []
				authMean = 0
				authMedian = 0
				authMode = 0
				authRounded = []
				
				for y in citPos:
					citMean = citMean + y
					citRounded.append(int(10 * round(float(y)/10)))
					
					
				
				citMean = citMean / len(citPos)
				citMedian = median(citPos)
				data = Counter(citRounded)
				citMode = data.most_common(1)[0][0]
				
				x['citPosMean'] = citMean
				x['citPosMedian'] = citMedian
				x['citPosMode'] = citMode
				
				
				
				
				for y in autPos:
					authMean = authMean + y
					authRounded.append(int(10 * round(float(y)/10)))
					
					
				
				authMean = authMean / len(autPos)
				authMedian = median(autPos)
				data = Counter(authRounded)
				authMode = data.most_common(1)[0][0]
				
				x['authPosMean'] = authMean
				x['authPosMedian'] = authMedian
				x['authPosMode'] = authMode
				
				
				
				
				#avg out the polarity for the cit and author
				
				citPositive = 0
				citNegative = 0
				for y in citPolPos:
					citPositive = citPositive + float(y)
				for y in citPolNeg:
					citNegative = citNegative + float(y)				
				
				x['citPolarityPositiveMean'] = citPositive / len(citPolPos)
				x['citPolarityNegativeMean'] = citNegative / len(citPolNeg)


				autPositive = 0
				autNegative = 0
				for y in autPolPos:
					autPositive = autPositive + float(y)
				for y in autPolNeg:
					autNegative = autNegative + float(y)
				
				x['authPolarityPositiveMean'] = autPositive / len(autPolPos)
				x['authPolarityNegativeMean'] = autNegative / len(autPolNeg)
				
									
				"""
				if len(autPolPos) > 1:
					print autPolPos
					print autPositive / len(autPolPos)

					print "-----"
					
					print autPolNeg
					print autNegative / len(citPolNeg)					
					
					sys.exit()
				"""

			
				
				
				
				
				
				
			
			f = open(bachModeOutputFile, "ab")
			
			#prepare the text for fileoutput csv-ish and putput
			for x in bachReport:
				
				for y in x:
					
					
					# we are using this a dilimiter
					try:
						x[y] = x[y].replace("`","")
										
						x[y] = x[y].replace('-\n', '')
						x[y] = x[y].replace('\n', ' ')
						x[y] = re.sub("\s+", " ", x[y])
						x[y] = x[y].strip()						
						
					except:
						x[y] = x[y]
						
					
				line = ""
				
				line = line + str(x['doc']) + '`'							#The file name 
				line = line + str(x['author']) + '`'						#author(s) on this biiblographic citation
				line = line + str(x['citFreqRaw']) + '`'					#How many times this specific  biiblographic citation was used in the whole document
				line = line + str(x['authorFreqRaw']) + '`'					#How many times this author was cited in the whole document
				line = line + str(x['docLen']) + '`'						#The length (chars or sentences) of the whole document
				line = line + str(x['page']) + '`'							#page number of this specifc citation, if available
				line = line + str(x['noteId']) + '`'						#the citation foot/note number of this specifc citation, if available
				line = line + str(x['posRaw']) + '`'						#The specific location of this instance of the bliblographic citation reference in the document
				line = line + str(x['posRel']) + '`'						#The Relative posititon of this specific bliblographic citation in relation to the whole document, a percentage
				line = line + str(x['citPosMean']) + '`'					#The Mean of of all occurances of this citation in relation the whole document, a percentage 
				line = line + str(x['citPosMedian']) + '`'					#The Median of of all occurances of this citation in relation the whole document, a percentage
				line = line + str(x['citPosMode']) + '`'					#The Mode of of all occurances of this citation (rounded to nearest 10th) in relation the whole document, a percentage 
				line = line + str(x['authPosMean']) + '`'					#The Mean of the location of all of this authors citations in relation to the document, a percentage
				line = line + str(x['authPosMedian']) + '`'					#The Median of the location of all of this authors citations in relation to the document, a percentage
				line = line + str(x['authPosMode']) + '`'					#The Mode of the location of all of this authors citations (rounded to nearest 10th) in relation to the document, a percentage 
				line = line + str(x['polarity']['results']) + '`'			#The classification of this specific citation, postitive or negative
				line = line + str(x['polarity']['positive']) + '`'			#The decimal postive value for the polarity of this specific citation (pos+neg=1.0)
				line = line + str(x['polarity']['negative']) + '`'			#The decimal negative value for the polarity of this specific citation (pos+neg=1.0)
				line = line + str(x['citPolarityPositiveMean']) + '`'		#The mean avg of the postive polarity of all the occurances of this citation in the document (pos+neg=1.0)
				line = line + str(x['citPolarityNegativeMean']) + '`'		#The mean avg of the negative polarity of all the occurances of this citation in the document (pos+neg=1.0)
				line = line + str(x['authPolarityPositiveMean']) + '`'		#The mean avg of the postive polarity of all the citations by this author in the document (pos+neg=1.0)
				line = line + str(x['authPolarityNegativeMean']) + '`'		#The mean avg of the negative polarity of all the citations by this author in the document (pos+neg=1.0)
				line = line + str(x['citation']) + '`'						#the bibilographic citation text
				line = line + str(x['note']) + '`'							#The note text (that includes biblographic citations) foot/end note only
				line = line + str(x['context'])								#the context of the note text
				#print line
				
				#we only want to show citations when we know hwere they are
				if x['posRaw'] != 0:
					f.write(line + "\n")
				

		#print aClassify	
		#print self.fontSizes
		#print self.fontSizeBody, self.fontSizeFoot 		


	def storeLayouts(self):		 
		self.layouts = []
		for page in self.pages:	
			self.interpreter.process_page(page)
			self.layouts.append(self.device.get_result())

	def storeFontSizes(self):
		
		fontSizes = {}
		  
		for layout in self.layouts:
			for lt_obj in layout:
				if lt_obj.__class__.__name__ == 'LTTextBoxHorizontal':
					for textLine in lt_obj:
						for textChar in textLine:				
							if textChar.__class__.__name__  == 'LTChar':	
								
								#if textChar.fontsize == 1:
								#	fontsize = round(textChar.size)
								#else:
								#	fontsize = textChar.fontsize	
									
								fontsize = round(textChar.size)

									
								if fontSizes.has_key(fontsize):
									fontSizes[fontsize] = fontSizes[fontsize] + 1
								else:
									fontSizes[fontsize] = 1
		
		self.fontSizes = fontSizes
				
		#get the top two font sizes
		fontSizesSorted = sorted(self.fontSizes.iteritems(), key=operator.itemgetter(1))
		#remove the rest
		del fontSizesSorted[0:len(fontSizesSorted)-2]

		if fontSizesSorted[0][0] > fontSizesSorted[1][0]:
			self.fontSizeBody = fontSizesSorted[0][0]
			self.fontSizeFoot = fontSizesSorted[1][0]
		else:
			self.fontSizeBody = fontSizesSorted[1][0]
			self.fontSizeFoot = fontSizesSorted[0][0]

			
		total = 0	
		for x in fontSizes:		
			total = total + fontSizes[x]
		
		self.fontDetectionError = False

		#if there is a font that is 98% (can be refined) of the text, then something went wrong or there are no footnotes, 
		#so just store all the text into on blob
		for x in fontSizes:		
			#print fontSizes[x], ":", fontSizes[x] / total * 100
			if fontSizes[x] / total * 100 >= 98:
				self.fontDetectionError = True
			
	def cleanSentence(self,sentence):		
		sentence = re.sub("\s\s+" , " ", sentence)		
		return sentence
		
	def roundUpToTens(self,x):
		return int(math.ceil(x / 10.0)) * 10

 
	def mean(self,numberList):
		if len(numberList) == 0:
			return float('nan')	 
		floatNums = [float(x) for x in numberList]
		return sum(floatNums) / len(numberList)

	def returnNextLine(self,lines,line):
	
		nextLine = False
		#returns the next possible line out of a dict of line posixfile
		for searchLine in  sorted(lines.iterkeys(),reverse=True):
			
			if nextLine:
				return searchLine
			
			
			if searchLine == line:
				nextLine = True
				continue
			
			
		return False

	def returnPrevLine(self,lines,line):
	
		nextLine = False
		#returns the next possible line out of a dict of line posixfile
		for searchLine in  sorted(lines.iterkeys(),reverse=False):
			
			if nextLine:
				return searchLine
			
			
			if searchLine == line:
				nextLine = True
				continue
			
			
		return False
		
		
	def extractNotes(self):
		
		
		footNoteLength = 0
		footNoteBodyLength = 0
		#first figure out if we have foot notes or end notes
		for x in self.pagesText[0:len(self.pagesText)-3]:
			footNoteLength = footNoteLength + len(x['footText'])
			footNoteBodyLength = footNoteBodyLength + len(x['bodyText'])

		endNoteLength = 0
		endNoteBodyLength = 0
		for x in self.pagesText[len(self.pagesText)-3:]:
			endNoteLength = endNoteLength + len(x['footText'])			
			endNoteBodyLength = endNoteBodyLength + len(x['bodyText'])
		
		
		
		
		self.isFootNote = False
		self.isEndNote = False

		if footNoteLength > endNoteLength and footNoteBodyLength > endNoteBodyLength:
			self.isFootNote = True
		else:
			self.isEndNote = True



		artBulletinLikeEndNotes = re.compile(r'(\n[0-9]{1}\.\s+[A-Za-z0-9"].*\n|\n[0-9]{2}\.\s+[A-Za-z0-9"].*\n|\n[0-9]{3}\.\s+[A-Za-z0-9"].*\n)')
		
		

		#this kind of works, but lets just do some double checks, things can vary so much
		#does the last page have endnotes?
		if (self.isFootNote):
			if (artBulletinLikeEndNotes.search(self.pagesText[len(self.pagesText)-1]['footText'])) or (artBulletinLikeEndNotes.search(self.pagesText[len(self.pagesText)-2]['footText'])):
				
				#count them
				endCount = len(artBulletinLikeEndNotes.findall(self.pagesText[len(self.pagesText)-1]['footText'])) + len(artBulletinLikeEndNotes.findall(self.pagesText[len(self.pagesText)-2]['footText']))
				
				if endCount >= 4:
					self.isFootNote = False
					self.isEndNote = True
				


		splitOnNumber = re.compile('(\n[0-9]{3}|\n[0-9]{2}|\n[0-9]{1})')
		splitOnNumberWithPeriod = re.compile('(\n[0-9]{3}\.|\n[0-9]{2}\.|\n[0-9]{1}\.)')
		
		self.notesWeb = {}
		self.bodyNoteSentences = {}
		self.bodyNoteSentencesLocation = {}
		self.bodyNotePageNumber = {}
		self.bodyTextLength = 0

		if self.isFootNote:
		
			self.footNotes = {}
			
			
			for idx, val in enumerate(self.pagesText):
				
				#foot notes are expected on that page from the body text?
				

				#
				body = val['bodyText'].encode("ascii","ignore")
				foot = val['footText'].encode("ascii","ignore")
				
				body = self.removePeriods(body)
				
				
				allNotes =  self.regexNoteInBody.findall(body)
				
		
				
				#print allNotes
				
				footSplit = splitOnNumber.split(foot)
				
				#print footSplit
				
				footLoc = {}
				
				for aNote in allNotes:
					
					 
					
					bodyText = body.split(aNote)
					bodyText = bodyText[0][::-1]					
					bodyText = bodyText[0:bodyText.find('.')]
					bodyText = bodyText[::-1]
					bodyText = bodyText + aNote
					


					aNote = aNote[1:]
					aNote = aNote.replace('.','').replace('"','').replace('?','').replace(',','').replace(')','')
					
					
					self.bodyNoteSentencesLocation[int(aNote)] = self.bodyTextLength + body.find(bodyText)
					self.bodyNotePageNumber[int(aNote)] = idx + 1
					
					
					self.bodyNoteSentences[int(aNote)] = bodyText
						
						
					#see if we can find this note in the foottext
					
					
					for aryPos, footId in enumerate(footSplit):
						if footId.strip() == aNote:
							footLoc[footId.strip()] = aryPos
							
				
				footLocAry = []
				for x in sorted(footLoc.iteritems(), key=operator.itemgetter(1)):					
					footLocAry.append([x[0],x[1]])
					
					
				
				firstIndex = 1000
				firstPageNote = 1000
				for x in range(0, len(footLocAry)):
					
					if footLocAry[x][1] < firstIndex:
						firstIndex = footLocAry[x][1]
					
					
					if x+1 in range(0, len(footLocAry)):						
						thisNoteAry = footSplit[footLocAry[x][1]:footLocAry[x+1][1]]
					else:
						thisNoteAry = footSplit[footLocAry[x][1]:]
					
					thisNoteText = ''.join(thisNoteAry)
					self.footNotes[int(footLocAry[x][0])] = thisNoteText
					
					if int(footLocAry[x][0]) < firstPageNote:
						firstPageNote = int(footLocAry[x][0])
					
					#print footLocAry[x][0], thisNoteAry
					#print "firstIndex",firstIndex
				
				
				#now check our work
				for aNote in allNotes:
					aNote = aNote[1:]
					aNote = int(aNote.replace('.','').replace('"','').replace('?','').replace(',','').replace(')',''))
					if self.footNotes.has_key(aNote) is False:
 						
						#look to see if a previous footnot exists, and if it does look through it for this one
						if self.footNotes.has_key(aNote-1):
							
							#print "looking in:", self.footNotes[aNote-1]							
							if self.footNotes[aNote-1].find(' ' + str(aNote) + ' ') != -1:								
								#print "It looks like its in here: " + self.footNotes[aNote-1]
								self.footNotes[aNote] = str(aNote-1) + ' ' + self.footNotes[aNote-1].split(' ' + str(aNote) + ' ')[0]
								self.footNotes[aNote-1] = str(aNote-1) + ' ' + self.footNotes[aNote-1].split(' ' + str(aNote) + ' ')[1]
								

				#was the first note we processed the start of the array? meaning was it the first bit of text
				firstIndexText = ''
				if firstIndex > 0:
					firstIndexText = ''.join(footSplit[0:firstIndex])
					
				#nope there was some leftovers, tag it onto the previous note if it exitst
				if firstIndexText.strip()!='':				
					if self.footNotes.has_key(firstPageNote-1):
						self.footNotes[firstPageNote-1] = self.footNotes[firstPageNote-1] + firstIndexText
					#else:
					#	print "NOTE NUMBER ", firstPageNote-1, " DOES NOT EXIST!"
						
						
			#for x in self.footNotes:
			#	print x," => " , self.footNotes[x]				
			
				#we are storing the lenfth of the body text to figure out where the citation occured in the document
				self.bodyTextLength = self.bodyTextLength + len(body)
			
			for x in self.bodyNoteSentences: 
				if self.footNotes.has_key(x):
					self.notesWeb[x] = {'id' : x, 'body' : self.bodyNoteSentences[x] , 'note' : self.footNotes[x], 'pos' : self.bodyNoteSentencesLocation[x], 'page' : self.bodyNotePageNumber[x]}
				else:
					self.notesWeb[x] = {'id' : x, 'body' : self.bodyNoteSentences[x] , 'note' : 'No note could be found', 'pos' : self.bodyNoteSentencesLocation[x], 'page' : self.bodyNotePageNumber[x]}
		 
				
		if self.isEndNote:
		
			self.endNotesFound = 0
			self.endNotesTotal = 0

			hasNumerThenDotThenChar = re.compile(r'(^[0-9]{1}\.\s+[A-Za-z0-9"]|^[0-9]{2}\.\s+[A-Za-z0-9"]|^[0-9]{3}\.\s+[A-Za-z0-9"])')

			
		
			self.endNotes = {}
			
			
			noteNumber = 0
			
			notesStartOnPage = 1000
			
			#TODO line continues over the page
			for idx, val in enumerate(self.pagesText):
				
				
				
				
				foot = val['footText'].encode("ascii","ignore")
				
				
				
				
				s = artBulletinLikeEndNotes.search(foot)
				
				if s:
					
					#all = artBulletinLikeEndNotes.findall(foot)
					
					if idx < notesStartOnPage:
						notesStartOnPage = idx
					
					for aLine in foot.split("\n"):
						
						#does it start with a number and dot?
						
						if hasNumerThenDotThenChar.search(aLine.strip()):
							
							if len(aLine) > 5:
								
								
								
								noteNumber = hasNumerThenDotThenChar.search(aLine.strip()).groups()[0]
								noteNumber = noteNumber[0:noteNumber.find('.')]
								
								#print "\n",noteNumber,"\n"
								
								if noteNumber.isdigit():
									
									
									
									#if (int(noteNumber) > 1):
									#	print noteNumber
										#print "Last Note:", noteNumber, "\n", self.endNotes[int(noteNumber)-1]
										
										
									self.endNotes[int(noteNumber)] = aLine + " "
									
								
								#
						else:
							
							#not yet into the note?
							if (noteNumber != 0):
							
								self.endNotes[int(noteNumber)] = self.endNotes[int(noteNumber)] + aLine + " "
							
					
						
						
						
			#			
					
			
			for key, value in self.endNotes.iteritems():
				
				#print "\n----",key,"----\n"
				#print value
				
				value = value.replace("-\n",'')
				
				self.notesWeb[key] = {'id' : key, 'body' : "" , 'note' : value, 'pos' : 0, 'page' : 0}

				
				
			
			returnNumbersOnly = re.compile(r'(\d+)')
			
			#now look through each page for the occurance in the body
			
			allBody = ""
			for idx, val in enumerate(self.pagesText):
							


				body = val['bodyText'].encode("ascii","ignore")
 				foot = val['footText'].encode("ascii","ignore")
 				
 				
 				bodyFromated = self.removePeriods(body)
 				footFromated = self.removePeriods(foot)
 				
 				
 				allNotes =  self.regexNoteInBody.findall(body)	
 				
				allBody = allBody + bodyFromated
				
				#if this is not the end notes page then also check the foot text, doesnt hurt
				if (idx < notesStartOnPage):
					allNotes =  allNotes + self.regexNoteInBody.findall(foot)	
					allBody = allBody + footFromated
					 

				allBody = allBody.replace("-\n","")
				allBody = allBody.replace("\n"," ") 	
							
 				for aNote in allNotes:
 					
 					#print "------------"
 					#print aNote
 					#print "------------"
 	 				
 	 				
 	 				#is this a real note?
 	 				
 	 				
 	 				noteNumber = returnNumbersOnly.search(aNote).groups()[0]
 	 				#if it is not yet in our notes
 	 				if int(noteNumber) in self.notesWeb:
 	 					
 	 					#if its not yet found
 	 					if self.notesWeb[int(noteNumber)]['body'] == "":
 	 					
 	 					
 	 					 	if (body.find(aNote) == -1):
  	 					 		useText = footFromated
  	 					 	else:
  	 					 		useText = bodyFromated
 	 						
 	 						#figure out the body sentence
 				 			bodyText = useText.split(aNote)
							bodyText = bodyText[0][::-1]					
							bodyText = bodyText[0:bodyText.find('.')]
							bodyText = bodyText[::-1]
							bodyText = bodyText + aNote
							bodyText = bodyText.replace("-\n","")
							bodyText = bodyText.replace("\n"," ")
							self.notesWeb[int(noteNumber)]['body'] = bodyText
							
							try:
								self.notesWeb[int(noteNumber)]['pos'] = allBody.find(bodyText)
							except:
								self.notesWeb[int(noteNumber)]['pos'] = 0 
							
							self.notesWeb[int(noteNumber)]['page'] = idx
							#print bodyText
							#print allBody.find(bodyText)
 				 	
 	
 		 	
 		 	for aWeb in self.notesWeb:
 		 		
 		 		if self.notesWeb[aWeb]['body'] == "":
 		 			self.notesWeb[aWeb]['body'] = "Context could not be found"
 		 		
	 	self.bodyTextLength = len(allBody)

 	 		 	
			
		
	def checkForInlineCitation(self):
		
		#look for occurances of author/date in the text
		bibExtract = re.compile('([a-z|\s|-]*),.*?([[0-9]{4}|[0-9]{4}a|[0-9]{4}b|[0-9]{4}c])')

		authorDates = []

		for x in self.bib:
			r = bibExtract.search(x.decode('utf-8').encode("ascii","ignore").lower())
			if r:
				
				print x.decode('utf-8').encode("ascii","ignore").lower()
				print r.groups()
				authorDates.append(r.groups())
				
				#print "--------"
	 
		 
		sys.exit()
		
					
	def extractBib(self):
		#look for the first bib format: "\nName*,*[year]
		self.regexBibEntry = re.compile('(\n[A-Z][a-z]*.*,.*[0-9]{4}\.)|(\n[A-Z][a-z]*.*,.*\([0-9]{4}\)\.)|(\n[A-Z][a-z]*.*,.*\(\s[0-9]{4}\s\)\s\.)|(\n[A-Z].*Team.*\([0-9]{4}\)\.)|(\n[A-Z][a-z]*.*,.*\([0-9]{4}\),)')
 
		bibText = ''
		
		firstPageOfBib = -1
		
		self.bibCitations = {}
		
		for x in range(len(self.pagesText)-1,0,-1):		
			
			#print "Does this page have bib refs?\n-----------------------------------\n", self.pagesText[x]['bodyText'], "\n-------------------------"
			
			results = self.regexBibEntry.findall(self.pagesText[x]['bodyText'])			
			
			if len(results) == 0 and bibText == '':
				continue
			
			
			if len(results) == 0:
				#print "----no----"
				break
				
				
			firstPageOfBib = x	
			
			bibText = self.pagesText[x]['bodyText'] + bibText
			#print "----Yes----"
				
		
		#no bib was found, try the foot text
		#print "error"
		if bibText == '':					
			for x in range(len(self.pagesText)-1,0,-1):		
				
				#print "Does this page have bib refs?\n-----------------------------------\n", self.pagesText[x]['footText'].encode("ascii","ignore"), "\n-------------------------"
				
				results = self.regexBibEntry.findall(self.pagesText[x]['footText'])			
				
				#print "Results:",results
				
				if len(results) == 0 and bibText == '':
					continue
				
				
				if len(results) == 0:
					#print "----no----"
					break
					
					
				firstPageOfBib = x	
				
				bibText = self.pagesText[x]['footText'] + bibText
				#print "----Yes----"			


		
			
		splitBib = self.regexBibEntry.split(bibText)
		#remove any text before the first reference
		del splitBib[0]
		

		
		#print self.regexBibEntry.split(bibText)
		aCit = ''
		allCits = []
		self.bib = []
		for x in splitBib:
		
			if x:
				if len(self.regexBibEntry.findall(x)) != 0:
					#print "New cit : ", x
					if aCit != '':
						allCits.append(aCit)
						aCit = ''
					aCit = x	
				else:
					aCit = aCit + x
				
				
		for x in allCits:
			
			x = x.replace('-\n','')
			x = x.replace('\n',' ')
			x = x.encode('utf8')
			x = x.strip()
			
			self.bib.append(x) 	
	
	
		#if there are any really short ones it is likely a mistake, put it with the cit before
		for idx, val in enumerate(self.bib):
			if len(val) < 30:	
				if idx != 0:
					self.bib[idx-1] = self.bib[idx-1] + ' ' + self.bib[idx]
					del self.bib[idx]
    		
		
		
		if self.quirksModePMLA:
			
			self.bib = []
			self.worksCited = []
			
			
			pmlaBib = re.compile('\sPrint\.')
			pmlaBibAuthor = re.compile('(^[A-Z].*?),')
			
			#for PMLA its stored in the foot text, jus tgotta find the page
			bibRaw = ""
			foundStart = False
			for idx, val in enumerate(self.pagesText):
				
				
				foot = val['footText'].encode("ascii","ignore")
				
				
				
				
				s = pmlaBib.search(foot)
				
				if s:		
		
					#print foot
					#can we find workds cited text
					if foot.lower().find("works cited") != -1 and foundStart == False:
						foot = foot[foot.lower().find("works cited"):]
						bibRaw = bibRaw + foot
						foundStart = True
					
					if foot.lower().find("works cited") == -1 and foundStart == False:
						foot = foot[foot.lower().find("print."):]
						bibRaw = bibRaw + foot
						foundStart = True
						
					elif foundStart == True:
						
						bibRaw = bibRaw + foot
					
			bibRaw = bibRaw.replace("Works Cited","")
			bibRaw = bibRaw.replace("WORKS CITED","")
			
			#print bibRaw
			
			
			lastAuthor = "error"		
			for x in  pmlaBib.split(bibRaw):
				
			
				
				aCit = x
				aCit = re.sub("\s\s+" , " ", aCit)	
				aCit = aCit.replace("-\n","")
				aCit = aCit.replace("\n","")
				aCit = aCit.replace(" . ",". ")
				aCit = aCit.replace(" , ",", ")
				aCit = aCit.strip()
				
				if aCit == "":
					continue
				
				author = ""
				title = ""
				
				
				#see if its foramted the way we think
				if pmlaBibAuthor.search(aCit.replace(" ","")):
					
					author = aCit.replace(" ","").split(",")[0]
					

				#the ibid char (at least in these docs)
				elif aCit[0] == '.':
					
					author = lastAuthor
					
				else:
					
					author = "error"
				
				try:
					title = aCit.split(".")[1]
				except:
					title = "Unkown Title"
				
				self.bib.append(aCit) 
				
				#print aCit,"\n\n"
				#print author
				
				
				if author != "error" and len(author) < 20:
					self.worksCited.append({ "author" : author, "title" : title, "cit" : aCit })
				
				lastAuthor = author
				
				#
					 
		
	
	
	def analyzeNotes(self):
		
		
		self.authorDirectory = []
		self.authorNoteIndex = {}
		self.webAuthorCount = {}
		self.badNotes = []
		
		previousUse = ""
		previousPossibleAuthors = ""

		hasParaCite = re.compile('([0-9]{4}\))')
		
 		
 
 		singleAuthorInKeyword = re.compile(r'\sin\s([A-Z][a-z]*?\s[A-Z][a-z]*)(,\s.*?\(.*?[0-9]{4}\))')
 		singleAuthorByInKeywork = re.compile(r'\sby\s([A-Z][a-z]*?\s[A-Z][a-z]*)(\sin\s.*?\(.*?[0-9]{4}\))')
 		
 		
 		singleAuthorInitials = re.compile(r'((([A-Z]\.\s[A-Z]\.\s|[A-Z]\.\s[A-Z]\.\s[A-Z]\.\s)([A-Z][a-z]*?)),.*?\(.*?[0-9]{4}\))')
 		#For example: G. E. M. Anscombe, Authority in Morals, in The Collected Philosophical Papers of G. E. M. Anscombe Volume III: Ethics, Religion, and Politics (Oxford: Blackwell, 1981)

		singleAuthorLastNameOnly = re.compile(r'\.\s(([A-Z][a-z]*?),\s[A-Z].*?\(.*?,\s[0-9]{4}\))')
		#for example: "...I do not react by asking for his credentials but for his reasons. Coady, Testimony (New York: Oxford, 1994)"

		singleAuthorOpCit = re.compile(r'([A-Z][a-z]*),\sop\.\scit')
		#such as: expressivism, see Scruton, op. cit. 


		singleAuthorSemiAndCit = re.compile(r';\s*(([A-Z][a-z]*\s([A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		#such as: 8 Harms, op. cit.; Brian Skyrms, Evolution of the Social Contract (New York: Cambridge, 1996)
		#must look at aNote not z
		
		singleAuthorSameAuthorAsPrevious = re.compile(r'^,\sand\s(.*?\(.*?[0-9]\))')
		#such as: , and Signals: Evolution, Learning and Information (New York: Oxford, 2010) 
		
		
		singleAuthorKnownAuthor = re.compile(r'[0-9]*?\s([A-Z][a-z]*)(,.*?\(.*?[0-9]{4}\))')
		#such as: 17 Skyrms, Signals, and Evolution of Signaling Systems with Multiple Senders and Receivers, Philosophical Transactions of the Royal Society of London B, ccclxiv (2009) 
		#but will check author to see if it already have it


		singleAuthorVaugeSee = re.compile(r'\s(See|see)\s([A-Z][a-z]*),')
		#such as: 13 see Skyrms, Signals. 
		#checks agains author list

		singleAuthorFullNameAndNumber = re.compile(r'^[0-9]*?\s(([A-Z][a-z]*\s([A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		#such as : 1 Brian Skyrms, Sex and Justice, this journal, xci, 6 ( June 1994) 


		singleAuthorHyphenSurname = re.compile(r'(([A-Z][a-z]*\s([A-Z][a-z]*\-[A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		#such as: 15 Maurice Merleau-Ponty, Phnomnologie de la perception (Paris: Gallimard, 1945) 


		singleAuthorVaugeIn = re.compile(r'\s(([A-Z][a-z]*\s([A-Z][a-z]*))\sin\s[A-Z][a-z]*.*?.*?\(.*?[0-9]{4}\))')
		#such as:  1 This view has been defended by, among others, Susan Hurley in Consciousness in Action (Cambridge: Harvard, 1998) 
		#not stable


		singleAuthorEtAl = re.compile(r'(([A-Z][a-z]+\s.*?)\set\sal.*?\(.*?[0-9]{4}\))')
		#such as: a description of KE and JO, see Helen A. Anema et al., A Double Dissociation between Somatosensory Processing for Perception and Action, Neuropsychologia, xlvii, 6 (May 2009) 
		
		
		removeSemiMultiDate = re.compile(r'\(([0-9]{4};).*?[0-9]{4}\)')
		#such as: Theodor Adorno, Can One Live after Auschwitz! (1962; Stanford: Stan ford University Press, 2003)
		#the semi-colin cauess problems
		
		
		singleAuthorFullNameAndNumberDot = re.compile(r'^[0-9]*?\.\s(([A-Z][a-z]*\s([A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		
		
		singleAuthorHyphenFirstName = re.compile(r'(([A-Z][a-z]*\-[A-Z][a-z]*\s([A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		#such as The plea for little narratives is made in Jean-Francois Lyotard, The Post modern Condition: A Report on Knowledge, trans. Geoffrey Bennington and Brian Massumi (Minneapolis: University of Minnesota Press, 1984)
		#gotta watch out for my dude Lyotard
		
		singleAuthorTheDe = re.compile(r'(([A-Z][a-z]*\sde\s([A-Z][a-z]*)),.*?\(.*?[0-9]{4}\))')
		#such as: Roger de Piles, Cours de peinture par principes (Geneva: Slatkine Reprints, 1969) 
		
		
		singleAuthorWellFormated = re.compile(r'(([A-Z][a-z]*),\s".*?,".*?[0-9]{4}\))')
		#such as Mirimonde, "Les sujets musicaux chez Antoine Watteau," Gazette des Beaux-Arts 58 (1961) 
		
		

		singleAuthorPerfectLastName = re.compile(r'((^[A-Z][a-z]*),\s.*?\s\(.*?,\s[0-9]{4}\))')
		#such as : Lively, Masks: Blackness, Race & the Imagination (Oxford: Oxford University Press, 2000) 
		
		
		
		looksLikeChicagoRef = re.compile(r'(\d+.*?[A-Z][a-z]*,.*?,\s[0-9])|(\d+.*?[A-Z][a-z]*,.*?,"\s[0-9])')


		for x in self.notesWeb:
			
			
 			#print self.notesWeb[x]
			
			#remove the line breaks
			note = self.notesWeb[x]['note'].replace('-\n','')
			note = note.replace('\n',' ')
			note = note.replace(' , ',', ')
			note = note.replace('Cf.','')
			note = note.replace('cf.','')
			note = note.replace('Cf ','')
			note = note.replace('cf ','')
			
			
			note = note.replace('see, for example, ','see, ') 
			note = note.replace('See, for example, ','See, ') 
			
			
			note = note.replace('; and','; ') 
			
			#note = note.replace('','') 
			 
			
			#The pranthesis style in text note citation format
			r = hasParaCite.search(note)
			
			
			
			
			if r:

	
				#print note
				
				thisNoteAuthors = []
				
				#NER the text
				for sent in nltk.sent_tokenize(note):
					for chunk in nltk.ne_chunk(nltk.pos_tag(nltk.word_tokenize(sent))):
						if hasattr(chunk, 'node'):
							if chunk.node == "PERSON":
								author = ' '.join(c[0] for c in chunk.leaves())
								
								if len(author.split()) > 1 and len(author.split()) < 5:
									self.authorDirectory.append(author)
									thisNoteAuthors.append(author)
									
								
								#lookup if this name is a short version of a long name
								if len(author.split()) == 1:
									for aName in self.authorDirectory:
										if aName.find(author) != -1:
											thisNoteAuthors.append(author)
											#print author, 'looks like', aName
									
				
				
				
				noteSplit = hasParaCite.split(note)
				
				
				a = 0
				while a < len(noteSplit) -1:
				
					if a+1 > len(noteSplit) -1:
						break
				
					aNote = noteSplit[a] + noteSplit[a+1]
					a = a + 2
					
					
					#clean up
					
					if removeSemiMultiDate.search(aNote):
						
						aNote = aNote.replace(removeSemiMultiDate.search(aNote).groups()[0],"")
						
						
					aNote = aNote.replace("; paperback",", paperback")
					aNote = aNote.replace("University;",",University ")
					aNote = aNote.replace("Press;","Press")
					
					
						
					
					for z in re.split(';\s|\.\sSee\s|\.\sSee,|\.\sFor\s|\.\sFor,',aNote):
						
						#print "\t->!",z
						
						if len(z) > 10:
							
							possibleAuthors = {}
							
							for aAuthor in self.authorDirectory:
								
								if z.find(aAuthor + ',') != -1 or z.find(aAuthor + ' and') != -1:
									possibleAuthors[aAuthor] = z[z.find(aAuthor):]
								
								
								#else:
									
									#try the last name only
								#	lastName = aAuthor.split()[len(aAuthor.split())-1]
								#	print "YTIING LASTNAME ", lastName
								#	if z.find(lastName + ',') != -1 or z.find(lastName + ' and') != -1:
								#		possibleAuthors[aAuthor] = z[z.find(aAuthor):]
									
							
							for aAuthor in self.authorDirectory:
								lastName = aAuthor.split()[len(aAuthor.split())-1]
								if z.find(lastName + ',') != -1 or z.find(lastName + ' and') != -1:
									possibleAuthors[aAuthor] = z[z.find(lastName):]						
						
							
						
							longest = 0
							use = ''
							for aPossible in possibleAuthors:
								if len(possibleAuthors[aPossible]) > longest:
									use = aPossible	
									longest = len(possibleAuthors[aPossible])
	
							
							
							#print "\t-->possibleAuthors", possibleAuthors
							
							#fully formed citations will have more than 1 comma
							if use != '':
								if len(possibleAuthors[use].split(',')) < 4 and possibleAuthors[use].find(':') == -1:
									use = ''
							
							
							
							if use != '':
								
								#print "FOUND:", use, "|", possibleAuthors[use], "|", len(possibleAuthors[use].split(','))
								#TODO Multuple authors in same line
								use = use
																
							else:
							
						
								#into regex hell
								foundSingleAuth = False
								foundSingleAuthType = ""
								
								s = singleAuthorInKeyword.search(z)
							
								if s and not foundSingleAuth:
									
									#print "In keyword ", s.groups()[0], s.groups()[1] 
									use = s.groups()[0]
									possibleAuthors[use] = s.groups()[0] + s.groups()[1]
									foundSingleAuth = True 
									foundSingleAuthType = 'singleAuthorInKeyword'
		
							
								s  = singleAuthorByInKeywork.search(z)
							
								if s and not foundSingleAuth:
									
									#print "In BY keyword ", s.groups()[0], s.groups()[1] 
									
									use = s.groups()[0]
									possibleAuthors[use] = s.groups()[0] + s.groups()[1] 
									foundSingleAuth = True
									foundSingleAuthType = 'foundSingleAuth'
							
							
								
								
								s = singleAuthorInitials.search(z)
								
								if s and not foundSingleAuth:
									
									use = s.groups()[1]
									
									#chop off the first name intitals
									
									
									
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[3]):]
									
									foundSingleAuth = True
									
									foundSingleAuthType = 'singleAuthorInitials'
								
								
								
								
								
								
								s = singleAuthorLastNameOnly.search(z)
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									possibleAuthors[use] = s.groups()[0]
									
									foundSingleAuth = True
									foundSingleAuthType = 'singleAuthorLastNameOnly'
								
							
							
								s = singleAuthorOpCit.search(z)
								
								if s and not foundSingleAuth:								
									
									
									surname = s.groups()[0]
									
									
									#see if we can find it 
									for q in self.notesWeb:
										if 'authors' in self.notesWeb[q]:
											for p in self.notesWeb[q]['authors']:
												if p[0].find(surname) != -1:
													#print "this is op cit of :", p
													use = p[0]
													possibleAuthors[use] = p[1]
													foundSingleAuth = True
													foundSingleAuthType = 'singleAuthorOpCit'
									
																	
								s = singleAuthorSemiAndCit.search(aNote)
								
								if s and not foundSingleAuth:								
									use = s.groups()[1]
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorSemiAndCit'	
									
														
								
								
								
								
								
								
								
								s = singleAuthorFullNameAndNumberDot.search(z)
								
								if s and not foundSingleAuth:								
									
									
									
									use = s.groups()[1]
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									
									foundSingleAuth = True
									foundSingleAuthType = 'singleAuthorFullNameAndNumberDot'									
								
								
								
														
								s = singleAuthorSameAuthorAsPrevious.search(z)
								
								if s and not foundSingleAuth:								
									
									
									
									use = previousUse
									possibleAuthors[use] = s.groups()[0]
									
									

									foundSingleAuth = True
									foundSingleAuthType = 'singleAuthorSameAuthorAsPrevious'						
							
							
								s = singleAuthorKnownAuthor.search(z)
								
								if s and not foundSingleAuth:								
									
									
									#see if this author exists in the existing authors yet
									for q in self.notesWeb:
										if 'authors' in self.notesWeb[q]:
											for p in self.notesWeb[q]['authors']:
												if p[0].find(s.groups()[0]) != -1:
													
													#print "Full author: ", p[0]
													use = p[0]
													possibleAuthors[use] = s.groups()[0] + s.groups()[1]
													#print possibleAuthors[use] 
													foundSingleAuth = True	
													foundSingleAuthType = 'singleAuthorKnownAuthor'	
													break
												
																			
									
								s = singleAuthorVaugeSee.search(z)
								
								if s and not foundSingleAuth:								
									
									
 									
									
									#see if this author exists in the existing authors yet
									for q in self.notesWeb:
										if 'authors' in self.notesWeb[q]:
											for p in self.notesWeb[q]['authors']:
												if p[0].find(s.groups()[1]) != -1:
													
													#print "Full author: ", p[0]
													use = p[0]
													possibleAuthors[use] = p[1]
													#print possibleAuthors[use] 
													break
													
									
 									 

									foundSingleAuth = True	
									foundSingleAuthType = 'singleAuthorVaugeSee'			
									
									
															
								s = singleAuthorHyphenSurname.search(z.strip())
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorHyphenSurname'							


								s = singleAuthorVaugeIn.search(z)
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorVaugeIn'							


								s = singleAuthorHyphenFirstName.search(z)
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorHyphenFirstName'									
							
							
								s = singleAuthorTheDe.search(z)
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0][s.groups()[0].find(s.groups()[2]):]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorTheDe'									
								
								
								s = singleAuthorWellFormated.search(z)
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorWellFormated'	


								s = singleAuthorPerfectLastName.search(z)
								
								
								if s and not foundSingleAuth:								
									
									
									use = s.groups()[1]
									
									possibleAuthors[use] = s.groups()[0]
									
									
									foundSingleAuth = True		
									foundSingleAuthType = 'singleAuthorPerfectLastName'									

						



								s = singleAuthorEtAl.search(z)
								
								
								if s and not foundSingleAuth:								
									
									try:
										use = s.groups()[1]
										
										surname = s.groups()[1].split(" ")
										
										surname = surname[len(surname)-1]
										
										
										
										possibleAuthors[use] = s.groups()[0][s.groups()[0].find(surname):]
										
										
										foundSingleAuth = True		
										foundSingleAuthType = 'singleAuthorEtAl'	
									except:
										
										use = ""
								
								
								
								#Ibid, that occured in a citation with other citations such as:
								#6 Ibid., pp. 2228, 52; Devitt, Designation (New York: Columbia, 1981)
								if (z.lower().find("ibid") != -1 or z.lower().find("ibid.") != -1) and not foundSingleAuth:	
									
									#if we can find a note with the 1 less id then this is a ibid reference to that one
									for q in self.notesWeb:
										
										#print self.notesWeb[q]['id'], self.notesWeb[x]['id'], self.notesWeb[x]['id'] - 1
										
										if self.notesWeb[q]['id'] == self.notesWeb[x]['id'] - 1:
											#print "IBID of:", self.notesWeb[q]
											if 'authors' in self.notesWeb[q]:
												self.notesWeb[x]['authors'] = self.notesWeb[q]['authors']
											#else:
											#	print "\n\tIbid of no author found:", self.notesWeb[q]								


							
								#the chicago same author ref
								if len(z.split(",")) == 3:
									
									cit = z.split(",")
									
									if cit[0].find(" ") != -1:
										author = cit[0].strip().split(" ")
										author = author[len(author)-1]
									else:
										author = cit[0]
										
									
									ref = cit[1].replace('"',"").strip()
									
							
									#TODO: work titles into the guess
									
									for q in self.notesWeb:
										if 'authors' in self.notesWeb[q]:
											for p in self.notesWeb[q]['authors']:
												if p[1].find(author) != -1:
													#print "this is op cit of :", p
													use = p[0]					
													possibleAuthors[use] = p[1]
							
							
							

							
							#clean up the name if it looks wrong
							if (use.find('See ') != -1):
								
								newUse = use.replace('See ','')
								
								possibleAuthors[newUse] = possibleAuthors[use].replace('See ','')
								
								use = newUse
								
							#make sure the citation is not a pharagraph some how
							if use != '':
								if len(possibleAuthors[use]) >= 325:
									use = ""
						
									
							if use != '':
								
								
								if 'authors' in self.notesWeb[x]:
								    self.notesWeb[x]['authors'].append([use,possibleAuthors[use]])
								else:
								    self.notesWeb[x]['authors'] = [[use,possibleAuthors[use]]]
								
								
								    
								if use in self.webAuthorCount:
									self.webAuthorCount[use] += 1
								else:
									self.webAuthorCount[use] = 1
								
								previousUse = use
								previousPossibleAuthors = possibleAuthors[use]
								
								
							else:
								
								#print "\n\nCould not locate cite for this one:\n\n",z,"\n----------\n"
								#print "\t->",aNote
								
								previousUse = ""
								previousPossibleAuthors = ""
																
								self.badNotes.append(z)
								
								if 'authors' not in self.notesWeb[x]:
									self.notesWeb[x]['authors'] = []				
			
		
							
			else:
			
				if note.lower().find("op. cit.") != -1 or note.lower().find("op cit") != -1:
					
					note = note.replace('op. cit.','op cit')
					
					
					#try to locate this author....
					#split on the op cit
					surname = note.split("op cit")[0]
					#print surname
					#the last word of that split in the first item should be the author surname
					try:
						
					
						surname = surname.split(" ")
						surname = surname[len(surname)-2]
						surname = surname.replace(",",'').strip()
						
						
						#print surname.split(" ")[len(surname.split(" "))-1]
					
					except:
						
						surname = ''
					
					
					
					if surname != '':
						
						
						
						#loop through the existsing authors and see if this in in there
							for q in self.notesWeb:
								if 'authors' in self.notesWeb[q]:
									for p in self.notesWeb[q]['authors']:
										if p[0].find(surname) != -1:
											#print "this is op cit of :", p
											self.notesWeb[x]['authors'] = [p]
											
											
											
							#
							#	print p
								#if self.notesWeb[q]['authors'][p][0].find(surname) != -1:
							
								#	
						
						
						
						
					
			
			
			
				elif note.lower().find("ibid") != -1:
					
					
					#print self.notesWeb[x]
					unBrokenNotes = True
					lastNote = 0
					lastAuthor = ""
					
					#print note
					
					#if we can find a note with the 1 less id then this is a ibid reference to that one
					for q in self.notesWeb:
						
						#print self.notesWeb[q]['id']
						
						
						
						if lastNote + 1 == self.notesWeb[q]['id']:
							unBrokenNotes = True
							
							if 'authors' in self.notesWeb[q]:
								lastAuthor = self.notesWeb[q]['authors']
							
						else:
							unBrokenNotes = False
							
							
							
						#if unBrokenNotes:
						#	print "Unbroke", self.notesWeb[q]['id']
						
						if self.notesWeb[q]['id'] == self.notesWeb[x]['id'] - 1:
							#print "IBID of:", self.notesWeb[q]
							if 'authors' in self.notesWeb[q]:
								self.notesWeb[x]['authors'] = self.notesWeb[q]['authors']
							else:
								#print "\n\tIbid of no author found:", self.notesWeb[q]
								
								
								#the idea is that if they use ibid. that does not mean that the last note was acutally contains a citation
								#so if we have had unbroken chain of notes, the last one found it likely it
								
								if (unBrokenNotes):
									#print "Could be",lastAuthor
									self.notesWeb[x]['authors'] = lastAuthor
									
									
									
								
						lastNote = self.notesWeb[q]['id']
						
						
				elif looksLikeChicagoRef.search(note) or note.find(" See ") != -1:
					
					note = note.replace("See ", "")
					note = note.replace("see ", "")
					note = note.replace("See, for instance,", "")
					note = note.replace("Indeed,  ", "")
					note = note.replace("ndeed,  ", "")
					
					cit = note.split(",")
					
					if cit[0].find(" ") != -1:
						author = cit[0].strip().split(" ")
						author = author[len(author)-1]
					else:
						author = cit[0]
						
					try:
						ref = cit[1].replace('"',"").replace(",","").strip()
					except:
						ref = ""

					wentWith = ""
					authorCount = 0
			
					#TODO: work titles into the guess, kind of done below
					
					for q in self.notesWeb:
						if 'authors' in self.notesWeb[q]:
							for p in self.notesWeb[q]['authors']:
								if p[1].find(author) != -1:
									#print "this is op cit of :", p
									self.notesWeb[x]['authors'] = [p]					
									authorCount = authorCount + 1
									wentWith = p[1]
					
					
					titleCount = 0
					if (authorCount > 1):
						
						#if there are multiple authors, try to see if we can find the right article/book, if not go with above
						for q in self.notesWeb:
							if 'authors' in self.notesWeb[q]:
								for p in self.notesWeb[q]['authors']:
									if p[1].find(author) != -1 and p[1].find(ref) != -1:
										#print "this is op cit of :", p
										self.notesWeb[x]['authors'] = [p]					
										titleCount = titleCount + 1
										wentWith = p[1]
						
										

					#if it is a classic reference format: EG:	Posner, Antoine Watteau, 160. 
					#check to see if we have that author already
					"""
					print "\n\n\n"
					print note
					print author
					print ref
					print "Found ", authorCount, " authors, titles: ", titleCount
					print wentWith

					print "\n\n\n"
					"""
						
				else:
					
					asdf=1
					#print "Could nit figure out:\n\n\n\n",note
						
					
			
			#	print note
			#	print "------------"
			#	print self.notesWeb[x]
			#	print "------------"
			#	print self.authorDirectory
	 		
	 	#print self.authorDirectory
	 	#print self.webAuthorCount
		
	#	print self.notesWeb
	#	sys.exit()
		
	def analyzeBib(self):
		
		
		
		
		self.webAuthorCount = {}
		self.notesWeb = {}
		count = 0
		
		
		
		
		if self.quirksModePMLA:
			
			paraText  = re.compile(r'(\(.*?\))')
		
			for idx, x in enumerate(self.tokenizedBodySentences):	
				
				
				
				senNormal = x.decode('utf-8').encode("ascii","ignore")
				sen = x.decode('utf-8').encode("ascii","ignore").lower()
		
				if paraText.search(sen):
					
					#print sen
					
					foundAuthors = []
					
					for para in paraText.findall(sen):
					
						#print para
						#print "\n"
						
						para = para.split(";")
						
						
						for aPara in para:
						
							#first see if we have an author match
							for a in self.worksCited:
								if aPara.lower().replace(" ",'').find(a['author'].lower()) != -1:
									
									if (a['author'] not in foundAuthors):
										
										
									
										#print "Found ", a['author'], " in ", aPara
										self.notesWeb[count] = {'body' : senNormal , 'note' : a['cit'], 'pos' : idx, 'page' : 'n/a', 'authors' : a['author']}
										foundAuthors.append(a['author'])
										
										if a['author'] in self.webAuthorCount:
											self.webAuthorCount[a['author']] =+ 1
										else:
											self.webAuthorCount[a['author']] = 1
											
										
										count += 1
									
									
									#TODO: The title is a major problem, with this data especially and the way they abbrivate and sometime not include the cit title
									
								
							
						#	print a
						
		
		
		
			
			return
			
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		 
		
		#self.tokenizedBodySentences
		
		bibExtract = re.compile('([a-z]*),.*?([0-9]{4})')
		authorExtract = re.compile('([a-z]*,.*?)([0-9]{4})')
		
		
		extractedBibs = []
		
		for x in self.bib:
			
			#can we find a author year patter, if so store it and a regex for its match
			r = bibExtract.search(x.decode('utf-8').encode("ascii","ignore").lower())
			if r:
				
				extractedBibs.append([r.groups(),re.compile(r"(" + re.escape(r.groups()[0]) +  r".*?"+ re.escape(r.groups()[1]) + r")" ),x])
				
				
		
		
 		for idx, x in enumerate(self.tokenizedBodySentences):	
			
			sen = x.decode('utf-8').encode("ascii","ignore").lower()
			
			for aBib in extractedBibs:
				
				
				
				
				#my_regex =  re.escape(aBib[0]) +  r".*?"+ re.escape(aBib[1])

				s = aBib[1].search(sen)
				if s:
				#if sen.find(aBib[0]) != -1 and sen.find(aBib[1]) != -1:
					
					#print "-----\n", aBib , "\n~~~~~~\n", sen, "\n--------\n"
					
					
					
					#TODO: Sometime a name is picked up with another's year
					context = ''
					
					#print "--------"
					#print len(s.groups()), len(s.groups()[0])
					#print aBib[1].findall(sen)
					#print sen.find(aBib[1]) - sen.find(aBib[0]) 
					
					#if it starts with a para thengrab the previous sentence
					if x[0] == "(":
						if idx != 0:
							context = self.tokenizedBodySentences[idx-1]
 					
					context = context + x
					
					#print context
					#print aBib[2]

			
					#try to grab some info about the citations
					
					
					
					authors = {}

					r = authorExtract.search(aBib[2].decode('utf-8').encode("ascii","ignore").lower())
					if r:
						
						authors = []
						
						if r.groups()[0].find(';') != -1:
							
							split = r.groups()[0].split(' and ')
							authors.append(split[1]) 
							
							split = split[0].split(';')
							
							for n in split:
								authors.append(n)
							
							#print "AUTHORS ; :", authors
							
						elif r.groups()[0].find(' and ') != -1:	
							
							#print aBib[2].decode('utf-8').encode("ascii","ignore").lower()
							
							split = r.groups()[0].split(' and ')
							authors.append(split[0]) 
							authors.append(split[1])
							
						elif r.groups()[0].find('&') != -1:	
							
							split = r.groups()[0].split(' & ')
							authors.append(split[1]) 
							
							split = split[0].split('.')
							
							for n in split:
								authors.append(n)
																	
					
							#print "AUTHORS and :", authors
							
						else:
							
							
							authors.append(r.groups()[0]) 
							#print "AUTHORS:", authors
			
						
						for n in range(0,len(authors)):
							
							authors[n] = authors[n].replace('(','')
							authors[n] = authors[n].strip()
							authors[n] = authors[n].replace('.','')
							if authors[n][len(authors[n])-1:] == ',':
								authors[n] = authors[n][0:len(authors[n])-1]
			
							authors[n] = authors[n].strip().title()
		
							if authors[n].find(',') == -1 and authors[n] != '':
								spaces = authors[n].split(' ')
								name = spaces[len(spaces)-1]
								name = name + ', ' + ' '.join(spaces[0:len(spaces)-1])
								authors[n] = name
								 
							if authors[n] == '':
								del authors[n]
													
						#print "AUTHORS:", authors
						
						
						for n in authors:
					
							if n in self.webAuthorCount:
								self.webAuthorCount[n] += 1
							else:
								self.webAuthorCount[n] = 1	
								
													
						#	if self.authors.has_key(n):
						#		self.authors[n].append(x)
						#	else:
						#		self.authors[n] = [x]

		

					self.notesWeb[count] = {'body' : context , 'note' : aBib[2], 'pos' : idx, 'page' : idx, 'authors' : authors}

					count += 1
		
		
		

		"""
		
		freeCit = freeCit[0:len(freeCit)-1]
		self.freeCit = freeCit
		
		
		#attempt to use freecit api
		import urllib
		import urllib2
		
		url = 'http://freecite.library.brown.edu/citations/create'
		values = {'citation[]' : freeCitAry}
		headers = { 'Accept' : 'text/xml' }

		data = urllib.urlencode(values,True)
		req = urllib2.Request(url, data,headers)
		response = urllib2.urlopen(req)
		the_page = response.read()
		print the_page
		"""
		
		

	def NERText(self):
	
	
		allBody = self.bodyText.encode("ascii","ignore")
		allFoot = self.footText.encode("ascii","ignore")

		url = 'http://api.opencalais.com/tag/rs/enrich'
		payload = ''.join(self.tokenizedBodySentences)
		headers = {'x-calais-licenseID': self.calaisKey, 'content-type' : 'TEXT/RAW', 'outputFormat' : 'Application/JSON'}
	
		r = requests.post(url, data=json.dumps(payload), headers=headers)
	
		print r.text
	
		sys.exit()
	

	def prepareText(self):
		
		#this just makes some vars we will use later
		
		#store the body text tokenized for later use
		allBody = ''
		for idx, val in enumerate(self.pagesText):
			
			body = val['bodyText'].encode("ascii","ignore")
			allBody = allBody + body		
			
			
		allBody = allBody.replace('-\n','')
		allBody = allBody.replace('\n',' ')
		allBody = allBody.replace('- ','')
	
		#:( 
		if self.quirksModePMLA:
			allBody = allBody.replace(' ing ','ing ')
			allBody = allBody.replace(' y ','y ')
			allBody = allBody.replace(' lly ','lly ')
			allBody = allBody.replace(' ly ','ly ')
			
		
		
		tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
		
		
		#if there is a bib we do not want to include it in the tonkenized list
		if len(self.bib) != 0:
			
			
			firstBib = self.bib[0].decode("ascii","ignore")
			 
			if allBody.find(firstBib)!=-1:
				allBody = allBody[0:allBody.find(firstBib)]
			#else:
			#	print "no first cit", firstBib
			#	print allBody
			
		#some abbrivations that trip up the tokenizer

		allBody = self.removePeriods(allBody)
					
		allBody = re.sub("\s\s+" , " ", allBody)	
		
		
		
		
			
		self.tokenizedBodySentences = tokenizer.tokenize(allBody)
		#print '\n-----\n'.join(self.tokenizedBodySentences)
    
		#sys.exit()
		
		
	def removePeriods(self,text):
		
		allBody = text
		#todo: clean this up
		allBody = allBody.replace('et al.','et al,')
		allBody = allBody.replace('e.g.','e g ')	
		allBody = allBody.replace('cf.','cf ')
		allBody = allBody.replace('i.e.','ie ')
		allBody = allBody.replace('I.E.','ie ')
		allBody = allBody.replace('Fig.','Fig ')
		allBody = allBody.replace('fig.','fig ')
		allBody = allBody.replace('ii.1','ii.one')
		allBody = allBody.replace('ii.2','ii.two')
		allBody = allBody.replace('ii.3','ii.three')
		allBody = allBody.replace('ii.4','ii.four')
		allBody = allBody.replace('ii.5','ii.five')
		allBody = allBody.replace('II.1','II.one')
		allBody = allBody.replace('II.2','II.two')
		allBody = allBody.replace('II.3','II.three')
		allBody = allBody.replace('II.4','II.four')
		allBody = allBody.replace('II.5','II.five')
		allBody = allBody.replace('III.1','III.one')
		allBody = allBody.replace('III.2','III.two')
		allBody = allBody.replace('III.3','III.three')
		allBody = allBody.replace('III.4','III.four')
		allBody = allBody.replace('III.5','III.five')
		allBody = allBody.replace('iii.1','iii.one')
		allBody = allBody.replace('iii.2','iii.two')
		allBody = allBody.replace('iii.3','iii.three')
		allBody = allBody.replace('iii.4','iii.four')
		allBody = allBody.replace('iii.5','iii.five')
		allBody = allBody.replace('IV.1','IV.one')
		allBody = allBody.replace('IV.2','IV.two')
		allBody = allBody.replace('IV.3','IV.three')
		allBody = allBody.replace('IV.4','IV.four')
		allBody = allBody.replace('IV.5','IV.five')
		allBody = allBody.replace('iv.1','iv.one')
		allBody = allBody.replace('iv.2','iv.two')
		allBody = allBody.replace('iv.3','iv.three')
		allBody = allBody.replace('iv.4','iv.four')
		allBody = allBody.replace('iv.5','iv.five')									
		allBody = allBody.replace('fig.','fig ')		
		allBody = allBody.replace('All use subject to JSTOR Terms and Conditions','')		
		
		
		jstorRegex = re.compile(r'(This content downloaded on\s[A-Z].*?AM)|(This content downloaded on\s[A-Z].*?PM)')
		
		
		s = jstorRegex.search(allBody)
		if s:
			allBody = allBody.replace(s.groups()[0],'')
			
			
			
			
		
		
		return allBody
	
	
	def analyzeText(self):
		
		self.citationTypeInline = False
		self.citationTypeNote = False
		
		
		allBody = self.bodyText.encode("ascii","ignore")
		allFoot = self.footText.encode("ascii","ignore")

		#remove decimals
		decimal = re.compile('([0-9]*\.[0-9]*)')
		if decimal.search(allBody):
			for dec in decimal.findall(allBody):
				if dec == '.':
					continue	
										
 				decimalValue = dec.replace('.',',')								
				allBody = allBody.replace(dec,decimalValue)	
		
	
	 
		self.regexNoteInBody = re.compile('[a-z]\.[0-9]{3}|[a-z]\.[0-9]{2}|[a-z]\.[0-9]{1}|[a-z]\."[0-9]{3}|[a-z]\."[0-9]{2}|[a-z]\."[0-9]{1}|[a-z]\.”[0-9]{3}|[a-z]\.”[0-9]{2}|[a-z]\.”[0-9]{1}|[a-z]\?[0-9]{2}|[a-z]\?[0-9]{1}|[a-z],[0-9]{3}|[a-z],[0-9]{2}|[a-z],[0-9]{1}|[a-z]\)\.[0-9]{3}|[a-z]\)\.[0-9]{2}|[a-z]\)\.[0-9]{1}|[a-z]"[0-9]{3}|[a-z]"[0-9]{2}|[a-z]"[0-9]{1}|[a-z]”[0-9]{3}|[a-z]”[0-9]{2}|[a-z]”[0-9]{1}|[a-z],[0-9]{3}\s|[a-z],[0-9]{2}\s|[a-z],[0-9]{1}\s',re.IGNORECASE)
		self.regexAPAStyle = re.compile('\([A-Z][a-z]*\s[0-9]{4}\)|[A-Z][a-z]*\s\(\s[0-9]{4}\s\)|[A-Z][a-z]*\s\(\s*[0-9]{4}:|[A-Z][a-z]*\s\([0-9]{4}\)|\([A-Z][a-z]*\s*&\s*[A-Z][a-z]*\s*[0-9]{4}')
		
		
		#self.regexFigureCaption = re.compile('^[0-9]*\s.*detail|^[0-9]*\s.*photograph')
		results = self.regexAPAStyle.findall(allBody)
		
		#print "error", len(results)
		#print results
		
		
				
		if (len(results)< len(self.layouts)/2):
			self.citationTypeNote = True
		else:
			self.citationTypeInline = True
			
		#if there is a bib and some inline, its inline
			
		if len(self.bib) != 0 and len(results) >= 10:
			 self.citationTypeInline = True
			 self.citationTypeNote = False
 
 
 
 		#if there are end notes, its notes...
 		artBulletinLikeEndNotes = re.compile(r'(\n[0-9]{1}\.\s+[A-Za-z0-9"].*\n|\n[0-9]{2}\.\s+[A-Za-z0-9"].*\n|\n[0-9]{3}\.\s+[A-Za-z0-9"].*\n)')
 		if artBulletinLikeEndNotes.search(allFoot):
 			
 			if len(artBulletinLikeEndNotes.findall(allFoot)) >= 10:
 				self.citationTypeNote = True
 				self.citationTypeInline = False
 		
  		if self.quirksModePMLA:
			 self.citationTypeInline = True
			 self.citationTypeNote = False 
	
	#returns the text formated based of a array of lines
	def arrangeText(self,textAry,threshold):
		 
		
		lineHeightAll = []
		lineHeightAllNumber = 0
		returnText = ''
		
		allX0 = {}
		
		for aLine in textAry:		
			
			#if this is a foot note number ignore it for our avg line height calulation, because it has weird bbox values, 
			#kind of a hack because I can't dedect superscript right now
			
			try:
				if aLine.get_text().strip().isnumeric():
					continue
			except:
				errorString = aLine.get_text()
		
			lineHeight = aLine.bbox[3]-aLine.bbox[1]
			lineHeightAll.append(lineHeight)
			lineHeightAllNumber = lineHeightAllNumber + lineHeight
			
 			if allX0.has_key(self.roundUpToTens(aLine.bbox[0])):
				allX0[self.roundUpToTens(aLine.bbox[0])] = allX0[self.roundUpToTens(aLine.bbox[0])] + 1
			else:
				allX0[self.roundUpToTens(aLine.bbox[0])] = 1
		
	
		#empty text array
		if len(lineHeightAll) == 0:
			return ''
		
		lineHeightAllAvg = lineHeightAllNumber / len(lineHeightAll)
		
		#print "lineHeightAllAvg : ",lineHeightAllAvg, "median :", median(lineHeightAll)
		lineHeightAllAvg = median(lineHeightAll)
		
		
		
		#figure out the most likely pos of the start of the text lines
		#allX0Sorted[0][0] will be the smallest X point with the most occurances	
		allX0Sorted = sorted(allX0.iteritems(), key=operator.itemgetter(1),reverse=True)
		startX = allX0Sorted[0][0]
 
		
		#footnotes, tweek it a little
		if threshold == self.fontSizeFoot:
			lineHeightAllAvg = lineHeightAllAvg - (threshold/2.5)
			
		
		"""
		#a little tweek, make it smaller window 		
		if threshold == 6:
			lineHeightAllAvg = lineHeightAllAvg - (threshold/1)
		elif threshold == 8:
			lineHeightAllAvg = lineHeightAllAvg - (threshold/5)
		else:
			lineHeightAllAvg = lineHeightAllAvg - (threshold/4)
		"""
	 
		startY = textAry[0].bbox[3] - (abs(textAry[0].bbox[3] - textAry[0].bbox[1])/2)
		
		lines = {startY : []}
		 
		for x in range(0,100):	
			key = startY - (lineHeightAllAvg * x)			
			key = math.ceil(key * 100000) / 100000.0			
			if key < 0:
				break
			lines[key] = []
		
 
		for aLine in textAry:		
			midPoint = aLine.bbox[3] - (abs(aLine.bbox[3] - aLine.bbox[1])/2)
			
			closestValue = 1000
			closetLine = -1
			
			#little tweek, superscript numbers have weird bboxs, bump it down a little	
			try:	
				if aLine.get_text().strip().isnumeric():
					midPoint = midPoint - (threshold/2)
			except:
				midPoint = midPoint
			
			for key, value in lines.iteritems():
				
				if abs(key - midPoint) < closestValue:
					closestValue = abs(key - midPoint)
					closetLine = key
				
			
			lines[closetLine].append(aLine)
			
		
		lineArray = []
		
		allWidth = {}
		
		for line in  sorted(lines.iterkeys(),reverse=True):
		
		
			if len(lines[line])==0:
				continue

				
			width = 0
			for x in lines[line]:				
				width = width + x.bbox[2] - x.bbox[0]
			
			width = self.roundUpToTens(round(width))
			
 			if allWidth.has_key(width):
				allWidth[width] = allWidth[width] + 1
			else:
				allWidth[width] = 1			
				
 		
		"""
		if self.debug:
			print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
			for line in  sorted(lines.iterkeys(),reverse=True):				
				print lines[line]		
			print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
		"""
			
		#sort them and store the results
		for line in  sorted(lines.iterkeys(),reverse=True):
		
			#print line
			
			if len(lines[line])==0:
				continue
				
			
			#foot notes	
			try:
				if len(lines[line])==1 and lines[line][0].get_text().strip().isnumeric():				
					#print "-----*-------"
					#print lines[line], line
					#print lines
					#print "-----*-------"
					if self.returnNextLine(lines,line):
						lines[self.returnNextLine(lines,line)].append(lines[line][0])
						lines[line] = []
						continue
						#print "This belongs in the line ", self.returnNextLine(lines,line)
			except:
				errorString = 	lines[line][0].get_text()	
			 
			"""
			if len(lines[line]) == 1:
				if lines[line][0].bbox[0] > startX + 10:
				
				
					
							
					
						#print "This line looks fishy " , lines[line][0]
						
						fishyWidth = lines[line][0].bbox[2] - lines[line][0].bbox[0]
						addToNextLine = False
						addToPreviousLine = False
						
						 
						if self.returnPrevLine(lines,line) is not False and threshold == 6:
								
								#loop through the previous line and see if there is a space where this text bit could possibly fit
								previousLines = {}
								for y in lines[self.returnPrevLine(lines,line)]:
									previousLines[y.bbox[0]] = y.bbox[2]
								
								previousLinesAry = []
								for pos in sorted(previousLines.iterkeys()):	
									previousLinesAry.append([pos,previousLines[pos]])
									
								
								#print "previousLinesAry", previousLinesAry
								
								for z in range(0,len(previousLinesAry)):
								
									if z-1 in range(0,len(previousLinesAry)):								
										gap = previousLinesAry[z][0] - previousLinesAry[z-1][1] 
										if abs(gap - fishyWidth) <= 15:
											addToPreviousLine = True		
											#print "previousLinesAry after gap: ",gap, gap - fishyWidth
											break
											
										
										
									if z+1 in range(0,len(previousLinesAry)):								
										gap = previousLinesAry[z+1][0] - previousLinesAry[z][1]
										if abs(gap - fishyWidth) <= 15:
											addToPreviousLine = True
											#print "previousLinesAry after gap: ",gap, gap - fishyWidth
											break											
										
										
										
						if self.returnNextLine(lines,line) is not False and threshold == 6:
						
								#loop through the next lines and see if there is a space where this text bit could possibly fit
								nextLines = {}
								for y in lines[self.returnNextLine(lines,line)]:
									nextLines[y.bbox[0]] = y.bbox[2]
								
								nextLinesAry = []
								for pos in sorted(nextLines.iterkeys()):	
									nextLinesAry.append([pos,nextLines[pos]])
									
								
								#print "nextLinesAry", nextLinesAry
								
								for z in range(0,len(nextLinesAry)):
								
									if z-1 in range(0,len(nextLinesAry)):								
										gap = nextLinesAry[z][0] - nextLinesAry[z-1][1] 
										
										#print "nextLinesAry before gap: ",gap
										if abs(gap - fishyWidth) <= 15:
											addToNextLine = True
											break
											
										
									if z+1 in range(0,len(nextLinesAry)):								
										gap = nextLinesAry[z+1][0] - nextLinesAry[z][1]
										
										#print "nextLinesAry after gap: ",gap
										if abs(gap - fishyWidth) <= 15:
											addToNextLine = True																		
											break
									
						#if addToNextLine:
						#	print "WOULD ADD TO NEXT LINE", fishyWidth, gap-fishyWidth
						#if addToPreviousLine:
						#	print "WOULD ADD TO PREVIOUS LINE", fishyWidth, gap-fishyWidth
						
							
			"""	
				
			someLines = []
			
			for x in lines[line]:
			
				#print "\t",x			
				someLines.append(x)
		
			lineArray.append(someLines)
			
			
		#if threshold == 6:
		#	print lineArray
			
			
			
			
		for aLine in lineArray:
		
			if len(aLine) == 0:
				continue
		
			textHash = {}
		
			for x in aLine:	
				if textHash.has_key(x.bbox[0]) == False:
					textHash[x.bbox[0]] = x.get_text()
				else:
					textHash[x.bbox[0]] = textHash[x.bbox[0]] + ' ' + x.get_text()

			
			finalText = ''
			
			for pos in sorted(textHash.iterkeys()):
				
				finalText = self.cleanSentence(finalText + textHash[pos].strip() + ' ')
				
				
				
			finalText = finalText.strip()
			
			returnText = returnText + '\n' + finalText
				

		
		
		return returnText
		  
		
	def returnText(self):

		bodyText = []
		footText = []		
		bodyTextLeft = []
		bodyTextRight = []
		footTextLeft = []
		footTextRight = []
		 
		column1 = []
		column2 = []
 
		counter = 0
		
		self.bodyText = ''
		self.footText = ''
		self.pagesText = []
		
		self.regexFigureCaptionFullFormat = re.compile('^figure[0-9]*\.|^figure\s[0-9]*\.|^table[0-9]*\.|^table\s[0-9]*\.')
		self.regexFigureCaption = re.compile('^[0-9]*\s.*detail|^[0-9]*\s.*photograph')		
		
		for layout in self.layouts:
		
			thisPageBody  = ''
			thisPageFoot = ''
		
			pageHeight = layout.bbox[3]
			pageWidth = layout.bbox[2]
			
			#grab the images/figures first
			#for lt_obj in layout:			 
				#if lt_obj.__class__.__name__ == 'LTTextBoxHorizontal':
			#	print lt_obj


			
			for lt_obj in layout:
			 
				if lt_obj.__class__.__name__ == 'LTTextBoxHorizontal':
					
					
					bodyCount = 0
					footCount = 0
					otherCount = 0	
 

					#if the y bbox is this high up and its is a short bit of text is is likely the header
					if lt_obj.bbox[1] > 500 and len(lt_obj.get_text()) < 100:
						continue
					
					if lt_obj.bbox[1] > 500  or lt_obj.bbox[1] < 100 and len(lt_obj.get_text()) < 10 and lt_obj.get_text().strip().isnumeric():
						continue
					
					
					text = self.cleanSentence(lt_obj.get_text().replace('\n',' ').lower().strip())
					
					#if text.find('table') != -1:
					#	print "------------table------------\n",text,"\n--------------------------\n"
					
					
					if self.regexFigureCaption.match(text) and len(lt_obj.get_text()) <= 150:
						#print "------------regexFigureCaption------------\n",text,"\n--------------------------\n"
						continue

						
					if self.regexFigureCaptionFullFormat.match(text):
						continue
						#print "-------------regexFigureCaptionFullFormat-----------\n",text,"\n--------------------------\n"
						
					
					for textLine in lt_obj:				
						#loop through the text chars and figure out the avg size of the text
						
						for textChar in textLine:								
							if textChar.__class__.__name__  == 'LTChar':

								#if textChar.fontsize == 1:
								#	fontsize = round(textChar.size)
								#else:
								#	fontsize = textChar.fontsize	
								
								fontsize = round(textChar.size)
								
									
								""" 
								print textLine.get_text(), '~', textChar.get_text()							
								print textChar.font							
								print 'descriptor', textChar.font.descriptor
								#print 'fontfile', textChar.font.fontfile
								print 'fontname', textChar.font.fontname
								print 'fontfile', textChar.font.hscale
								print 'descent', textChar.font.descent
								#print 'vertical', textChar.font.vertical
								#print 'cidcoding', textChar.font.cidcoding
								print 'basefont', textChar.font.basefont
								print 'widths', textChar.font.widths
								#print 'cidsysteminfo', textChar.font.cidsysteminfo
								print 'default_width', textChar.font.default_width
								#print 'cmap', textChar.font.cmap
								#print 'cmap decode', textChar.font.cmap.decode()
								print 'flags', textChar.font.flags
								print 'unicode_map', textChar.font.unicode_map		
								#print 'unicode_map get_unichr', textChar.font.get_unichr
								#print 'default_disp', textChar.font.default_disp
								print 'leading', textChar.font.leading
								print 'italic_angle', textChar.font.italic_angle
								#print 'disps', textChar.font.disps
								print 'ascent', textChar.font.ascent							
								print 'vscale', textChar.font.vscale							
								print 'bbox', textChar.font.bbox							
								"""
								
								
								if fontsize == self.fontSizeBody:
									bodyCount = bodyCount + 1
								elif fontsize == self.fontSizeFoot:
									footCount = footCount + 1
								else:
									otherCount = otherCount + 1
									
									
					#print [bodyCount,footCount,otherCount]
					
					isBody = False
					isFoot = False
					
					
					if bodyCount >= footCount:
						isBody = True
						threshold = self.fontSizeBody
					elif footCount > bodyCount:
						isFoot = True					
						threshold = self.fontSizeFoot
					
					#if otherCount >= (bodyCount + footCount):
					#	print "-------------------------"
					#	print lt_obj
					#	print "^^^^^^^^^^^ other text"						
					
					
					
					#if the y postion is not even 1/2 down the page, it is not likely a foot note
					if self.layoutColumnOne:
						if lt_obj.bbox[3] > pageHeight / 2:
							isBody = True
							isFoot = False
							#print "---is body---",lt_obj.bbox[2]
						
					
		
					for textLine in lt_obj:				
						#loop through and piece together the lines 			

						

						if self.layoutColumnTwo:
						
						
							#print lt_obj.bbox[0]
							#print lt_obj
							
							
							if self.quirksModePMLA:
								midpage = 250
							else:
								midpage = pageWidth / 2
							
							
							
							if lt_obj.bbox[0] < midpage:
							
								if isBody == True:
									bodyTextLeft.append(textLine)
								if isFoot == True:
									footTextLeft.append(textLine)						

							else:

								if isBody == True:
									bodyTextRight.append(textLine)
								if isFoot == True:
									footTextRight.append(textLine)						
							
								
							
						else:						
							
							if isBody == True:
								bodyText.append(textLine)
							if isFoot == True:
								footText.append(textLine)					
								
						#if isFoot:	
						#	print textLine, isBody, bodyCount, isFoot, footCount
			
						
			
			if self.fontDetectionError is False:
				
				if self.layoutColumnTwo:
				
					if len(bodyTextLeft) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(bodyTextLeft,self.fontSizeBody)
						thisPageBody = thisPageBody + self.arrangeText(bodyTextLeft,self.fontSizeBody)
 						bodyTextLeft = []				
						
					if len(bodyTextRight) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(bodyTextRight,self.fontSizeBody)			
						thisPageBody =  thisPageBody + self.arrangeText(bodyTextRight,self.fontSizeBody)			
						bodyTextRight = []				
						
					if len(footTextLeft) > 0:
						self.footText =  self.footText + self.arrangeText(footTextLeft,self.fontSizeFoot)			
						thisPageFoot =  thisPageFoot + self.arrangeText(footTextLeft,self.fontSizeFoot)			
						footTextLeft = []							

					if len(footTextRight) > 0:
						self.footText =  self.footText + self.arrangeText(footTextRight,self.fontSizeFoot)			
						thisPageFoot = thisPageFoot + self.arrangeText(footTextRight,self.fontSizeFoot)			
						footTextRight = []						
						 
					
				else:
				
					if len(bodyText) > 0:
						self.bodyText = self.bodyText + self.arrangeText(bodyText,self.fontSizeBody)			
						thisPageBody = self.arrangeText(bodyText,self.fontSizeBody)									
						bodyText = []			

					if len(footText) > 0:		
						#print "\n--------------\n",self.arrangeText(footText,self.fontSizeBody),"\n-----------------\n"
						self.footText = self.footText + self.arrangeText(footText,self.fontSizeFoot)			
						thisPageFoot = self.arrangeText(footText,self.fontSizeFoot)		
						
						footText = []

						
			#if there was an error detecting the foot note or body diffrent fonts, just blob it all together
			else:
			
				if self.layoutColumnTwo:
				 
					if len(bodyTextLeft) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(bodyTextLeft,self.fontSizeBody)			
						thisPageBody =  thisPageBody + self.arrangeText(bodyTextLeft,self.fontSizeBody)			
						bodyTextLeft = []				
					if len(bodyTextRight) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(bodyTextRight,self.fontSizeBody)			
						thisPageBody =  thisPageBody + self.arrangeText(bodyTextRight,self.fontSizeBody)			
						bodyTextRight = []				
						
					if len(footTextLeft) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(footTextLeft,self.fontSizeFoot)			
						thisPageBody =  thisPageBody + self.arrangeText(footTextLeft,self.fontSizeFoot)			
						
						footTextLeft = []							

					if len(footTextRight) > 0:
						self.bodyText =  self.bodyText + self.arrangeText(footTextRight,self.fontSizeFoot)			
						thisPageBody =  thisPageBody + self.arrangeText(footTextRight,self.fontSizeFoot)			
						footTextRight = []						
						 
					
				else:
				
					if len(bodyText) > 0:
						self.bodyText = self.bodyText + self.arrangeText(bodyText,self.fontSizeBody)			
						thisPageBody = thisPageBody + self.arrangeText(bodyText,self.fontSizeBody)									
						bodyText = []			

					if len(footText) > 0:		
						self.bodyText = self.bodyText + self.arrangeText(footText,self.fontSizeFoot)			
						thisPageBody = thisPageBody + self.arrangeText(footText,self.fontSizeFoot)
						footText = []			
 					 
			
			self.pagesText.append({'bodyText':thisPageBody, 'footText' : thisPageFoot})

			#print thisPageBody.encode("ascii","ignore")
			#print "----------"
			#print thisPageFoot.encode("ascii","ignore")
			#print "\n\n\n\n\n\n"
			
			
			counter = counter +1
			#if len(self.pagesText) > 15:
			#	sys.exit()			
	

	 
	def analyzePages(self):
		
		itemWidths = []
		itemWidthsTotal = 0
		
		columnOne = 0
		columnTwo = 0
		
		numberOfImages = 0
		
			
		for layout in self.layouts:
		
			pageHeight = layout.bbox[3]
			pageWidth = layout.bbox[2]
			 
			#find the avg width of the text items
			for lt_obj in layout:
			
 				if lt_obj.__class__.__name__ == 'LTTextBoxHorizontal':
					#if lt_obj.bbox[2]-lt_obj.bbox[0]>200:
					#	itemWidths.append(lt_obj.bbox[2]-lt_obj.bbox[0])
					#	itemWidthsTotal = itemWidthsTotal + (lt_obj.bbox[2]-lt_obj.bbox[0])
					
					itemWidths.append(self.roundUpToTens(lt_obj.bbox[2]-lt_obj.bbox[0]))
					
				
				if lt_obj.__class__.__name__ == 'LTFigure':
					numberOfImages = numberOfImages +1
				
			#see where the majority of the text items start
			for lt_obj in layout:
				if lt_obj.__class__.__name__ == 'LTTextBoxHorizontal':		
					
					
					
					#only large text blocks
					if len(lt_obj.get_text()) > 250:		
						#print lt_obj.bbox[0],pageWidth/2
						if lt_obj.bbox[0] >= (pageWidth/2):
							columnTwo = columnTwo + 1					
 						else:
							columnOne = columnOne + 1
					
			 
		
		#print "Avg width of text is :", itemWidthsTotal / len(itemWidths)
		
		#this could be refined, works for now
		
		if columnTwo >= len(self.layouts)-1:
			self.layoutColumnOne = False
			self.layoutColumnTwo = True		
		else:
			self.layoutColumnOne = True
			self.layoutColumnTwo = False
		
		if self.quirksModePMLA:
			self.layoutColumnOne = False
			self.layoutColumnTwo = True	
					
		#print "columnOne: ", columnOne, self.layoutColumnOne
		#print "columnTwo: ", columnTwo, self.layoutColumnTwo, len(self.layouts)
		


#this is the bayes classifyer
class classify:
	
	
		
	def getWordsInPhrases(self,phrases):
	    all_words = []
	    for (words, sentiment) in phrases:
	      all_words.extend(words)
	    return all_words
	
	
	def getWordFeatures(self,wordlist):
	    wordlist = nltk.FreqDist(wordlist)
	    word_features = wordlist.keys()
	    return word_features
	
	
	def extractFeatures(self,document):
	    document_words = set(document)
	    features = {}
	    for word in self.wordFeatures:
	        features['contains(%s)' % word] = (word in document_words)
	    return features	
	
	def  __init__(self):
		
		
		#load the training datasets
		
		
		self.posPhrases = []
		self.negPhrases = []
		
		with file ('positive.csv', 'rt') as f:
		   for line in f.readlines():
		       self.posPhrases.append((line.replace("\n",""), 'positive'))
		
		 
		with file ('negative.csv', 'rt') as f:
		   for line in f.readlines():
		       self.negPhrases.append((line.replace("\n",""), 'negative'))
		
		#if there are too many postive vs neg, need to make a random sample
		if self.posPhrases > self.negPhrases:
		    newPosPhrase = []
		    for i in range(len(self.negPhrases)):		        
		        randomPos = self.posPhrases[random.randrange(0,len(self.posPhrases))]
		        newPosPhrase.append(randomPos)		
		             
		    self.posPhrases = newPosPhrase		
		
		self.phrases = []
		exclude = set(string.punctuation)
		
		for (words, sentiment) in self.posPhrases + self.negPhrases:
		     
		    wordsFiltered = []
		    for item in nltk.bigrams(words.split()):
		       wordsFiltered.append(' '.join(item).lower())
		         
		    if len(wordsFiltered) > 0:
		        self.phrases.append((wordsFiltered, sentiment))

		
		self.wordFeatures = self.getWordFeatures(self.getWordsInPhrases(self.phrases))
		self.trainingSet = nltk.classify.apply_features(self.extractFeatures, self.phrases)
		self.classifier = nltk.NaiveBayesClassifier.train(self.trainingSet)


	def judge(self,text):
		
		
		text = text.replace(".","").replace("?","").replace(",","").replace(";","").replace(":","").replace("!","").replace('"',"").replace("'","")

	
		text = text.replace('-\n', '')
		text = text.replace('\n', ' ')
		text = re.sub("\d+", "", text)
		text = re.sub("\s+", " ", text)
		text = text.strip()
				
		textBigram = []
		
		for item in nltk.bigrams(text.split()):
		   textBigram.append(' '.join(item).lower())
		
		
		probdist = self.classifier.prob_classify(self.extractFeatures(textBigram))
		results  = self.classifier.classify(self.extractFeatures(textBigram))
		
		
		#print text
		
		return {'results' : results, "positive" : "{0:.10f}".format(probdist.prob('positive')), "negative" : "{0:.10f}".format(probdist.prob('negative'))}
		#print '{ "results" : "' + results + '", "positive" : "' + "{0:.10f}".format(probdist.prob('positive')) + '", "negative" : "' + "{0:.10f}".format(probdist.prob('negative')) + '"}'
 
		
		
		
		
if __name__ == "__main__":
	
	aClassify = classify()
	
	try:
		mode = sys.argv[2]
	except:
		mode = "single"
	
	
	if mode == "single":
		aCit = cit('/a/complete/path/' + sys.argv[1])
	
	if mode == "batch":
		
		sys.argv[1]
		
		for root, _, files in os.walk('/a/complete/path/'):
			
			for f in files:
				
				if f.find(sys.argv[1]) != -1:
					
					print f
					aCit = cit('/a/complete/path/' + f)
		
	

