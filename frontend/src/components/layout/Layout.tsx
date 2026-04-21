import{Outlet}from 'react-router-dom'
import Sidebar from './Sidebar'
export default function Layout(){return(
<div className="flex min-h-screen bg-slate-950">
  <Sidebar/>
  <main className="flex-1 ml-64 p-8 overflow-y-auto min-h-screen max-w-[calc(100vw-16rem)]"><Outlet/></main>
</div>
)}
