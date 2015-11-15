'''
Created on 17/07/2013

@author: Hansen
'''
import os
import glob
import struct
import mmap

def scandirs(path):
    files = []
    for currentFile in glob.glob( os.path.join(path, '*') ):
        if os.path.isdir(currentFile):
            files += scandirs(currentFile)
        else:
            files.append(currentFile)
    return files

class Archive:
    Name = None
    Id = None
    

class MountIt(object):

    def __init__(self, **kwargs):
        '''
        Constructor
        '''
        filename = kwargs.get('filename', None)
        assert filename != None
        
        self.__file = open(filename, "rb")
        
    def __MakeHeader(self):
        self.header = {}        
        self.__file.seek(0x20)
        # ARM9 data
        self.header.update({"arm9_bin_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm9_exec_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm9_ram_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm9_bin_lenght" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        # ARM7 data
        self.header.update({"arm7_bin_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm7_exec_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm7_ram_address" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm7_bin_lenght" : ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        # FNT data
        self.header.update({"fnt_address": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"fnt_lenght": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        # FAT data
        self.header.update({"fat_address": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"fat_lenght": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        # ARM9 Overlay data
        self.header.update({"arm9_overlay_address": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm9_overlay_lenght": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})    
        # ARM7 Overlay data
        self.header.update({"arm7_overlay_address": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.header.update({"arm7_overlay_lenght": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        self.rom.seek(8, 1)
        # BANNER data
        self.header.update({"banner_address": ( self.__file.tell(), struct.unpack('<L', self.__file.read(4))[0] )})
        
    def DumpFileTable(self):
        fnt_tbl = self.__read_file_name_table()
        fat_tbl = self.__read_file_address_table()
        
        


    def __read_file_address_table(self):
        self.__file.seek(self.header["fat_address"], 0)

        map = mmap.mmap(-1, self.header["fat_size"])
        map.write(self.rom.read(self.header["fat_size"]))
        map.seek(0,0)

        self.address_table = []
        for _ in range(len(map)/8):#map.size()/8):
            begin = struct.unpack('<L', map.read(4))[0]
            end = struct.unpack('<L', map.read(4))[0]
            self.address_table.append((begin, (end - begin)))

        map.close()
        return self.address_table

    def __read_file_name_table(self):
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

        self.__file.seek(self.header["fnt_address"], 0)

        map = mmap.mmap(-1, self.header["fnt_size"])
        map.write(self.rom.read(self.header["fnt_size"]))
        map.seek(0,0)

        self.name_table = create_name_table(read_folder_struct(map), "", [])

        map.close()
        return self.name_table        
        
if __name__ == "__main__":
    
    
        
        
        