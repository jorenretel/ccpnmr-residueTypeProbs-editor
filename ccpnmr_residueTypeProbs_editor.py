'''

Copyright (C) 2013 Joren Retel (FMP Berlin)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

This program is a macro/plug-in for CCPN analysis. CCPN analysis itself is
copyrighted as follows:

Copyright (C) 2005 Wayne Boucher and Tim Stevens (University of Cambridge)

A copy of the CCPN license can be found in ../../../license/CCPN.license.

'''

from memops.gui.ButtonList import ButtonList
from memops.gui.Frame import Frame
from memops.gui.PulldownList import PulldownList
from ccpnmr.analysis.popups.BasePopup import BasePopup
from memops.gui.ScrolledMatrix import ScrolledMatrix


def open_type_probs_editor(argServer):
    """Descrn: Opens the macro.
         Inputs: ArgumentServer
         Output: None
    """
    editResidueTypePopup(argServer.parent)


class editResidueTypePopup(BasePopup):
    '''
    The main popup that is shown when the macro is loaded.
    '''

    def __init__(self, parent, *args, **kw):

        self.font = 'Helvetica 10'
        self.sFont = 'Helvetica %d'
        self.project = parent.project
        self.guiParent = parent
        self.chemCompDict = {}
        self.createChemCompDict()
        self.waiting = False
        BasePopup.__init__(self, parent,
                           title="Residue Type Probabilities", **kw)

    def open(self):

        self.updateAfter()
        BasePopup.open(self)

    def body(self, guiFrame):
        '''Describes where all the GUI element are.'''

        self.geometry('400x500')
        guiFrame.expandGrid(0, 0)
        tableFrame = Frame(guiFrame)
        tableFrame.grid(row=0, column=0, sticky='nsew', )
        tableFrame.expandGrid(0, 0)
        buttonFrame = Frame(guiFrame)
        buttonFrame.grid(row=1, column=0, sticky='nsew', )
        headingList = ['Spinsystem Number', 'Assignment', 'Residue Type Probs']
        self.table = ScrolledMatrix(tableFrame, headingList=headingList,
                                    callback=self.updateSpinSystemSelection,
                                    multiSelect=True)
        self.table.grid(row=0, column=0, sticky='nsew')
        texts = ['Add Prob']
        commands = [self.addProb]
        self.AddProbButton = ButtonList(buttonFrame, commands=commands,
                                        texts=texts)
        self.AddProbButton.grid(row=0, column=0, sticky='nsew')
        texts = ['Remove Prob']
        commands = [self.removeProb]
        self.AddProbButton = ButtonList(buttonFrame, commands=commands,
                                        texts=texts)
        self.AddProbButton.grid(row=0, column=2, sticky='nsew')
        selectCcpCodes = sorted(self.chemCompDict.keys())
        tipText = 'select ccpCode'
        self.selectCcpCodePulldown = PulldownList(buttonFrame,
                                                  texts=selectCcpCodes,
                                                  grid=(0, 1),
                                                  tipText=tipText)

        selectCcpCodes = ['All Residue Types']

        tipText = 'select ccpCode'
        self.selectCcpCodeRemovePulldown = PulldownList(buttonFrame,
                                                        texts=selectCcpCodes,
                                                        index=0,
                                                        grid=(0, 3),
                                                        tipText=tipText)
        self.updateTable()

    def updateSpinSystemSelection(self, obj, row, col):
        '''Called after selectin a row in the table.'''
        self.updateRemoveCcpCodePullDown()

    def updateRemoveCcpCodePullDown(self):
        '''Updates the pulldown showing all current residueTypeProbs
           for a resonanceGroup that can be removed.

        '''

        removeCcpCodes = []
        for spinSystem in self.table.currentObjects:
            removeCcpCodes.extend([typeProp.possibility.ccpCode for typeProp in spinSystem.getResidueTypeProbs()])
        removeCcpCodes = ['All Residue Types'] + list(set(removeCcpCodes))
        self.selectCcpCodeRemovePulldown.setup(texts=removeCcpCodes,
                                               objects=removeCcpCodes,
                                               index=0)

    def getSpinSystems(self):
        '''Get resonanceGroups (spin systems) in the project.'''
        return self.nmrProject.resonanceGroups

    def addProb(self):
        '''Add the residue type selected in the selectCcpCodePulldown
           as an residueTypeProb.

        '''
        ccpCode = self.selectCcpCodePulldown.object
        for spinSystem in self.table.currentObjects:
            if ccpCode not in [typeProp.possibility.ccpCode for typeProp in spinSystem.getResidueTypeProbs()]:
                chemComp = self.chemCompDict.get(ccpCode)
                spinSystem.newResidueTypeProb(possibility=chemComp)
        self.updateTable()
        self.updateRemoveCcpCodePullDown()

    def removeProb(self):
        '''Removes the residueTypeProb selected in the
           selectCcpCodeRemovePulldown from the selected resonanceGroup.

        '''
        ccpCode = self.selectCcpCodeRemovePulldown.object
        for spinSystem in self.table.currentObjects:
            residueTypeProbs = spinSystem.getResidueTypeProbs()
            for typeProb in residueTypeProbs:
                if ccpCode == 'All Residue Types' or ccpCode == typeProb.possibility.ccpCode:
                    typeProb.delete()
        self.updateTable()
        self.updateRemoveCcpCodePullDown()

    def createChemCompDict(self):
        '''Make a list of all amino acid types present in any of the
           molecular chains present in the project.

        '''
        chains = self.getChains()
        for chain in chains:
            for residue in chain.sortedResidues():
                if residue.ccpCode not in self.chemCompDict:
                    self.chemCompDict[residue.ccpCode] = residue.chemCompVar.chemComp

    def getChains(self):
        '''Get all molecular chains stored in the project.'''
        chains = []
        if self.project:
            for molSystem in self.project.sortedMolSystems():
                for chain in molSystem.sortedChains():
                    if chain.residues:
                        chains.append(chain)
        return chains

    def updateTable(self):
        '''Update the whole table.'''
        objectList = []
        data = []
        for spinSystem in self.getSpinSystems():
            objectList.append(spinSystem)
            residueTypeProbs = spinSystem.getResidueTypeProbs()
            spinSystemInfo = self.getStringDescriptionOfSpinSystem(spinSystem)
            probString = ''
            for typeProp in residueTypeProbs:
                probString += typeProp.possibility.ccpCode + ' '
            data.append([spinSystem.serial, spinSystemInfo, probString])
        self.table.update(objectList=objectList, textMatrix=data)

    def getStringDescriptionOfSpinSystem(self, spinsys):
        '''Get a simple identifier for the assignment status of a
           resonanceGroup.

        '''

        spinSystemInfo = ''
        if spinsys.residue:
            spinSystemInfo += str(spinsys.residue.seqCode) + ' ' + spinsys.residue.ccpCode
        elif spinsys.residueProbs:
            for residueProb in spinsys.residueProbs:
                res = residueProb.possibility
                spinSystemInfo += '{} {}? /'.format(res.seqCode, res.ccpCode)
            spinSystemInfo = spinSystemInfo[:-1]
        elif spinsys.ccpCode:
            spinSystemInfo += spinsys.ccpCode
        return spinSystemInfo
