import{useState,useEffect}from 'react'
import{getSampleLeads,SampleLead}from '../../services/api'
import TopBar from '../layout/TopBar'
import toast from 'react-hot-toast'

const TIER_STYLE:Record<string,string>={HOT:'badge-hot',WARM:'badge-warm',COLD:'badge-cold'}

export default function LeadsList(){
  const[leads,setLeads]=useState<SampleLead[]>([])
  const[filtered,setFiltered]=useState<SampleLead[]>([])
  const[loading,setLoading]=useState(true)
  const[filter,setFilter]=useState({tier:'',source:'',search:''})

  useEffect(()=>{getSampleLeads().then(r=>{setLeads(r.data.leads);setFiltered(r.data.leads)}).catch(()=>toast.error('Could not load leads')).finally(()=>setLoading(false))},[])

  useEffect(()=>{
    let r=leads
    if(filter.tier) r=r.filter(l=>l.tier===filter.tier)
    if(filter.source) r=r.filter(l=>l.source===filter.source)
    if(filter.search) r=r.filter(l=>l.client_name.toLowerCase().includes(filter.search.toLowerCase())||l.location_preference.toLowerCase().includes(filter.search.toLowerCase()))
    setFiltered(r)
  },[filter,leads])

  const sources=[...new Set(leads.map(l=>l.source))]

  return(
<div>
  <TopBar title="All Leads — 200 Records" subtitle="200 synthetic leads with realistic scores, tiers, and demographics"/>
  <div className="card mb-6">
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <input className="input" placeholder="Search by name or location…" value={filter.search} onChange={e=>setFilter(p=>({...p,search:e.target.value}))}/>
      <select className="select" value={filter.tier} onChange={e=>setFilter(p=>({...p,tier:e.target.value}))}>
        <option value="">All Tiers</option>
        {['HOT','WARM','COLD'].map(t=><option key={t} value={t}>{t}</option>)}
      </select>
      <select className="select" value={filter.source} onChange={e=>setFilter(p=>({...p,source:e.target.value}))}>
        <option value="">All Sources</option>
        {sources.map(s=><option key={s} value={s}>{s}</option>)}
      </select>
    </div>
    <div className="mt-3 text-xs text-slate-500">Showing {filtered.length} of {leads.length} leads</div>
  </div>
  {loading?<div className="flex items-center justify-center h-32"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"/></div>:(
  <div className="card overflow-x-auto">
    <table className="w-full text-sm">
      <thead><tr className="text-xs text-slate-500 border-b border-slate-800 text-left">
        {['ID','Name','Budget (AED)','Type','Location','Score','Tier','Source','Status'].map(h=><th key={h} className="py-3 px-3 font-medium">{h}</th>)}
      </tr></thead>
      <tbody>
        {filtered.map(l=>(
          <tr key={l.lead_id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
            <td className="py-3 px-3 font-mono text-xs text-slate-500">{l.lead_id}</td>
            <td className="py-3 px-3 font-medium text-white">{l.client_name}</td>
            <td className="py-3 px-3 text-slate-300">AED {l.budget_aed.toLocaleString()}</td>
            <td className="py-3 px-3 text-slate-400 capitalize">{l.property_type}</td>
            <td className="py-3 px-3 text-slate-400 max-w-[120px] truncate">{l.location_preference}</td>
            <td className="py-3 px-3">
              <div className="flex items-center gap-1">
                <div className="h-1.5 rounded-full bg-slate-700 flex-1 max-w-[60px]"><div className="h-full rounded-full bg-brand-500" style={{width:`${l.lead_score}%`}}/></div>
                <span className="text-xs font-mono text-white">{l.lead_score}</span>
              </div>
            </td>
            <td className="py-3 px-3"><span className={TIER_STYLE[l.tier]}>{l.tier}</span></td>
            <td className="py-3 px-3 text-slate-400 capitalize">{l.source}</td>
            <td className="py-3 px-3 text-slate-400 capitalize text-xs">{l.status}</td>
          </tr>
        ))}
      </tbody>
    </table>
    {filtered.length===0&&<div className="text-center py-12 text-slate-500">No leads match your filters</div>}
  </div>
  )}
</div>
)}
