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

        setattr(self, "rom", rom)

        self.read_header()

    def close(self):
        self.rom.close()

    def __str__(self):
        return '''\
Game Title: %s
Gamecode: %s
Makercode: %s
Unitcode: %s
Encryption Seed Select: %s
Device Capacity: %s bytes
''' % (self.header["game_title"], self.header["gamecode"], self.header["makercode"],
       self.header["unitcode"], self.header["encryption_seed"], 128*1024*2**self.header["device_capacity"])

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

        # Continuar adicionando dados no header - Hansen
        self.rom.seek(0x40)
        self.header.update({"fnt_address": struct.unpack('<L', self.rom.read(4))[0]})
        self.header.update({"fnt_size": struct.unpack('<L', self.rom.read(4))[0]})
        self.header.update({"fat_address": struct.unpack('<L', self.rom.read(4))[0]})
        self.header.update({"fat_size": struct.unpack('<L', self.rom.read(4))[0]})

    def read_file_address_table(self):
        self.rom.seek(self.header["fat_address"], 0)

        map = mmap.mmap(-1, self.header["fat_size"])
        map.write(self.rom.read(self.header["fat_size"]))
        map.seek(0,0)

        self.address_table = []
        for x in range(len(map)/8):#map.size()/8):
            begin = struct.unpack('<L', map.read(4))[0]
            end = struct.unpack('<L', map.read(4))[0]
            self.address_table.append((begin, (end - begin)))

        map.close()
        return self.address_table

    def read_file_name_table(self):
        def read_folder_struct(data):
            sub_table_address = struct.unpack('<L', data.read(4))[0]
            first_file_id = struct.unpack('<H', data.read(2))[0]
            data.read(2)

            address = data.tell()
            data.seek(sub_table_address, 0)

            folder = []
            while True:
                byte = struct.unpack('B', data.read(1))[0]
                if byte == 0:
                    break
                type = (byte >> 7) & 0x1
                lenght = (byte & 0x7F)
                if type == 1:
                    name = data.read(lenght)
                    id = struct.unpack('<H', data.read(2))[0] # Precisarei usar??
                    folder.append((name, []))
                else:
                    name = data.read(lenght)
                    folder.append((name, first_file_id))
                    first_file_id += 1

            data.seek(address, 0)

            _folder = []
            for x in folder:
                if isinstance(x[1], list):
                    _folder.append((x[0], read_folder_struct(data)))
                else:
                    _folder.append(x)
            return _folder

        def create_name_table(folder, path, path_list):
            for f in folder:
                if isinstance(f[1], list):
                    create_name_table(f[1], path + f[0] + "/", path_list)
                else:
                    path_list.append((path + f[0], f[1]))
            return path_list

        self.rom.seek(self.header["fnt_address"], 0)

        map = mmap.mmap(-1, self.header["fnt_size"])
        map.write(self.rom.read(self.header["fnt_size"]))
        map.seek(0,0)

        self.name_table = create_name_table(read_folder_struct(map), "", [])

        map.close()
        return self.name_table

		
def scandirs(path):
	files = []
	for currentFile in glob.glob( os.path.join(path, '*') ):
		if os.path.isdir(currentFile):
			files += scandirs(currentFile)
		else:
			files.append(currentFile)
	return files
	
def Crc16(string):
	polynomial = 0xA001
	
	table = array.array('H')
	#Geração dos polinômios
	for byte in range(256):
		crc = 0
		for bit in range(8):
			if (byte ^ crc) & 1:
				crc = (crc >> 1) ^ polynomial
			else:
				crc >>= 1
			byte >>= 1
		table.append(crc)

	#Cálculo do CHECKSUM
	crc = 0xffff
	for x in string:
		crc = (crc >> 8) ^ table[(crc ^ ord(x)) & 0xff]
		
	return crc
		
def parseCSV( file = "file_list.csv" ):
	fd = open( file, "r" )
	fdict = {}
	for f in fd.readlines():
		f = f.replace('\n', '')
		path,ffile = f.split(';')
		fdict[ffile] = path
		
	fd.close()
	return fdict
		
		
	
		
if __name__ == "__main__":
	
	rom = NdsRom(ROMFILE)
	
	addr = rom.header["fat_address"]
	
	fat = rom.read_file_address_table()
	fnt = rom.read_file_name_table()
	
	a = map(lambda x: "%08X" % x, sorted(map(lambda x: x[0], fat)))
	
	rom.rom.close()
	
	files = scandirs("../All Files")
	
	dict = {}
	for x in range(len(fnt)):
		dict.update({fnt[x][0]:x+1})
		
	init = 0x49E0060
	
	ret = parseCSV()
		
	#raw_input()
		
	file = open(ROMFILE, "r+b")
	for name in files:
		with open(name, "rb") as f:
			buffer = array.array("c", f.read())
			
			file.seek(init, 0)
			begin = file.tell()
			buffer.tofile(file)
			end = file.tell()
			
			init += len(buffer)
			while init % 0x200 != 0:
				init += 1

			nm = os.path.basename(name); print ret
			name = os.path.join(ret[nm] , nm)				
						
				
			print name, dict[name.replace("\\", "/")] 
			file.seek(addr + (dict[name.replace("\\", "/")] * 8), 0)
			file.write(struct.pack("<L", begin))
			file.write(struct.pack("<L", end))
			
	file.seek(0x80, 0)
	file.write(struct.pack('<L', end))
	#Atualiza o CRC do header
	file.seek(0x00, 0)
	string = file.read(0x15E)
	crc = Crc16(string)
	
	file.seek(0x15E, 0)
	file.write(struct.pack('<H', crc))
	
	file.close()
			
			
	
	
	
	
