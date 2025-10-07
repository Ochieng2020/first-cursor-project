import { contextBridge } from 'electron'

contextBridge.exposeInMainWorld('echo', {
  version: '0.1.0'
})
