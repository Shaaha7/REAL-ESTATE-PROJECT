import{useState,useEffect}from 'react'
import{getHealth}from '../../services/api'
export default function TopBar({title,subtitle}:{title:string;subtitle?:string}){
  const[health,setHealth]=useState<any>(null)
  useEffect(()=>{getHealth().then(r=>setHealth(r.data)).catch(()=>{})},[])
  return(
  <div className="flex items-center justify-between mb-8">
    <div><h1 className="text-2xl font-bold text-white">{title}</h1>{subtitle&&<p className="text-slate-400 text-sm mt-1">{subtitle}</p>}</div>
    <div className="flex items-center gap-3">
      {health&&<div className="flex items-center gap-2 bg-slate-800 rounded-xl px-3 py-2 border border-slate-700">
        <div className={`w-2 h-2 rounded-full animate-pulse ${health.status==='healthy'?'bg-emerald-400':'bg-red-400'}`}/>
        <span className="text-xs text-slate-400">{health.model||'gemini-1.5-flash'}</span>
        <span className="text-xs text-slate-600">|</span>
        <span className="text-xs text-slate-400">{health.rag_chunks} chunks</span>
      </div>}
    </div>
  </div>
)}
