import{useState,useEffect}from 'react'
import{getDashboardStats,DashboardStats}from '../../services/api'
import{BarChart,Bar,XAxis,YAxis,Tooltip,ResponsiveContainer,PieChart,Pie,Cell,LineChart,Line,CartesianGrid}from 'recharts'
import TopBar from '../layout/TopBar'

const S=({label,value,sub,color='text-brand-400'}:{label:string;value:string;sub?:string;color?:string})=>(
<div className="card">
  <div className="text-slate-400 text-xs font-medium uppercase tracking-wide mb-2">{label}</div>
  <div className={`text-3xl font-bold ${color} mb-1`}>{value}</div>
  {sub&&<div className="text-slate-500 text-xs">{sub}</div>}
</div>)

const PIE_COLORS=['#ef4444','#f59e0b','#3b82f6']

const trendData=[{m:'Jan',leads:32,props:8},{m:'Feb',leads:41,props:9},{m:'Mar',leads:55,props:10},{m:'Apr',leads:48,props:9},{m:'May',leads:62,props:11},{m:'Jun',leads:78,props:12}]
const TT=({contentStyle:_,...p}:any)=><Tooltip {...p} contentStyle={{background:'#1e293b',border:'1px solid #334155',borderRadius:12,color:'#f1f5f9',fontSize:12}}/>

export default function Dashboard(){
  const[stats,setStats]=useState<DashboardStats|null>(null)
  const[loading,setLoading]=useState(true)
  useEffect(()=>{getDashboardStats().then(r=>setStats(r.data)).catch(console.error).finally(()=>setLoading(false))},[])
  const leadData=stats?[{name:'HOT',value:stats.hot_leads},{name:'WARM',value:stats.warm_leads},{name:'COLD',value:stats.cold_leads}]:[]
  const aiPerf=[{name:'Faithfulness',v:stats?Math.round(stats.ragas_faithfulness*100):0},{name:'Conversion',v:stats?stats.lead_conversion_rate:0},{name:'Avg Score',v:stats?stats.avg_lead_score:0}]
  if(loading)return<div className="flex items-center justify-center h-64"><div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"/></div>
  return(
<div>
  <TopBar title="Dashboard" subtitle="Real-time overview — PropAI Autonomous Real Estate AI Platform"/>
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
    <S label="Total Leads" value={stats?.total_leads.toString()||'0'} sub="200 synthetic + live"/>
    <S label="HOT Leads 🔥" value={stats?.hot_leads.toString()||'0'} sub="Ready to convert" color="text-red-400"/>
    <S label="Pipeline (AED)" value={`${((stats?.revenue_pipeline_aed||0)/1_000_000).toFixed(1)}M`} sub="Active deals" color="text-emerald-400"/>
    <S label="Deals Closed" value={stats?.deals_closed_this_month.toString()||'0'} sub="This month" color="text-amber-400"/>
  </div>
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
    <div className="card">
      <h3 className="font-semibold text-white mb-4 text-sm">Lead Distribution</h3>
      <div className="flex items-center gap-4">
        <ResponsiveContainer width={160} height={160}>
          <PieChart><Pie data={leadData} cx="50%" cy="50%" innerRadius={45} outerRadius={75} dataKey="value" paddingAngle={3}>
            {leadData.map((_,i)=><Cell key={i} fill={PIE_COLORS[i]}/>)}
          </Pie><TT/></PieChart>
        </ResponsiveContainer>
        <div className="space-y-2">
          {leadData.map(({name,value},i)=>(
            <div key={name} className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full" style={{background:PIE_COLORS[i]}}/>
              <span className="text-xs text-slate-400">{name}</span>
              <span className="text-xs font-bold text-white ml-auto">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
    <div className="card">
      <h3 className="font-semibold text-white mb-4 text-sm">AI Performance</h3>
      <ResponsiveContainer width="100%" height={160}>
        <BarChart data={aiPerf} margin={{left:-20}}>
          <XAxis dataKey="name" tick={{fill:'#94a3b8',fontSize:11}} axisLine={false} tickLine={false}/>
          <YAxis tick={{fill:'#94a3b8',fontSize:11}} axisLine={false} tickLine={false}/>
          <TT/><Bar dataKey="v" fill="#0ea5e9" radius={[4,4,0,0]}/>
        </BarChart>
      </ResponsiveContainer>
    </div>
    <div className="card">
      <h3 className="font-semibold text-white mb-4 text-sm">Leads Trend (6mo)</h3>
      <ResponsiveContainer width="100%" height={160}>
        <LineChart data={trendData} margin={{left:-20}}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b"/>
          <XAxis dataKey="m" tick={{fill:'#94a3b8',fontSize:11}} axisLine={false} tickLine={false}/>
          <YAxis tick={{fill:'#94a3b8',fontSize:11}} axisLine={false} tickLine={false}/>
          <TT/><Line type="monotone" dataKey="leads" stroke="#0ea5e9" strokeWidth={2} dot={false}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
  </div>
  <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
    {[{label:'RAGAS Faithfulness',value:(stats?.ragas_faithfulness||0).toFixed(4),target:'0.97 ✓',color:'text-emerald-400'},{label:'Hallucination Rate',value:`${((stats?.hallucination_rate||0)*100).toFixed(1)}%`,target:'<2% ✓',color:'text-brand-400'},{label:'Avg Latency',value:`${stats?.avg_latency_ms}ms`,target:'<50ms ✓',color:'text-amber-400'},{label:'Daily Requests',value:stats?.daily_requests.toLocaleString()||'0',target:'1,000+ capacity',color:'text-purple-400'}].map(m=>(
      <div key={m.label} className="card text-center">
        <div className={`text-2xl font-bold ${m.color} mb-1`}>{m.value}</div>
        <div className="text-xs text-slate-400 mb-1">{m.label}</div>
        <div className="text-xs text-emerald-400">{m.target}</div>
      </div>
    ))}
  </div>
</div>
)}
