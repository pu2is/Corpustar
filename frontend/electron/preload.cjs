const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  selectDocumentFile: () => ipcRenderer.invoke('select-document-file'),
  readDocumentText: (filePath) => ipcRenderer.invoke('read-document-text', filePath),
})
