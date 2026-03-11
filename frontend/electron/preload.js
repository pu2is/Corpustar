import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  selectDocumentFile: () => ipcRenderer.invoke('select-document-file'),
})
