import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  selectDocumentFile: () => ipcRenderer.invoke('select-document-file'),
  selectRuleFile: () => ipcRenderer.invoke('select-rule-file'),
  readDocumentText: (filePath) => ipcRenderer.invoke('read-document-text', filePath),
  selectSavePath: (defaultFilename: string) => ipcRenderer.invoke('select-save-path', defaultFilename),
})
