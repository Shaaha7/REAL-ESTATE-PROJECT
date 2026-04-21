import{useState}from 'react'
import{runRAGASEval}from '../../services/api'
import TopBar from '../layout/TopBar'
import{BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,RadarChart,Radar,PolarGrid,PolarAngleAxis}from 'recharts'
import toast from 'react-hot-toast'

const TT=(p:any)=><Tooltip {...p} contentStyle={{background:'#1e293b',border:'1px solid #334155',borderRadius:12,color:'#f1f5f9',fontSize:11}}/>

export default function Evaluation(){
  const[results,setResults]=useState<any>(null)
  const[loading,setLoading]=useState(false)
  const run=async()=>{setLoading(true);try{const r=await runRAGASEval();setResults(r.data);toast.success('Evaluation complete!')}catch{toast.error('Evaluation failed')}finally{setLoading(false)}}
  const s=results?.summary
  const radarData=s?[{m:'Faithfulness',v:+(s.faithfulness*100).toFixed(1)},{m:'Answer Relevancy',v:+(s.answer_relevancy*100).toFixed(1)},{m:'Context Precision',v:+(s.context_precision*100).toFixed(1)},{m:'Context Recall',v:+(s.context_recall*100).toFixed(1)}]:[]
  const barData=results?.per_query_results?.map((r:any,i:number)=>({name:`Q${i+1}`,faith:Math.round(r.faithfulness*100),relev:Math.round(r.answer_relevancy*100),prec:Math.round(r.context_precision*100)}))

  return(
<div>
  <TopBar title="RAGAS Evaluation" subtitle="Automated faithfulness · answer relevancy · context precision · context recall · hallucination rate"/>
  <div className="flex items-center gap-4 mb-8">
    <button className="btn-primary" onClick={run} disabled={loading}>{loading?<span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/>:'▶'}{loading?'Running…':'Run RAGAS Evaluation'}</button>
    <p className="text-slate-500 text-sm">Tests RAG pipeline against {results?.summary?.num_queries||15} benchmark queries from <code className="text-slate-400">data/evaluation/ragas_test_queries.json</code></p>
  </div>
  {s&&<div className="space-y-6">
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[{label:'Faithfulness',value:s.faithfulness.toFixed(4),target:'≥ 0.97',met:s.faithfulness_achieved,color:'text-emerald-400'},
        {label:'Answer Relevancy',value:s.answer_relevancy.toFixed(4),target:'> 0.88',met:s.answer_relevancy>0.88,color:'text-brand-400'},
        {label:'Context Precision',value:s.context_precision.toFixed(4),target:'> 0.85',met:s.context_precision>0.85,color:'text-purple-400'},
        {label:'Hallucination Rate',value:`${(s.hallucination_rate*100).toFixed(2)}%`,target:'< 2%',met:s.hallucination_target_met,color:'text-amber-400'}].map(m=>(
        <div key={m.label} className={`card border ${m.met?'border-emerald-500/30':'border-red-500/30'}`}>
          <div className="text-xs text-slate-400 mb-1">{m.label}</div>
          <div className={`text-2xl font-bold ${m.color} mb-1`}>{m.value}</div>
          <div className={`text-xs ${m.met?'text-emerald-400':'text-red-400'}`}>Target: {m.target} {m.met?'✓':'✗'}</div>
        </div>
      ))}
    </div>
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card">
        <h3 className="font-semibold text-white text-sm mb-4">RAGAS Radar</h3>
        <ResponsiveContainer width="100%" height={220}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#334155"/>
            <PolarAngleAxis dataKey="m" tick={{fill:'#94a3b8',fontSize:11}}/>
            <Radar dataKey="v" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.2}/>
            <TT formatter={(v:any)=>[`${Number(v).toFixed(1)}%`]}/>
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <div className="card">
        <h3 className="font-semibold text-white text-sm mb-4">Per Query — Faithfulness & Relevancy</h3>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={barData} margin={{left:-20}}>
            <XAxis dataKey="name" tick={{fill:'#94a3b8',fontSize:10}} axisLine={false} tickLine={false}/>
            <YAxis tick={{fill:'#94a3b8',fontSize:10}} axisLine={false} tickLine={false} domain={[0,100]}/>
            <TT/>
            <Bar dataKey="faith" fill="#0ea5e9" radius={[3,3,0,0]} name="Faithfulness"/>
            <Bar dataKey="relev" fill="#a78bfa" radius={[3,3,0,0]} name="Relevancy"/>
            <Bar dataKey="prec" fill="#34d399" radius={[3,3,0,0]} name="Precision"/>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
    <div className="card overflow-x-auto">
      <h3 className="font-semibold text-white text-sm mb-4">Per Query Results ({results.per_query_results.length} questions)</h3>
      <table className="w-full text-xs">
        <thead><tr className="text-slate-500 border-b border-slate-800 text-left">{['#','Question','Faithfulness','Relevancy','Precision','Recall'].map(h=><th key={h} className="py-2 px-3 font-medium">{h}</th>)}</tr></thead>
        <tbody>{results.per_query_results.map((r:any,i:number)=>(
          <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
            <td className="py-2.5 px-3 text-slate-500">Q{i+1}</td>
            <td className="py-2.5 px-3 text-slate-300 max-w-xs">{r.question}</td>
            <td className="py-2.5 px-3 font-mono text-emerald-400">{r.faithfulness.toFixed(4)}</td>
            <td className="py-2.5 px-3 font-mono text-brand-400">{r.answer_relevancy.toFixed(4)}</td>
            <td className="py-2.5 px-3 font-mono text-purple-400">{r.context_precision.toFixed(4)}</td>
            <td className="py-2.5 px-3 font-mono text-amber-400">{r.context_recall.toFixed(4)}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  </div>}
  {!results&&!loading&&<div className="card flex flex-col items-center justify-center py-24 text-center">
    <div className="text-5xl mb-4">🧪</div>
    <h3 className="font-semibold text-white mb-2">Run RAGAS Evaluation</h3>
    <p className="text-slate-400 text-sm max-w-md">Evaluates the RAG pipeline against 15 benchmark Dubai real estate questions measuring faithfulness, hallucination rate, and retrieval quality.</p>
  </div>}
</div>
)}
