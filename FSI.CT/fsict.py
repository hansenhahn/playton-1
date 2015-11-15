#!/usr/bin/env python
# -*- coding: utf-8 -*-

# nds.py

# Copyright 2010/11 Diego Hansen Hahn (aka DiegoHH) <diegohh90 [at] hotmail [dot] com>

# Nitro VieWeR is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License.

# Nitro VieWeR is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Nitro VieWeR. If not, see <http://www.gnu.org/licenses/>.

import array
import mmap
import struct
import os
import glob

ROMFILE = "../Output/2897 - Professor Layton and the Curious Village (E)(M5)(XMS).nds"

nintendo_logo = "\
\x24\xff\xae\x51\x69\x9a\xa2\x21\x3d\x84\x82\x0a\x84\xe4\x09\xad\
\x11\x24\x8b\x98\xc0\x81\x7f\x21\xa3\x52\xbe\x19\x93\x09\xce\x20\
\x10\x46\x4a\x4a\xf8\x27\x31\xec\x58\xc7\xe8\x33\x82\xe3\xce\xbf\
\x85\xf4\xdf\x94\xce\x4b\x09\xc1\x94\x56\x8a\xc0\x13\x72\xa7\xfc\
\x9f\x84\x4d\x73\xa3\xca\x9a\x61\x58\x97\xa3\x27\xfc\x03\x98\x76\
\x23\x1d\xc7\x61\x03\x04\xae\x56\xbf\x38\x84\x00\x40\xa7\x0e\xfd\
\xff\x52\xfe\x03\x6f\x95\x30\xf1\x97\xfb\xc0\x85\x60\xd6\x80\x25\
\xa9\x63\xbe\x03\x01\x4e\x38\xe2\xf9\xa2\x34\xff\xbb\x3e\x03\x44\
\x78\x00\x90\xcb\x88\x11\x3a\x94\x65\xc0\x7c\x63\x87\xf0\x3c\xaf\
\xd6\x25\xe4\x8b\x38\x0a\xac\x72\x21\xd4\xf8\x07"

arm9 = "arm9.bin"
arm9ovltable = "arm9ovltable.bin"
arm7 = "arm7.bin"
arm7ovltable = "arm7ovltable.bin"

banner = "banner.bin"
fat = "fat.bin"
fnt = "fnt.bin"

ndsheader = "ndsheader.bin"

ovlname7 = "overlay7_%04d.bin"
ovlname9 = "overlay9_%04d.bin"

def Crc16(string):
	polynomial = 0xA001
	
	table = array.array('H')
	#Gera��o dos polin�mios
	for byte in range(256):
		crc = 0
		for bit in range(8):
			if (byte ^ crc) & 1:
				crc = (crc >> 1) ^ polynomial
			else:
				crc >>= 1
			byte >>= 1
		table.append(crc)

	#C�lculo do CHECKSUM
	crc = 0xffff
	for x in string:
		crc = (crc >> 8) ^ table[(crc ^ ord(x)) & 0xff]
		
	return crc

class DataStructure:
	def __init__(self, addr, data):
		self.addr = addr
		self.data = data

class NdsRom(object):
	def __init__(self, filename):
		rom = open(filename, 'rb')

		rom.seek(0xC0, 0)
		if rom.read(156) != nintendo_logo:
			rom.close()
			raise TypeError("Missing Nintendo's Logo. File is not a NDS ROM.")

		if rom.read(2) != "\x56\xcf":
			rom.close()
			raise TypeError("Invalid Checksum. File is not a NDS ROM.")

		self.rom = rom
		self.read_header()

	def close(self):
		self.rom.close()

	def read_header(self):
		if not hasattr(self, "rom"):
			raise AttributeError()

		self.header = {}
		self.rom.seek(0,0)
		self.header.update({"game_title": self.rom.read(12)})
		self.header.update({"gamecode": self.rom.read(4)})
		self.header.update({"makercode": self.rom.read(2)})
		self.header.update({"unitcode": struct.unpack('B', self.rom.read(1))[0]})
		self.header.update({"encryption_seed": struct.unpack('B', self.rom.read(1))[0]})
		self.header.update({"device_capacity": struct.unpack('B', self.rom.read(1))[0]})
		self.rom.read(9)
		
		self.rom.seek(0x20)
		# ARM9 data
		self.header.update({"arm9_bin_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm9_exec_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm9_ram_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm9_bin_lenght" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		# ARM7 data
		self.header.update({"arm7_bin_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm7_exec_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm7_ram_address" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm7_bin_lenght" : ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		# FNT data
		self.header.update({"fnt_address": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"fnt_lenght": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		# FAT data
		self.header.update({"fat_address": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"fat_lenght": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		# ARM9 Overlay data
		self.header.update({"arm9_overlay_address": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm9_overlay_lenght": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})	
		# ARM7 Overlay data
		self.header.update({"arm7_overlay_address": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.header.update({"arm7_overlay_lenght": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		self.rom.seek(8, 1)
		
		self.header.update({"banner_address": ( self.rom.tell(), struct.unpack('<L', self.rom.read(4))[0] )})
		
	def write_data(self, indata, outdata):
		while outdata.tell() % 0x200 != 0:
			outdata.seek( 1, 1)
		print hex(outdata.tell())
		addr = outdata.tell()
		data = indata.read()
		
		outdata.seek(len(data), 1)
		return DataStructure(addr, data)

	def updatefsi(self):
		with open("fsict.bin", "w+b") as out:
			a = open(ndsheader, "rb")
			out.write(a.read())
			a.close()
					
			with open(arm9, "rb") as fd:
				Arm9Structure = self.write_data(fd, out)

			with open(arm9ovltable, "rb") as fd:
				Arm9OvlStructure = self.write_data(fd, out)							

			with open(arm7, "rb") as fd:
				Arm7Structure = self.write_data(fd, out)
			
			with open(arm7ovltable, "rb") as fd:
				Arm7OvlStructure = self.write_data(fd, out)			
		
			with open(fnt, "rb") as fd:
				FntStructure = self.write_data(fd, out)	

			with open(fat, "rb") as fd:
				FatStructure = self.write_data(fd, out)	

			with open(banner, "rb") as fd:
				BannerStructure = self.write_data(fd, out)	
			
			out.seek(0x80)
			out.seek(struct.unpack('<L', out.read(4))[0])
			with open(ovlname9 % 0, "rb") as fd:
				Ovl9Structure = self.write_data(fd, out)				

			#print hex(Arm9Structure.addr)
			out.seek(Arm9Structure.addr, 0)
			out.write(Arm9Structure.data)
			out.seek(self.header["arm9_bin_address"][0], 0)
			out.write(struct.pack("<L", Arm9Structure.addr))
			out.seek(self.header["arm9_bin_lenght"][0], 0)
			out.write(struct.pack("<L", len(Arm9Structure.data)))		
			
			#print hex(Arm9OvlStructure.addr)
			out.seek(Arm9OvlStructure.addr, 0)
			out.write(Arm9OvlStructure.data)	
			out.seek(self.header["arm9_overlay_address"][0], 0)
			out.write(struct.pack("<L", Arm9OvlStructure.addr))
			out.seek(self.header["arm9_overlay_lenght"][0], 0)
			out.write(struct.pack("<L", len(Arm9OvlStructure.data)))							

			#print hex(Ovl9Structure.addr)
			
			out.seek(Arm7Structure.addr, 0)
			out.write(Arm7Structure.data)
			out.seek(self.header["arm7_bin_address"][0], 0)
			out.write(struct.pack("<L", Arm7Structure.addr))
			out.seek(self.header["arm7_bin_lenght"][0], 0)
			out.write(struct.pack("<L", len(Arm7Structure.data)))				
			
			#print hex(self.header["fnt_address"][0])
			out.seek(FntStructure.addr, 0)
			out.write(FntStructure.data)	
			out.seek(self.header["fnt_address"][0], 0)
			out.write(struct.pack("<L", FntStructure.addr))
			out.seek(self.header["fnt_lenght"][0], 0)
			out.write(struct.pack("<L", len(FntStructure.data)))				

			out.seek(FatStructure.addr, 0)
			out.write(FatStructure.data)
			# Corrige o overlay
			out.seek(FatStructure.addr, 0)
			out.write(struct.pack('<L', Ovl9Structure.addr))
			out.write(struct.pack('<L', Ovl9Structure.addr+len(Ovl9Structure.data)))
				
			out.seek(self.header["fat_address"][0], 0)
			out.write(struct.pack("<L", FatStructure.addr))
			out.seek(self.header["fat_lenght"][0], 0)
			out.write(struct.pack("<L", len(FatStructure.data)))							

			#print hex(self.header["banner_address"][0])
			out.seek(BannerStructure.addr, 0)
			out.write(BannerStructure.data)		
			out.seek(self.header["banner_address"][0], 0)
			out.write(struct.pack("<L", BannerStructure.addr))
			

			end = Ovl9Structure.addr+len(Ovl9Structure.data)			
			
			out.seek( 0x80, 0)
			out.write(struct.pack('<L', end))
			
			out.seek(0,0)
			
			crc = Crc16(out.read(0x15E))
			out.seek(0x15e, 0)
			out.write(struct.pack("<H", crc))
			
			out.seek(0,0)
			with open("2897 - Professor Layton and the Curious Village (E)(M5)(XMS).nds", "r+b") as f:
				f.write(out.read())
				
				f.seek(Ovl9Structure.addr, 0)
				f.write(Ovl9Structure.data)
								
				

if __name__ == "__main__":
	a = NdsRom("ndsheader.bin")
	a.updatefsi()
	a.close()
		