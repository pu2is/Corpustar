import { spawn } from 'node:child_process'
import { FRONTEND_DEV_URL } from '../config/ports.mjs'

const command = `wait-on ${FRONTEND_DEV_URL} && electron .`

const child = spawn(command, {
  shell: true,
  stdio: 'inherit',
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})
