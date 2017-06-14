# -*- coding: utf-8 -*-
    # --------------------------------------------------------------------------------------------
    # Copyright (C) 2016  Gerhard Hepp
    #
    # This program is free software; you can redistribute it and/or modify it under the terms of
    # the GNU General Public License as published by the Free Software Foundation; either version 2
    # of the License, or (at your option) any later version.
    #
    # This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
    # without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    # See the GNU General Public License for more details.
    #
    # You should have received a copy of the GNU General Public License along with this program; if
    # not, write to the Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston,
    # MA 02110, USA
    # ---------------------------------------------------------------------------------------------

#
# Start scratchClient for multiple arduino using ident code
#

from PyQt4 import QtCore, QtGui
import sys
import threading
import untitled 
import scratchClientArduinoStartup
import time
import subprocess
import os
#
# sudo apt-get install python-qt4
#

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class ScratchClientRunner(threading.Thread):
    
    def __init__(self, cmd):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.start()

    def run(self):
        
        popen = subprocess.Popen( self.cmd, cwd='/home/pi/scratchClient' )   
        popen.wait() 
        
        
class ExampleAppController():
    def __init__(self, parent):
        self.parent = parent
        initThread = InitThread(self)
        initThread.start()
        
    def setModel(self, model):
        self.model = model
        
    def setSelectionModel(self, selectionModel):
        self.selectionModel = selectionModel
        
    def on_exit_clicked(self):
        print("on_exit_clicked")
        quit()
      
    def _getSelectedRow(self):    
        for index in self.selectionModel.selectedRows ():
            return index.row() 
        return None
    
    def on_button_clicked(self):
        r = self._getSelectedRow()
        aConfig = arduinoConfig.getConfigFile(r)
        
        parameterReplaceConfig = scratchClientArduinoStartup.ParameterReplaceConfig( aConfig, arduinoConfig)
        
        parameterReplaceConfig.setDirIn( 'config' )
        parameterReplaceConfig.setFileIn( aConfig['file'] )
        
        parameterReplaceConfig.setDirOut( modulePathHandler.getScratchClientBaseRelativePath('temp' ))
        parameterReplaceConfig.setFileOut( 'config_execute.xml' )
        
        parameterReplaceConfig.process()

        self.executeScratchClient( modulePathHandler.getScratchClientBaseRelativePath('temp' ), 'config_execute.xml')
        
    def executeScratchClient(self, cDir, cFile):
        arec_cmd = ["python3", "/home/pi/scratchClient/src/scratchClient.py",  "-c",  cDir + "/" + cFile, "-d" ]  
         
        self.scratchClientRunner = ScratchClientRunner(arec_cmd)
        
    def on_selection_changed(self):
        print("on_selection_changed")
        
        r = self._getSelectedRow()
        sI = ''
        sN = ''
        
        if r == None:
            self.parent.ui.pushButton.setEnabled(False)
            pass
        else:
            sep = ''
            c = self.config[r]
            if c['active']:
                self.parent.ui.pushButton.setEnabled(True)
            else:
                self.parent.ui.pushButton.setEnabled(False)
            idents = c['idents']
            sI = "Ident | "
            sN = "Nano | "
            for ident in idents:
                sI += sep + ident['ident']
                sN += sep + ident['alias']
                sep = '; '
        self.parent.ui.label_1.setText(sI)
        self.parent.ui.label_2.setText(sN)
        
    def showConfig(self, config):
        self.config = config
        rows = len( config )
                
        for r in range(rows):
            c = config[r]
            row1 = []
            
            if c['active'] :
                item = QtGui.QStandardItem('active')
                item.setBackground( QtGui.QBrush( QtGui.QColor(0x68c665)))
            else:
                item = QtGui.QStandardItem('') 
            row1.append(item)
            
            item = QtGui.QStandardItem( c['description'] )
            row1.append(item)  
            
            self.model.appendRow( row1)
            
    def setStatus(self, status):
        self.parent.ui.statusbar.showMessage("Status | " + status)
        
class MyQt4App():
    def __init__(self):
        # --------------------
        # avoid error message:
        # [xcb] Most likely this is a multi-threaded client and XInitThreads has not been called
        #
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_X11InitThreads)
        # --------------------
        self.app = QtGui.QApplication(sys.argv)
    
        MainWindow = QtGui.QMainWindow()
        self.ui = untitled.Ui_MainWindow()
        self.ui.setupUi(MainWindow)
        MainWindow.show()
        
        self.model = QtGui.QStandardItemModel()
        
        self.model.setColumnCount(2)
        headerNames = []
        headerNames.append("active")
        headerNames.append("comment")
        self.model.setHorizontalHeaderLabels(headerNames)
        if False:
            for i in range(100):
                row1 = [QtGui.QStandardItem('active' if i%2 else ''), QtGui.QStandardItem( 'data_'+str(i)) ];    self.model.appendRow( row1)
            
            
        self.ui.tableView.setModel(self.model)
        
        self.ui.statusbar.showMessage("hugo")
                
        self.selectionModel = QtGui.QItemSelectionModel(self.model)
        
        self.ui.tableView.setSelectionModel( self.selectionModel )
        # selectionModel.selectionChanged(on_selection_changed)
         
        print("---")
        print (QtCore.SIGNAL("clicked()"))
    
        self.controller = ExampleAppController(self)
        self.controller.setModel(self.model)
        self.controller.setSelectionModel(self.selectionModel)

        QtCore.QObject.connect(self.selectionModel,  
                        QtCore.SIGNAL("selectionChanged(QItemSelection, QItemSelection)"),  
                        self.controller.on_selection_changed) 
        QtCore.QObject.connect( self.ui.actionExit, QtCore.SIGNAL("triggered()"), self.controller.on_exit_clicked)
        QtCore.QObject.connect( self.ui.pushButton, QtCore.SIGNAL("clicked()"), self.controller.on_button_clicked)
        
    
        #ui.statusbar.showMessage("System Status | Normal")
        
        sys.exit(self.app.exec_())

class InitThread( threading.Thread):
    def __init__(self, controller):
        threading.Thread.__init__(self)
        self.controller = controller

    def run(self):
        time.sleep(1)
        self.controller.setStatus("initializing")
          
        
        self.controller.setStatus("reading config")
        time.sleep(1)
        self.controller.setStatus("polling USB")
        arduinoScanner = scratchClientArduinoStartup.ArduinoScanner(arduinoConfig)
        
        arduinoScanner.scan()
        arduinoConfig.markPossibleConfig()
      
        time.sleep(1)
        self.controller.setStatus("ready")
        self.controller.showConfig(arduinoConfig.getConfigurations())
        
class ModulePathHandler:
    modulePath = None
    moduleDir = None
    
    def __init__(self):
        _cwd = os.getcwd()
        _file = __file__
        
        if sys.platform == "linux" or sys.platform == "linux2":
            # linux
            self.modulePath = _cwd + '/' + _file
            self.moduleDir =  os.path.split(self.modulePath)[0]
            
        elif sys.platform == "darwin":
            # MAC OS X
            self.modulePath = _cwd + '/' + _file
            self.moduleDir =  os.path.split(self.modulePath)[0]
            
        elif sys.platform == "win32":
            # Windows
            self.modulePath = _file
            self.moduleDir =  os.path.split(self.modulePath)[0]
            
        
    def getModulePath(self):
        return self.modulePath
    
    def getModuleDir(self):
        return self.moduleDir
    #
    # specific methods for scratchClient
    #
    def getScratchClientBaseDir(self):
        return os.path.join( sys.path[0], '..')
    
    def getScratchClientBaseRelativePath(self, relPath):
        return os.path.normpath( 
                                os.path.join( self.getScratchClientBaseDir(), relPath )
                                )
        
modulePathHandler = ModulePathHandler()

            
if __name__ == "__main__":
    
    configFile = 'config/config.json'
    try:
        i = 1
        while i <  len (sys.argv):
            if '-config' == sys.argv[i]:
                configFile = sys.argv[i+1]
                i += 1
            i += 1
    except Exception:
        pass

    if os.path.exists(configFile) and os.path.isfile(configFile):
        pass
    else:
        print("Error, file does not exist ", configFile)
        quit()

    arduinoConfig = scratchClientArduinoStartup.ArduinoConfig( fileName=configFile)  
    modulePathHandler = ModulePathHandler()

    MyQt4App()
    

