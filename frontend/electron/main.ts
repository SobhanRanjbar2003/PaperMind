import { app, BrowserWindow, shell, Menu } from 'electron';
import * as path from 'path';

const isDev = !!process.env.ELECTRON_START_URL;
const startUrl =
  process.env.ELECTRON_START_URL ||
  `file://${path.join(__dirname, '..', 'out', process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'fa', 'index.html')}`;

const DEEP_LINK_PROTOCOL = 'PaperMind';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 920,
    minHeight: 600,
    show: false,
    title: 'PaperMind',
    backgroundColor: '#0a0d14',
    autoHideMenuBar: true,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Open external links in default browser, never inside the window
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  mainWindow.loadURL(startUrl);

  if (isDev) {
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

// Hide the menu bar on Linux/Windows; native macOS menu stays
if (process.platform !== 'darwin') {
  Menu.setApplicationMenu(null);
}

// Deep link: PaperMind://jobs/<id>
if (process.defaultApp) {
  if (process.argv.length >= 2) {
    app.setAsDefaultProtocolClient(DEEP_LINK_PROTOCOL, process.execPath, [
      path.resolve(process.argv[1] ?? ''),
    ]);
  }
} else {
  app.setAsDefaultProtocolClient(DEEP_LINK_PROTOCOL);
}

const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', (_e, argv) => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
    const deepLink = argv.find((arg) => arg.startsWith(`${DEEP_LINK_PROTOCOL}://`));
    if (deepLink) {
      handleDeepLink(deepLink);
    }
  });

  app.on('open-url', (event, url) => {
    event.preventDefault();
    handleDeepLink(url);
  });

  app.whenReady().then(createWindow);
}

function handleDeepLink(url: string) {
  if (!mainWindow) return;
  // PaperMind://jobs/<id>  ->  /<locale>/jobs/<id>
  const stripped = url.replace(`${DEEP_LINK_PROTOCOL}://`, '');
  const locale = process.env.NEXT_PUBLIC_DEFAULT_LOCALE || 'fa';
  const target = isDev
    ? `${startUrl.replace(/\/$/, '')}/${locale}/${stripped}`
    : `file://${path.join(__dirname, '..', 'out', locale, stripped, 'index.html')}`;
  mainWindow.loadURL(target);
}

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
