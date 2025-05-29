import axios from "axios";

export interface Container {
  id: string;
  name: string;
  status: string;
  image?: string[];
  ports?: Record<string, any>;
  labels?: Record<string, any>;
}

export interface ContainerActionResponse {
  container_id: string;
  action: string;
  result: {
    status: string;
    message: string;
  };
}

export interface ContainerLogsResponse {
  container_id: string;
  logs: string;
}

export async function fetchContainers(): Promise<Container[]> {
  const response = await axios.get<Container[]>("/api/containers");
  return response.data;
}

export async function fetchContainer(containerId: string): Promise<Container> {
  const response = await axios.get<Container>(`/api/containers/${containerId}`);
  return response.data;
}

export async function performContainerAction(
  containerId: string,
  action: "start" | "stop" | "restart"
): Promise<ContainerActionResponse> {
  const response = await axios.post<ContainerActionResponse>(
    `/api/containers/${containerId}/action`,
    { action }
  );
  return response.data;
}

export async function fetchContainerLogs(
  containerId: string
): Promise<ContainerLogsResponse> {
  const response = await axios.get<ContainerLogsResponse>(
    `/api/logs/${containerId}`
  );
  return response.data;
}

export async function fetchContainerMetrics(containerId: string): Promise<any> {
  const response = await axios.get(`/api/containers/${containerId}/metrics`);
  return response.data;
}
