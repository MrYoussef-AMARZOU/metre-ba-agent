const { app, BrowserWindow, ipcMain, dialog, shell } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

let mainWindow;
let pythonProcess = null;
let apiReady = false;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    titleBarStyle: 'hiddenInset',
    title: 'Métré BA Agent',
    icon: path.join(__dirname, 'assets', 'icon.png'),
  });

  mainWindow.loadFile(path.join(__dirname, 'src', 'index.html'));
}

function startPythonBackend() {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const apiPath = path.join(__dirname, '..', 'backend', 'api.py');

  pythonProcess = spawn(pythonCmd, ['-m', 'uvicorn', 'backend.api:app',
    '--host', '127.0.0.1', '--port', '8765', '--reload'],
    { cwd: path.join(__dirname, '..'), stdio: ['pipe', 'pipe', 'pipe'] });

  pythonProcess.stdout.on('data', (data) => {
    const msg = data.toString();
    if (msg.includes('Uvicorn running')) {
      apiReady = true;
      if (mainWindow) mainWindow.webContents.send('api-ready');
    }
  });

  pythonProcess.stderr.on('data', (data) => {
    // uvicorn logs to stderr
    const msg = data.toString();
    if (msg.includes('Uvicorn running')) {
      apiReady = true;
      if (mainWindow) mainWindow.webContents.send('api-ready');
    }
  });

  pythonProcess.on('close', () => {
    apiReady = false;
    pythonProcess = null;
  });
}

app.whenReady().then(() => {
  createWindow();
  startPythonBackend();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) pythonProcess.kill();
  app.quit();
});

app.on('before-quit', () => {
  if (pythonProcess) pythonProcess.kill();
});

// IPC handlers
ipcMain.handle('select-pdf', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [{ name: 'PDF', extensions: ['pdf'] }, { name: 'Images', extensions: ['png', 'jpg', 'jpeg'] }]
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('select-xlsx', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openFile'],
    filters: [{ name: 'Excel', extensions: ['xlsx', 'xlsm'] }]
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('open-output', async (event, filePath) => {
  shell.showItemInFolder(filePath);
});

ipcMain.handle('download-file', async (event, filePath) => {
  const result = await dialog.showSaveDialog(mainWindow, {
    defaultPath: path.basename(filePath),
  });
  if (!result.canceled) {
    fs.copyFileSync(filePath, result.filePath);
    return result.filePath;
  }
  return null;
});

ipcMain.handle('get-api-status', () => apiReady);
