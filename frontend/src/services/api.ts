import axios from 'axios'
const api=axios.create({baseURL:'/api',timeout:60000})
api.interceptors.response.use(r=>r,err=>{console.error('API:',err.response?.data||err.message);return Promise.reject(err)})
export default api
export interface LeadScoreRequest{client_name:string;budget_aed:number;property_type?:string;location_preference?:string;bedrooms?:number;timeline_months?:number;num_interactions?:number;avg_response_hours?:number;message_quality_score?:number;source?:string}
export interface ShapFeature{feature:string;shap_value:number;direction:string}
export interface LeadScoreResponse{lead_id:string;client_name:string;score:number;tier:'HOT'|'WARM'|'COLD';budget_score:number;urgency_score:number;engagement_score:number;property_match_score:number;communication_score:number;recommended_action:string;reasoning:string;shap_top_features:ShapFeature[]}
export interface SampleLead{lead_id:string;client_name:string;budget_aed:number;property_type:string;location_preference:string;lead_score:number;tier:string;source:string;status:string;notes:string}
export interface Property{id:string;title:string;location:string;price:number;bedrooms:number;bathrooms:number;area_sqft:number;property_type:string;amenities:string[];status:string;images:string[];description:string;yield_pct:number;service_charge_yearly:number;match_score?:number;match_reasons?:string[]}
export interface RAGResponse{answer:string;sources:string[];confidence:number;answer_found_in_context:boolean;retrieved_chunks?:string[]}
export interface AgentResponse{session_id:string;input:string;output:any;intermediate_steps:any[];latency_ms:number;provider:string}
export interface DashboardStats{total_leads:number;hot_leads:number;warm_leads:number;cold_leads:number;total_properties:number;ragas_faithfulness:number;hallucination_rate:number;avg_latency_ms:number;daily_requests:number;lead_conversion_rate:number;avg_lead_score:number;revenue_pipeline_aed:number;deals_closed_this_month:number}
export const getHealth=()=>api.get('/health')
export const getDashboardStats=()=>api.get<DashboardStats>('/stats/dashboard')
export const scoreLead=(d:LeadScoreRequest)=>api.post<LeadScoreResponse>('/leads/score',d)
export const getSampleLeads=()=>api.get<{leads:SampleLead[],total:number}>('/leads/sample')
export const getAllProperties=()=>api.get<{properties:Property[]}>('/properties')
export const searchProperties=(d:any)=>api.post<{properties:Property[],returned:number}>('/properties/search',d)
export const getProperty=(id:string)=>api.get<Property>(`/properties/${id}`)
export const ragQuery=(question:string)=>api.post<RAGResponse>('/rag/query',{question})
export const listDocuments=()=>api.get('/rag/documents')
export const agentChat=(message:string,session_id?:string)=>api.post<AgentResponse>('/agent/chat',{message,session_id})
export const runRAGASEval=()=>api.get('/evaluation/ragas')
export const getMetrics=()=>api.get('/metrics')
