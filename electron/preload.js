const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  // File dialogs
  selectPdf: () => ipcRenderer.invoke('select-pdf'),
  selectXlsx: () => ipcRenderer.invoke('select-xlsx'),

  // File operations
  openOutput: (path) => ipcRenderer.invoke('open-output', path),
  downloadFile: (path) => ipcRenderer.invoke('download-file', path),

  // Status
  getApiStatus: () => ipcRenderer.invoke('get-api-status'),
  getAppUrl: () => ipcRenderer.invoke('get-app-url'),

  // External
  openExternal: (url) => ipcRenderer.invoke('open-external', url),
  openLogFile: () => ipcRenderer.invoke('open-log-file'),
  useLocalServer: () => ipcRenderer.invoke('use-local-server'),

  // Event listeners
  onApiReady: (callback) => ipcRenderer.on('api-ready', callback),
  onBackendStopped: (callback) => ipcRenderer.on('backend-stopped', callback),
  onAppUrl: (callback) => ipcRenderer.on('app-url', (event, url) => callback(url)),
  onShowAbout: (callback) => ipcRenderer.on('show-about', callback),
});