import { app, BrowserWindow, dialog, ipcMain } from 'electron'
import { readFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { FRONTEND_DEV_URL } from '../config/ports.mjs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

function createWindow() {
  const windowIcon = path.join(__dirname, 'icon_corpustar.png')

  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    icon: windowIcon,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      preload: path.join(__dirname, 'preload.cjs'),
    },
  })

  if (!app.isPackaged) {
    win.loadURL(FRONTEND_DEV_URL)
    win.webContents.openDevTools()
  } else {
    win.loadFile(path.join(__dirname, '../dist/index.html'))
  }
}

ipcMain.handle('select-document-file', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  const result = await dialog.showOpenDialog(win, {
    properties: ['openFile'],
    filters: [
      {
        name: 'Supported Documents',
        extensions: ['txt', 'doc', 'docx', 'odt'],
      },
    ],
  })

  if (result.canceled || result.filePaths.length === 0) {
    return null
  }

  return path.resolve(result.filePaths[0])
})

ipcMain.handle('select-rule-file', async (event) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  const result = await dialog.showOpenDialog(win, {
    properties: ['openFile'],
    filters: [
      {
        name: 'CSV Files',
        extensions: ['csv'],
      },
    ],
  })

  if (result.canceled || result.filePaths.length === 0) {
    return null
  }

  return path.resolve(result.filePaths[0])
})

async function handleReadDocumentText(_event, filePath) {
  if (typeof filePath !== 'string' || !filePath.trim()) {
    throw new Error('A valid text file path is required.')
  }

  const absolutePath = path.resolve(filePath)
  return readFile(absolutePath, 'utf-8')
}

ipcMain.handle('read-document-text', handleReadDocumentText)

ipcMain.handle('select-save-path', async (event, defaultFilename) => {
  const win = BrowserWindow.fromWebContents(event.sender)
  const result = await dialog.showSaveDialog(win, {
    defaultPath: defaultFilename,
    filters: [{ name: 'CSV Files', extensions: ['csv'] }],
  })

  if (result.canceled || !result.filePath) {
    return null
  }

  const fullPath = path.resolve(result.filePath)
  return { dir: path.dirname(fullPath), filename: path.basename(fullPath) }
})
ipcMain.handle('red-document-text', handleReadDocumentText)

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})
