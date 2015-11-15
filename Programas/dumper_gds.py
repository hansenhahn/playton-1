#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
import os
import sys
import struct
import array
import shutil
import datetime
import binascii
import re

from pytable import normal_table

def Extrai_GDS():

	for name in os.listdir("GDS en"):
		pfile = open(os.path.join("GDS en", name), "rb")
		# O tamanho do arquivo - 6
		psize = struct.unpack("<L", pfile.read(4))[0] - 2

		tfile = open(os.path.join("../Textos Originais - GDS", "%s.txt" % name.split(".")[0]), "wb")
		
		while ((pfile.tell() - 4) < psize):
			# Sempre 0x00BA0000 ??
			stamp1 = struct.unpack("<L", pfile.read(4))[0]
			if (stamp1 == 0x00BA0000) or (stamp1 == 0x00CF0000):
				# Sempre 0x0001 ??
				stamp2 = struct.unpack("<H", pfile.read(2))[0] 
				# Entrada
				entry = struct.unpack("<L", pfile.read(4))[0]
				# Sempre 0x0003 ??
				stamp3 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]
				
				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write(pfile.read(lenght - 1))
				tfile.write("\r\n<%08X>" % entry)
				tfile.write("\r\n!******************************!\r\n")			
				pfile.seek(1, 1)
			elif (stamp1 == 0x00BC0000)  or (stamp1 == 0x00BD0000):
				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write("%s" % binascii.hexlify(pfile.read(54)))
				tfile.write("\r\n!******************************!\r\n")
			elif (stamp1 == 0x00C60000) or (stamp1 == 0x00C80000):
				# Sempre 0x0003 ??
				stamp2 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]

				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write(pfile.read(lenght - 1).replace("\x0A", "\r\n"))
				#tfile.write("\r\n<%04X>" % entry)
				tfile.write("\r\n!******************************!\r\n")			
				pfile.seek(1, 1)			
			elif (stamp1 == 0x00C70000) or (stamp1 == 0x00C90000):
				# Sempre 0x0003 ??
				stamp2 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]

				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write(pfile.read(lenght - 1).replace("\x0A", "\r\n"))
	
				pfile.seek(1, 1)
				
				# Sempre 0x0001 ??
				stamp3 = struct.unpack("<H", pfile.read(2))[0]
				# Entrada
				entry = struct.unpack("<L", pfile.read(4))[0]
				tfile.write("\r\n<%08X>" % entry)
				tfile.write("\r\n!******************************!\r\n")

			elif (stamp1 == 0x00CA0000) or (stamp1 == 0x00CB0000):
				# Sempre 0x0003 ??
				stamp2 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]

				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write(pfile.read(lenght - 1).replace("\x0A", "\r\n"))
	
				pfile.seek(1, 1)
				# Sempre 0x0001
				stamp3 = struct.unpack("<H", pfile.read(2))[0]
				# Entrada
				entry = struct.unpack("<L", pfile.read(4))[0]
				tfile.write("\r\n<%08X>" % entry)
				tfile.write("\r\n!******************************!\r\n")		
				# Sempre 0x00000001
				stamp4 = struct.unpack("<L", pfile.read(4))[0]
				pfile.seek(2, 1)	
			
			elif (stamp1 == 0x00DC0000):
				# Sempre 0x0001 ??
				stamp2 = struct.unpack("<H", pfile.read(2))[0] 
				# Entrada
				entry = struct.unpack("<L", pfile.read(4))[0]			
				# Sempre 0x0003 ??
				stamp3 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]
				
				tfile.write("[%08X]\r\n" % stamp1)
				tfile.write(pfile.read(lenght - 1))
				tfile.write("\r\n")
				pfile.seek(1, 1)
				# Sempre 0x0003 ??
				stamp3 = struct.unpack("<H", pfile.read(2))[0]
				# Largura da string
				lenght = struct.unpack("<H", pfile.read(2))[0]			
				
				tfile.write(pfile.read(lenght - 1))
				tfile.write("\r\n<%08X>" % entry)
				tfile.write("\r\n!******************************!\r\n")			
				pfile.seek(1, 1)
				
			else:
				print "%08X" % stamp1

				
		tfile.close()
		pfile.close()
	
	return
	
def Empacota_GDS():
	for name in os.listdir("../Textos Traduzidos e Revisados - GDS"):
		tfile = open(os.path.join("../Textos Traduzidos e Revisados - GDS", name), "rb")
		pfile = open(os.path.join("../Arquivos GDS", "%s.gds" % name.split(".")[0]), "wb")
		
		pfile.seek(4, 1)	# Será preenchido depois		
		for line in tfile:
			line = line.strip('\r\n')
			if re.match(r'^\[.+\]$', line):
				stamp = int(re.split(r'^\[(.+)\]$', line)[1], 16)
				buffer = array.array('c')
				buffer1 = array.array('c')
			elif re.match(r'^\<.+\>$', line):
				entry = int(re.split(r'^\<(.+)\>$', line)[1], 16)
			elif re.match(r'^!\D{30}!$', line):
				if (stamp == 0x00CA0000) or (stamp == 0x00CB0000):
					buffer.extend("\x00")
					pfile.write(struct.pack("<L", stamp))
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer)))
					buffer.tofile(pfile)
					pfile.write(struct.pack("<H", 0x0001))
					pfile.write(struct.pack("<L", entry))
					pfile.write(struct.pack("<L", 0x00000001))
					pfile.write(struct.pack("<H", 0x0000))
				elif (stamp == 0x00BC0000) or (stamp == 0x00BD0000):
					pfile.write(struct.pack("<L", stamp))
					buffer.tofile(pfile)
				elif (stamp == 0x00C60000) or (stamp == 0x00C80000):
					buffer.extend("\x00")
					pfile.write(struct.pack("<L", stamp))
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer)))
					buffer.tofile(pfile)
				elif (stamp == 0x00C70000) or (stamp == 0x00C90000):
					buffer.extend("\x00")
					pfile.write(struct.pack("<L", stamp))
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer)))
					buffer.tofile(pfile)
					pfile.write(struct.pack("<H", 0x0001))
					pfile.write(struct.pack("<L", entry))
				elif (stamp == 0x00BA0000) or (stamp == 0x00CF0000):
					buffer.extend("\x00")
					pfile.write(struct.pack("<L", stamp))
					pfile.write(struct.pack("<H", 0x0001))
					pfile.write(struct.pack("<L", entry))
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer)))
					buffer.tofile(pfile)
				elif (stamp == 0x00DC0000):
					buffer.extend("\x00")
					buffer1.extend("\x00")
					pfile.write(struct.pack("<L", stamp))
					pfile.write(struct.pack("<H", 0x0001))
					pfile.write(struct.pack("<L", entry))
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer)))
					buffer.tofile(pfile)
					pfile.write(struct.pack("<H", 0x0003))
					pfile.write(struct.pack("<H", len(buffer1)))
					buffer1.tofile(pfile)						
			else:
				if (stamp == 0x00BC0000) or (stamp == 0x00BD0000):
					buffer.extend(binascii.unhexlify(line))
				elif (stamp == 0x00DC0000):
					if not buffer:
						buffer.extend(line.replace("ã", "ä"))
					else:
						buffer1.extend(line.replace("ã", "ä"))				
				else:
					if buffer:
						buffer.extend("\x0a" + line.replace("ã", "ä"))
					else:
						buffer.extend(line.replace("ã", "ä"))

		pfile.write("\x0c\x00")
		lenght = pfile.tell()
		pfile.seek(0, 0)
		pfile.write(struct.pack("<L", lenght - 4))
		
		tfile.close()
		pfile.close()
		

	return
	
if __name__ == "__main__":
	#Extrai_GDS()
	Empacota_GDS()
		

		
		
		
		
	
	
	
	
	
	
	


	
