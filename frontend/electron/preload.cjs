const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  selectDocumentFile: () => ipcRenderer.invoke('select-document-file'),
  selectRuleFile: () => ipcRenderer.invoke('select-rule-file'),
  readDocumentText: (filePath) => ipcRenderer.invoke('read-document-text', filePath),
  selectSavePath: (defaultFilename) => ipcRenderer.invoke('select-save-path', defaultFilename),
})
