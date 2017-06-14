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

import serial

import logging
logger = logging.getLogger(__name__)

import json
import pprint
import sys
import re

debug = True
verbose = True

# --------------------------------------------------------------------------------------
class ArduinoConfig:
    config = None
    
    def __init__(self, fileName = None):
        if debug:
            print(fileName)
        with open(fileName) as data_file:
            self.config = json.load(data_file)
    
        if verbose:
            pprint.pprint(self.config) 
        
        for c in self.getConfigurations():
            c['active'] =False
        pass
    
    def getConfigFile(self, index):
        return self.getConfigurations()[index]
    
    def markPossibleConfig(self):
        nIdent = 0
        if debug:
            print("loop through all connections")
        for device in self.getDevices():
            if debug:
                print(device)
            if 'ident' in device:
                nIdent += 1
                
        if debug:
            print("nIdent", nIdent)
        
        for config in self.getConfigurations():
            # check only these configurations which match the number of available USB devices
            if len ( config['idents'] ) == nIdent:
            # print("matching nIdent for " + setting['file'])
            
                if self.matchDevices( config, self.getDevices() ):
                    if verbose:
                        print("yep, found, execute " + config['file'] + '   ' + config['description'])
                    config['active'] = True
                   

    def matchDevices(self, setting, devices):
        #
        # the devices are enriched with IDENT if available
        #
        foundIdents = []
        for device in devices:
            if 'ident' in device:
                dident = device['ident']
                foundIdents.append(dident)
        nFound = 0
                    
        for ident in setting['idents']:
            if 'ident' in ident:
                sIdent = ident['ident']
                #
                # validate the ident from configuration with the found idents
                for fIdent in foundIdents:
                    if re.match( sIdent, fIdent):
                        nFound += 1
                    
        if nFound == len(foundIdents):             
            return True
        return False
    
    def getDeviceForIdent(self, ident):
        for device in self.getDevices():
            if 'ident' in device:
                dident = device['ident']
                if ident == dident:
                    return device['device']
        return None
            
    def getDevices(self):
        return self.config['devices']
    
    def getConfigurations(self):
        return self.config['configs']
    
    def showConfig(self):
        pprint.pprint(self.config)
         
# --------------------------------------------------------------------------------------
class ArduinoScanner:
    def __init__(self, arduinoConfig):
        self.arduinoConfig = arduinoConfig
        self.speed=115200

    def scan(self):
        print("platform is " + sys.platform)
        for connection in self.arduinoConfig.getDevices():
            
            if sys.platform !=  connection['os'] :
                continue
            
            state = 0
            if debug:
                print("xonnection", connection)
            device = connection['device']
            try:
                ser = serial.Serial( device, self.speed, timeout=0.1 )
                state = 0
                while True:
                    line = ser.readline()
                    if line == '':
                        continue
                    if debug:
                        print (line)
                    if state == 0:
                        
                        if line.startswith( 'config?'):
                            if verbose:
                                print("found arduino", line)
                            state = 10
                            
                    elif state == 10:
                        ser.write('cident?'+"\n");
                        ser.flush()
                        
                        state = 20
                    elif state == 20:
                        if line.startswith( 'ident:'):
                            ident =line.split(':')[1]
                            # remove trailing \n
                            ident = ident.split()[0]
                            if debug:
                                print("found ident {i:s} on {d:s}".format(i=ident, d=device))
                            connection['ident'] = ident
                            state = 999
                    elif state == 999:
                        if debug: 
                            print("complete")
                        break
                ser.close()
            except Exception as e:
                if verbose:
                    print(e)
# --------------------------------------------------------------------------------------
class ParameterReplaceConfig:
    def __init__(self, configFile, arduinoConfig ):
        if debug:
            print(configFile)
        self.configFile = configFile
        
        self.arduinoConfig = arduinoConfig
    
    def setFileIn(self, fileIn):
        self.fileIn = fileIn
        
    def setDirIn(self, dirIn):
        self.dirIn = dirIn
        
    def setFileOut(self, fileOut):
        self.fileOut = fileOut
        
    def setDirOut(self, dirOut):
        self.dirOut = dirOut
            
    def process(self):
        fr = open( self.dirIn + '/' +  self.fileIn, 'r')
        fs = fr.read()    
        fr.close()
        
        for connection in self.configFile['idents']:
            if debug:
                print("replace {a:s} {r:s}".format(a=connection['alias'], r= self.arduinoConfig.getDeviceForIdent(connection['ident'])))
            fs = fs.replace(  '${' + connection['alias'] + '}', self.arduinoConfig.getDeviceForIdent(connection['ident'])  )
        
        fw =  open( self.dirOut + '/' + self.fileOut, 'w')
        fw.write( fs)    
        fw.close()
        
