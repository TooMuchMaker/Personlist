!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "TRAEWORK"
OutFile "TRAEWORK-Setup.exe"
InstallDir "$PROGRAMFILES64\TRAEWORK"
InstallDirRegKey HKLM "Software\TRAEWORK" "Install_Dir"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "traework\assets\icon.ico"
!define MUI_UNICON "traework\assets\icon.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "SimpChinese"

Section "TRAEWORK (required)" SecMain
    SectionIn RO
    
    SetOutPath $INSTDIR
    
    File /r "dist\*.*"
    
    WriteRegStr HKLM "Software\TRAEWORK" "Install_Dir" "$INSTDIR"
    
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TRAEWORK" "DisplayName" "TRAEWORK"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TRAEWORK" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TRAEWORK" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TRAEWORK" "NoRepair" 1
    
    WriteUninstaller "$INSTDIR\uninstall.exe"
    
    CreateDirectory "$SMPROGRAMS\TRAEWORK"
    CreateShortcut "$SMPROGRAMS\TRAEWORK\TRAEWORK.lnk" "$INSTDIR\TRAEWORK.exe"
    CreateShortcut "$SMPROGRAMS\TRAEWORK\卸载 TRAEWORK.lnk" "$INSTDIR\uninstall.exe"
    
SectionEnd

Section "开机自启动" SecAutoStart
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TRAEWORK" "$INSTDIR\TRAEWORK.exe"
SectionEnd

Section "桌面快捷方式" SecDesktop
    CreateShortcut "$DESKTOP\TRAEWORK.lnk" "$INSTDIR\TRAEWORK.exe"
SectionEnd

LangString DESC_SecMain ${LANG_SIMPCHINESE} "TRAEWORK 主程序（必需）"
LangString DESC_SecAutoStart ${LANG_SIMPCHINESE} "开机时自动启动 TRAEWORK"
LangString DESC_SecDesktop ${LANG_SIMPCHINESE} "在桌面创建快捷方式"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} $(DESC_SecMain)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecAutoStart} $(DESC_SecAutoStart)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\TRAEWORK"
    DeleteRegKey HKLM "Software\TRAEWORK"
    DeleteRegValue HKCU "Software\Microsoft\Windows\CurrentVersion\Run" "TRAEWORK"
    
    Delete "$SMPROGRAMS\TRAEWORK\*.*"
    RMDir "$SMPROGRAMS\TRAEWORK"
    Delete "$DESKTOP\TRAEWORK.lnk"
    
    RMDir /r "$INSTDIR"
SectionEnd
