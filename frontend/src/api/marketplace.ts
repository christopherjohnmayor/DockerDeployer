import axios from "axios";

// Type definitions matching backend models
export interface Template {
  id: number;
  name: string;
  description: string;
  author_id: number;
  category_id: number;
  version: string;
  docker_compose_yaml: string;
  tags: string[];
  status: "pending" | "approved" | "rejected";
  downloads: number;
  rating_avg: number;
  rating_count: number;
  approved_by?: number;
  approved_at?: string;
  rejection_reason?: string;
  created_at: string;
  updated_at: string;
  author_username?: string;
  category_name?: string;
}

export interface TemplateCreate {
  name: string;
  description: string;
  category_id: number;
  docker_compose_yaml: string;
  tags?: string[];
  version: string;
}

export interface TemplateUpdate {
  name?: string;
  description?: string;
  category_id?: number;
  docker_compose_yaml?: string;
  tags?: string[];
  version?: string;
}

export interface TemplateList {
  templates: Template[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface TemplateSearch {
  query?: string;
  category_id?: number;
  min_rating?: number;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  page?: number;
  per_page?: number;
}

export interface Category {
  id: number;
  name: string;
  description?: string;
  icon?: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  template_count?: number;
}

export interface Review {
  id: number;
  template_id: number;
  user_id: number;
  rating: number;
  comment?: string;
  created_at: string;
  updated_at: string;
  username?: string;
}

export interface ReviewCreate {
  rating: number;
  comment?: string;
}

export interface TemplateApproval {
  approved: boolean;
  rejection_reason?: string;
}

export interface MarketplaceStats {
  total_templates: number;
  approved_templates: number;
  pending_templates: number;
  rejected_templates: number;
  total_reviews: number;
  average_rating: number;
  total_downloads: number;
  top_categories: Array<{
    category_name: string;
    template_count: number;
  }>;
  recent_activity: Array<{
    action: string;
    template_name: string;
    timestamp: string;
  }>;
}

// API Client Functions
const API_BASE = "/api/marketplace";

// Template operations
export async function fetchTemplates(params: TemplateSearch = {}): Promise<TemplateList> {
  const response = await axios.get<TemplateList>(`${API_BASE}/templates`, { params });
  return response.data;
}

export async function fetchTemplate(id: number): Promise<Template> {
  const response = await axios.get<Template>(`${API_BASE}/templates/${id}`);
  return response.data;
}

export async function createTemplate(data: TemplateCreate): Promise<Template> {
  const response = await axios.post<Template>(`${API_BASE}/templates`, data);
  return response.data;
}

export async function updateTemplate(id: number, data: TemplateUpdate): Promise<Template> {
  const response = await axios.put<Template>(`${API_BASE}/templates/${id}`, data);
  return response.data;
}

export async function deleteTemplate(id: number): Promise<void> {
  await axios.delete(`${API_BASE}/templates/${id}`);
}

// Review operations
export async function fetchTemplateReviews(templateId: number): Promise<Review[]> {
  const response = await axios.get<Review[]>(`${API_BASE}/templates/${templateId}/reviews`);
  return response.data;
}

export async function createReview(templateId: number, data: ReviewCreate): Promise<Review> {
  const response = await axios.post<Review>(`${API_BASE}/templates/${templateId}/reviews`, data);
  return response.data;
}

// Category operations
export async function fetchCategories(): Promise<Category[]> {
  const response = await axios.get<Category[]>(`${API_BASE}/categories`);
  return response.data;
}

// Admin operations
export async function fetchPendingTemplates(): Promise<Template[]> {
  const response = await axios.get<Template[]>(`${API_BASE}/admin/pending`);
  return response.data;
}

export async function approveTemplate(id: number, data: TemplateApproval): Promise<Template> {
  const response = await axios.post<Template>(`${API_BASE}/admin/templates/${id}/approve`, data);
  return response.data;
}

export async function fetchMarketplaceStats(): Promise<MarketplaceStats> {
  const response = await axios.get<MarketplaceStats>(`${API_BASE}/admin/stats`);
  return response.data;
}

// User templates
export async function fetchMyTemplates(): Promise<Template[]> {
  const response = await axios.get<Template[]>(`${API_BASE}/my-templates`);
  return response.data;
}
