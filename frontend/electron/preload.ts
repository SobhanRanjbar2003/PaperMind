import { contextBridge } from 'electron';

contextBridge.exposeInMainWorld('PaperMind', {
  platform: process.platform,
  isElectron: true,
  versions: {
    electron: process.versions.electron,
    chrome: process.versions.chrome,
    node: process.versions.node,
  },
});

export {};
