@echo off
set JAVA_HOME=C:\Users\Administrator\ai-shisho\_jdk21\jdk-21.0.4+7
set PATH=%JAVA_HOME%\bin;%PATH%
set JADX=C:\Users\Administrator\ai-shisho\_ghidra\jadx\lib\jadx-1.5.1-all.jar
set APK=C:\Users\Administrator\AppData\Local\hermes\cache\documents\doc_d5117e0e61d4_StockHunter Malaysia 3.7.1.apk
set OUT=C:\Users\Administrator\ai-shisho\stockhunter_out
"C:\Users\Administrator\ai-shisho\_jdk21\jdk-21.0.4+7\bin\java.exe" -Xmx4g -cp "%JADX%" jadx.cli.JadxCLI -d "%OUT%" --no-res --threads-count 4 "%APK%"
echo DONE_JADX
