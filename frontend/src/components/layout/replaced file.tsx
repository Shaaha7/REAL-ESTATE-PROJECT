import{NavLink}from 'react-router-dom'
const nav=[{to:'/',label:'Dashboard',icon:'📊'},{to:'/leads',label:'Score a Lead',icon:'🎯'},{to:'/leads/list',label:'All Leads (200)',icon:'👥'},{to:'/properties',label:'Properties',icon:'🏠'},{to:'/rag',label:'Knowledge Base',icon:'📚'},{to:'/agent',label:'AI Agent Chat',icon:'🤖'},{to:'/evaluation',label:'RAGAS Evaluation',icon:'🧪'}]
export default function Sidebar(){return(
<aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-40">
  <div className="p-6 border-b border-slate-800">
    <div className="flex items-center gap-3">
      <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-brand-600 to-brand-800 flex items-center justify-center text-white font-black text-lg">P</div>
      <div><div className="font-bold text-white">PropAI</div><div className="text-xs text-slate-400">Real Estate AI Platform</div></div>
    </div>
  </div>
  <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
    {nav.map(({to,label,icon})=>(
      <NavLink key={to} to={to} end={to==='/'||to==='/leads'}
        className={({isActive})=>`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${isActive?'bg-brand-600 text-white shadow-lg':'text-slate-400 hover:text-slate-100 hover:bg-slate-800'}`}>
        <span>{icon}</span>{label}
      </NavLink>
    ))}
  </nav>
  <div className="p-4 border-t border-slate-800 space-y-1">
    <div className="text-xs text-slate-500 text-center">Gemini 1.5 Flash + LangChain</div>
    <div className="text-xs text-slate-600 text-center">FAISS · XGBoost · SHAP · RAGAS</div>
  </div>
</aside>
)}
