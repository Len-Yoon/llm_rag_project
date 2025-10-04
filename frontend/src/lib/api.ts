import axios from "axios";

const BASE =
  // 1) .env에 VITE_API_BASE가 있으면 그걸 쓰고
  import.meta.env.VITE_API_BASE ??
  // 2) 개발환경이면 Vite 프록시(/api) 경유
  (import.meta.env.DEV ? "/api" : "http://127.0.0.1:8000");

export const api = axios.create({
  baseURL: BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 120000,
});

// 백엔드 응답 타입
export type QueryContext = { title: string; url: string; preview: string };
export type QueryResponse = { answer: string; contexts: QueryContext[] };

export async function query(question: string, k = 4) {
  const { data } = await api.post<QueryResponse>("/query", { question, k });
  return data;
}
