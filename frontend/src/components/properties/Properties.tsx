import{useState,useEffect}from 'react'
import{getAllProperties,searchProperties,Property}from '../../services/api'
import TopBar from '../layout/TopBar'
import toast from 'react-hot-toast'

const fmt=(p:number)=>p>=1_000_000?`AED ${(p/1_000_000).toFixed(2)}M`:`AED ${p.toLocaleString()}`

function Card({p}:{p:Property}){return(
<div className="card-hover group flex flex-col">
  <div className="h-44 rounded-xl overflow-hidden mb-4 bg-slate-800 flex-shrink-0">
    <img src={p.images[0]} alt={p.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" onError={e=>{(e.target as HTMLImageElement).src='https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800'}}/>
  </div>
  <div className="flex items-start justify-between mb-2 gap-2">
    <h3 className="font-semibold text-white text-sm leading-tight flex-1">{p.title}</h3>
    <span className="text-xs bg-brand-600/20 text-brand-400 border border-brand-600/30 px-2 py-0.5 rounded-lg whitespace-nowrap capitalize flex-shrink-0">{p.property_type}</span>
  </div>
  <div className="text-slate-400 text-xs mb-2">📍 {p.location}</div>
  <p className="text-slate-500 text-xs mb-3 leading-relaxed line-clamp-2">{p.description}</p>
  <div className="text-xl font-bold text-white mb-3">{fmt(p.price)}</div>
  <div className="flex gap-3 text-xs text-slate-400 mb-3">
    <span>🛏 {p.bedrooms>0?p.bedrooms:'Studio'}</span>
    <span>🚿 {p.bathrooms}</span>
    <span>📐 {p.area_sqft?.toLocaleString()} sqft</span>
    {p.yield_pct&&<span className="text-emerald-400 font-semibold ml-auto">{p.yield_pct}% yield</span>}
  </div>
  <div className="flex flex-wrap gap-1 mb-3">
    {p.amenities.slice(0,4).map(a=><span key={a} className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-lg">{a}</span>)}
    {p.amenities.length>4&&<span className="text-xs text-slate-500">+{p.amenities.length-4}</span>}
  </div>
  {p.service_charge_yearly&&<div className="text-xs text-slate-600 mt-auto">Service charge: AED {p.service_charge_yearly.toLocaleString()}/yr</div>}
  {p.match_score&&<div className="mt-2 pt-2 border-t border-slate-800 flex items-center justify-between"><span className="text-xs text-slate-500">Match Score</span><span className="text-xs font-bold text-emerald-400">{(p.match_score*100).toFixed(0)}%</span></div>}
</div>
)}

export default function Properties(){
  const[properties,setProperties]=useState<Property[]>([])
  const[loading,setLoading]=useState(true)
  const[filters,setFilters]=useState({location:'',property_type:'',budget_max:'',bedrooms:''})
  const[searching,setSearching]=useState(false)

  useEffect(()=>{getAllProperties().then(r=>setProperties(r.data.properties)).catch(console.error).finally(()=>setLoading(false))},[])

  const handleSearch=async(e:React.FormEvent)=>{
    e.preventDefault(); setSearching(true)
    try{
      const payload:any={}
      if(filters.location) payload.location=filters.location
      if(filters.property_type) payload.property_type=filters.property_type
      if(filters.budget_max) payload.budget_max=Number(filters.budget_max)
      if(filters.bedrooms) payload.bedrooms=Number(filters.bedrooms)
      const r=await searchProperties(payload); setProperties(r.data.properties)
      toast.success(`Found ${r.data.properties.length} properties`)
    }catch{toast.error('Search failed')}finally{setSearching(false)}
  }

  const handleReset=()=>{setFilters({location:'',property_type:'',budget_max:'',bedrooms:''});setLoading(true);getAllProperties().then(r=>setProperties(r.data.properties)).catch(console.error).finally(()=>setLoading(false))}

  return(
<div>
  <TopBar title="Properties" subtitle="10 Dubai listings with full details, yields, amenities, and images"/>
  <form onSubmit={handleSearch} className="card mb-8">
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
      <input className="input" placeholder="Location…" value={filters.location} onChange={e=>setFilters(p=>({...p,location:e.target.value}))}/>
      <select className="select" value={filters.property_type} onChange={e=>setFilters(p=>({...p,property_type:e.target.value}))}>
        <option value="">All Types</option>
        {['apartment','villa','townhouse','penthouse','studio'].map(t=><option key={t} value={t}>{t.charAt(0).toUpperCase()+t.slice(1)}</option>)}
      </select>
      <input type="number" className="input" placeholder="Max Budget (AED)" value={filters.budget_max} onChange={e=>setFilters(p=>({...p,budget_max:e.target.value}))}/>
      <input type="number" className="input" placeholder="Bedrooms" value={filters.bedrooms} onChange={e=>setFilters(p=>({...p,bedrooms:e.target.value}))}/>
      <div className="flex gap-2">
        <button type="submit" className="btn-primary flex-1 justify-center" disabled={searching}>{searching?<span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin"/>:'🔍'}Search</button>
        <button type="button" onClick={handleReset} className="btn-secondary px-3">↺</button>
      </div>
    </div>
  </form>
  {loading?<div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"/></div>:(
  <>
    <p className="text-slate-400 text-sm mb-4">{properties.length} properties</p>
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      {properties.map(p=><Card key={p.id} p={p}/>)}
      {properties.length===0&&<div className="col-span-3 card text-center py-16"><div className="text-4xl mb-3">🏠</div><p className="text-slate-400">No properties match your filters.</p></div>}
    </div>
  </>
  )}
</div>
)}
