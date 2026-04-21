import{useState,useRef,useEffect}from 'react'
import{agentChat}from '../../services/api'
import TopBar from '../layout/TopBar'
import toast from 'react-hot-toast'

interface Msg{role:'user'|'assistant';content:string;steps?:any[];latency?:number;ts:Date}

const STARTERS=['Score this lead: Ahmed Al Mansoori, AED 2.5M, 3BR villa Dubai Hills, 1 month, 8 interactions, referral','Search for 2BR apartments in Dubai Marina under AED 1.5M','What are the DLD transfer fees when buying property in Dubai?','Draft a follow-up email for a warm lead interested in Business Bay canal view apartments','Explain what RERA regulates and how to verify a developer is registered','What is the Golden Visa property investment criteria?']

export default function AgentChat(){
  const[msgs,setMsgs]=useState<Msg[]>([{role:'assistant',content:"Hello! I'm your PropAI Agent powered by LangChain + Gemini. I can score leads (XGBoost+LLM), search 10 Dubai properties, answer real estate knowledge questions using the FAISS RAG pipeline, and draft client emails. What can I help you with?",ts:new Date()}])
  const[input,setInput]=useState('')
  const[loading,setLoading]=useState(false)
  const[sessionId]=useState(()=>`session-${Date.now()}`)
  const bottomRef=useRef<HTMLDivElement>(null)
  useEffect(()=>{bottomRef.current?.scrollIntoView({behavior:'smooth'})},[msgs])

  const send=async(msg?:string)=>{
    const text=msg||input; if(!text.trim()) return
    setInput(''); setMsgs(p=>[...p,{role:'user',content:text,ts:new Date()}]); setLoading(true)
    try{
      const r=await agentChat(text,sessionId); const d=r.data
      let content=''
      if(typeof d.output==='string') content=d.output
      else if(d.output?.response) content=d.output.response
      else if(d.output?.answer) content=d.output.answer
      else content=JSON.stringify(d.output,null,2)
      setMsgs(p=>[...p,{role:'assistant',content,steps:d.intermediate_steps,latency:d.latency_ms,ts:new Date()}])
    }catch(e){
      toast.error('Agent error. Check backend is running with API key.')
      setMsgs(p=>[...p,{role:'assistant',content:'Sorry, I encountered an error. Please ensure the backend is running and the API key is set in .env.',ts:new Date()}])
    }finally{setLoading(false)}
  }

  return(
<div>
  <TopBar title="AI Agent Chat" subtitle="LangChain Orchestrator → Lead Scoring + Property Search + RAG + Communication agents"/>
  <div className="grid grid-cols-1 xl:grid-cols-4 gap-8">
    <div className="xl:col-span-3 flex flex-col h-[72vh]">
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {msgs.map((m,i)=>(
          <div key={i} className={`flex ${m.role==='user'?'justify-end':'justify-start'}`}>
            <div className={`max-w-[82%] ${m.role==='user'?'bg-brand-600 text-white rounded-2xl rounded-tr-md':'bg-slate-800 text-slate-200 rounded-2xl rounded-tl-md border border-slate-700'} px-4 py-3 text-sm leading-relaxed`}>
              <pre className="whitespace-pre-wrap font-sans">{m.content}</pre>
              {m.latency&&<div className="text-xs opacity-40 mt-1">{m.latency.toFixed(0)}ms · {msgs[0]?.content?'gemini':'?'}</div>}
              {m.steps&&m.steps.length>0&&<div className="mt-2 pt-2 border-t border-slate-700 space-y-1">
                {m.steps.map((s,si)=><div key={si} className="text-xs text-slate-400 flex items-center gap-1"><span className="text-brand-400">⚡</span><span className="font-mono">{s.tool}</span></div>)}
              </div>}
            </div>
          </div>
        ))}
        {loading&&<div className="flex justify-start"><div className="bg-slate-800 rounded-2xl rounded-tl-md px-4 py-3 flex items-center gap-1.5 border border-slate-700">
          {[0,150,300].map(d=><span key={d} className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{animationDelay:`${d}ms`}}/>)}
        </div></div>}
        <div ref={bottomRef}/>
      </div>
      <div className="flex gap-3">
        <input className="input flex-1" placeholder="Ask the PropAI agent anything…" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&send()} disabled={loading}/>
        <button className="btn-primary px-6" onClick={()=>send()} disabled={loading||!input.trim()}>Send</button>
      </div>
    </div>
    <div className="space-y-4">
      <div className="card"><h3 className="font-semibold text-white text-sm mb-3">Quick Starts</h3>
        <div className="space-y-2">{STARTERS.map((s,i)=><button key={i} onClick={()=>send(s)} disabled={loading} className="w-full text-left text-xs text-slate-400 hover:text-brand-300 hover:bg-slate-800 p-2.5 rounded-lg transition-colors border border-slate-800 hover:border-brand-700">{s}</button>)}</div>
      </div>
      <div className="card"><h3 className="font-semibold text-white text-sm mb-2">Available Tools</h3>
        {[['🎯','Lead Scoring (XGBoost+LLM)'],['🏠','Property Search (10 listings)'],['📚','Knowledge Base (RAG)'],['✉️','Email Drafting'],['🔍','SHAP Explainability']].map(([icon,label])=><div key={label as string} className="flex items-center gap-2 py-1.5 text-xs text-slate-400"><span>{icon}</span><span>{label}</span></div>)}
      </div>
    </div>
  </div>
</div>
)}
