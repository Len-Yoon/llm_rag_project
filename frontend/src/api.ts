// frontend/src/api.ts
import axios from "axios";

export type Source = {
  title?: string;
  url: string;
  preview?: string;
};

export type AskReq = {
  question: string;
  k?: number;
  fast?: boolean;
  conversation_id?: string | null;
};

export type AskRes =
  | { answer: string; contexts: Source[]; error?: string }
  | any;

const base = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export async function ask(body: AskReq): Promise<AskRes> {
  const { data } = await axios.post(`${base}/query`, body, { timeout: 60000 });
  return data;
}

export async function clearConversation(conversation_id?: string | null) {
  const { data } = await axios.post(`${base}/vector/clear`, { conversation_id }, { timeout: 15000 });
  return data;
}

export async function stats() {
  const { data } = await axios.get(`${base}/vector/stats`, { timeout: 10000 });
  return data;
}
