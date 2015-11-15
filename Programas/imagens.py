#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import struct
import array
import os
import sys
import shutil
import tempfile

from libs import lzss, rle, huffman, images, bmp

try:
	import psyco
	psyco.full()
except: pass

def gba2tuple(fd):
	rgb = struct.unpack('<H', fd.read(2))[0] & 0x7FFF
	rgb = map(lambda x,y: float((x >> y) & 0x1F)/31.0, [rgb]*3, [0,5,10])
	return rgb
	
def tuple2gba(color):
	r, g, b = map(lambda x: int(float(x)/255.0*31), color)
	color = ((b << 10) | (g << 5) | r ) & 0x7FFF
	return struct.pack('<H', color)

def unpackBackground():
	outdir = ['../Imagens/_bg/', '../Imagens/_bg/en/']
	for i, dir in enumerate(['../Imagens/bg/', '../Imagens/bg/en/']):
		for name in os.listdir(dir):
			if name in ('es', 'en', 'de', 'it', 'fr'): pass
			else:
				print name
				temp = open('temp', 'w+b')	
				file = open(dir + name, 'rb')
				type = struct.unpack('<L', file.read(4))[0]
				if type == 1:
					buffer = rle.uncompress(file, 0x4)
				elif type == 2:		
					buffer = lzss.uncompress(file, 0x4)
				elif type == 3 or type == 4:
					buffer = huffman.uncompress(file, 0x4)
				else:
					file.seek(0,0)
					buffer = array.array('c', file.read())
				buffer.tofile(temp)
				file.close()
				
				temp.seek(0,0)
				# L� a paleta de cores
				colormap = []
				entries = struct.unpack('<L', temp.read(4))[0]
				for x in range(entries):
					colormap.append(gba2tuple(temp))
				
				# L� o tile set da imagem
				tilelist = []	
				ntiles = struct.unpack('<L', temp.read(4))[0]
				for x in range(ntiles):
					tilelist.append(temp.read(64))
					
				# L� os par�metros da imagem e o tilemap
				buffer = array.array('c')
				width = struct.unpack('<H', temp.read(2))[0]
				height = struct.unpack('<H', temp.read(2))[0]
				for x in range(width*height):
					bytes = struct.unpack('<H', temp.read(2))[0]
					# v_mirror = bytes & 0x0800
					# h_mirror = bytes & 0x0400
					string = tilelist[bytes & 0x3FF]
					# if v_mirror:
						# string = vertical(string)
					# if h_mirror:
						# string = horizontal(string)
					buffer.extend(string)

				output = open(outdir[i] + name + '.bmp', 'wb')

				
				w = images.Writer((width, height), 8, colormap, False, 1)
				w.write(output, buffer, 8, 'BMP')
				
				output.close()
				temp.close()
			
	os.unlink(temp.name)
	
	
def packBackground():
	outdir = ['../Imagens/bg_pt/', '../Imagens/bg_pt/pt/']
	originals = ['../Imagens/bg/', '../Imagens/bg/en/']
	for i, dir in enumerate(['../Imagens/_bg_pt/', '../Imagens/_bg_pt/pt/']):
		for name in os.listdir(dir):
			if name in ('es', 'en', 'de', 'it', 'fr', 'pt'): pass
			else:
				print name
				
				input = open(dir + name, 'rb')
				w = images.Reader(input)
				data, colormap = w.as_data(mode = 1, bitdepth = 8)

				width = len(w.data[0])
				height = len(w.data)
				
				tilelist = []
				tileset = array.array('c')
				tilemap = array.array('c')
				
				for x in range(width*height/64):
					string = data[64*x:64*(x+1)]
					if string in tilelist:
						mapper = tilelist.index(string)
						tilemap.extend(struct.pack('<H', mapper))
					else:
						tilelist.append(string)
						mapper = tilelist.index(string)
						tileset.extend(string)
						tilemap.extend(struct.pack('<H', mapper))
					
				temp = open('temp', 'w+b')
				# Escrita do arquivo tempor�rio:
				temp.write(struct.pack('<L', 0xE0))#len(colormap)))
				for x in range(0xE0):#colormap:
					temp.write(tuple2gba(colormap[x]))
				temp.write(struct.pack('<L', len(tilelist)))
				tileset.tofile(temp)
				
				temp.write(struct.pack('<H', width / 8))
				temp.write(struct.pack('<H', height / 8))
				tilemap.tofile(temp)
				
				
				output = open(outdir[i] + name.replace('.bmp', ''), 'wb')
				output.write(struct.pack('<L', 2))
				
				buffer = lzss.compress(temp)
				buffer.tofile(output)
				
				output.close()
				temp.close()
				
def unpackSprite():
	outdir = ['../Imagens/_ani/nazo/drawinput/']
	for i, dir in enumerate(['../Imagens/ani/nazo/drawinput/']):
		for name in os.listdir(dir):
			#try:
				with tempfile.TemporaryFile() as f:
					if name in ('es', 'en', 'de', 'it', 'fr'):
						pass
					else:
						print name
						file = open(dir + name, 'rb')
						type = struct.unpack('<L', file.read(4))[0]
						if type == 1:
							buffer = rle.uncompress(file, 0x4)
						elif type == 2:		
							buffer = lzss.uncompress(file, 0x4)
						elif type == 3 or type == 4:
							buffer = huffman.uncompress(file, 0x4)
						else:
							file.seek(0,0)
							buffer = array.array('c', file.read())
						buffer.tofile(f)#.file)
						file.close()

						if re.match(r'^.*\.arc$', name):
							f.seek(0,0)
							entries = struct.unpack('<H', f.read(2))[0]
							type = struct.unpack('<H', f.read(2))[0]
							objs = []
							
							if type == 3:
								for p in range(entries):
									xcoord = struct.unpack('<H', f.read(2))[0]
									ycoord = struct.unpack('<H', f.read(2))[0]
									obj_entries = struct.unpack('<L', f.read(4))[0]
									
									objs_params = []
									
									for x in range(obj_entries):
										obj_xcoord = struct.unpack('<H', f.read(2))[0]
										obj_ycoord = struct.unpack('<H', f.read(2))[0]			
										obj_width = 4 * (2 ** struct.unpack('<H', f.read(2))[0]) # 4 BPP)
										obj_height = 8 * (2 ** struct.unpack('<H', f.read(2))[0])
										obj_data = []

										for y in range(obj_height):
											obj_data.append(f.read(obj_width))
											
										objs_params.append( (obj_xcoord, obj_ycoord,
															 obj_width, obj_height, obj_data) )

									width = 0
									height = 0

									for obj_param in objs_params:
										if width <= obj_param[0] + obj_param[2]*2:
											width = obj_param[0] + obj_param[2]*2
										if height <= obj_param[1] + obj_param[3]:
											height = obj_param[1] + obj_param[3]

									buffer = array.array('c', '\xFF' * width * height)

									for obj_param in objs_params:
										obj_data = obj_param[4]
										for y in range(obj_param[3]):
											buffer[width/2*(obj_param[1] + y) + (obj_param[0])/2:
												   width/2*(obj_param[1] + y) + (obj_param[0])/2 + obj_param[2]] = array.array('c', obj_data.pop(0))						

									objs.append((width, height, buffer))
												   
								pal_entries = struct.unpack('<L', f.read(4))[0]			
								colormap = []
								for x in range(pal_entries):
									colormap.append(gba2tuple(f))

								for x in range(entries):
									output = open(os.path.join(outdir[i], '%s-%02d-%02d.bmp' %(name, (x+1), entries)), 'wb')
									w = images.Writer((objs[x][0], objs[x][1]), colormap, 4, 2)
									w.write(output, objs[x][2], 4, 'BMP')
									output.close()

							elif type == 4:
								for p in range(entries):
									xcoord = struct.unpack('<H', f.read(2))[0]
									ycoord = struct.unpack('<H', f.read(2))[0]
									obj_entries = struct.unpack('<L', f.read(4))[0]
									
									objs_params = []						

									for x in range(obj_entries):
										obj_xcoord = struct.unpack('<H', f.read(2))[0]
										obj_ycoord = struct.unpack('<H', f.read(2))[0]			
										obj_width = 8 * (2 ** struct.unpack('<H', f.read(2))[0])
										obj_height = 8 * (2 ** struct.unpack('<H', f.read(2))[0])
										obj_data = []
										for y in range(obj_height):
											obj_data.append(f.read(obj_width))							

										objs_params.append( (obj_xcoord, obj_ycoord,
															 obj_width, obj_height, obj_data) )
							
									width = 0
									height = 0

									for obj_param in objs_params:
										if width <= obj_param[0] + obj_param[2]:
											width = obj_param[0] + obj_param[2]
										if height <= obj_param[1] + obj_param[3]:
											height = obj_param[1] + obj_param[3]						
		
									buffer = array.array('c', '\xFF' * width * height)
									
									for obj_param in objs_params:
										obj_data = obj_param[4]
										for y in range(obj_param[3]):
											buffer[width*(obj_param[1] + y) + (obj_param[0]):
												   width*(obj_param[1] + y) + (obj_param[0]) + obj_param[2]] = array.array('c', obj_data.pop(0))						
							
									objs.append((width, height, buffer))

								pal_entries = struct.unpack('<L', f.read(4))[0]			
								colormap = []
								for x in range(pal_entries):
									colormap.append(gba2tuple(f))								
									
								for x in range(entries):
									output = open(os.path.join(outdir[i], '%s-%02d-%02d.bmp' %(name, (x+1), entries)), 'wb')
									w = images.Writer((objs[x][0], objs[x][1]), colormap, 8, 2)
									w.write(output, objs[x][2], 8, 'BMP')
									output.close()													
								
							else:
								print 'except %s' % name

						elif re.match(r'^.*\.arj$', name):
							f.seek(0,0)
							objs = []
						
							entries = struct.unpack('<H', f.read(2))[0]
							type = struct.unpack('<H', f.read(2))[0]						
							pal_entries = struct.unpack('<L', f.read(4))[0]
							for p in range(entries):
								xcoord = struct.unpack('<H', f.read(2))[0]
								ycoord = struct.unpack('<H', f.read(2))[0]
								obj_entries = struct.unpack('<L', f.read(4))[0]
								
								objs_params = []
								
								for x in range(obj_entries):
									obj_shape = struct.unpack('<H', f.read(2))[0]
									obj_size = struct.unpack('<H', f.read(2))[0]
									obj_xcoord = struct.unpack('<H', f.read(2))[0]
									obj_ycoord = struct.unpack('<H', f.read(2))[0]
									obj_width = 8 * (2**struct.unpack('<H', f.read(2))[0])
									obj_height = 8 * (2**struct.unpack('<H', f.read(2))[0])	
									obj_data = []
									for y in range(obj_width * obj_height / 64):
										obj_data.append(f.read(64))
										
									objs_params.append( (obj_shape, obj_size, obj_xcoord, obj_ycoord,
														 obj_width, obj_height, obj_data) )
								width = 0
								height = 0

								for obj_param in objs_params:
									if width <= obj_param[2] + obj_param[4]:
										width = obj_param[2] + obj_param[4]
									if height <= obj_param[3] + obj_param[5]:
										height = obj_param[3] + obj_param[5]
																			
								buffer = array.array('c', '\xFF' * width * height)
								
								for obj_param in objs_params:
									obj_data = obj_param[6]
									for y in range(obj_param[5] / 8):
										for w in range(obj_param[4] / 8):
											buffer[(width*(obj_param[3] + y*8)) + obj_param[2]*8 + 64*(w):
												   (width*(obj_param[3] + y*8)) + obj_param[2]*8 + 64*(w+1)] = array.array('c',obj_data.pop(0))

								objs.append((width, height, buffer))
						
							colormap = []
							for x in range(pal_entries):
								colormap.append(gba2tuple(f))

							for x in range(entries):
								output = open(os.path.join(outdir[i], '%s-%02d-%02d.bmp' %(name, (x+1), entries)), 'wb')
								w = images.Writer((objs[x][0], objs[x][1]), colormap, 8, 1)
								w.write(output, objs[x][2], 8, 'BMP')
								output.close()
			#except:pass
							
def packSprite():
	holder = {}
	outdir = ['../Imagens/ani_pt/_pt/']
   	#outdir = ['../Imagens/ani_pt/_nazo/drawinput/pt']
	originals = ['../Imagens/Ani Originais/']
   	#originals = ['../Imagens/Nazo Originais/']
	# Passo 1 - Gerar um dicion�rio com todos os sprites a serem empacotados
	print "Buffering..."
	for i, dir in enumerate(['../Imagens/_ani_pt/pt/']):
   	#for i, dir in enumerate(['../Imagens/_ani_pt/nazo/drawinput/pt/']):
		for name in os.listdir(dir):
			print ">>> ", name
			a = re.match(r'^(.*)-(.*)-(.*)\.bmp$', name)
			if a.group(1) not in holder:
				holder.update({a.group(1):{}})#[]})
				
			w = bmp.Reader(os.path.join(dir, name))
			d = w.read()
			p = w.read_palette()
			w.file.close()
			holder[a.group(1)].update({int(a.group(2)) - 1: (d,p)})#append((d, p))
	
	compressions = {}
	# Passo 2 - Descompactar os arquivos originais
	for name in holder.keys():
		file = open(os.path.join(originals[0], name), "rb")
		type = struct.unpack('<L', file.read(4))[0]
		if type == 1:
			buffer = rle.uncompress(file, 0x4)
		elif type == 2:		
			buffer = lzss.uncompress(file, 0x4)
		elif type == 3 or type == 4:
			buffer = huffman.uncompress(file, 0x4)
		else:
			file.seek(0,0)
			buffer = array.array('c', file.read())
		compressions.update({name:type})
		file.close()

		file = open(os.path.join(outdir[0], name), "wb")
		buffer.tofile(file)
		file.close()

	# Passo 3 - Atualizar os containers com os novos sprites
	for i, dir in enumerate(outdir):
		for name in os.listdir(dir):
			print "Atualizando ", os.path.join(dir, name)
			arrays = []
			with open(os.path.join(dir, name), "rb") as f:
				f.seek(0,0)
				if re.match(r'^.*\.arc$', name):
					entries = struct.unpack("<H", f.read(2))[0]
					bitdepth = 2 ** (struct.unpack("<H", f.read(2))[0] - 1)
					for x in range(entries):
						sprite_data = holder[name][x][0]
						sprite_pal = holder[name][x][1]
						# Leitura do header do sprite
						f.seek(4, 1) # As coordenadas n�o ser�o mudadas a principio
						obj_entries = struct.unpack("<L", f.read(4))[0]
						for y in range(obj_entries):
							xpos = struct.unpack("<H", f.read(2))[0]
							ypos = struct.unpack("<H", f.read(2))[0]
							width = 8 * (2 ** struct.unpack("<H", f.read(2))[0])
							height = 8 * (2 ** struct.unpack("<H", f.read(2))[0])
							obj = []
							for w in range(height):
								obj.append(sprite_data[ypos + w][xpos:xpos + width])

							bitarray = array.array('B')
							for row in obj:
								if bitdepth < 8:
									row = zip(*[iter(row)]*(8/bitdepth))
									row = map(lambda e: reduce(lambda x,y:(x << bitdepth) + y, reversed(e)), row)
								bitarray.extend(row)
								
							arrays.append((f.tell(), array.array("c", bitarray.tostring())))
							f.seek(len(bitarray.tostring()), 1)

					pal_entries = struct.unpack('<L', f.read(4))[0]
					
				elif re.match(r'^.*\.arj$', name): 
					entries = struct.unpack("<H", f.read(2))[0]
					bitdepth = 2 ** (struct.unpack("<H", f.read(2))[0] - 1)
					colors = struct.unpack("<L", f.read(4))[0]
					for x in range(entries):
						sprite_data = holder[name][x][0]
						sprite_pal = holder[name][x][1]
						
						sprite_xpos = struct.unpack("<H", f.read(2))[0]
						sprite_ypos = struct.unpack("<H", f.read(2))[0]
						obj_entries = struct.unpack("<L", f.read(4))[0]
						
						for y in range(obj_entries):
							obj_shape = struct.unpack('<H', f.read(2))[0]
							obj_size = struct.unpack('<H', f.read(2))[0]
							obj_xcoord = struct.unpack('<H', f.read(2))[0]
							obj_ycoord = struct.unpack('<H', f.read(2))[0]
							obj_width = 2**struct.unpack('<H', f.read(2))[0]
							obj_height = 2**struct.unpack('<H', f.read(2))[0]
							
							obj = [[list() for p in range(obj_width)] for t in range(obj_height)]

							for ypos in range(obj_height):
								for xpos in range(obj_width):
									for w in range(8):
										obj[ypos][xpos] += (sprite_data[obj_ycoord + ypos*8 + w][obj_xcoord + xpos*8:obj_xcoord + xpos*8 + 8])
								
							bitarray = array.array('B')
							for row in obj:
								for d in row:
									bitarray.extend(d)
								
							arrays.append((f.tell(), array.array("c", bitarray.tostring())))
							f.seek(len(bitarray.tostring()), 1)
							
			with open(os.path.join(dir, name), "r+b") as f:	
				for par in arrays:
					f.seek(par[0], 0)
					par[1].tofile(f)				

					
	# Passo 4
	print "Comprimindo..."
	for name in os.listdir("../Imagens/ani_pt/_pt/"):
	#for name in os.listdir("../Imagens/ani_pt/_nazo/drawinput/pt/"):
		print ">>> ", name
		with open(os.path.join("../Imagens/ani_pt/_pt/", name), "rb") as f:
		#with open(os.path.join("../Imagens/ani_pt/_nazo/drawinput/pt/", name), "rb") as f:
			type = compressions[name]
			if type == 1:
				buffer = rle.compress(f)
			elif type == 2:
				buffer = lzss.compress(f)
			elif type == 3:
				buffer = huffman.compress(f, 4)
			elif type == 4:
				buffer = huffman.compress(f, 8)

		g = open(os.path.join("../Imagens/ani_pt/pt/", name), "wb")
		#g = open(os.path.join("../Imagens/ani_pt/nazo/drawinput/pt/", name), "wb")
		g.write(struct.pack("<L", type))
		buffer.tofile(g)
		g.close()
							
if __name__ == "__main__":

	print '\nCopyright 2010 - Monkeys Traducoes'
	print '\nLayton\'s Image Dumper'
	
	# unpackBackground()
	#packBackground()
	#unpackSprite()
	packSprite()
