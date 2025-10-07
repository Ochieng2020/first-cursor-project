import React, { useEffect, useMemo, useRef, useState } from 'react'
import { ApiClient } from '../../shared/src/api'
import type { Message } from '../../shared/src/types'

export const App: React.FC = () => {
  const [baseUrl, setBaseUrl] = useState<string>(localStorage.getItem('baseUrl') || 'http://localhost:8000')
  const [token, setToken] = useState<string | undefined>(localStorage.getItem('token') || undefined)
  const [userId, setUserId] = useState<string | undefined>(localStorage.getItem('userId') || undefined)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState(false)
  const [dark, setDark] = useState<boolean>(localStorage.getItem('dark') === '1')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('dark', dark ? '1' : '0')
  }, [dark])

  const api = useMemo(() => new ApiClient({ baseUrl, getToken: () => token }), [baseUrl, token])

  async function doLogin() {
    const t = await api.login(email, password)
    setToken(t.access_token)
    localStorage.setItem('token', t.access_token)
    const me = await api.register(email, password).catch(() => null)
    if (me) {
      setUserId(me.id)
      localStorage.setItem('userId', me.id)
    } else {
      // fetch memories to ensure auth works
      const mems = await api.listMemories()
      if (mems.length && mems[0].user_id) {
        setUserId(mems[0].user_id)
        localStorage.setItem('userId', mems[0].user_id)
      }
    }
  }

  async function sendMessage() {
    if (!userId) return
    const userMsg: Message = { id: crypto.randomUUID(), userId, role: 'user', content: input, createdAt: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setStreaming(true)
    let assistantContent = ''
    await api.chat(userId, userMsg.content, (t) => {
      assistantContent += t
      setMessages(prev => {
        const cloned = [...prev]
        const lastIsAssistant = cloned[cloned.length - 1]?.role === 'assistant'
        if (lastIsAssistant) {
          cloned[cloned.length - 1] = { ...cloned[cloned.length - 1], content: assistantContent }
        } else {
          cloned.push({ id: crypto.randomUUID(), userId, role: 'assistant', content: assistantContent, createdAt: new Date().toISOString() })
        }
        return cloned
      })
    })
    setStreaming(false)
  }

  return (
    <div className="h-screen flex flex-col bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100">
      <header className="p-3 border-b border-zinc-200 dark:border-zinc-800 flex items-center gap-3">
        <input className="border rounded px-2 py-1 w-72 dark:bg-zinc-800" value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="Backend URL" />
        <button className="px-3 py-1 border rounded" onClick={()=>setDark(d=>!d)}>{dark? 'Light':'Dark'}</button>
        <div className="ml-auto flex items-center gap-2">
          <input className="border rounded px-2 py-1 dark:bg-zinc-800" placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} />
          <input className="border rounded px-2 py-1 dark:bg-zinc-800" placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} />
          <button className="px-3 py-1 border rounded" onClick={doLogin}>Login</button>
        </div>
      </header>
      <main className="flex-1 grid grid-cols-4">
        <section className="col-span-3 flex flex-col">
          <div className="flex-1 overflow-auto p-4 space-y-2">
            {messages.map((m, i) => (
              <div key={i} className={m.role==='user'? 'text-right': 'text-left'}>
                <div className={"inline-block px-3 py-2 rounded max-w-[70%] " + (m.role==='user'? 'bg-blue-600 text-white':'bg-zinc-100 dark:bg-zinc-800') }>{m.content}</div>
              </div>
            ))}
          </div>
          <div className="p-3 border-t border-zinc-200 dark:border-zinc-800 flex gap-2">
            <input className="flex-1 border rounded px-3 py-2 dark:bg-zinc-800" value={input} onChange={e=>setInput(e.target.value)} placeholder="Say hi to Echo" />
            <button className="px-4 py-2 border rounded" disabled={!userId || !input || streaming} onClick={sendMessage}>Send</button>
          </div>
        </section>
        <aside className="col-span-1 border-l border-zinc-200 dark:border-zinc-800 p-3 space-y-3">
          <h2 className="font-semibold">Memory</h2>
          {/* Placeholder list via live fetch on demand */}
          <button className="px-3 py-1 border rounded w-full" onClick={async()=>{
            try {
              const mems = await api.listMemories();
              alert(mems.map((m: any)=>`- ${m.content}`).join('\n'))
            } catch (e:any) {
              alert(e.message)
            }
          }}>View memories</button>
          <h2 className="font-semibold">Settings</h2>
          <button className="px-3 py-1 border rounded w-full" onClick={()=>{localStorage.clear(); location.reload()}}>Clear local</button>
        </aside>
      </main>
    </div>
  )
}
