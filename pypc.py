#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pypc.py
#       
#       Copyright 2011 Di SONG <di@di-dibian>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       
#       
import re
import os
import getopt
import sys
from types import BooleanType,IntType,FloatType,StringType
import cStringIO

#############################################################
#
# Define Context Manager
#
#############################################################
class ContextManager(object):
	__instance = None
	__already_init = False
	def __new__(cls):
		if not cls.__instance:
			cls.__instance = super(ContextManager, cls).__new__(cls)
		return cls.__instance
		
	def __init__(self):
		if not self.__class__.__already_init:
			self.__doInit()
			self.__class__.__already_init = True
	
	def __doInit(self):
		self.__global_define_dict = {}
		self.__local_define_dict = {}
		self.__done_list = []
		self.__backup_stack = []
		self.__namespace_of_currentfile = None
	
	def set_options(self,options):
		
		self.__srcdir = options["srcdir"]
		self.__todir = options["todir"]
		self.__export = options.get("export",False)
		self.__comment = options.get("comment","#")
		
		if os.path.isdir(self.__srcdir):
			self.__src_base_dir = self.__srcdir
		else:
			self.__src_base_dir = os.path.split(self.__srcdir)[0]
			
		if os.path.isdir(self.__todir):
			self.__to_base_dir = self.__todir
		else:
			self.__to_base_dir = os.path.split(self.__todir)[0]
	
	def getGlobalDefine(self, key):
		try:
			return self.__global_define_dict[key]
		except KeyError:
			raise KeyError, 'Fail to find a value for %s in Global Define' % (key)
		
	def addGlobalDefine(self, key, value):
		self.__global_define_dict[key] = value
	
	def getLocalDefine(self, key):
		try:
			return self.__local_define_dict["%s.%s" % (self.__namespace_of_currentfile, key)]
		except KeyError:
			raise KeyError, 'Fail to find a value for %s in Local Defines' % (key)
		
	def addLocalDefine(self, key, value):
		self.__local_define_dict["%s.%s" % (self.__namespace_of_currentfile, key)] = value
		
	def getDefineValue(self, key):
		try:
			return self.__local_define_dict["%s.%s" % (self.__namespace_of_currentfile, key)]
		except KeyError:
			try:
				return self.__global_define_dict[key]
			except KeyError:
				raise KeyError, 'Fail to find a value for %s' % (key)
	
	def backupContext(self):
		if self.__namespace_of_currentfile:
			self.__backup_stack.append(self.__namespace_of_currentfile)
	
	def restoreContext(self):
		if len(self.__backup_stack):
			self.__namespace_of_currentfile = self.__backup_stack.pop()
	
	def addFileToDone(self, file):
		self.__done_list.append(file)
	
	def hasFileInDone(self, file):
		return file in self.__done_list
	@property
	def src_base_dir(self):
		return self.__src_base_dir
	
	@property
	def to_base_dir(self):
		return self.__to_base_dir
	
	@property
	def srcdir(self):
		return self.__srcdir
	
	@property
	def todir(self):
		return self.__todir
	
	@todir.setter
	def todir(self, value):
		self.__todir = value
			
	@property
	def export(self):
		return self.__export
			
	@property
	def comment(self):
		return self.__comment
		
	@property
	def namespace_of_currentfile(self):
		return self.__namespace_of_currentfile
	
	@namespace_of_currentfile.setter
	def namespace_of_currentfile(self, value):
		self.__namespace_of_currentfile = value
		
	def reset(self):
		self.__doInit() 
		
	def printAllParam(self):
		print self.__param_dict

############################################################
#
# Define kit functions
#
############################################################

_compile_integer = re.compile(r"[+-]?\d+")
def isInteger(value):
	return _compile_integer.match(value)	
	
_compile_float = re.compile(r"[+-]?\d+(\.\d+)?")
def isFloat(value):
	return _compile_float.match(value)

_compile_string = re.compile(r'^\".+\"$')
def isString(value):
	return _compile_string.match(value)
	
_compile_bool = re.compile(r"((true)|(True)|(TRUE)|(false)|(False)|(FALSE)){1}")
def isBool(value):
	return _compile_bool.match(value)
	
############################################################
#
# Define a base class for Parser
#
############################################################

class Parser(object):
	"""A base class for all express parser"""
	
	def processExpress(self,express):
		express_tuple = self.parseExpress(express)
		if express_tuple:
			return self.checkExpress(express_tuple)
			
		return False
	
	def parseExpress(self, express):
		return None
	
	def checkExpress(self, express):
		return False

#############################################################
#
# Define all parsers
#
#############################################################

class DefineGlobalBooleanParser(Parser):
	'''# #define global BOOL TRUE'''
	
	def parseExpress(self, statement):
		
		index = statement.find("global")
		express = statement[index+6:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1].lower() 
			if value == "true":
				express_list[1] = True
			elif value == "false":
				express_list[1] = False
			else:
				raise TypeError, "[ %s ] must be a Boolean Type" % (value)
				
			return tuple(express_list)
		else:
			return None

class DefineGlobalIntegerParser(Parser):
	'''# #define global INT 123'''
	def parseExpress(self, statement):
		
		index = statement.find("global")
		express = statement[index+6:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1]
			if isInteger(value):
				express_list[1] = int(value)
			else:
				raise TypeError, "[ %s ] must be a Integer Type" % (value)

			return tuple(express_list)
		else:
			return None
			
class DefineGlobalFloatParser(Parser):
	'''# #define global FLOAT 123'''
	def parseExpress(self, statement):
		index = statement.find("global")
		express = statement[index+6:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1]
			if isFloat(value):
				express_list[1] = float(value)
			else:
				raise TypeError, "[ %s ] must be a Float Type" % (value)

			return tuple(express_list)
		else:
			return None			


class DefineGlobalStringParser(Parser):
	'''# #define global str "I am a string" '''
	def parseExpress(self, statement):
		index = statement.find("global")
		express = statement[index+6:].strip()
		express_list = express.split(None, 1)
		if len(express_list) == 2:
			return (express_list[0], express_list[1].strip('"\r\n\t '))
		else:
			return None
			
class DefineBooleanParser(Parser):
	'''# #define BOOL TRUE'''
	def parseExpress(self, statement):
		
		index = statement.find("#define")
		express = statement[index+7:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1].lower() 
			if value == "true":
				express_list[1] = True
			elif value == "false":
				express_list[1] = False
			else:
				raise TypeError, "[ %s ] must be a Boolean Type" % (value)
				
			return tuple(express_list)
		else:
			return None

class DefineIntegerParser(Parser):
	'''# #define INT 123'''
	def parseExpress(self, statement):
		index = statement.find("#define")
		express = statement[index+7:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1]
			if isInteger(value):
				express_list[1] = int(value)
			else:
				raise TypeError, "[ %s ] must be a Integer Type" % (value)

			return tuple(express_list)
		else:
			return None
			
class DefineFloatParser(Parser):
	'''# #define FLOAT 123'''
	def parseExpress(self, statement):
		
		index = statement.find("#define")
		express = statement[index+7:].strip()
		express_list = express.split()
		if len(express_list) == 2:
			value = express_list[1]
			if isInteger(value):
				express_list[1] = float(value)
			else:
				raise TypeError, "[ %s ] must be a Float Type" % (value)

			return tuple(express_list)
		else:
			return None	

class DefineStringParser(Parser):
	'# #define str "I am a string"'
	def parseExpress(self, statement):
		
		index = statement.find("#define")
		express = statement[index+7:].strip()
		express_list = express.split(None, 1)
		if len(express_list) == 2:
			return (express_list[0], express_list[1].strip('"\r\n\t '))
		else:
			return None

class ValueParser(Parser):
	'''
	 value1 == value2
	 global v1 == v2
	 global v1 == global v2
	'''	
	def parseExpress(self, statement):
		"""
		it is deiierent with other parsers
		the return is to replace right variable with tis value
		"""
		express_list = statement.split()
		express_length = len(express_list)
		if express_length == 3:
			# value1 == value2
			left = express_list[2]
			value = ContextManager().getDefineValue(left)
			express_list[2] = value
		
		elif express_length == 4:
			# global value1 == value2
			left = express_list[3]
			value = ContextManager().getDefineValue(left)
			express_list[3] = value
		
		elif express_length == 5:
			# global value1 == global value2
			left = express_list[4]
			value = ContextManager().getGlobalDefine(left)
			express_list[3] = ""
			express_list[4] = value
		
		else:
			return None
			
		return express_list
	
	def checkExpress(self, express):
		
		right_value = express[-1]
		right_type = type(right_value)
		
		express = " ".join(map(lambda x:str(x),express))
		
		if right_type is BooleanType:
			return BooleanParser().processExpress(express)
		elif right_type is IntType:
			return IntegerParser().processExpress(express)
		elif right_type is FloatType:
			return FloatParser().processExpress(express)
		elif right_type is StringType:
			return StringParser().processExpress(express)
		else:
			return False
				
class BooleanParser(Parser):
	"""
	key == true
	global key == false
	"""
	
	def parseExpress(self, express):

		express_list = express.split()
		if express.startswith("global") and len(express_list) == 4:
			# global key == false
			express_list = express_list[1:]
			#now, key == false
			key = express_list[0]
			value = ContextManager().getGlobalDefine(key)
		
		elif len(express_list) == 3:
			key = express_list[0]
			value = ContextManager().getDefineValue(key)
		
		else:
			return None
		
		if type(value) is not BooleanType:
			raise TypeError, "[ %s ] must be a Boolean Type" % (key)
		express_list[0] = value
				
		# key == false
		value = express_list[2].lower() 
		if value == "true":
			express_list[2] = True
		elif value == "false":
			express_list[2] = False
		else:
			raise TypeError, "[ %s ] must be a Boolean Type" % (express_list[2])
				
		return tuple(express_list)
		
	
	def checkExpress(self, express):

		if express[1] == "==":
			return express[0] == express[2]
		elif express[1] == "!=":
			return express[0] != express[2]
		else:
			return False	
	

class FloatParser(BooleanParser):
	'''
	global float = 100.99
	float = 99.99
	'''		
		
	def parseExpress(self, express):
		
		express_list = express.split()
		if express.startswith("global") and len(express_list) == 4:
			# global float == 99.99
			express_list = express_list[1:]
			#now, float == 99.99
			key = express_list[0]
			value = ContextManager().getGlobalDefine(key)
			
		elif len(express_list) == 3:
			key = express_list[0]
			value = ContextManager().getDefineValue(key)
		
		else:
			return None
			
		if type(value) is not FloatType and type(value) is not IntType:
			raise TypeError, "[ %s ] must be a Float or Integer Type" % (key)
		express_list[0] = value
		
		#float = 99.99
		value = express_list[2]
		express_list[2] = float(value)
		return tuple(express_list)
		
			
	def checkExpress(self, express):

		left = express[0]
		compare = express[1]
		right = express[2]

		if compare == "==":
			return left == right
		if compare == "!=":
			return left != right
		if compare == ">=":
			return left >= right
		if compare == ">":
			return left > right
		if compare == "<=":
			return left <= right
		if compare == "<":
			return left < right

		return False

class IntegerParser(FloatParser):
	'''
	global int == 10
	int == 10
	'''
	def parseExpress(self, express):

		express_list = express.split()
		if express.startswith("global") and len(express_list) == 4:
			# global int == 10
			express_list = express_list[1:]
			#now, int == 10
			key = express_list[0]
			value = ContextManager().getGlobalDefine(key)
			
		elif len(express_list) == 3:
			key = express_list[0]
			value = ContextManager().getDefineValue(key)
		
		else:
			return None
			

		if type(value) is not IntType and type(value) is not FloatType:
			raise TypeError, "[ %s ] must be a Integer or Float Type" % (key)
		express_list[0] = value
		
		# int == 10
		value = express_list[2]
		express_list[2] = int(value)
		return tuple(express_list)


class OnlyKeyParser(Parser):
	'''
	global key
	key
	'''	
	def parseExpress(self, express):

		express_list = express.split()
		try:
			if express.startswith("global") and len(express_list) == 2:
				# global key
				express_list = express_list[1:]
				#now, key
				key = express_list[0]
				value = ContextManager().getGlobalDefine(key)
				
			elif len(express_list) == 1:
				key = express_list[0]
				value = ContextManager().getDefineValue(key)
			else:
				return None

			express_list[0] = value
			return tuple(express_list)
				
		except KeyError:
			return None

	def checkExpress(self, express):

		try:
			value = express[0]
			if type(value) is not BooleanType:
				return True
			else:
				return value
		except KeyError, e:
			return False

class StringParser(Parser):
	'''
	global str == "a string here"
	str == "a string here"
	'''	
	def parseExpress(self, express):
		
		if express.startswith("global"):
			express_list = express.split(None,3)
		else:
			express_list = express.split(None,2)
			
		if express.startswith("global") and len(express_list) == 4:
			# global str == "a string"
			express_list = express_list[1:]
			#now, str == "a string"
			key = express_list[0]
			value = ContextManager().getGlobalDefine(key)
			
		elif len(express_list) == 3:
			key = express_list[0]
			value = ContextManager().getDefineValue(key)
		else:
			return None
			
		if type(value) is not StringType:
			raise TypeError, "[ %s ] must be a String Type" % (key)
		
		express_list[0] = value
		
		# str == "a string"
		express_list[2] = express_list[2].strip('"\r\n\t ')
		return tuple(express_list)
			
	def checkExpress(self, express):

		left = express[0]
		compare = express[1]
		right = express[2]
		result = cmp(left, right)
				
		if compare == "==":
			if result == 0:
				return True
			else:
				return False
		
		if compare == "!=":
			if result != 0:
				return True
			else:
				return False
		
		if compare == ">=":
			if result >= 0:
				return True
			else:
				return False
		
		if compare == ">":
			if result > 0:
				return True
			else:
				return False
				
		if compare == "<=":
			if result <= 0:
				return True
			else:
				return False
				
		if compare == "<":
			if result < 0:
				return True
			else:
				return False
		
		return False
		
#############################################################
#
# Define iterator decoration class
#
#############################################################
class FileIterator(object):
	
	__slots__ = ('hasMore', 'next', '__file', '__next')
	def __init__(self, file):
		self.__file = file
		
	def __getHasMore(self):
		self.__next = self.__file.readline()
		if self.__next:
			return True
		else:
			return False

	hasMore = property(__getHasMore)
	
	def __getNext(self):
		if self.__next:
			return self.__next
		else:
			return None
	next = property(__getNext)

#############################################################
#
# Define a base class for Tag Processor
#
#############################################################
class TagProcessor(object):
	
	"""A base class for all tag processor"""
	
	def __init__(self, parser=None):
		if parser:
			if isinstance(parser, Parser):
				self._parser = parser
			else:
				raise TypeError, "[ %s ] must be a Parser Type" % (parser)
		
	
	def process(self, src, dest):
		
		if ContextManager().export:
			self.doExportProcess(src, dest)
		else:
			self.doNonExportProcess(src, dest)
	
	def doNonExportProcess(self, src, dest):
		dest.write(src.next)
		self.doExportProcess(src, dest)
		
	def doExportProcess(self, src, dest):
		pass
#############################################################
#
# Define all tag processors
#
#############################################################

class DefineGlobalProcessor(TagProcessor):
	
	def doExportProcess(self, src, dest):
		if self._parser:
			key_value = self._parser.parseExpress(src.next)
			ContextManager().addGlobalDefine(key_value[0], key_value[1])

class DefineProcessor(TagProcessor):
	
	def doExportProcess(self, src, dest):
		if self._parser:
			key_value = self._parser.parseExpress(src.next)
			ContextManager().addLocalDefine(key_value[0], key_value[1])

class ElseProcessor(TagProcessor):
	
	def doExportProcess(self, src, dest):
		while src.hasMore:
			line = src.next
			p = TagSelector.getTagProcessor(src.next)
			if p:

				if isinstance(p, EndifProcessor):
					p.process(src, dest)
					return
				else:
					p.process(src, dest)
			else:
				dest.write(line)


class NotNeedElseProcessor(TagProcessor):
	
	def doNonExportProcess(self, src, dest):
		
		comment = ContextManager().comment
		dest.write(src.next)
		count_if = 1
		while src.hasMore:
			line = src.next
			p = TagSelector.getTagProcessor(line)
			if p:
				if isinstance(p, IfdefProcessor) or isinstance(p, IfndefProcessor):
					count_if += 1
				elif isinstance(p, EndifProcessor):
					count_if -= 1
					p.process(src, dest)
					if count_if == 0:
						return

			dest.write("%s %s" % (comment, line))

	def doExportProcess(self, src, dest):
		count_if = 1
		while src.hasMore:
			line = src.next
			p = TagSelector.getTagProcessor(line)
			if p:
				if isinstance(p, IfdefProcessor) or isinstance(p, IfndefProcessor):
					count_if += 1
				elif isinstance(p, EndifProcessor):
					count_if -= 1
					p.process(src, dest)
					if count_if == 0:
						return

class EndifProcessor(TagProcessor):
	pass
	
class IfdefProcessor(TagProcessor):
	'''
	# #ifdef key == value
	'''
	def __init__(self):
		self._tag = "#ifdef"
		self._tag_length = len(self._tag)
	
	def getExpressResult(self,src):
		line = src.next
		index = line.find(self._tag)
		express = line[index + self._tag_length:]
		or_express_list = express.split("or")
		or_result = False
		for and_express in or_express_list:
			and_express_list = and_express.split("and")
			and_result = True
			for express in and_express_list:
				express = express.strip("\r\n\t ")
				parser = ExpressSelector.getExpressProcessor(express)
				if parser:
					result = parser.processExpress(express)
					if not result:
						and_result = False
						break # jump out and loop
				else:
					raise SyntaxError, " %s is a illegale express" % express
			if and_result:
				or_result = True
				break # jump out or loop
		
		#print "or_result = %s" % or_result
		return or_result
		
	def doExportProcess(self, src, dest):

		or_result = self.getExpressResult(src)
		if or_result:
			self.recordIfBlockOnly(src, dest)
		else:
			self.recordElseBlockOnly(src, dest)
				
	def recordIfBlockOnly(self, src, dest):
		while src.hasMore:
			line = src.next
			p = TagSelector.getTagProcessor(line)
			if p:
				if isinstance(p, EndifProcessor):
					p.process(src, dest)
					return
				elif isinstance(p, ElseProcessor):
					NotNeedElseProcessor().process(src, dest)
					return
				else:
					p.process(src, dest)
			else:
				dest.write(line)
	
	def recordElseBlockOnly(self, src, dest):
		export = ContextManager().export
		comment = ContextManager().comment
		count_if = 1

		while src.hasMore:
			line = src.next
			p = TagSelector.getTagProcessor(line)
			if p:
				if isinstance(p, ElseProcessor) and count_if == 1:
					p.process(src, dest)
					return
				else:
					if isinstance(p, IfdefProcessor) or isinstance(p, IfndefProcessor):
						count_if += 1
						if not export:
							dest.write(line)
					elif isinstance(p, EndifProcessor):
						count_if -= 1
						p.process(src, dest)
						if count_if == 0:
							return
					elif not export:
						dest.write(line)
					
			elif not export:
				dest.write("%s %s" % (comment, line))
		
class IfndefProcessor(IfdefProcessor):
	
	def __init__(self):
		self._tag = "#ifndef"
		self._tag_length = len(self._tag)
	
	def doExportProcess(self, src, dest):
		
		or_result = self.getExpressResult(src)
		if not or_result:
			self.recordIfBlockOnly(src, dest)
		else:
			self.recordElseBlockOnly(src, dest)

class IncludeProcessor(TagProcessor):
	'''
	# #include "file name"
	'''
	def doExportProcess(self, src, dest):
		express = src.next
		express_list = express.split(None, 2)
		if len(express_list) == 3:
			file_name = express_list[2].strip('"\r\n\t ')
			include_full_path = os.path.join(ContextManager().src_base_dir,file_name)
			if not os.path.exists(include_full_path):
				raise Exception, "%s does not exist." % include_full_path
				
			dest.write(express)
			
			include_dest = os.path.join(ContextManager().to_base_dir,file_name)
			ContextManager().backupContext()
			_processfile(include_full_path,include_dest)
			ContextManager().restoreContext()

	def doNonExportProcess(self,src,dest):
		self.doExportProcess(src,dest)
		
class OutputProcessor(TagProcessor):
	'''
	# #<< key
	'''
	def doExportProcess(self, src, dest):
		line = src.next
		express_list = line.split()
		if len(express_list) == 3:
			value = ContextManager().getDefineValue(express_list[2])
			dest.write(line.replace(express_list[2],str(value)).replace("#<<",express_list[2] + " =="))

	def doNonExportProcess(self, src, dest):
		self.doExportProcess(src, dest)
		
class OutputGlobalProcessor(OutputProcessor):
	'''
	# #<< global key
	# GLOBAL key == value
	'''
	def doExportProcess(self, src, dest):
		line = src.next
		express_list = line.split()
		if len(express_list) == 4:
			key = express_list[3]
			value = ContextManager().getGlobalDefine(key)
			dest.write(line.replace(key,"").replace("global","").replace("#<<","GLOBAL " + key + " == " + str(value)))
	
class UnknownProcessor(TagProcessor):
	'''
	Do nothing
	'''
	pass

	
#############################################################
#
# Define tag selector
#
#############################################################

class TagSelector(object):

	"""This is a tag selector. It can return a tag processor with a sample string"""
	__tag_processors_tuple = (
							DefineProcessor(DefineBooleanParser()),
							DefineProcessor(DefineIntegerParser()),
							DefineProcessor(DefineFloatParser()),
							DefineProcessor(DefineStringParser()),
							
							DefineGlobalProcessor(DefineGlobalBooleanParser()),
							DefineGlobalProcessor(DefineGlobalIntegerParser()),
							DefineGlobalProcessor(DefineGlobalFloatParser()),
							DefineGlobalProcessor(DefineGlobalStringParser()),
							
							IfdefProcessor(),
							IfndefProcessor(),
							
							ElseProcessor(),
							EndifProcessor(),
							OutputProcessor(),
							OutputGlobalProcessor(),
							IncludeProcessor(),
							UnknownProcessor()	
							)
	__compile_list = None
	
	@classmethod
	def setComment(cls,comment):
		
		__str_pattern_tuple = (
					# #define bool true
					"^\\s*" + comment + "\\s*#define\\s+[A-Za-z_]+\\w*\\s+((true)|(True)|(TRUE)|(false)|(False)|(FALSE)){1}\\s*$",
					# #define int 123
					"^\\s*" + comment + "\\s*#define\\s+[A-Za-z_]+\\w*\\s+[+-]?\\d+\\s*$",
					# #define float 123.4
					"^\\s*" + comment + "\\s*#define\\s+[A-Za-z_]+\\w*\\s+[+-]?\\d+(\\.?\\d+){1}\\s*$",
					# #define str "hello world"
					"^\\s*" + comment + "\\s*#define\\s+[A-Za-z_]+\\w*\\s+\".+\"\\s*$",
					
					# #define global bool true
					"^\\s*" + comment + "\\s*#define\\s+global\\s+[A-Za-z_]+\\w*\\s+((true)|(True)|(TRUE)|(false)|(False)|(FALSE)){1}\\s*$",
					# #define global int 123
					"^\\s*" + comment + "\\s*#define\\s+global\\s+[A-Za-z_]+\\w*\\s+[+-]?\\d+\\s*$",
					# #define global float 123.4
					"^\\s*" + comment + "\\s*#define\\s+global\\s+[A-Za-z_]+\\w*\\s+[+-]?\\d+(\\.?\\d+){1}\\s*$",
					# #define global str "hello world"
					"^\\s*" + comment + "\\s*#define\\s+global\\s+[A-Za-z_]+\\w*\\s+\".+\"\\s*$",
					
					# #ifdef
					"^\\s*" + comment + "+\\s*#ifdef\\s+.+$",
					# #ifndef
					"^\\s*" + comment + "+\\s*#ifndef\\s+.+$", 

					# #else
					"^\\s*" + comment + "\\s*#else\\s*$",
					# #endif
					"^\\s*" + comment + "\\s*#endif\\s*$",
					# #<< param
					"^\\s*" + comment + "\\s*#<<\\s+[A-Za-z_]+\\w*\\s*$",
					# #<< global param
					"^\\s*" + comment + "\\s*#<<\\s+global\\s+[A-Za-z_]+\\w*\\s*$",
					# #include file
					"^\\s*" + comment + "\\s*#include\\s+\".+\"\\s*$",
					# #whatever else
					"^\\s*" + comment + "\\s*#.+\\s*$"
					)
				
		cls.__compile_list = map(lambda x: re.compile(x),__str_pattern_tuple)
			
	@classmethod
	def getTagProcessor(cls, sample):

		
		for index,c in enumerate(cls.__compile_list):
			
			if c.match(sample):
				#print " %s ========>> match" % sample.rstrip("\r\n\t ")
				return cls.__tag_processors_tuple[index]
		return None
	
		
	def showPatterns(self):
		print self.__class__.__compile_list

#############################################################
#
# Define express selector
#
#############################################################

class ExpressSelector(object):

	"""This is a tag selector. It can return a tag processor with a sample string"""
	__express_processors_tuple = (
							
							BooleanParser(),
							IntegerParser(),
							FloatParser(),
							StringParser(),
							ValueParser(),
							OnlyKeyParser(),
							)
		
	__str_pattern_tuple = (
							
							"(global\\s+)?[A-Za-z_]+\\w*\\s+(((==)|(!=))+\\s+((true)|(True)|(TRUE)|(false)|(False)|(FALSE)){1})$",
							"(global\\s+)?[A-Za-z_]+\\w*\\s+(((==)|(!=)|(<=)|(>=)|(<)|(>)){1}\\s+[+-]?\\d+)$",
							"(global\\s+)?[A-Za-z_]+\\w*\\s+(((==)|(!=)|(<=)|(>=)|(<)|(>)){1}\\s+[+-]?\\d+(\\.\\d+){1})$",
							"(global\\s+)?[A-Za-z_]+\\w*\\s+(((==)|(!=)|(<=)|(>=)|(<)|(>)){1}\\s+\".+\")$",
							"(global\\s+)?[A-Za-z_]+\\w*\\s+(((==)|(!=)|(<=)|(>=)|(<)|(>)){1}\\s+(global\\s+)?[a-zA-Z_]+\\w*)$",
							"(global\\s+)?[A-Za-z_]+\\w*$",
						)
								
	__compile_list = map(lambda x: re.compile(x),__str_pattern_tuple)
			
	@classmethod
	def getExpressProcessor(cls, sample):

		for index,c in enumerate(cls.__compile_list):
			
			if c.match(sample):
				#print " %s ========>> match" % sample.rstrip("\r\n\t ")
				return cls.__express_processors_tuple[index]
		return None
	
		
	def showPatterns(self):
		print self.__class__.__compile_list

#############################################################
#
# Define CheckSyntax
#
#############################################################
class SyntaxCheck(object):

	__types_tokens = {
				IfdefProcessor : "#ifdef",
				IfndefProcessor : "#ifndef",
				ElseProcessor : "#else",
				EndifProcessor :"#endif" ,
				}
    
	def __init__(self, srcfile):
		self.__srcfile = srcfile
		self.__src = open(srcfile, "r")
		self.__token_stack = []

	def check(self):
		
		try:
			it = FileIterator(self.__src)
			self.__number_line = 0
			while it.hasMore:
				self.__number_line += 1
				self.__current_line = it.next
				p = TagSelector.getTagProcessor(self.__current_line)
				if p:
					if isinstance(p, UnknownProcessor):
						raise SyntaxError, self.__create_exception_string(" Expect one  #ifdef ,  #ifndef ,  #else  or  #endif ")
					else:
						token = self.__types_tokens.get(type(p),None)
						if token:
							self.__analyseToken(token)
			
			if self.__token_stack:
				self.__number_line += 1
				self.__current_line = "\r\n"
				raise SyntaxError, self.__create_exception_string(" Expect #endif")

			print "======>> syntax check done. src = %s" % self.__srcfile 
			return True
		finally:
			self.__src.close()
			
	def __analyseToken(self,token):
		
		if token in ["#ifdef" , "#ifndef"]:
			self.__check_ifdef_ifndef(token);
		elif token == "#else":
			self.__check_else(token)
		elif token == "#endif":
			self.__check_endif(token)
    
	def __check_ifdef_ifndef(self,token):
		
		if "#ifdef" in self.__current_line:
			index = self.__current_line.find("#ifdef")
			or_express_list = self.__current_line[index + 6:].split("or")
		elif "#ifndef" in self.__current_line:
			index = self.__current_line.find("#ifndef")
			or_express_list = self.__current_line[index + 7:].split("or")
			
		for and_express in or_express_list:
			express_list = and_express.split("and")
			for express in express_list:
				express = express.strip("\r\n\t ")
				if not ExpressSelector.getExpressProcessor(express):
					raise SyntaxError, self.__create_exception_string(" Illegale Express = %s" % express)
		self.__token_stack.append(token)
        
	def __check_else(self,token):
    
		if not self.__token_stack:
			raise SyntaxError, self.__create_exception_string(" Expect one  #ifdef  or  #ifndef  before the current line")
					
		top_token = self.__token_stack[-1]
		if top_token in ["#ifdef" , "#ifndef"]:
			self.__token_stack.append(token)
		else:
			raise SyntaxError, self.__create_exception_string(" Expect one  #ifdef  or  #ifndef  before the current line")
		
	def __check_endif(self,token):

		if not self.__token_stack:
			raise SyntaxError, self.__create_exception_string(" Expect one  #ifdef ,  #ifndef  or  #else  before the current line")
					
		top_token = self.__token_stack[-1];
		if top_token in ["#ifdef" , "#ifndef"]:
			# pop ifdef or ifndef
			self.__token_stack.pop()
		elif top_token == "#else":
			# pop else
			self.__token_stack.pop()
			# pop ifdef or ifndef
			self.__token_stack.pop()
		else:
			raise SyntaxError, self.__create_exception_string(" Expect one  #ifdef ,  #ifndef  or  #else  before the current line")

	def __create_exception_string(self,detail):
		
		out = cStringIO.StringIO()
		out.write("\r\n");
		out.write("[SyntaxError]:\r\n");
		out.write("[File]: ");
		out.write(self.__srcfile);
		out.write("\r\n[Line]: ");
		out.write(str(self.__number_line));
		out.write("\r\n[Content]: ");
		out.write(self.__current_line);
		out.write("[Error]:");
		out.write(detail);
		out.write("\r\n");
		msg = out.getvalue()
		out.close()
		return msg

#############################################################
#
# Define some methods for preprocessing
#
#############################################################

def do_preprocess(options):
	
	if not os.path.exists(options["srcdir"]):
		raise Exception, "%s does not exist." % options["srcdir"]
	
	if not os.path.exists(options["todir"]):
		os.mkdir(options["todir"])
	
	cm = ContextManager()
	cm.set_options(options)
	TagSelector.setComment(options.get("comment","#"))
	
	#process global.def first
	global_def_fullpath = options["global"]
	print "======>> using global file = %s" % global_def_fullpath
	if os.path.exists(global_def_fullpath):
		filename = os.path.split(global_def_fullpath)[1]
		_processfile(global_def_fullpath,os.path.join(options["todir"],filename))
	else:
		print "======>> fail to find global file = %s\r\n======>> skip it....going on" % global_def_fullpath
	
	_preprocess(options["srcdir"])

		
def _processfile(srcfile, tofile):
	
	cm = ContextManager()
	if cm.hasFileInDone(srcfile):
		return
	
	print '======>> processing src = %s dest = %s' % (srcfile, tofile)
	
	checker = SyntaxCheck(srcfile)
	if not checker.check():
		return
	
	cm.namespace_of_currentfile = srcfile
	
	src = open(srcfile, "r")
	dest = open(tofile, "w")
	it = FileIterator(src)
	while it.hasMore:
		line = it.next
		p = TagSelector.getTagProcessor(line)
		if p:
			p.process(it, dest)
		else:
			dest.write(line)
	cm.addFileToDone(srcfile)
	src.close()
	dest.close()
	print '======>> done. src = %s ' % srcfile

def _preprocess(srcfile):
	
	cm = ContextManager()
		
	if os.path.isdir(srcfile):
		for file in os.listdir(srcfile):
			fullpath = os.path.realpath(os.path.join(srcfile,file))
			#print fullpath
			if os.path.isfile(fullpath):
				_preprocess(fullpath)
			else:
				old_dir = cm.todir
				new_todir = os.path.join(old_dir, file)
				#print new_todir
				if not os.path.exists(new_todir):
					os.mkdir(new_todir)
				cm.todir = new_todir
				_preprocess(fullpath)
				cm.todir = old_dir
	else:
		filename = os.path.basename(srcfile)
		todir = os.path.join(cm.todir, filename)
		#do preprocess
		_processfile(srcfile, todir)		
    		
		
def usage():
	
	print """HELP for pypc:
	python pypc.py -s srcfile [-d destdir [-e [-i initfile [-m comment ]]]]
	-s source file/dir
	-d destination dir. default is a dir named "done" which is in the same path with the source dir
	-e flag to export, setting it is to export without all useless code blocks, otherwise, just to comment all useless code blocks
	-i define a initfile, default is "global.def" which is in the same path with the source dir
	-m define a character for comment, default is "#"
"""

def main():
	
	try:
		opts, args = getopt.getopt(sys.argv[1:], "s:d:ei:m:")

		if not opts or '-s' not in map(lambda x:x[0],opts):
			usage()
			sys.exit(2)
	
	except getopt.GetoptError:
		# print help information and exit:
		usage()
		sys.exit(2)
	 
	base_dir = os.getcwd()

	options = {
					"srcdir" : base_dir,
					"todir"	: os.path.join(base_dir ,"done"),
					"global" : os.path.join(base_dir,"global.def")
				}
	for opt,arg in opts:
		
		if opt == '-s':
			if os.path.isabs(arg):
				options["srcdir"] = arg
			else:
				options["srcdir"] = os.path.join(base_dir,arg)
		
		elif opt == "-d":
			if os.path.isabs(arg):
				options["todir"] = arg
			else:
				options["todir"] = os.path.join(base_dir,arg)
		elif opt == "-e":
			options["export"] = True
		elif opt == "-i":
			if os.path.isabs(arg):
				options["global"] = arg
			else:
				options["global"] = os.path.join(base_dir,arg)
		elif opt == "-m":
			options["comment"] = arg
							
	do_preprocess(options)

	return 0

if __name__ == '__main__':
	main()

