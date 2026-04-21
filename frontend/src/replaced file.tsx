import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './components/dashboard/Dashboard'
import LeadScoring from './components/leads/LeadScoring'
import LeadsList from './components/leads/LeadsList'
import Properties from './components/properties/Properties'
import KnowledgeBase from './components/rag/KnowledgeBase'
import AgentChat from './components/rag/AgentChat'
import Evaluation from './components/evaluation/Evaluation'
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout/>}>
        <Route index element={<Dashboard/>}/>
        <Route path="leads" element={<LeadScoring/>}/>
        <Route path="leads/list" element={<LeadsList/>}/>
        <Route path="properties" element={<Properties/>}/>
        <Route path="rag" element={<KnowledgeBase/>}/>
        <Route path="agent" element={<AgentChat/>}/>
        <Route path="evaluation" element={<Evaluation/>}/>
      </Route>
    </Routes>
  )
}
