import React, { useMemo, useState } from 'react'
import { SafeAreaView, View } from 'react-native'
import { Provider as PaperProvider, Button, TextInput, Text } from 'react-native-paper'
import { ApiClient } from '../../shared/src/api'

export default function App() {
  const [baseUrl, setBaseUrl] = useState('http://localhost:8000')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [token, setToken] = useState<string | undefined>()
  const [userId, setUserId] = useState<string | undefined>()
  const [input, setInput] = useState('')
  const [reply, setReply] = useState('')

  const api = useMemo(() => new ApiClient({ baseUrl, getToken: () => token }), [baseUrl, token])

  async function login() {
    const t = await api.login(email, password)
    setToken(t.access_token)
  }

  async function send() {
    if (!userId) return
    let collected = ''
    await api.chat(userId, input, (t) => {
      collected += t
      setReply(collected)
    })
  }

  return (
    <PaperProvider>
      <SafeAreaView>
        <View style={{ padding: 16, gap: 12 }}>
          <Text variant="titleMedium">Echo Mobile</Text>
          <TextInput label="Backend URL" value={baseUrl} onChangeText={setBaseUrl} />
          <TextInput label="Email" value={email} onChangeText={setEmail} />
          <TextInput label="Password" value={password} secureTextEntry onChangeText={setPassword} />
          <Button mode="contained" onPress={login}>Login</Button>
          <TextInput label="User ID" value={userId} onChangeText={setUserId} />
          <TextInput label="Message" value={input} onChangeText={setInput} />
          <Button mode="contained" onPress={send}>Send</Button>
          <Text>{reply}</Text>
        </View>
      </SafeAreaView>
    </PaperProvider>
  )
}
