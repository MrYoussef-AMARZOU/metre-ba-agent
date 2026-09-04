const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  selectPdf: () => ipcRenderer.invoke('select-pdf'),
  selectXlsx: () => ipcRenderer.invoke('select-xlsx'),
  openOutput: (path) => ipcRenderer.invoke('open-output', path),
  downloadFile: (path) => ipcRenderer.invoke('download-file', path),
  getApiStatus: () => ipcRenderer.invoke('get-api-status'),
  onApiReady: (callback) => ipcRenderer.on('api-ready', callback),
});
