import axios from "axios";

export interface Container {
  id: string;
  name: string;
  status: string;
  image?: string[];
  ports?: Record<string, any>;
  labels?: Record<string, any>;
}

export async function fetchContainers(): Promise<Container[]> {
  const response = await axios.get<Container[]>("/api/containers");
  return response.data;
}
