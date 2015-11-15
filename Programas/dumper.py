#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tempfile
import os
import sys
import struct
import array
import shutil
import datetime

from pytable import normal_table
from libs import lzss

fat_address = 0x13fa00

filenames = ['e000.txt', 'e100.txt', 'e200.txt', 'etext.txt', 'htext.txt', 'itext.txt', 'otext.txt',
			'q000.txt', 'q050.txt', 'q100.txt', 'tobj.txt', 'stext.txt', 'storytext.txt', 'wifi.txt']
#compressed_data = [0x5d70, 0x5d78, 0x5d80, 0x5d88, 0x5e10, 0x5e38, 0x6618, 0x6620, 0x6628, 0x6680, 0x8218, 0x8240, 0x8520]

filenames2 = ['otext.txt']
uncompressed_data = [0x5e68]
prefix = [['art_d%d.txt', 'art_t%d.txt', 'chr%d.txt', 'laytonv%d.txt', 'laytonvs%d.txt', 'lukev%d.txt', 'lukevs%d.txt', 'music%d.txt', 'n_%d.txt']]
entries2 = [[20, 20, 40, 36, 27, 23, 14, 19, 40]]


def Extract(filename = '2897 - Professor Layton and the Curious Village (E)(M5)(XMS).nds'):
	# Gera a tabela
	table = normal_table('layton.tbl')
	table.fill_with('61=a', '41=A', '30=0')
	table.add_items('0A= ')
	
	romfile = open(filename, 'rb')
	
	print '>> Extraindo Arquivos Comprimidos...'
	for x in range(len(compressed_data)):
		romfile.seek(fat_address + compressed_data[x], 0)
		file_address = struct.unpack('<L', romfile.read(4))[0]

		buffer = lzss.uncompress(romfile, file_address)		
		file = tempfile.NamedTemporaryFile()
		buffer.tofile(file.file)
		# Extraindo os dados do arquivo descomprimido
		file.seek(0,0)
		output = open('../Textos Originais/' + filenames[x], 'wb')
		
		# Lendo o header do arquivo
		base_address = 0x10
		stamp1 = struct.unpack('<L', file.read(4))[0]
		size = struct.unpack('<L', file.read(4))[0]
		entries = struct.unpack('<L', file.read(4))[0]
		stamp2 = struct.unpack('<L', file.read(4))[0]
		
		for entry in range(entries):
			file.seek(base_address, 0)
			# Lendo o header do bloco
			stamp3 = struct.unpack('<L', file.read(4))[0]
			block_lenght = struct.unpack('<L', file.read(4))[0]
			padding = file.read(4)
			string_lenght = struct.unpack('<L', file.read(4))[0]
		
			# L� o nome do bloco e grava no arquivo (nome do bloco tem no m�ximo 16 bytes de tamanho):
			block_name = file.read(16)
			output.write('[')
			for c in block_name:
				if c == '\x00':
					break
				output.write(c)
			output.write(']\r\n')
			# L� a string
			
			d = 0
			while d < string_lenght:
				byte = file.read(1)
				if byte == '@':
					tag = file.read(1)
					if tag == 'p':		# Pause
						output.write('<W>')
					elif tag == 'c': 	# Clear
						output.write('\r\n!------------------------------!\r\n')
					else:
						output.write('<@' + tag + '>')
				elif byte == '\x00':
					break
				elif byte in table:
					output.write(table[byte])
				else:
					output.write('[[%02X]]' % struct.unpack('B', byte)[0])
				d += 1
					
			output.write('\r\n!******************************!\r\n')
	
			base_address += block_lenght
			
			
		file.close()
		output.close()
		
		print '>> \'' + filenames[x] +'\' descomprimido e extraido com sucesso.'
		return
	print '>> Extraindo Arquivos Descomprimidos...'

	for x in range(len(uncompressed_data)):
		romfile.seek(fat_address + uncompressed_data[x], 0)
		base_address = struct.unpack('<L', romfile.read(4))[0]
		output = open('../Textos Originais/' + filenames2[x], 'wb')
		for y in range(len(prefix[x])):
			# Gera a lista de nomes dos arquivos...
			names = [prefix[x][y] % (d+1) for d in range(entries2[x][y])]
			# ...e organiza alfabeticamente
			names.sort(key = str.lower)
			# Hora da extra��o:
			for name in names:
				romfile.seek(base_address, 0)
				output.write('[%s]\r\n' % name)
				while True:
					byte = romfile.read(1)
					if byte == '@':
						tag = romfile.read(1)
						if tag == 'p':		# Pause
							output.write('<W>')
						elif tag == 'c': 	# Clear
							output.write('\r\n!------------------------------!')
						else:
							output.write('<@' + tag + '>')
					elif byte == '\xff':
						break
					elif byte in table:
						output.write(table[byte])
					else:
						output.write('[[%02X]]' % struct.unpack('B', byte)[0])
				output.write('\r\n!******************************!\r\n')
				base_address += 0x200	
		print '>> \'' + filenames2[x] +'\' extraido com sucesso.'
	
		
	romfile.close()
		
	return
	
def Insert():
	table = normal_table('layton.tbl')
	table.fill_with('61=a', '41=A', '30=0')	
	table.set_mode('inverted')
	
	# print '>> Criando Backup...'
	# shutil.copy('PLayton.nds', 'PLayton (BR).nds')	
	
	# romfile = open('PLayton (BR).nds', 'r+b')
	
	# romfile.seek(0x80, 0)
	# init_address = struct.unpack('<L', romfile.read(4))[0]
	# init_address += init_address % 4
	
	print '>> Comprimindo e Inserindo Arquivos...'
	
	for txtname in os.listdir('../Textos Traduzidos e Revisados'):
		if txtname in filenames:	
			file = open('../Textos Traduzidos e Revisados/' + txtname, 'rb')
			head, tail  = os.path.split(txtname)
			f, ext = tail.split('.')	
			comp = open('../Arquivos Gerados/' + f + '.dec', 'w+b')
			
			tbuffer = {}
			w = 0

			blocks = []
			
			for line in file:
				try:
					line = line.strip('\r\n')
					if line.startswith('[') and line.endswith(']'):
						name = line[1:-1]
						while len(name) % 16 != 0:
							name += '\x00'
						buffer = array.array('c')
					elif not line:
						buffer.extend('\x0a')
					elif line == '!------------------------------!':
						buffer.extend('@c')
					elif line == '!******************************!':
						buffer.pop()
						blocks.append((name, buffer))
						# Escreve a sa�da no arquivo
					else:
						x = 0 # Inicializa o tamanho da frase
						while x < (len(line)):
							if line[x] == '<':
								tag = ''
								while line[x] != '>':
									tag += line[x]
									x += 1				
								tag += line[x]
								x += 1
								if tag[1:-1] == 'W':
									buffer.extend('@p')
								else:
									buffer.extend(tag[1:-1])
							elif line[x:x+2] == '[[':
								tag = ''
								while line[x-1:x+1] != ']]':
									tag += line[x]
									x += 1				
								tag += line[x]
								x += 1
								buffer.extend(chr(int(tag[2:-2], 16)))								
							else:
								buffer.extend(table[line[x]])
								x += 1
						buffer.extend('\x0a')
				except:
					print '\t<< ',line

			# Hora de gerar o arquivo de sa�da
			base_address = 0x10
			comp.write(struct.pack('<L', 0x10)) 		# STAMP1
			comp.write(struct.pack('<L', 0))		# SIZE... ser� corrigido depois
			comp.write(struct.pack('<L', len(blocks)))	# Entradas
			comp.write('LPCK')							# STAMP2
			
			for data in blocks:
				comp.write(struct.pack('<L', 0x20))
				comp.write(struct.pack('<L', 0x10 + len(data[0]) + len(data[1]) + (16 - len(data[1]) % 16)))
				comp.write(struct.pack('<L', 0))
				comp.write(struct.pack('<L', len(data[1])))
				comp.write(data[0])
				comp.write(data[1])
				comp.write('\x00' * (16 - len(data[1]) % 16))
				
			comp.seek(4, 0)
			comp.write(struct.pack('<L', os.path.getsize(comp.name)))
				
			buffer = lzss.compress(comp)
			comp.close()
			
			output = open('../Arquivos Comprimidos/' + f + '.pcm', 'w+b')
			buffer.tofile(output)		
			output.close()
			
			# romfile.seek(init_address, 0)
			# buffer.tofile(romfile)
			
			# romfile.seek(fat_address + compressed_data[filenames.index(txtname)], 0)
			# romfile.write(struct.pack('<L', init_address))
			# romfile.write(struct.pack('<L', init_address + len(buffer)))
			
			# init_address += len(buffer)
			# init_address += init_address % 4		
			
			print '>> \'' + f + '.pcm\' gerado e comprimido com sucesso.'
			
			file.close()
		else:
			pass
			
	# for txtname in os.listdir('Textos Traduzidos'):
		# if txtname in filenames2:	
			# pass
		# pass

	#Atualiza o tamanho da rom
	# romfile.seek(0x80, 0)
	# romfile.write(struct.pack('<L', init_address))
	#Atualiza o CRC do header
	# romfile.seek(0x00, 0)
	# string = romfile.read(0x15E)
	# crc = Crc16(string)
	
	# romfile.seek(0x15E, 0)
	# romfile.write(struct.pack('<H', crc))
		
	# romfile.close()

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
	
def GeneratePatch():
	time = datetime.datetime.now()

	cmd = '"xDelta\\xdelta.exe" -efs "2897 - Professor Layton and the Curious Village (E)(M5)(XMS).nds" "PLayton (BR).nds" "%%cd%%\\Patches\\laypton.pt-br.%02d.%02d.xdelta"'
	cmdfile = '@echo off\necho Gerando Patch...\n'
	
	cmdfile += cmd%(time.month, time.day)
	
	cmdfile += '\necho Patch Gerado com sucesso.\npause'
	
	open('Layton.bat','w').write(cmdfile)
	os.system('Layton.bat')	
	os.unlink('Layton.bat')
		
if __name__ == "__main__":
	#import psyco
	#psyco.full()
	
	print 'Layton\'s Dumper - Monkeys Traducoes 2010'
	opt = int(raw_input(" [1] Extrair \n [2] Inserir \n [3] Sair \n>> "))
	
	if opt == 1:
		Extract()
	elif opt == 2:
		Insert()
		# GeneratePatch()
	elif opt == 3:
		sys.exit(1)
	sys.exit(1)
