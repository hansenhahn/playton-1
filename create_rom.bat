@echo off

echo "Layton's Assembler by DiegoHH"

rem Copia alguns arquivos "estratégicos" para a pasta com a Rom Modificada
copy "Arquivos\banner.bin" "ROM Modificada\PLAYTON" /B/Y
copy "Arquivos\utility.bin" "ROM Modificada\PLAYTON\data\dwc" /B/Y

rem Arquivos copiados do espanhol, pelo fato de serem maiores ou terem a paleta de cores modificada
copy "ROM Original\PLAYTON\data\data\ani\es\jiten_num.arc" "ROM Modificada\PLAYTON\data\data\ani\en\jiten_num.arc" /B/Y
copy "ROM Original\PLAYTON\data\data\ani\es\story_gfx.arc" "ROM Modificada\PLAYTON\data\data\ani\en\story_gfx.arc" /B/Y
copy "ROM Original\PLAYTON\data\data\ani\es\story_page_buttons.arc" "ROM Modificada\PLAYTON\data\data\ani\en\story_page_buttons.arc" /B/Y

rem Copia os arquivos de fonte
copy "Fontes\font18.NFTR" "ROM Modificada\PLAYTON\data\data\font" /B/Y
copy "Fontes\fontevent.NFTR" "ROM Modificada\PLAYTON\data\data\font" /B/Y
copy "Fontes\fontq.NFTR" "ROM Modificada\PLAYTON\data\data\font" /B/Y

rem Executa os packers de imagem e texto
cd Programas
call pack_images.bat
call pack_text.bat
cd ..

rem Monta a ROM nova e gera um patch
cd ROM Modificada
call pack_rom.bat
call do_patch.bat
cd ..