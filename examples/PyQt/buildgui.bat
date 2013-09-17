echo Building GUI

call pyuic4 mainwindow.ui > mainwindow.py

::echo Building resource file

::call pyrcc4 icons/tow_resources.qrc -o tow_resources_rc.py

echo Done