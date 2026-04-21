import{useState}from 'react'
import{scoreLead,LeadScoreRequest,LeadScoreResponse}from '../../services/api'
import TopBar from '../layout/TopBar'
import toast from 'react-hot-toast'

const Bar=({label,value,color}:{label:string;value:number;color:string})=>(
<div><div className="flex justify-between text-xs text-slate-400 mb-1"><span>{label}</span><span className="font-bold text-white">{value.toFixed(0)}/100</span></div>
<div className="h-2 bg-slate-800 rounded-full overflow-hidden"><div className={`h-full ${color} rounded-full transition-all duration-700`} style={{width:`${value}%`}}/></div></div>)

export default function LeadScoring(){
  const[form,setForm]=useState<LeadScoreRequest>({client_name:'',budget_aed:0,property_type:'apartment',location_preference:'',bedrooms:undefined,timeline_months:undefined,num_interactions:0,avg_response_hours:24,message_quality_score:0.5,source:'web'})
  const[result,setResult]=useState<LeadScoreResponse|null>(null)
  const[loading,setLoading]=useState(false)
  const up=(k:keyof LeadScoreRequest,v:any)=>setForm(p=>({...p,[k]:v}))
  const tier={HOT:{cls:'text-red-400',bg:'border-red-500/30 bg-red-500/5',label:'🔥 HOT LEAD'},WARM:{cls:'text-amber-400',bg:'border-amber-500/30 bg-amber-500/5',label:'☀️ WARM LEAD'},COLD:{cls:'text-blue-400',bg:'border-blue-500/30 bg-blue-500/5',label:'❄️ COLD LEAD'}}

  const handleSubmit=async(e:React.FormEvent)=>{
    e.preventDefault()
    if(!form.client_name){toast.error('Client name required');return}
    setLoading(true)
    try{const r=await scoreLead(form);setResult(r.data);toast.success(`${r.data.tier} — Score: ${r.data.score.toFixed(0)}`)}
    catch{toast.error('Scoring failed. Ensure backend is running.')}
    finally{setLoading(false)}
  }

  const DEMO_LEADS=[
    {client_name:'Ahmed Al Mansoori',budget_aed:2500000,property_type:'villa',location_preference:'Dubai Hills Estate',bedrooms:3,timeline_months:1,num_interactions:8,avg_response_hours:0.5,message_quality_score:0.9,source:'referral'},
    {client_name:'Sarah Johnson',budget_aed:1200000,property_type:'apartment',location_preference:'Dubai Marina',bedrooms:2,timeline_months:6,num_interactions:2,avg_response_hours:24,message_quality_score:0.5,source:'portal'},
    {client_name:'Unknown Visitor',budget_aed:0,property_type:'studio',location_preference:'',bedrooms:undefined,timeline_months:24,num_interactions:0,avg_response_hours:96,message_quality_score:0.1,source:'web'},
  ]

  return(
<div>
  <TopBar title="Lead Scoring" subtitle="XGBoost ML (60%) + Gemini LLM (40%) ensemble · Trained on 3,000 synthetic records · SHAP explainability"/>
  <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
    <div className="space-y-4">
      {/* Quick demos */}
      <div className="card">
        <p className="text-xs text-slate-400 mb-3 font-medium">QUICK DEMO LEADS</p>
        <div className="grid grid-cols-3 gap-2">
          {DEMO_LEADS.map((d,i)=>(
            <button key={i} onClick={()=>setForm(p=>({...p,...d}))}
              className={`text-xs p-2 rounded-xl border transition-all text-left ${i===0?'border-red-500/30 bg-red-500/5 text-red-400':i===1?'border-amber-500/30 bg-amber-500/5 text-amber-400':'border-blue-500/30 bg-blue-500/5 text-blue-400'}`}>
              <div className="font-bold">{i===0?'HOT':i===1?'WARM':'COLD'}</div>
              <div className="text-slate-400 mt-0.5 truncate">{d.client_name}</div>
            </button>
          ))}
        </div>
      </div>
      {/* Form */}
      <div className="card">
        <h2 className="text-sm font-semibold text-white mb-4">Lead Details</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-400 mb-1 block">Client Name *</label><input className="input" placeholder="Ahmed Al Mansoori" value={form.client_name} onChange={e=>up('client_name',e.target.value)}/></div>
            <div><label className="text-xs text-slate-400 mb-1 block">Budget (AED)</label><input type="number" className="input" placeholder="2000000" value={form.budget_aed||''} onChange={e=>up('budget_aed',Number(e.target.value))}/></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-400 mb-1 block">Property Type</label><select className="select" value={form.property_type} onChange={e=>up('property_type',e.target.value)}>{['apartment','villa','townhouse','penthouse','studio'].map(t=><option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}</select></div>
            <div><label className="text-xs text-slate-400 mb-1 block">Location Preference</label><input className="input" placeholder="Dubai Hills, Marina…" value={form.location_preference} onChange={e=>up('location_preference',e.target.value)}/></div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="text-xs text-slate-400 mb-1 block">Bedrooms</label><input type="number" className="input" placeholder="3" value={form.bedrooms||''} onChange={e=>up('bedrooms',Number(e.target.value)||undefined)}/></div>
            <div><label className="text-xs text-slate-400 mb-1 block">Timeline (months)</label><input type="number" className="input" placeholder="2" value={form.timeline_months||''} onChange={e=>up('timeline_months',Number(e.target.value)||undefined)}/></div>
            <div><label className="text-xs text-slate-400 mb-1 block">Interactions</label><input type="number" className="input" placeholder="5" value={form.num_interactions||''} onChange={e=>up('num_interactions',Number(e.target.value))}/></div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div><label className="text-xs text-slate-400 mb-1 block">Avg Response (hrs)</label><input type="number" className="input" placeholder="2" value={form.avg_response_hours||''} onChange={e=>up('avg_response_hours',Number(e.target.value))}/></div>
            <div><label className="text-xs text-slate-400 mb-1 block">Source</label><select className="select" value={form.source} onChange={e=>up('source',e.target.value)}>{['web','referral','portal','agent','social media'].map(s=><option key={s} value={s}>{s.charAt(0).toUpperCase()+s.slice(1)}</option>)}</select></div>
          </div>
          <div><label className="text-xs text-slate-400 mb-1 block">Message Quality: {((form.message_quality_score||0)*100).toFixed(0)}%</label><input type="range" min="0" max="1" step="0.05" className="w-full accent-brand-500" value={form.message_quality_score} onChange={e=>up('message_quality_score',Number(e.target.value))}/></div>
          <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
            {loading?<span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/>:null}
            {loading?'Scoring Lead…':'Score This Lead'}
          </button>
        </form>
      </div>
    </div>

    {/* Result */}
    {result?(
      <div className="space-y-4">
        <div className={`card border ${tier[result.tier].bg}`}>
          <div className="flex items-center justify-between mb-4">
            <div><div className="text-4xl font-black text-white">{result.score.toFixed(0)}<span className="text-lg text-slate-400">/100</span></div><div className="text-slate-400 text-sm mt-1">{result.client_name}</div></div>
            <div className={`text-2xl font-black ${tier[result.tier].cls}`}>{tier[result.tier].label}</div>
          </div>
          <div className="bg-slate-800 rounded-xl p-3 text-sm text-brand-300 mb-3 border border-slate-700">💡 {result.recommended_action}</div>
          <p className="text-slate-400 text-xs leading-relaxed">{result.reasoning}</p>
        </div>
        <div className="card space-y-3">
          <h3 className="text-sm font-semibold text-white">Score Breakdown</h3>
          <Bar label="Budget Alignment" value={result.budget_score} color="bg-emerald-500"/>
          <Bar label="Urgency Score" value={result.urgency_score} color="bg-amber-500"/>
          <Bar label="Engagement Score" value={result.engagement_score} color="bg-brand-500"/>
          <Bar label="Property Match" value={result.property_match_score} color="bg-purple-500"/>
          <Bar label="Communication Quality" value={result.communication_score} color="bg-pink-500"/>
        </div>
        {result.shap_top_features.length>0&&(
          <div className="card">
            <h3 className="text-sm font-semibold text-white mb-3">SHAP Attribution — Top 5 Factors</h3>
            <div className="space-y-2">
              {result.shap_top_features.map((f,i)=>(
                <div key={i} className="flex items-center justify-between">
                  <span className="text-xs text-slate-400 capitalize">{f.feature.replace(/_/g,' ')}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs ${f.direction.includes('increases')?'text-emerald-400':'text-red-400'}`}>{f.direction.includes('increases')?'▲ increases':'▼ decreases'} score</span>
                    <span className="text-xs font-mono text-white bg-slate-800 px-2 py-0.5 rounded">{f.shap_value.toFixed(3)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    ):(
      <div className="card flex flex-col items-center justify-center min-h-64 text-center">
        <div className="text-5xl mb-4">🎯</div>
        <p className="text-slate-400 text-sm">Use a demo lead above or fill the form, then click <strong className="text-white">Score This Lead</strong> to get instant AI scoring with SHAP explainability.</p>
        <p className="text-slate-500 text-xs mt-2">Model trained on 3,000 synthetic records • XGBoost + Gemini ensemble</p>
      </div>
    )}
  </div>
</div>
)}
